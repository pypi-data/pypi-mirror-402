"""
CDC Stream - MSSQL Support
Provides trigger management and event polling for SQL Server.
Uses trigger-based approach since CDC feature requires Enterprise edition.
"""

import json
import threading
import time
from typing import Optional, Callable, List, Dict, Any
from queue import Queue

# Try pyodbc first (Windows Auth), fallback to pymssql
try:
    import pyodbc
    HAS_PYODBC = True
except ImportError:
    HAS_PYODBC = False

try:
    import pymssql
    HAS_PYMSSQL = True
except ImportError:
    HAS_PYMSSQL = False


# ============================================================================
# SQL Templates for MSSQL
# ============================================================================

CREATE_CDC_EVENTS_TABLE_SQL = """
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'cdcstream_cdc_events')
BEGIN
    CREATE TABLE cdcstream_cdc_events (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        table_schema NVARCHAR(128) DEFAULT 'dbo',
        table_name NVARCHAR(128) NOT NULL,
        operation NVARCHAR(10) NOT NULL,
        row_data NVARCHAR(MAX),
        old_row_data NVARCHAR(MAX),
        created_at DATETIME2 DEFAULT GETDATE(),
        processed BIT DEFAULT 0
    );

    CREATE INDEX IX_cdcstream_cdc_events_processed ON cdcstream_cdc_events(processed, created_at);
    CREATE INDEX IX_cdcstream_cdc_events_table ON cdcstream_cdc_events(table_name, created_at);
END
"""

CREATE_TRIGGER_TEMPLATE = """
CREATE OR ALTER TRIGGER trg_{table}_cdc
ON {schema}.{table}
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    -- INSERT
    IF EXISTS (SELECT 1 FROM inserted) AND NOT EXISTS (SELECT 1 FROM deleted)
    BEGIN
        INSERT INTO cdcstream_cdc_events (table_schema, table_name, operation, row_data)
        SELECT '{schema}', '{table}', 'INSERT',
            (SELECT i.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)
        FROM inserted i;
    END

    -- UPDATE
    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
    BEGIN
        INSERT INTO cdcstream_cdc_events (table_schema, table_name, operation, row_data, old_row_data)
        SELECT '{schema}', '{table}', 'UPDATE',
            (SELECT i.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER),
            (SELECT d.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)
        FROM inserted i
        INNER JOIN deleted d ON i.{primary_key} = d.{primary_key};
    END

    -- DELETE
    IF NOT EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
    BEGIN
        INSERT INTO cdcstream_cdc_events (table_schema, table_name, operation, old_row_data)
        SELECT '{schema}', '{table}', 'DELETE',
            (SELECT d.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)
        FROM deleted d;
    END
END
"""

CHECK_TRIGGER_EXISTS_SQL = """
SELECT COUNT(*) FROM sys.triggers WHERE name = ?
"""

GET_PRIMARY_KEY_SQL = """
SELECT c.COLUMN_NAME
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE c
    ON tc.CONSTRAINT_NAME = c.CONSTRAINT_NAME
WHERE tc.TABLE_SCHEMA = ?
AND tc.TABLE_NAME = ?
AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
"""

GET_UNPROCESSED_EVENTS_SQL = """
SELECT TOP 100 id, table_schema, table_name, operation, row_data, old_row_data, created_at
FROM cdcstream_cdc_events
WHERE processed = 0
ORDER BY id ASC
"""

MARK_EVENTS_PROCESSED_SQL = """
UPDATE cdcstream_cdc_events SET processed = 1 WHERE id IN ({ids})
"""

GET_TABLE_COLUMNS_SQL = """
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
ORDER BY ORDINAL_POSITION
"""


def get_mssql_connection(config: dict):
    """
    Create MSSQL connection.
    Supports both Windows Auth (pyodbc) and SQL Server Auth (pymssql).
    """
    windows_auth = config.get('windows_auth', False)
    server = config.get('host', 'localhost')
    database = config.get('database', 'master')
    port = config.get('port', 1433)

    if windows_auth and HAS_PYODBC:
        # Windows Authentication
        if port != 1433:
            server = f"{server},{port}"
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes"
        return pyodbc.connect(conn_str)
    elif HAS_PYMSSQL:
        # SQL Server Authentication
        return pymssql.connect(
            server=server,
            user=config.get('user', ''),
            password=config.get('password', ''),
            database=database,
            port=str(port) if port != 1433 else None,
            login_timeout=10
        )
    elif HAS_PYODBC:
        # SQL Server Auth via pyodbc
        if port != 1433:
            server = f"{server},{port}"
        user = config.get('user', '')
        password = config.get('password', '')
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={user};PWD={password}"
        return pyodbc.connect(conn_str)
    else:
        raise ImportError("Neither pyodbc nor pymssql is installed!")


