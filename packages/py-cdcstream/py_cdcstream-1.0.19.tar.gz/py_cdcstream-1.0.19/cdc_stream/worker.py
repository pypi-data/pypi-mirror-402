"""
CDC Stream - Worker
Processes CDC events from alert-based queues, evaluates rules, and sends notifications.
Each alert has its own queue and worker thread for parallel processing.
"""

from __future__ import annotations

import json
import time
import threading
from typing import Any, Mapping, Optional

from rich import print as rprint
from rich.console import Console

from .django_setup import setup_django_if_needed
from .dispatchers import SlackDispatcher, WebhookDispatcher, SmtpDispatcher, RestApiDispatcher
from .rules import RuleEngine
from .listener import MultiDatabaseListener
from .trigger_manager import TriggerManager, get_connection, ensure_postgres_triggers
from .queue_manager import (
    QueueManager,
    create_queue_manager,
    get_queue_manager,
    initialize_queues_from_rules
)
from .anomaly import anomaly_engine, AnomalyResult

console = Console()

# Global state
_worker_running = False
_queue_manager: Optional[QueueManager] = None
_multi_listener: Optional[MultiDatabaseListener] = None


def _broadcast_cdc_event(rule_id: int, event_data: dict):
    """Broadcast CDC event to the live stream queue for UI."""
    try:
        from api.views import add_cdc_event
        add_cdc_event(rule_id, event_data)
    except Exception as e:
        rprint(f"[red]❌ Failed to broadcast event: {e}[/]")


def _truncate_for_log(obj: Any, limit: int = 2000) -> Any:
    """Truncate object for logging."""
    try:
        raw = json.dumps(obj, ensure_ascii=False)
        if len(raw) <= limit:
            return obj
        return {"truncated": True, "preview": raw[:limit]}
    except Exception:
        return str(obj)[:limit]


def _compose_message(rule_name: str, data: Mapping[str, Any] | None, operation: str = "INSERT") -> str:
    """Compose notification message."""
    preview = _truncate_for_log(data or {}, 512)
    return f"[CDC Stream] {operation} matched rule: {rule_name}\nData: {json.dumps(preview, ensure_ascii=False, default=str)}"


def _ensure_triggers(datasources: list) -> dict:
    """Ensure CDC triggers are installed on all datasource tables and view base tables."""
    results = {'success': [], 'failed': [], 'views': []}

    for ds in datasources:
        config = ds.connector_config or {}
        if not config.get('host'):
            continue

        try:
            conn = get_connection(config)
            manager = TriggerManager(conn)

            # Get all active rules for this datasource
            from api.models import Rule
            rules = Rule.objects.filter(datasource=ds, is_active=True)

            for rule in rules:
                schema = rule.schema_name or 'public'
                table = rule.table_name
                object_type = getattr(rule, 'object_type', 'table') or 'table'

                if not table:
                    continue

                if object_type == 'view':
                    # For views, create trigger on the single base table
                    # Only views with 1 base table are supported
                    base_tables = getattr(rule, 'base_tables', []) or []

                    # If base_tables not stored, fetch them
                    if not base_tables:
                        base_tables = manager.get_view_base_tables(schema, table)
                        # Only save if exactly 1 base table
                        if len(base_tables) == 1:
                            rule.base_tables = base_tables
                            rule.save(update_fields=['base_tables'])

                    if len(base_tables) == 1:
                        bt = base_tables[0]
                        bt_schema = bt.get('schema', schema)
                        bt_table = bt.get('table', '')
                        if bt_table:
                            if manager.create_trigger(bt_schema, bt_table):
                                results['success'].append(f"{ds.name}:{bt_schema}.{bt_table}")
                                results['views'].append(f"{schema}.{table} -> {bt_schema}.{bt_table}")
                            else:
                                results['failed'].append(f"{ds.name}:{bt_schema}.{bt_table}")
                    elif len(base_tables) > 1:
                        rprint(f"[yellow]⚠️ View {schema}.{table} has {len(base_tables)} base tables, skipping (only single-table views supported)[/]")
                else:
                    # Regular table
                    if manager.create_trigger(schema, table):
                        results['success'].append(f"{ds.name}:{schema}.{table}")
                    else:
                        results['failed'].append(f"{ds.name}:{schema}.{table}")

            conn.close()
        except Exception as e:
            rprint(f"[red]Failed to setup triggers for {ds.name}: {e}[/]")
            results['failed'].append(f"{ds.name}: {str(e)}")

    return results


