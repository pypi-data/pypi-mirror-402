"""
CDC Stream - Queue Manager
Manages alert-based queues for parallel event processing.
Each alert has its own queue and worker thread.
"""

from __future__ import annotations

import threading
from queue import Queue, Empty
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
import time

from rich import print as rprint


@dataclass
class QueueStats:
    """Statistics for a single queue."""
    events_received: int = 0
    events_processed: int = 0
    notifications_sent: int = 0
    errors: int = 0
    last_event_time: Optional[float] = None
    processing_time_total: float = 0.0

    @property
    def avg_processing_time(self) -> float:
        if self.events_processed == 0:
            return 0.0
        return self.processing_time_total / self.events_processed


class AlertQueue:
    """
    A queue for a specific alert with its own worker thread.
    Each alert processes events independently.
    Supports both tables and views.
    """

    def __init__(
        self,
        rule_id: int,
        rule_name: str,
        schema: str,
        table: str,
        processor: Callable[[dict, Any], int],
        get_rule: Callable[[], Any],
        object_type: str = 'table',
        base_tables: list = None,
        max_size: int = 10000
    ):
        """
        Initialize alert queue.

        Args:
            rule_id: Alert/Rule ID
            rule_name: Alert name for logging
            schema: Database schema name
            table: Table name (or view name)
            processor: Function to process events (event, rule) -> notifications_sent
            get_rule: Function to get the rule object
            object_type: 'table' or 'view'
            base_tables: For views, list of base tables [{'schema': 'x', 'table': 'y'}, ...]
            max_size: Maximum queue size
        """
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.schema = schema
        self.table = table
        self.object_type = object_type
        self.base_tables = base_tables or []
        self.key = f"alert_{rule_id}"
        self.queue: Queue = Queue(maxsize=max_size)
        self.processor = processor
        self.get_rule = get_rule

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stats = QueueStats()
        self._lock = threading.Lock()

    def matches_event(self, event: dict) -> bool:
        """Check if this alert should receive the event."""
        event_schema = event.get('schema', 'public')
        event_table = event.get('table', '')

        if self.object_type == 'view':
            # For views, check if event is from the single base table
            # Views with multiple base tables are not supported
            if self.base_tables and len(self.base_tables) == 1:
                bt = self.base_tables[0]
                bt_schema = bt.get('schema', 'public')
                bt_table = bt.get('table', '')
                return bt_table == event_table and (not bt_schema or bt_schema == event_schema)
            return False
        else:
            # Regular table matching
            # Schema match (empty schema = any schema)
            if self.schema and self.schema != event_schema:
                return False

            # Table must match
            if self.table != event_table:
                return False

            return True

    def put(self, event: dict) -> bool:
        """Add event to queue. Returns False if queue is full."""
        try:
            self.queue.put_nowait(event)
            with self._lock:
                self._stats.events_received += 1
                self._stats.last_event_time = time.time()
            return True
        except Exception:
            with self._lock:
                self._stats.errors += 1
            return False

    def _worker_loop(self):
        """Worker loop for this alert's queue."""
        rprint(f"[cyan]🔄 Worker started for alert '{self.rule_name}' (ID: {self.rule_id})[/]")

        while self._running:
            try:
                event = self.queue.get(timeout=1.0)
                start_time = time.time()

                # Get current rule state
                rule = self.get_rule()

                if rule and rule.is_active:
                    # Process event for this specific rule
                    notifications = self.processor(event, rule)

                    with self._lock:
                        self._stats.notifications_sent += notifications

                processing_time = time.time() - start_time

                with self._lock:
                    self._stats.events_processed += 1
                    self._stats.processing_time_total += processing_time

            except Empty:
                continue
            except Exception as e:
                rprint(f"[red]Worker error for alert {self.rule_id}: {e}[/]")
                with self._lock:
                    self._stats.errors += 1
                time.sleep(0.1)

        rprint(f"[yellow]🛑 Worker stopped for alert '{self.rule_name}'[/]")

    def start(self):
        """Start the worker thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._worker_loop,
            name=f"worker-alert-{self.rule_id}",
            daemon=True
        )
        self._thread.start()

    def stop(self):
        """Stop the worker thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def is_running(self) -> bool:
        return self._running and self._thread and self._thread.is_alive()

    def get_stats(self) -> dict:
        with self._lock:
            return {
                'rule_id': self.rule_id,
                'rule_name': self.rule_name,
                'schema': self.schema,
                'table': self.table,
                'key': self.key,
                'running': self.is_running(),
                'queue_size': self.queue.qsize(),
                'events_received': self._stats.events_received,
                'events_processed': self._stats.events_processed,
                'notifications_sent': self._stats.notifications_sent,
                'errors': self._stats.errors,
                'avg_processing_time_ms': round(self._stats.avg_processing_time * 1000, 2),
                'last_event_time': self._stats.last_event_time
            }