class MSSQLTriggerManager:
    """
    Manages CDC triggers for SQL Server.
    Creates cdcstream_cdc_events table and triggers on monitored tables.
    """

    def __init__(self, connection):
        self.conn = connection
        self._ensure_cdcstream_cdc_events_table()

    def _ensure_cdcstream_cdc_events_table(self):
        """Create cdcstream_cdc_events table if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute(CREATE_CDC_EVENTS_TABLE_SQL)
        self.conn.commit()
        cursor.close()

    def get_primary_key(self, schema: str, table: str) -> Optional[str]:
        """Get the primary key column of a table."""
        cursor = self.conn.cursor()
        cursor.execute(GET_PRIMARY_KEY_SQL, (schema, table))
        row = cursor.fetchone()
        cursor.close()
        return row[0] if row else None

    def trigger_exists(self, table: str) -> bool:
        """Check if CDC trigger exists for a table."""
        trigger_name = f"trg_{table}_cdc"
        cursor = self.conn.cursor()
        cursor.execute(CHECK_TRIGGER_EXISTS_SQL, (trigger_name,))
        count = cursor.fetchone()[0]
        cursor.close()
        return count > 0

    def create_trigger(self, schema: str, table: str, primary_key: Optional[str] = None) -> bool:
        """Create CDC trigger for a table."""
        try:
            # Get primary key if not provided
            if not primary_key:
                primary_key = self.get_primary_key(schema, table)

            if not primary_key:
                # Try common primary key names
                for pk_name in ['id', f'{table}_id', 'ID', f'{table}Id']:
                    primary_key = pk_name
                    break
                if not primary_key:
                    primary_key = 'id'  # Default fallback

            sql = CREATE_TRIGGER_TEMPLATE.format(
                schema=schema,
                table=table,
                primary_key=primary_key
            )

            cursor = self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()
            cursor.close()

            print(f"✅ MSSQL trigger created for {schema}.{table}")
            return True

        except Exception as e:
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['permission', 'denied', 'privilege', 'alter']):
                print(f"""
❌ PERMISSION ERROR: Cannot create trigger on {schema}.{table}

Your database user does not have sufficient privileges.

🔧 SOLUTION - For SQL Server:
   GRANT CREATE TABLE TO your_user;
   GRANT ALTER ON SCHEMA::{schema} TO your_user;
   GRANT SELECT, INSERT, DELETE ON SCHEMA::{schema} TO your_user;

📝 Or connect using an existing admin/sysadmin account.

Original error: {e}
""")
            else:
                print(f"❌ Failed to create MSSQL trigger for {schema}.{table}: {e}")
            return False

    def drop_trigger(self, schema: str, table: str) -> bool:
        """Drop CDC trigger for a table."""
        try:
            trigger_name = f"trg_{table}_cdc"
            cursor = self.conn.cursor()
            cursor.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"❌ Failed to drop trigger: {e}")
            return False

    def get_table_columns(self, schema: str, table: str) -> List[Dict[str, str]]:
        """Get table columns with their types."""
        cursor = self.conn.cursor()
        cursor.execute(GET_TABLE_COLUMNS_SQL, (schema, table))
        columns = [{"name": row[0], "type": row[1]} for row in cursor.fetchall()]
        cursor.close()
        return columns

    def list_tables(self, schema: str = 'dbo') -> List[str]:
        """List all tables in schema."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = ? AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """, (schema,))
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables


class MSSQLListener:
    """
    Polls cdcstream_cdc_events table for new events and pushes them to a queue.
    This is the MSSQL equivalent of PostgreSQL's LISTEN/NOTIFY.
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
        """Establish connection to MSSQL and ensure cdcstream_cdc_events table exists."""
        try:
            self._conn = get_mssql_connection(self.config)
            # Ensure cdcstream_cdc_events table exists
            self._ensure_cdcstream_cdc_events_table()
            return True
        except Exception as e:
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['login failed', 'authentication', '18456']):
                print(f"""
❌ AUTHENTICATION ERROR: MSSQL connection failed

Invalid username or password, or user does not have access.

🔧 SOLUTIONS:
   1. Verify username and password
   2. Enable SQL Server Authentication in SQL Server Configuration
   3. Use Windows Authentication (check 'Windows Auth' option)