def _send_notification(channel, rule, event: dict, message: str):
    """Send notification through the appropriate channel (ManyToMany target_channels)."""
    from datetime import datetime
    config = channel.config or {}
    channel_type = channel.channel_type

    # Build event context for templates
    data = event.get('data', {})
    event_context = {
        'table': event.get('table', ''),
        'schema': event.get('schema', 'public'),
        'operation': event.get('operation', ''),
        'timestamp': event.get('timestamp', ''),
        'data': data,
        'old_data': event.get('old_data', {}),
        'alert_name': rule.name,  # Add alert name for {{alert_name}}
        'alert_description': getattr(rule, 'description', '') or '',  # Add description
        'triggered_at': datetime.now().isoformat(),  # Add trigger time
        'table_name': event.get('table', ''),
        'schema_name': event.get('schema', 'public'),
        'rule_name': rule.name,   # Alias
    }
    # Add data fields directly to context for easy access like {{field_name}}
    for key, value in data.items():
        if key not in event_context:  # Don't override system fields
            event_context[key] = value

    if channel_type == 'slack':
        result = SlackDispatcher.send(config, message, event_context)
        if not result.get('success'):
            raise Exception(result.get('error', 'Slack send failed'))

    elif channel_type == 'webhook':
        payload = {'rule': rule.name, 'data': data, 'message': message}
        result = WebhookDispatcher.send(config, payload, event_context)
        if not result.get('success'):
            raise Exception(result.get('error', 'Webhook send failed'))

    elif channel_type == 'smtp':
        result = SmtpDispatcher.send(config, f"[CDC Stream] {rule.name}", message, event_context)
        if not result.get('success'):
            raise Exception(result.get('error', 'SMTP send failed'))

    elif channel_type == 'rest_api':
        payload = {'rule': rule.name, 'data': data, 'message': message}
        result = RestApiDispatcher.send(config, payload, event_context)
        if not result.get('success'):
            raise Exception(result.get('error', 'REST API send failed'))

    else:
        rprint(f"[yellow]Unknown channel type: {channel_type}[/]")


def _send_inline_notification(channel_type: str, config: dict, rule, event: dict, message: str):
    """Send notification through an inline channel config (from JSON field)."""

    # Build event context for templates
    data = event.get('data', {})
    event_context = {
        'table': event.get('table', ''),
        'schema': event.get('schema', 'public'),
        'operation': event.get('operation', ''),
        'timestamp': event.get('timestamp', ''),
        'triggered_at': event.get('timestamp', ''),  # Alias for timestamp
        'data': data,
        'old_data': event.get('old_data', {}),
        'alert_name': rule.name,  # Add alert name for {{alert_name}}
        'alert_description': rule.description or '',  # Add alert description
        'rule_name': rule.name,   # Alias
        'rule_description': rule.description or '',   # Alias
        'table_name': event.get('table', ''),  # Alias for table
        'schema_name': event.get('schema', 'public'),  # Alias for schema
    }
    # Add data fields directly to context for easy access like {{field_name}}
    for key, value in data.items():
        if key not in event_context:  # Don't override system fields
            event_context[key] = value

    if channel_type == 'slack':
        result = SlackDispatcher.send(config, message, event_context)
        if not result.get('success'):
            raise Exception(result.get('error', 'Slack send failed'))

    elif channel_type == 'webhook':
        payload = {'rule': rule.name, 'data': event_context.get('data', {}), 'message': message}
        # Pass full event_context so system vars like alert_name, alert_description work
        result = WebhookDispatcher.send(config, payload, event_context)
        if not result.get('success'):
            raise Exception(result.get('error', 'Webhook send failed'))

    elif channel_type == 'email' or channel_type == 'smtp':
        # Pass event_data for template rendering
        result = SmtpDispatcher.send(config, f"[CDC Stream] {rule.name}", message, event_context)
        if not result.get('success'):
            raise Exception(result.get('error', 'SMTP send failed'))

    elif channel_type == 'rest_api':
        payload = {'rule': rule.name, 'data': event_context.get('data', {}), 'message': message}
        result = RestApiDispatcher.send(config, payload, event_context)
        if not result.get('success'):
            raise Exception(result.get('error', 'REST API send failed'))

    else:
        raise ValueError(f"Unknown channel type: {channel_type}")


