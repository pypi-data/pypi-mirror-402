"""
CDC Stream - Trigger Manager
Automatically creates and manages PostgreSQL triggers for CDC.
Uses cdcstream_cdc_events table as temporary buffer (same as MSSQL/MySQL).
Events are deleted immediately after processing.
"""

import json
import threading
import time
from typing import Optional, Callable, List, Dict, Any
from queue import Queue


# ============================================================================
# SQL Templates for PostgreSQL
# ============================================================================

# Create cdcstream_cdc_events table (temporary buffer - events deleted after processing)
CREATE_CDC_EVENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS cdcstream_cdc_events (
    id BIGSERIAL PRIMARY KEY,
    table_schema VARCHAR(128) DEFAULT 'public',
    table_name VARCHAR(128) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    row_data JSONB,
    old_row_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cdcstream_cdc_events_created ON cdcstream_cdc_events(created_at);
"""

# Trigger function that writes to cdcstream_cdc_events table
CDC_CAPTURE_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION cdc_stream_capture()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO cdcstream_cdc_events (table_schema, table_name, operation, row_data, old_row_data)
    VALUES (
        TG_TABLE_SCHEMA,
        TG_TABLE_NAME,
        TG_OP,
        CASE TG_OP
            WHEN 'DELETE' THEN NULL
            ELSE to_jsonb(NEW)
        END,
        CASE TG_OP
            WHEN 'INSERT' THEN NULL
            ELSE to_jsonb(OLD)
        END
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;
"""

CREATE_TRIGGER_SQL = """
DROP TRIGGER IF EXISTS {trigger_name} ON {schema}.{table};
CREATE TRIGGER {trigger_name}
AFTER {operations} ON {schema}.{table}
FOR EACH ROW EXECUTE FUNCTION cdc_stream_capture();
"""

DROP_TRIGGER_SQL = """
DROP TRIGGER IF EXISTS {trigger_name} ON {schema}.{table};
"""

CHECK_TRIGGER_EXISTS_SQL = """
SELECT EXISTS (
    SELECT 1 FROM pg_trigger t
    JOIN pg_class c ON t.tgrelid = c.oid
    JOIN pg_namespace n ON c.relnamespace = n.oid
    WHERE t.tgname = %s
    AND c.relname = %s
    AND n.nspname = %s
);
"""

CHECK_FUNCTION_EXISTS_SQL = """
SELECT EXISTS (
    SELECT 1 FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE p.proname = 'cdc_stream_capture'
    AND n.nspname = 'public'
);
"""

LIST_CDC_TRIGGERS_SQL = """
SELECT
    n.nspname as schema_name,
    c.relname as table_name,
    t.tgname as trigger_name
FROM pg_trigger t
JOIN pg_class c ON t.tgrelid = c.oid
JOIN pg_namespace n ON c.relnamespace = n.oid
WHERE t.tgname LIKE 'cdc_stream_%'
AND NOT t.tgisinternal;
"""

GET_UNPROCESSED_EVENTS_SQL = """
SELECT id, table_schema, table_name, operation, row_data, old_row_data, created_at
FROM cdcstream_cdc_events
ORDER BY id ASC
LIMIT 100;
"""

DELETE_PROCESSED_EVENTS_SQL = """
DELETE FROM cdcstream_cdc_events WHERE id = ANY(%s);
"""

# SQL to get base tables of a view
GET_VIEW_DEPENDENCIES_SQL = """
SELECT DISTINCT
    vcu.table_schema,
    vcu.table_name
FROM information_schema.view_column_usage vcu
WHERE vcu.view_schema = %s
AND vcu.view_name = %s;
"""


class TriggerManager:
    """Manages CDC triggers on PostgreSQL tables."""

    def __init__(self, connection):
        """
        Initialize TriggerManager with a database connection.

        Args:
            connection: psycopg2 connection object
        """
        self.conn = connection
        self.conn.autocommit = True
        self._ensure_cdcstream_cdc_events_table()

    def _ensure_cdcstream_cdc_events_table(self):
        """Create cdcstream_cdc_events table if it doesn't exist."""
        try:
            with self.conn.cursor() as cur:
                cur.execute(CREATE_CDC_EVENTS_TABLE_SQL)
        except Exception as e:
            print(f"⚠️ Could not create cdcstream_cdc_events table: {e}")

    def _get_trigger_name(self, schema: str, table: str) -> str:
        """Generate trigger name for a table."""
        return f"cdc_stream_{schema}_{table}"

    def _format_permission_error(self, error: Exception, operation: str) -> str:
        """Format permission errors with helpful guidance."""
        error_str = str(error).lower()

        # Check for common permission error patterns
        if any(keyword in error_str for keyword in ['permission denied', 'access denied', 'privilege', 'denied']):
            return f"""
❌ PERMISSION ERROR: {operation}

Your database user does not have sufficient privileges.

🔧 SOLUTION - Run the following SQL for PostgreSQL:
   GRANT USAGE, CREATE ON SCHEMA public TO your_user;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO your_user;

📝 Or connect using an existing admin/superuser account.

Original error: {error}
"""
        return str(error)

    def ensure_capture_function(self) -> bool:
        """
        Ensure the CDC capture function exists and is up-to-date.
        Always recreates to ensure correct table name (cdcstream_cdc_events).

        Returns:
            bool: True if function exists or was created successfully
        """
        try:
            with self.conn.cursor() as cur:
                # Always create/update function (CREATE OR REPLACE handles existing)
                cur.execute(CDC_CAPTURE_FUNCTION_SQL)
                print("✅ CDC capture function created/updated")
                return True
        except Exception as e:
            error_msg = self._format_permission_error(e, "CDC fonksiyonu oluşturulamadı")
            print(error_msg)
            return False

    def create_trigger(
        self,
        schema: str,
        table: str,
        operations: list[str] = None
    ) -> bool:
        """
        Create a CDC trigger on a table.

        Args:
            schema: Database schema name
            table: Table name
            operations: List of operations to track ['INSERT', 'UPDATE', 'DELETE']

        Returns:
            bool: True if trigger was created successfully
        """
        if operations is None:
            operations = ['INSERT', 'UPDATE', 'DELETE']

        # Ensure capture function exists
        if not self.ensure_capture_function():
            return False

        trigger_name = self._get_trigger_name(schema, table)
        operations_str = ' OR '.join(operations)

        try:
            with self.conn.cursor() as cur:
                sql = CREATE_TRIGGER_SQL.format(
                    trigger_name=trigger_name,
                    schema=schema,
                    table=table,
                    operations=operations_str
                )
                cur.execute(sql)
                print(f"✅ Trigger '{trigger_name}' created on {schema}.{table}")
                return True
        except Exception as e:
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['permission denied', 'access denied', 'privilege', 'denied']):
                print(f"""
❌ PERMISSION ERROR: Cannot create trigger on {schema}.{table}

Your database user does not have TRIGGER creation privileges.

🔧 SOLUTION - For PostgreSQL:
   GRANT CREATE ON SCHEMA {schema} TO your_user;

📝 Or connect using an existing admin/superuser account.

Original error: {e}
""")
            else:
                print(f"❌ Failed to create trigger on {schema}.{table}: {e}")
            return False

    def drop_trigger(self, schema: str, table: str) -> bool:
        """Drop a CDC trigger from a table."""
        trigger_name = self._get_trigger_name(schema, table)

        try:
            with self.conn.cursor() as cur:
                sql = DROP_TRIGGER_SQL.format(
                    trigger_name=trigger_name,
                    schema=schema,
                    table=table
                )
                cur.execute(sql)
                print(f"✅ Trigger '{trigger_name}' dropped from {schema}.{table}")
                return True
        except Exception as e:
            print(f"❌ Failed to drop trigger from {schema}.{table}: {e}")
            return False

    def trigger_exists(self, schema: str, table: str) -> bool:
        """Check if a CDC trigger exists on a table."""
        trigger_name = self._get_trigger_name(schema, table)

        try:
            with self.conn.cursor() as cur:
                cur.execute(CHECK_TRIGGER_EXISTS_SQL, (trigger_name, table, schema))
                return cur.fetchone()[0]
        except Exception as e:
            print(f"❌ Failed to check trigger existence: {e}")
            return False

    def list_triggers(self) -> list[dict]:
        """List all CDC Stream triggers in the database."""
        try:
            with self.conn.cursor() as cur:
                cur.execute(LIST_CDC_TRIGGERS_SQL)
                rows = cur.fetchall()
                return [
                    {
                        'schema': row[0],
                        'table': row[1],
                        'trigger_name': row[2]
                    }
                    for row in rows
                ]
        except Exception as e:
            print(f"❌ Failed to list triggers: {e}")
            return []

    def get_view_base_tables(self, schema: str, view_name: str) -> list[dict]:
        """Get the base tables that a view depends on."""
        try:
            with self.conn.cursor() as cur:
                cur.execute(GET_VIEW_DEPENDENCIES_SQL, (schema, view_name))
                rows = cur.fetchall()
                return [{'schema': row[0], 'table': row[1]} for row in rows]
        except Exception as e:
            print(f"❌ Failed to get view dependencies: {e}")
            return []

    def create_triggers_for_view(
        self,
        schema: str,
        view_name: str,
        operations: list[str] = None
    ) -> dict:
        """Create CDC triggers on all base tables of a view."""
        result = {'base_tables': [], 'success': [], 'failed': []}

        base_tables = self.get_view_base_tables(schema, view_name)
        result['base_tables'] = base_tables

        if not base_tables:
            print(f"⚠️ No base tables found for view {schema}.{view_name}")
            return result

        if not self.ensure_capture_function():
            result['failed'] = [f"{t['schema']}.{t['table']}" for t in base_tables]
            return result

        for bt in base_tables:
            if self.create_trigger(bt['schema'], bt['table'], operations):
                result['success'].append(f"{bt['schema']}.{bt['table']}")
            else:
                result['failed'].append(f"{bt['schema']}.{bt['table']}")

        print(f"✅ View '{schema}.{view_name}' -> triggers on: {result['success']}")
        return result