class QueueManager:
    """
    Manages alert-specific queues for parallel processing.

    Each alert has its own queue and worker thread.
    Events are broadcast to all matching alert queues.
    """

    def __init__(
        self,
        processor: Callable[[dict, Any], int],
        max_queue_size: int = 10000
    ):
        """
        Initialize queue manager.

        Args:
            processor: Function to process events (event, rule) -> notifications_sent
            max_queue_size: Maximum size per queue
        """
        self.processor = processor
        self.max_queue_size = max_queue_size

        self._queues: Dict[int, AlertQueue] = {}  # rule_id -> AlertQueue
        self._lock = threading.Lock()
        self._running = False

        # Global stats
        self._total_events = 0
        self._routed_events = 0
        self._dropped_events = 0

    def create_queue_for_alert(self, rule) -> AlertQueue:
        """Create a new queue for an alert (called when alert is created)."""
        rule_id = rule.id

        with self._lock:
            if rule_id in self._queues:
                rprint(f"[dim]Queue already exists for alert {rule_id}[/]")
                return self._queues[rule_id]

            def get_rule():
                try:
                    from api.models import Rule
                    return Rule.objects.prefetch_related(
                        'target_channels', 'datasource'
                    ).get(pk=rule_id)
                except Exception:
                    return None

            # Get object_type and base_tables
            object_type = getattr(rule, 'object_type', 'table') or 'table'
            base_tables = getattr(rule, 'base_tables', []) or []

            queue = AlertQueue(
                rule_id=rule_id,
                rule_name=rule.name,
                schema=rule.schema_name or 'public',
                table=rule.table_name,
                processor=self.processor,
                get_rule=get_rule,
                object_type=object_type,
                base_tables=base_tables,
                max_size=self.max_queue_size
            )
            self._queues[rule_id] = queue

            if self._running:
                queue.start()

            type_label = "view" if object_type == "view" else "table"
            rprint(f"[green]✨ Queue + Worker created for alert '{rule.name}' ({type_label}) (ID: {rule_id})[/]")

            if object_type == "view" and base_tables:
                base_str = ", ".join([f"{bt['schema']}.{bt['table']}" for bt in base_tables])
                rprint(f"[dim]   → Monitoring base tables: {base_str}[/]")

            return queue

    def delete_queue_for_alert(self, rule_id: int) -> bool:
        """Delete queue for an alert (called when alert is deleted)."""
        with self._lock:
            if rule_id not in self._queues:
                return False

            queue = self._queues[rule_id]
            queue.stop()
            del self._queues[rule_id]

            rprint(f"[yellow]🗑️ Queue + Worker deleted for alert ID: {rule_id}[/]")
            return True

    def update_queue_for_alert(self, rule) -> None:
        """Update queue when alert is modified."""
        rule_id = rule.id

        with self._lock:
            if rule_id in self._queues:
                old_queue = self._queues[rule_id]
                # Update schema/table info
                old_queue.schema = rule.schema_name or 'public'
                old_queue.table = rule.table_name
                old_queue.rule_name = rule.name
                old_queue.object_type = getattr(rule, 'object_type', 'table') or 'table'
                old_queue.base_tables = getattr(rule, 'base_tables', []) or []

    def has_queue(self, rule_id: int) -> bool:
        """Check if queue exists for an alert."""
        with self._lock:
            return rule_id in self._queues

    def route_event(self, event: dict) -> int:
        """
        Route an event to all matching alert queues.

        Args:
            event: CDC event with 'schema' and 'table' fields

        Returns:
            Number of queues the event was routed to
        """
        table = event.get('table', '')

        if not table:
            self._dropped_events += 1
            return 0

        self._total_events += 1
        routed_count = 0

        with self._lock:
            matching_queues = [
                q for q in self._queues.values()
                if q.matches_event(event)
            ]

        for queue in matching_queues:
            if queue.put(event):
                routed_count += 1
            else:
                self._dropped_events += 1
                rprint(f"[yellow]Queue full for alert {queue.rule_id}, event dropped![/]")

        if routed_count > 0:
            self._routed_events += 1

        return routed_count

    def start(self):
        """Start all queue workers."""
        self._running = True

        with self._lock:
            for queue in self._queues.values():
                if not queue.is_running():
                    queue.start()

        rprint(f"[green]🚀 Queue Manager started with {len(self._queues)} alert queue(s)[/]")

    def stop(self):
        """Stop all queue workers."""
        self._running = False

        with self._lock:
            for queue in self._queues.values():
                queue.stop()

        rprint(f"[yellow]🛑 Queue Manager stopped[/]")

    def get_queue_count(self) -> int:
        """Get number of active queues."""
        with self._lock:
            return len(self._queues)

    def get_all_stats(self) -> dict:
        """Get statistics for all queues."""
        with self._lock:
            queue_stats = {
                rule_id: queue.get_stats()
                for rule_id, queue in self._queues.items()
            }

        # Aggregate stats
        total_received = sum(q['events_received'] for q in queue_stats.values())
        total_processed = sum(q['events_processed'] for q in queue_stats.values())
        total_notifications = sum(q['notifications_sent'] for q in queue_stats.values())
        total_errors = sum(q['errors'] for q in queue_stats.values())

        return {
            'running': self._running,
            'queue_count': len(queue_stats),
            'total_events': self._total_events,
            'routed_events': self._routed_events,
            'dropped_events': self._dropped_events,
            'aggregate': {
                'events_received': total_received,
                'events_processed': total_processed,
                'notifications_sent': total_notifications,
                'errors': total_errors
            },
            'queues': queue_stats
        }

    def get_queue_for_alert(self, rule_id: int) -> Optional[AlertQueue]:
        """Get queue for a specific alert."""
        with self._lock:
            return self._queues.get(rule_id)


# Singleton instance
_queue_manager: Optional[QueueManager] = None


def get_queue_manager() -> Optional[QueueManager]:
    """Get the global queue manager instance."""
    return _queue_manager


def create_queue_manager(
    processor: Callable[[dict, Any], int]
) -> QueueManager:
    """Create and set the global queue manager."""
    global _queue_manager
    _queue_manager = QueueManager(processor)
    return _queue_manager


def initialize_queues_from_rules():
    """Initialize queues based on existing active rules."""
    global _queue_manager

    if not _queue_manager:
        return

    from .django_setup import setup_django_if_needed
    setup_django_if_needed()

    from api.models import Rule

    rules = Rule.objects.filter(is_active=True, table_name__isnull=False).exclude(table_name='')

    for rule in rules:
        _queue_manager.create_queue_for_alert(rule)

    rprint(f"[green]✅ Initialized {_queue_manager.get_queue_count()} queue(s) from existing alerts[/]")