def process_event_for_rule(event: dict, rule) -> int:
    """
    Process a single CDC event for a specific rule.
    This function is called by each alert's worker thread.

    Args:
        event: CDC event data
        rule: The specific rule to evaluate

    Returns:
        Number of notifications sent
    """
    notifications_sent = 0

    schema = event.get('schema', 'public')
    table = event.get('table', '')
    operation = event.get('operation', 'INSERT')
    data = event.get('data', {})

    # Only process INSERT operations (as per user requirement)
    if operation not in ('INSERT',):
        return 0

    # Track event status for UI
    final_status = "filter_passed"
    processing_stage = 4  # Done

    # Apply filters
    filters_config = rule.filters or []
    if filters_config:
        engine = RuleEngine()
        try:
            filters_pass = engine.evaluate_filters(filters_config, data)
        except Exception as e:
            rprint(f"[yellow]Filter error for rule {rule.name}: {e}[/]")
            filters_pass = False

        if not filters_pass:
            final_status = "filter_rejected"
            # Broadcast single event with final status
            _broadcast_cdc_event(rule.id, {
                'operation': operation,
                'schema': schema,
                'table': table,
                'data': _truncate_for_log(data, 500),
                'status': final_status,
                'processingStage': processing_stage,
                'timestamp': event.get('timestamp')
            })
            # Log filter_rejected status to TriggerLog
            from api.models import TriggerLog
            TriggerLog.objects.create(
                rule=rule,
                event={
                    'table': table,
                    'schema': schema,
                    'operation': operation,
                    'data': _truncate_for_log(data, 1000),
                    'timestamp': event.get('timestamp')
                },
                dispatch_results={'reason': 'filter_rejected'},
                status='filter_rejected'
            )
            return 0

    # Apply condition rules
    condition_config = rule.condition or {}
    if condition_config:
        engine = RuleEngine()
        try:
            condition_pass = engine.evaluate(condition_config, data)
            # Debug log for condition evaluation
            rprint(f"[dim]🔍 Rule '{rule.name}': condition_pass={condition_pass}, data keys={list(data.keys()) if data else 'None'}[/]")
            if 'salary_min' in data or 'salary_max' in data:
                rprint(f"[dim]   salary_min={data.get('salary_min')}, salary_max={data.get('salary_max')}[/]")
        except Exception as e:
            rprint(f"[yellow]Condition error for rule {rule.name}: {e}[/]")
            condition_pass = False

        if not condition_pass:
            final_status = "rule_rejected"
            # Broadcast single event with final status
            _broadcast_cdc_event(rule.id, {
                'operation': operation,
                'schema': schema,
                'table': table,
                'data': _truncate_for_log(data, 500),
                'status': final_status,
                'processingStage': processing_stage,
                'timestamp': event.get('timestamp')
            })
            # Log rule_rejected status to TriggerLog (filter passed but rule didn't match)
            from api.models import TriggerLog
            TriggerLog.objects.create(
                rule=rule,
                event={
                    'table': table,
                    'schema': schema,
                    'operation': operation,
                    'data': _truncate_for_log(data, 1000),
                    'timestamp': event.get('timestamp')
                },
                dispatch_results={'reason': 'rule_rejected'},
                status='rule_rejected'
            )
            return 0

    # All checks passed - send notifications
    final_status = "rule_matched"
    message = _compose_message(rule.name, data, operation)

    # Collect all dispatch results for a single TriggerLog entry
    all_dispatch_results = []
    has_success = False
    has_failure = False
    error_messages = []

    # Send to target_channels (ManyToMany)
    for channel in rule.target_channels.all():
        try:
            _send_notification(channel, rule, event, message)
            notifications_sent += 1
            has_success = True
            all_dispatch_results.append({
                'channel': channel.name,
                'channel_type': channel.channel_type,
                'status': 'success'
            })
            rprint(f"[green]✓ Alert '{rule.name}': {operation} on {schema}.{table} → {channel.name}[/]")

        except Exception as e:
            has_failure = True
            error_messages.append(f"{channel.name}: {str(e)}")
            all_dispatch_results.append({
                'channel': channel.name,
                'channel_type': channel.channel_type,
                'status': 'failed',
                'error': str(e)
            })
            rprint(f"[red]Notification failed ({channel.name}): {e}[/]")

    # Also send to notification_channels (JSON field - inline channels)
    inline_channels = rule.notification_channels or []
    for ch_config in inline_channels:
        ch_type = ch_config.get('channel_type', '')
        ch_name = ch_config.get('name', 'Inline Channel')
        config = ch_config.get('config', {})

        try:
            _send_inline_notification(ch_type, config, rule, event, message)
            notifications_sent += 1
            has_success = True
            all_dispatch_results.append({
                'channel': ch_name,
                'channel_type': ch_type,
                'status': 'success'
            })
            rprint(f"[green]✓ Alert '{rule.name}': {operation} on {schema}.{table} → {ch_name}[/]")
        except Exception as e:
            has_failure = True
            error_messages.append(f"{ch_name}: {str(e)}")
            all_dispatch_results.append({
                'channel': ch_name,
                'channel_type': ch_type,
                'status': 'failed',
                'error': str(e)
            })
            rprint(f"[red]Notification failed ({ch_name}): {e}[/]")

    # Determine final status
    if has_success and not has_failure:
        final_status = "notification_sent"
        log_status = "success"
    elif has_success and has_failure:
        final_status = "notification_sent"
        log_status = "partial"  # Some succeeded, some failed
    elif has_failure:
        final_status = "notification_failed"
        log_status = "failed"
    else:
        final_status = "rule_matched"
        log_status = "no_channels"  # No channels configured

    # Create a SINGLE TriggerLog entry for the entire event
    if all_dispatch_results:
        from api.models import TriggerLog
        TriggerLog.objects.create(
            rule=rule,
            event={
                'table': table,
                'schema': schema,
                'operation': operation,
                'data': _truncate_for_log(data, 2000),
                'timestamp': event.get('timestamp')
            },
            dispatch_results={'channels': all_dispatch_results},
            status=log_status,
            error_message='; '.join(error_messages) if error_messages else ""
        )

    # Broadcast final event with complete status
    _broadcast_cdc_event(rule.id, {
        'operation': operation,
        'schema': schema,
        'table': table,
        'data': _truncate_for_log(data, 500),
        'status': final_status,
        'processingStage': processing_stage,
        'timestamp': event.get('timestamp')
    })

    return notifications_sent