Original error: {e}
""")
            else:
                print(f"❌ MSSQL connection failed: {e}")
            self._stats['errors'] += 1
            return False

    def _ensure_cdcstream_cdc_events_table(self):
        """Create cdcstream_cdc_events table if it doesn't exist."""
        try:
            cursor = self._conn.cursor()
            cursor.execute(CREATE_CDC_EVENTS_TABLE_SQL)
            self._conn.commit()
            cursor.close()
        except Exception as e:
            print(f"⚠️ Could not create cdcstream_cdc_events table: {e}")

    def _disconnect(self):
        """Close the database connection."""
        if self._conn:
            try:
                self._conn.close()
            except:
                pass
            self._conn = None

    def _poll_events(self) -> List[Dict[str, Any]]:
        """Poll for unprocessed events."""
        events = []
        try:
            cursor = self._conn.cursor()
            cursor.execute(GET_UNPROCESSED_EVENTS_SQL)

            rows = cursor.fetchall()
            event_ids = []

            for row in rows:
                event_id = row[0]
                event_ids.append(str(event_id))

                # Parse JSON data
                row_data = None
                old_row_data = None

                try:
                    if row[4]:  # row_data
                        row_data = json.loads(row[4])
                except:
                    row_data = {"raw": row[4]} if row[4] else None

                try:
                    if row[5]:  # old_row_data
                        old_row_data = json.loads(row[5])
                except:
                    old_row_data = {"raw": row[5]} if row[5] else None

                event = {
                    'id': event_id,
                    'schema': row[1] or 'dbo',
                    'table': row[2],
                    'operation': row[3],
                    'data': row_data,
                    'old_data': old_row_data,
                    'timestamp': str(row[6]) if row[6] else None
                }
                events.append(event)

            # Delete processed events immediately (no data left in user's DB)
            if event_ids:
                ids_str = ','.join(event_ids)
                cursor.execute(f"DELETE FROM cdcstream_cdc_events WHERE id IN ({ids_str})")
                self._conn.commit()

            cursor.close()

        except Exception as e:
            error_str = str(e).lower()
            if any(kw in error_str for kw in ['permission', 'denied', 'privilege', 'select']):
                print(f"""
❌ PERMISSION ERROR: Cannot read events from cdcstream_cdc_events

Your database user's permissions may have been revoked.

🔧 SOLUTION: Run in SQL Server:
   GRANT SELECT, DELETE ON cdcstream_cdc_events TO your_user;

Original error: {e}
""")
                # Log to TriggerLog for UI visibility
                try:
                    import django
                    django.setup()
                    from api.models import TriggerLog, Rule
                    # Find rules using this datasource
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
                print(f"❌ MSSQL poll error: {e}")

            self._stats['errors'] += 1
            # Try to reconnect
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
        print(f"🟢 MSSQL Listener started (polling every {self.poll_interval}s)")

    def stop(self):
        """Stop the listener."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self._disconnect()
        print("🔴 MSSQL Listener stopped")

    def ensure_running(self):
        """Check if listener thread is alive, restart if needed."""
        if not self._running:
            return False

        if self._thread is None or not self._thread.is_alive():
            print(f"⚠️ MSSQL Listener thread died, restarting...")
            self._stats['reconnects'] += 1
            self._running = False  # Reset first
            import time
            time.sleep(1)
            self.start()
            return True
        return True

    @property
    def running(self) -> bool:
        # Also check if thread is actually alive
        if self._running and self._thread and not self._thread.is_alive():
            return False
        return self._running

    @property
    def stats(self) -> dict:
        return self._stats.copy()


def ensure_mssql_triggers(datasource) -> dict:
    """
    Ensure CDC triggers are installed for all rules using this MSSQL datasource.
    Called when an alert is created or updated.
    """
    results = {'success': [], 'failed': []}
    config = datasource.connector_config or {}

    if datasource.connector_type != 'sqlserver':
        return results

    try:
        conn = get_mssql_connection(config)
        manager = MSSQLTriggerManager(conn)

        # Get all active rules for this datasource
        from api.models import Rule
        rules = Rule.objects.filter(datasource=datasource, is_active=True)

        for rule in rules:
            schema = rule.schema_name or 'dbo'
            table = rule.table_name

            if not table:
                continue

            # Always create/update trigger (CREATE OR ALTER handles existing triggers)
            if manager.create_trigger(schema, table):
                results['success'].append(f"{schema}.{table}")
            else:
                results['failed'].append(f"{schema}.{table}")

        conn.close()

    except Exception as e:
        print(f"❌ MSSQL trigger setup error: {e}")
        results['failed'].append(str(e))

    return results