class PostgreSQLListener:
    """
    Polls cdcstream_cdc_events table for new events and pushes them to a queue.
    Events are deleted immediately after processing (no data left in user's DB).
    Same architecture as MSSQL/MySQL for consistency.
    """

    def __init__(
        self,
        connection_config: dict,
        event_queue: Queue,
        on_event: Optional[Callable] = None,
        poll_interval: float = 1.0,
        datasource_id: int = None
    ):
        self.config = connection_config
        self.queue = event_queue
        self.on_event = on_event
        self.poll_interval = poll_interval
        self.datasource_id = datasource_id

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._conn = None
        self._stats = {
            'events_received': 0,
            'errors': 0,
            'reconnects': 0,
            'last_event_time': None
        }

    def _connect(self) -> bool:
        """Establish connection to PostgreSQL."""
        try:
            import psycopg2
            self._conn = psycopg2.connect(
                host=self.config.get('host', 'localhost'),
                port=int(self.config.get('port', 5432)),
                user=self.config.get('user', 'postgres'),
                password=self.config.get('password', ''),
                dbname=self.config.get('database', 'postgres'),
                connect_timeout=10
            )
            self._conn.autocommit = True
            return True
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            self._stats['errors'] += 1
            return False

    def _disconnect(self):
        """Close the database connection."""
        if self._conn:
            try:
                self._conn.close()
            except:
                pass
            self._conn = None

    def _poll_events(self) -> List[Dict[str, Any]]:
        """Poll for events and delete them immediately."""
        events = []
        try:
            with self._conn.cursor() as cursor:
                cursor.execute(GET_UNPROCESSED_EVENTS_SQL)
                rows = cursor.fetchall()
                event_ids = []

                for row in rows:
                    event_id = row[0]
                    event_ids.append(event_id)

                    # Parse data (JSONB comes as dict in psycopg2)
                    row_data = row[4] if row[4] else None
                    old_row_data = row[5] if row[5] else None

                    event = {
                        'id': event_id,
                        'schema': row[1] or 'public',
                        'table': row[2],
                        'operation': row[3],
                        'data': row_data,
                        'old_data': old_row_data,
                        'timestamp': str(row[6]) if row[6] else None
                    }
                    events.append(event)

                # Delete processed events immediately (no data left in user's DB)
                if event_ids:
                    cursor.execute(DELETE_PROCESSED_EVENTS_SQL, (event_ids,))

        except Exception as e:
            error_str = str(e).lower()
            if any(kw in error_str for kw in ['permission denied', 'access denied', 'privilege']):
                print(f"""
❌ PERMISSION ERROR: Cannot read events from cdcstream_cdc_events

Your database user's permissions may have been revoked.

🔧 SOLUTION: Run in PostgreSQL:
   GRANT SELECT, DELETE ON cdcstream_cdc_events TO your_user;

Original error: {e}
""")
                # Log to TriggerLog for UI visibility
                try:
                    import django
                    django.setup()
                    from api.models import TriggerLog, Rule
                    rules = Rule.objects.filter(datasource_id=self.datasource_id, is_active=True)
                    for rule in rules:
                        TriggerLog.objects.create(
                            rule=rule,
                            event={'error': 'polling_permission_denied'},
                            dispatch_results={},
                            status='failed',
                            error_message=f"Permission denied: Cannot read events. Check database user permissions. Error: {e}"
                        )
                except Exception:
                    pass
            else:
                print(f"❌ PostgreSQL poll error: {e}")

            self._stats['errors'] += 1
            self._disconnect()
            time.sleep(2)
            self._connect()

        return events

    def _listen_loop(self):
        """Main polling loop."""
        while self._running:
            if not self._conn:
                if not self._connect():
                    time.sleep(5)
                    self._stats['reconnects'] += 1
                    continue

            events = self._poll_events()

            for event in events:
                self._stats['events_received'] += 1
                self._stats['last_event_time'] = time.time()

                # Push to queue
                self.queue.put(event)

                # Callback if provided
                if self.on_event:
                    try:
                        self.on_event(event)
                    except Exception as e:
                        print(f"❌ Event callback error: {e}")

            # Sleep between polls
            time.sleep(self.poll_interval)

    def start(self):
        """Start the listener in a background thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print(f"🟢 PostgreSQL Listener started (polling every {self.poll_interval}s)")

    def stop(self):
        """Stop the listener."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self._disconnect()
        print("🔴 PostgreSQL Listener stopped")

    def ensure_running(self):
        """Check if listener thread is alive, restart if needed."""
        if not self._running:
            return False

        if self._thread is None or not self._thread.is_alive():
            print(f"⚠️ PostgreSQL Listener thread died, restarting...")
            self._stats['reconnects'] += 1
            self._running = False  # Reset first
            time.sleep(1)
            self.start()
            return True
        return True

    def is_running(self) -> bool:
        return self._running and self._thread and self._thread.is_alive()

    def get_stats(self) -> dict:
        return {
            **self._stats,
            'running': self.is_running(),
            'connected': self._conn is not None
        }