def process_event_for_anomaly_detector(event: dict, detector) -> bool:
    """
    Process a CDC event through an anomaly detector.
    Updates statistics and checks for anomalies.

    Args:
        event: CDC event data
        detector: AnomalyDetector model instance

    Returns:
        True if anomaly was detected, False otherwise
    """
    from api.models import AnomalyLog
    from django.utils import timezone

    schema = event.get('schema', 'public')
    table = event.get('table', '')
    operation = event.get('operation', 'INSERT')
    data = event.get('data', {})

    # Check operation filter
    if detector.operations and operation not in detector.operations:
        return False

    # Build detector config
    detector_config = {
        "id": detector.id,
        "algorithm": detector.algorithm,
        "parameters": detector.parameters,
        "target_columns": detector.target_columns,
    }

    # Get current model state
    model_state = detector.model_state or {}

    # Process event through anomaly engine
    try:
        result, updated_model_state = anomaly_engine.process_event(
            detector_config,
            {"data": data},
            model_state
        )
    except Exception as e:
        rprint(f"[red]❌ Anomaly detection error for {detector.name}: {e}[/]")
        return False

    # Update model state in database
    detector.model_state = updated_model_state
    detector.training_sample_count = sum(
        s.get("count", 0) for s in updated_model_state.get("field_stats", {}).values()
    ) // max(len(detector.target_columns), 1)
    detector.last_trained_at = timezone.now()
    detector.save(update_fields=["model_state", "training_sample_count", "last_trained_at"])

    # If anomaly detected, log and send notifications
    if result.is_anomaly:
        rprint(f"[red]🚨 ANOMALY DETECTED by '{detector.name}': score={result.score:.4f} (threshold={result.threshold:.4f})[/]")
        rprint(f"[yellow]   Anomaly fields: {result.anomaly_fields}[/]")
        rprint(f"[dim]   Data: {_truncate_for_log(data, 200)}[/]")

        # Create anomaly log
        anomaly_log = AnomalyLog.objects.create(
            detector=detector,
            event_data={
                'table': table,
                'schema': schema,
                'operation': operation,
                'data': _truncate_for_log(data, 2000),
                'timestamp': event.get('timestamp')
            },
            anomaly_score=result.score,
            anomaly_fields=result.anomaly_fields,
            threshold_used=result.threshold,
            dispatch_results={}
        )

        # Send notifications
        dispatch_results = []
        message = f"🚨 ANOMALY DETECTED by '{detector.name}'\n\nScore: {result.score:.4f} (threshold: {result.threshold:.4f})\nFields: {', '.join(result.anomaly_fields)}\nTable: {schema}.{table}\n\nData: {json.dumps(_truncate_for_log(data, 500), default=str)}"

        # Build event context for templates
        event_context = {
            'detector_name': detector.name,
            'algorithm': detector.algorithm,
            'anomaly_score': result.score,
            'threshold': result.threshold,
            'anomaly_fields': result.anomaly_fields,
            'schema': schema,
            'table': table,
            'operation': operation,
            'data': data,
            **data  # Add data fields directly
        }

        for channel in detector.target_channels.filter(is_active=True):
            ch_type = channel.channel_type
            ch_config = channel.config or {}

            try:
                if ch_type == 'slack':
                    result_dispatch = SlackDispatcher.send(ch_config, message, event_context)
                elif ch_type == 'webhook':
                    payload = {'detector': detector.name, 'anomaly_score': result.score, 'data': data}
                    result_dispatch = WebhookDispatcher.send(ch_config, payload, event_context)
                elif ch_type in ('email', 'smtp'):
                    result_dispatch = SmtpDispatcher.send(ch_config, f"🚨 Anomaly: {detector.name}", message, event_context)
                elif ch_type == 'rest_api':
                    payload = {'detector': detector.name, 'anomaly_score': result.score, 'data': data}
                    result_dispatch = RestApiDispatcher.send(ch_config, payload, event_context)
                else:
                    continue

                dispatch_results.append({
                    'channel': channel.name,
                    'type': ch_type,
                    'success': result_dispatch.get('success', False)
                })

            except Exception as e:
                dispatch_results.append({
                    'channel': channel.name,
                    'type': ch_type,
                    'success': False,
                    'error': str(e)
                })

        # Update anomaly log with dispatch results
        anomaly_log.dispatch_results = {'channels': dispatch_results}
        anomaly_log.save(update_fields=['dispatch_results'])

        return True

    return False


