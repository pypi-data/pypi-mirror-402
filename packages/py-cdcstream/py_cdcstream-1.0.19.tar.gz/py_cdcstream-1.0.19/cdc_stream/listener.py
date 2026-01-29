"""
CDC Stream - Multi-Database Listener
Manages event polling for PostgreSQL, MSSQL, and MySQL.
All databases use the same polling approach with cdc_events table.
"""

import json
import threading
import time
from queue import Queue, Empty
from typing import Callable, Optional, Any


class MultiDatabaseListener:
    """
    Manages listeners for multiple database connections.
    Supports PostgreSQL, MSSQL, and MySQL - all using polling approach.
    """

    def __init__(self, event_queue: Queue):
        """
        Initialize multi-database listener.

        Args:
            event_queue: Shared queue for all events
        """
        self.queue = event_queue
        self.listeners: dict[int, Any] = {}  # datasource_id -> listener
        self.listener_types: dict[int, str] = {}  # datasource_id -> connector type

    def add_datasource(self, datasource_id: int, config: dict, connector_type: str = 'postgres', on_event: Callable = None):
        """Add a new datasource to listen to."""
        if datasource_id in self.listeners:
            self.remove_datasource(datasource_id)

        listener = None

        if connector_type == 'postgres':
            # Use PostgreSQL Listener (polling cdc_events - same as MSSQL/MySQL)
            try:
                from .trigger_manager import PostgreSQLListener
                listener = PostgreSQLListener(config, self.queue, on_event, poll_interval=1.0, datasource_id=datasource_id)
                print(f"📡 Added PostgreSQL listener for datasource #{datasource_id}")
            except ImportError as e:
                print(f"❌ PostgreSQL support not available: {e}")
                return

        elif connector_type == 'sqlserver':
            # Use MSSQL Listener
            try:
                from .mssql_support import MSSQLListener
                listener = MSSQLListener(config, self.queue, on_event, poll_interval=1.0, datasource_id=datasource_id)
                print(f"📡 Added MSSQL listener for datasource #{datasource_id}")
            except ImportError as e:
                print(f"❌ MSSQL support not available: {e}")
                return

        elif connector_type == 'mysql':
            # Use MySQL Listener
            try:
                from .mysql_support import MySQLListener
                listener = MySQLListener(config, self.queue, on_event, poll_interval=1.0, datasource_id=datasource_id)
                print(f"📡 Added MySQL listener for datasource #{datasource_id}")
            except ImportError as e:
                print(f"❌ MySQL support not available: {e}")
                return

        elif connector_type == 'mongodb':
            # Use MongoDB Change Stream Listener
            try:
                from .mongodb_support import MongoDBListener
                # Get watch database from config
                watch_db = config.get('database', '')
                listener = MongoDBListener(
                    config,
                    self.queue,
                    on_event,
                    poll_interval=1.0,
                    datasource_id=datasource_id,
                    watch_database=watch_db
                )
                print(f"📡 Added MongoDB listener for datasource #{datasource_id}")
            except ImportError as e:
                print(f"❌ MongoDB support not available: {e}")
                return

        else:
            print(f"⚠️ Unsupported connector type: {connector_type}")
            return

        if listener:
            self.listeners[datasource_id] = listener
            self.listener_types[datasource_id] = connector_type
            listener.start()

    def remove_datasource(self, datasource_id: int):
        """Remove a datasource listener."""
        if datasource_id in self.listeners:
            self.listeners[datasource_id].stop()
            del self.listeners[datasource_id]
            if datasource_id in self.listener_types:
                del self.listener_types[datasource_id]
            print(f"📴 Removed listener for datasource #{datasource_id}")

    def start_all(self):
        """Start all listeners."""
        for listener in self.listeners.values():
            if not listener.is_running():
                listener.start()

    def stop_all(self):
        """Stop all listeners."""
        for listener in self.listeners.values():
            listener.stop()
        self.listeners.clear()

    def get_all_stats(self) -> dict:
        """Get stats for all listeners."""
        return {
            ds_id: listener.get_stats()
            for ds_id, listener in self.listeners.items()
        }


# Standalone listener for testing
def run_standalone_listener(config: dict, connector_type: str = 'postgres'):
    """Run a standalone listener for testing."""
    from queue import Queue

    event_queue = Queue()

    def on_event(event):
        print(f"📥 Event: {event['operation']} on {event['schema']}.{event['table']}")
        print(f"   Data: {json.dumps(event.get('data', {}), indent=2, default=str)[:200]}")

    multi = MultiDatabaseListener(event_queue)
    multi.add_datasource(1, config, connector_type, on_event)

    try:
        print(f"\n🎧 Listening for {connector_type} changes... Press Ctrl+C to stop\n")

        while True:
            try:
                event = event_queue.get(timeout=1)
                # Event is already printed by on_event callback
            except Empty:
                continue

    except KeyboardInterrupt:
        print("\n⏹️ Stopping...")
    finally:
        multi.stop_all()


if __name__ == "__main__":
    # Test with default PostgreSQL connection
    config = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'postgres',
        'database': 'postgres'
    }
    run_standalone_listener(config, 'postgres')