def get_connection(config: dict):
    """Create a PostgreSQL connection from config."""
    import psycopg2

    return psycopg2.connect(
        host=config.get('host', 'localhost'),
        port=int(config.get('port', 5432)),
        user=config.get('user', 'postgres'),
        password=config.get('password', ''),
        dbname=config.get('database', 'postgres'),
        connect_timeout=10
    )


def ensure_postgres_triggers(datasource) -> dict:
    """Ensure CDC triggers are installed for all rules using this PostgreSQL datasource."""
    results = {'success': [], 'failed': [], 'views': []}
    config = datasource.connector_config or {}

    if datasource.connector_type != 'postgres':
        return results

    try:
        conn = get_connection(config)
        manager = TriggerManager(conn)

        from api.models import Rule
        rules = Rule.objects.filter(datasource=datasource, is_active=True)

        for rule in rules:
            schema = rule.schema_name or 'public'
            table = rule.table_name
            object_type = getattr(rule, 'object_type', 'table') or 'table'

            if not table:
                continue

            if object_type == 'view':
                base_tables = getattr(rule, 'base_tables', []) or []
                if not base_tables:
                    base_tables = manager.get_view_base_tables(schema, table)

                if len(base_tables) == 1:
                    bt = base_tables[0]
                    bt_schema = bt.get('schema', schema)
                    bt_table = bt.get('table', '')
                    if bt_table:
                        if manager.create_trigger(bt_schema, bt_table):
                            results['success'].append(f"{bt_schema}.{bt_table}")
                            results['views'].append(f"{schema}.{table} -> {bt_schema}.{bt_table}")
                        else:
                            results['failed'].append(f"{bt_schema}.{bt_table}")
            else:
                if manager.create_trigger(schema, table):
                    results['success'].append(f"{schema}.{table}")
                else:
                    results['failed'].append(f"{schema}.{table}")

        conn.close()

    except Exception as e:
        print(f"❌ PostgreSQL trigger setup error: {e}")
        results['failed'].append(str(e))

    return results


# Convenience functions
def install_trigger(config: dict, schema: str, table: str, operations: list[str] = None) -> bool:
    """Install a CDC trigger on a table."""
    conn = get_connection(config)
    try:
        manager = TriggerManager(conn)
        return manager.create_trigger(schema, table, operations)
    finally:
        conn.close()


def uninstall_trigger(config: dict, schema: str, table: str) -> bool:
    """Remove a CDC trigger from a table."""
    conn = get_connection(config)
    try:
        manager = TriggerManager(conn)
        return manager.drop_trigger(schema, table)
    finally:
        conn.close()


def check_trigger(config: dict, schema: str, table: str) -> bool:
    """Check if a CDC trigger exists on a table."""
    conn = get_connection(config)
    try:
        manager = TriggerManager(conn)
        return manager.trigger_exists(schema, table)
    finally:
        conn.close()