def start_listeners() -> MultiDatabaseListener:
    """Start listeners for all active PostgreSQL, MSSQL, and MySQL datasources."""
    global _queue_manager

    setup_django_if_needed()
    from api.models import DataSource
    from queue import Queue

    # Create a dummy queue - events will be routed by queue manager
    dummy_queue = Queue()
    multi_listener = MultiDatabaseListener(dummy_queue)

    # Listen to PostgreSQL datasources (CDC uses pg_notify)
    pg_datasources = DataSource.objects.filter(connector_type='postgres')
    for ds in pg_datasources:
        config = ds.connector_config or {}
        if config.get('host'):
            def on_event(event, ds_name=ds.name):
                # Route event to all matching alert queues
                if _queue_manager:
                    routed_count = _queue_manager.route_event(event)
                    if routed_count > 0:
                        rprint(f"[blue]📥 {ds_name}: {event.get('operation')} on {event.get('schema')}.{event.get('table')} → {routed_count} alert(s)[/]")

            multi_listener.add_datasource(ds.id, config, 'postgres', on_event)

    # Listen to MSSQL datasources (CDC uses polling cdc_events table)
    mssql_datasources = DataSource.objects.filter(connector_type='sqlserver')
    for ds in mssql_datasources:
        config = ds.connector_config or {}
        if config.get('host'):
            def on_event(event, ds_name=ds.name):
                # Route event to all matching alert queues
                if _queue_manager:
                    routed_count = _queue_manager.route_event(event)
                    if routed_count > 0:
                        rprint(f"[blue]📥 {ds_name} (MSSQL): {event.get('operation')} on {event.get('schema')}.{event.get('table')} → {routed_count} alert(s)[/]")

            multi_listener.add_datasource(ds.id, config, 'sqlserver', on_event)

    # Listen to MySQL datasources (CDC uses polling cdc_events table)
    mysql_datasources = DataSource.objects.filter(connector_type='mysql')
    for ds in mysql_datasources:
        config = ds.connector_config or {}
        if config.get('host'):
            def on_event(event, ds_name=ds.name):
                # Route event to all matching alert queues
                if _queue_manager:
                    routed_count = _queue_manager.route_event(event)
                    if routed_count > 0:
                        rprint(f"[blue]📥 {ds_name} (MySQL): {event.get('operation')} on {event.get('schema')}.{event.get('table')} → {routed_count} alert(s)[/]")

            multi_listener.add_datasource(ds.id, config, 'mysql', on_event)

    # Listen to MongoDB datasources (CDC uses Change Streams)
    mongodb_datasources = DataSource.objects.filter(connector_type='mongodb')
    for ds in mongodb_datasources:
        config = ds.connector_config or {}
        if config.get('host') or config.get('connection_string'):
            def on_event(event, ds_name=ds.name):
                # Route event to all matching alert queues
                if _queue_manager:
                    routed_count = _queue_manager.route_event(event)
                    if routed_count > 0:
                        rprint(f"[blue]📥 {ds_name} (MongoDB): {event.get('operation')} on {event.get('schema')}.{event.get('table')} → {routed_count} alert(s)[/]")

            multi_listener.add_datasource(ds.id, config, 'mongodb', on_event)

    return multi_listener


def run_worker() -> None:
    """
    Main entry point - starts listeners and workers.
    This is a blocking function that runs until interrupted.
    """
    global _worker_running, _queue_manager, _multi_listener

    setup_django_if_needed()

    # Run migrations
    try:
        from django.core.management import call_command
        call_command("migrate", interactive=False, verbosity=0)
    except Exception:
        pass

    from api.models import DataSource, Rule

    # Check for all datasources
    pg_datasources = list(DataSource.objects.filter(connector_type='postgres'))
    mssql_datasources = list(DataSource.objects.filter(connector_type='sqlserver'))
    mysql_datasources = list(DataSource.objects.filter(connector_type='mysql'))
    mongodb_datasources = list(DataSource.objects.filter(connector_type='mongodb'))
    all_datasources = pg_datasources + mssql_datasources + mysql_datasources + mongodb_datasources

    if not all_datasources:
        rprint("[yellow]⏳ No datasources configured. Waiting for connections...[/]")
        rprint("[dim]   Configure a database connection in the UI: http://localhost:5858[/]")
        # Keep running - will be restarted when datasources are added
        while True:
            time.sleep(5)
            pg_datasources = list(DataSource.objects.filter(connector_type='postgres'))
            mssql_datasources = list(DataSource.objects.filter(connector_type='sqlserver'))
            mysql_datasources = list(DataSource.objects.filter(connector_type='mysql'))
            mongodb_datasources = list(DataSource.objects.filter(connector_type='mongodb'))
            all_datasources = pg_datasources + mssql_datasources + mysql_datasources + mongodb_datasources
            if all_datasources:
                break

    if pg_datasources:
        rprint(f"[cyan]📡 Found {len(pg_datasources)} PostgreSQL datasource(s)[/]")
    if mssql_datasources:
        rprint(f"[cyan]📡 Found {len(mssql_datasources)} MSSQL datasource(s)[/]")
    if mysql_datasources:
        rprint(f"[cyan]📡 Found {len(mysql_datasources)} MySQL datasource(s)[/]")
    if mongodb_datasources:
        rprint(f"[cyan]📡 Found {len(mongodb_datasources)} MongoDB datasource(s)[/]")

    # Ensure PostgreSQL triggers are installed
    if pg_datasources:
        rprint("[cyan]🔧 Setting up PostgreSQL CDC triggers...[/]")
        trigger_results = _ensure_triggers(pg_datasources)
        if trigger_results['success']:
            rprint(f"[green]✅ PostgreSQL triggers installed: {', '.join(trigger_results['success'])}[/]")
        if trigger_results.get('views'):
            rprint(f"[blue]👁️ Views configured: {', '.join(trigger_results['views'])}[/]")
        if trigger_results['failed']:
            rprint(f"[yellow]⚠️ PostgreSQL trigger failures: {', '.join(trigger_results['failed'])}[/]")

    # Ensure MSSQL triggers are installed
    if mssql_datasources:
        rprint("[cyan]🔧 Setting up MSSQL CDC triggers...[/]")
        try:
            from .mssql_support import ensure_mssql_triggers
            for ds in mssql_datasources:
                mssql_results = ensure_mssql_triggers(ds)
                if mssql_results['success']:
                    rprint(f"[green]✅ MSSQL triggers for {ds.name}: {', '.join(mssql_results['success'])}[/]")
                if mssql_results['failed']:
                    rprint(f"[yellow]⚠️ MSSQL trigger failures for {ds.name}: {', '.join(mssql_results['failed'])}[/]")
        except ImportError as e:
            rprint(f"[yellow]⚠️ MSSQL support not available: {e}[/]")

    # Ensure MySQL triggers are installed
    if mysql_datasources:
        rprint("[cyan]🔧 Setting up MySQL CDC triggers...[/]")
        try:
            from .mysql_support import ensure_mysql_triggers
            for ds in mysql_datasources:
                mysql_results = ensure_mysql_triggers(ds)
                if mysql_results['success']:
                    rprint(f"[green]✅ MySQL triggers for {ds.name}: {', '.join(mysql_results['success'])}[/]")
                if mysql_results['failed']:
                    rprint(f"[yellow]⚠️ MySQL trigger failures for {ds.name}: {', '.join(mysql_results['failed'])}[/]")
        except ImportError as e:
            rprint(f"[yellow]⚠️ MySQL support not available: {e}[/]")

    # Check MongoDB replica set status (Change Streams require replica set)
    if mongodb_datasources:
        rprint("[cyan]🔧 Checking MongoDB Change Streams support...[/]")
        try:
            from .mongodb_support import check_replica_set
            for ds in mongodb_datasources:
                config = ds.connector_config or {}
                rs_status = check_replica_set(config)
                if rs_status.get('is_replica_set'):
                    rprint(f"[green]✅ MongoDB {ds.name}: Replica Set '{rs_status.get('set_name')}' with {rs_status.get('members')} member(s)[/]")
                else:
                    rprint(f"[yellow]⚠️ MongoDB {ds.name}: {rs_status.get('error', 'Not a replica set')}[/]")
                    rprint(f"[dim]   Change Streams require Replica Set. See docs for setup instructions.[/]")
        except ImportError as e:
            rprint(f"[yellow]⚠️ MongoDB support not available: {e}[/]")

    # Create queue manager with alert-based queues
    rprint("[cyan]📦 Initializing queue manager (per-alert threads)...[/]")
    _queue_manager = create_queue_manager(processor=process_event_for_rule)

    # Initialize queues from existing rules
    initialize_queues_from_rules()

    # Start queue manager
    _queue_manager.start()

    # Start listeners
    rprint("[cyan]🎧 Starting database listeners...[/]")
    _multi_listener = start_listeners()

    # Start daily log cleanup worker
    rprint("[cyan]🗑️ Starting daily log cleanup worker...[/]")
    from .daily_cleanup import start_daily_cleanup_worker
    start_daily_cleanup_worker()

    _worker_running = True

    try:
        rprint("\n[bold green]✅ CDC Stream is running![/]")
        rprint(f"[dim]   Active alert workers: {_queue_manager.get_queue_count()}[/]")
        rprint("[dim]   Each alert has its own thread for parallel processing[/]")
        rprint("[dim]   Listening for database changes...[/]")
        rprint("[dim]   Press Ctrl+C to stop[/]\n")

        # Keep main thread alive and periodically show stats
        last_stats_time = time.time()
        last_health_check = time.time()
        while _worker_running:
            time.sleep(1)

            # Health check listeners every 10 seconds
            if time.time() - last_health_check >= 10:
                try:
                    for ds_id, listener in list(_multi_listener.listeners.items()):
                        # Use ensure_running if available (MySQL, MSSQL, PostgreSQL listeners)
                        if hasattr(listener, 'ensure_running'):
                            listener.ensure_running()
                        # Fallback for listeners without ensure_running
                        elif hasattr(listener, '_thread') and listener._thread is not None:
                            if not listener._thread.is_alive():
                                rprint(f"[yellow]⚠️ Listener for datasource #{ds_id} died, restarting...[/]")
                                listener._running = False
                                time.sleep(0.5)
                                listener.start()
                        elif hasattr(listener, '_running') and not listener._running:
                            rprint(f"[yellow]⚠️ Listener for datasource #{ds_id} stopped, restarting...[/]")
                            listener.start()
                except Exception as e:
                    rprint(f"[red]❌ Health check error: {e}[/]")
                last_health_check = time.time()

            # Show stats every 60 seconds
            if time.time() - last_stats_time >= 60:
                stats = _queue_manager.get_all_stats()
                if stats['aggregate']['events_processed'] > 0:
                    rprint(f"[dim]📊 Stats: {stats['aggregate']['events_processed']} events, "
                           f"{stats['aggregate']['notifications_sent']} notifications, "
                           f"{stats['queue_count']} alert workers[/]")
                last_stats_time = time.time()

    except KeyboardInterrupt:
        rprint("\n[yellow]⏹️ Shutting down...[/]")
    finally:
        _worker_running = False
        if _multi_listener:
            _multi_listener.stop_all()
        if _queue_manager:
            _queue_manager.stop()
        # Stop daily cleanup worker
        from .daily_cleanup import stop_daily_cleanup_worker
        stop_daily_cleanup_worker()


def stop_worker():
    """Stop the worker."""
    global _worker_running, _queue_manager, _multi_listener
    _worker_running = False
    if _multi_listener:
        _multi_listener.stop_all()
    if _queue_manager:
        _queue_manager.stop()


# ============================================
# Queue Management API (called from Django signals)
# ============================================

def on_rule_created(rule) -> None:
    """
    Called when a new rule/alert is created.
    Creates a queue and worker thread for the alert.
    """
    global _queue_manager

    if not _queue_manager:
        return

    if not rule.table_name:
        return

    _queue_manager.create_queue_for_alert(rule)


def on_rule_deleted(rule_id: int) -> None:
    """
    Called when a rule/alert is deleted.
    Stops the worker thread and deletes the queue.
    """
    global _queue_manager

    if not _queue_manager:
        return

    _queue_manager.delete_queue_for_alert(rule_id)


def on_rule_updated(rule) -> None:
    """
    Called when a rule is updated.
    Updates the queue configuration.
    """
    global _queue_manager

    if not _queue_manager:
        return

    if not rule.table_name:
        # Table removed - delete queue
        _queue_manager.delete_queue_for_alert(rule.id)
    elif _queue_manager.has_queue(rule.id):
        # Update existing queue
        _queue_manager.update_queue_for_alert(rule)
    else:
        # Table added - create queue
        _queue_manager.create_queue_for_alert(rule)


def get_worker_stats() -> dict:
    """Get worker statistics."""
    global _queue_manager, _worker_running

    if not _queue_manager:
        return {'running': False, 'queue_count': 0}

    stats = _queue_manager.get_all_stats()
    stats['worker_running'] = _worker_running

    # Add daily cleanup worker stats
    try:
        from .daily_cleanup import get_daily_cleanup_stats
        stats['daily_cleanup'] = get_daily_cleanup_stats()
    except ImportError:
        stats['daily_cleanup'] = None

    return stats


# For backwards compatibility
def run_kafka_worker(bootstrap_servers: str | None = None, group_id: str | None = None) -> None:
    """Legacy Kafka worker - deprecated."""
    rprint("[yellow]⚠️ Kafka worker is deprecated. Use run_worker() instead.[/]")
    run_worker()
