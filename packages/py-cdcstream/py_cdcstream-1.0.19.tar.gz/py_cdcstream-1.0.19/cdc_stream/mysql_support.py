"""
CDC Stream - MySQL Support
Provides trigger management and event polling for MySQL/MariaDB.
Uses trigger-based approach for simplicity (binlog requires additional setup).
"""

import json
import threading
import time
from typing import Optional, Callable, List, Dict, Any
from queue import Queue

# Try mysql-connector-python first, fallback to pymysql
try:
    import mysql.connector
    HAS_MYSQL_CONNECTOR = True
except ImportError:
    HAS_MYSQL_CONNECTOR = False

try:
    import pymysql
    HAS_PYMYSQL = True
except ImportError:
    HAS_PYMYSQL = False


# ============================================================================
# SQL Templates for MySQL
# ============================================================================

CREATE_CDC_EVENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS cdcstream_cdc_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    table_schema VARCHAR(128) DEFAULT NULL,
    table_name VARCHAR(128) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    row_data JSON,
    old_row_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed TINYINT(1) DEFAULT 0,
    INDEX idx_processed (processed, created_at),
    INDEX idx_table (table_name, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

# MySQL trigger templates - one for each operation since MySQL doesn't support multi-event triggers
CREATE_INSERT_TRIGGER_TEMPLATE = """
CREATE TRIGGER trg_{table}_insert
AFTER INSERT ON `{schema}`.`{table}`
FOR EACH ROW
BEGIN
    INSERT INTO cdcstream_cdc_events (table_schema, table_name, operation, row_data)
    VALUES ('{schema}', '{table}', 'INSERT', JSON_OBJECT({column_mappings_new}));
END
"""

CREATE_UPDATE_TRIGGER_TEMPLATE = """
CREATE TRIGGER trg_{table}_update
AFTER UPDATE ON `{schema}`.`{table}`
FOR EACH ROW
BEGIN
    INSERT INTO cdcstream_cdc_events (table_schema, table_name, operation, row_data, old_row_data)
    VALUES ('{schema}', '{table}', 'UPDATE',
            JSON_OBJECT({column_mappings_new}),
            JSON_OBJECT({column_mappings_old}));
END
"""

CREATE_DELETE_TRIGGER_TEMPLATE = """
CREATE TRIGGER trg_{table}_delete
AFTER DELETE ON `{schema}`.`{table}`
FOR EACH ROW
BEGIN
    INSERT INTO cdcstream_cdc_events (table_schema, table_name, operation, old_row_data)
    VALUES ('{schema}', '{table}', 'DELETE', JSON_OBJECT({column_mappings_old}));
END
"""

CHECK_TRIGGER_EXISTS_SQL = """
SELECT COUNT(*) FROM information_schema.TRIGGERS
WHERE TRIGGER_SCHEMA = %s AND TRIGGER_NAME = %s
"""

GET_PRIMARY_KEY_SQL = """
SELECT COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = %s
AND TABLE_NAME = %s
AND CONSTRAINT_NAME = 'PRIMARY'
ORDER BY ORDINAL_POSITION
LIMIT 1
"""

GET_UNPROCESSED_EVENTS_SQL = """
SELECT id, table_schema, table_name, operation, row_data, old_row_data, created_at
FROM cdcstream_cdc_events
WHERE processed = 0
ORDER BY id ASC
LIMIT 100
"""

MARK_EVENTS_PROCESSED_SQL = """
UPDATE cdcstream_cdc_events SET processed = 1 WHERE id IN ({ids})
"""

GET_TABLE_COLUMNS_SQL = """
SELECT COLUMN_NAME, DATA_TYPE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
ORDER BY ORDINAL_POSITION
"""


def get_mysql_connection(config: dict, autocommit: bool = False):
    """
    Create MySQL connection.
    Supports mysql-connector-python and pymysql.
    """
    host = config.get('host', 'localhost')
    port = int(config.get('port', 3306))
    user = config.get('user', 'root')
    password = config.get('password', '')
    database = config.get('database', '')

    if HAS_MYSQL_CONNECTOR:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=10,
            autocommit=autocommit
        )
        return conn
    elif HAS_PYMYSQL:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=10,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=autocommit
        )
        return conn
    else:
        raise ImportError("Neither mysql-connector-python nor pymysql is installed! Install with: pip install mysql-connector-python")


class MySQLTriggerManager:
    """
    Manages CDC triggers for MySQL/MariaDB.
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
        if row:
            return row[0] if isinstance(row, (list, tuple)) else row.get('COLUMN_NAME')
        return None

    def get_table_columns(self, schema: str, table: str) -> List[Dict[str, str]]:
        """Get table columns with their types."""
        cursor = self.conn.cursor()
        cursor.execute(GET_TABLE_COLUMNS_SQL, (schema, table))
        rows = cursor.fetchall()
        cursor.close()

        columns = []
        for row in rows:
            if isinstance(row, dict):
                columns.append({"name": row['COLUMN_NAME'], "type": row['DATA_TYPE']})
            else:
                columns.append({"name": row[0], "type": row[1]})
        return columns

    def _build_column_mappings(self, schema: str, table: str) -> tuple:
        """Build column mapping strings for JSON_OBJECT in triggers."""
        columns = self.get_table_columns(schema, table)

        if not columns:
            # Fallback to id only
            new_mappings = "'id', NEW.id"
            old_mappings = "'id', OLD.id"
        else:
            # Build mappings for all columns
            new_parts = []
            old_parts = []
            for col in columns:
                col_name = col['name']
                new_parts.append(f"'{col_name}', NEW.`{col_name}`")
                old_parts.append(f"'{col_name}', OLD.`{col_name}`")

            new_mappings = ', '.join(new_parts)
            old_mappings = ', '.join(old_parts)

        return new_mappings, old_mappings

    def trigger_exists(self, schema: str, table: str, operation: str = 'insert') -> bool:
        """Check if CDC trigger exists for a table and operation."""
        trigger_name = f"trg_{table}_{operation}"
        cursor = self.conn.cursor()
        cursor.execute(CHECK_TRIGGER_EXISTS_SQL, (schema, trigger_name))
        row = cursor.fetchone()
        cursor.close()

        if row:
            count = row[0] if isinstance(row, (list, tuple)) else row.get('COUNT(*)', 0)
            return count > 0
        return False

    def create_triggers(self, schema: str, table: str) -> bool:
        """Create all three CDC triggers (INSERT, UPDATE, DELETE) for a table."""
        try:
            new_mappings, old_mappings = self._build_column_mappings(schema, table)
            cursor = self.conn.cursor()

            # Drop existing triggers first to ensure they use correct table name
            self.drop_triggers(schema, table)

            # Create INSERT trigger
            sql = CREATE_INSERT_TRIGGER_TEMPLATE.format(
                schema=schema,
                table=table,
                column_mappings_new=new_mappings
            )
            try:
                cursor.execute(sql)
                print(f"  ✅ INSERT trigger created for {schema}.{table}")
            except Exception as e:
                print(f"  ⚠️ INSERT trigger failed: {e}")

            # Create UPDATE trigger
            sql = CREATE_UPDATE_TRIGGER_TEMPLATE.format(
                schema=schema,
                table=table,
                column_mappings_new=new_mappings,
                column_mappings_old=old_mappings
            )
            try:
                cursor.execute(sql)
                print(f"  ✅ UPDATE trigger created for {schema}.{table}")
            except Exception as e:
                print(f"  ⚠️ UPDATE trigger failed: {e}")

            # Create DELETE trigger
            sql = CREATE_DELETE_TRIGGER_TEMPLATE.format(
                schema=schema,
                table=table,
                column_mappings_old=old_mappings
            )
            try:
                cursor.execute(sql)
                print(f"  ✅ DELETE trigger created for {schema}.{table}")
            except Exception as e:
                print(f"  ⚠️ DELETE trigger failed: {e}")

            self.conn.commit()
            cursor.close()
            print(f"✅ MySQL triggers created for {schema}.{table}")
            return True

        except Exception as e:
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['permission', 'denied', 'privilege', 'access denied', 'trigger']):
                print(f"""
❌ PERMISSION ERROR: Cannot create triggers on {schema}.{table}

Your database user does not have sufficient privileges.

🔧 SOLUTION - For MySQL:
   GRANT SELECT, INSERT, DELETE, CREATE, TRIGGER ON {schema}.* TO 'your_user'@'%';
   FLUSH PRIVILEGES;

📝 Or connect using an existing admin/root account.

Original error: {e}
""")
            else:
                print(f"❌ Failed to create MySQL triggers for {schema}.{table}: {e}")
            return False

    def drop_triggers(self, schema: str, table: str) -> bool:
        """Drop all CDC triggers for a table."""
        try:
            cursor = self.conn.cursor()
            for op in ['insert', 'update', 'delete']:
                trigger_name = f"trg_{table}_{op}"
                cursor.execute(f"DROP TRIGGER IF EXISTS `{schema}`.`{trigger_name}`")
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"❌ Failed to drop triggers: {e}")
            return False

    def list_tables(self, schema: str) -> List[str]:
        """List all tables in schema."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT TABLE_NAME FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """, (schema,))
        rows = cursor.fetchall()
        cursor.close()

        tables = []
        for row in rows:
            if isinstance(row, dict):
                tables.append(row['TABLE_NAME'])
            else:
                tables.append(row[0])
        return tables


class MySQLListener:
    """
    Polls cdcstream_cdc_events table for new events and pushes them to a queue.
    This is the MySQL equivalent of PostgreSQL's LISTEN/NOTIFY.
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
        """Establish connection to MySQL and ensure cdcstream_cdc_events table exists."""
        try:
            # Use autocommit=True to avoid REPEATABLE READ snapshot issues
            # Without this, listener would see the same snapshot and miss new events
            self._conn = get_mysql_connection(self.config, autocommit=True)
            # Ensure cdcstream_cdc_events table exists
            self._ensure_cdcstream_cdc_events_table()
            return True
        except Exception as e:
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['access denied', 'authentication', '1045']):
                print(f"""
❌ AUTHENTICATION ERROR: MySQL connection failed

Invalid username or password, or user does not have access.

🔧 SOLUTIONS:
   1. Verify username and password
   2. Ensure user has access from your host: 'user'@'%' or 'user'@'localhost'
   3. Check GRANT privileges for the database

Original error: {e}
""")
            else:
                print(f"❌ MySQL connection failed: {e}")
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

    def _check_connection(self) -> bool:
        """Check if connection is alive using a simple query."""
        if self._conn is None:
            return False

        try:
            # Use a simple query to check connection - most reliable method
            cursor = self._conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception as e:
            print(f"⚠️ MySQL connection check failed: {e}")
            return False

    def _poll_events(self) -> List[Dict[str, Any]]:
        """Poll for unprocessed events."""
        events = []
        try:
            # Check if connection is still alive
            if self._conn is None:
                print("⚠️ MySQL: Connection is None, reconnecting...")
                if not self._connect():
                    return events

            # Check connection health
            if not self._check_connection():
                print(f"⚠️ MySQL: Connection dead, reconnecting...")
                self._disconnect()
                if not self._connect():
                    print(f"❌ MySQL: Reconnection failed")
                    return events
                print(f"✅ MySQL: Reconnected successfully")

            cursor = self._conn.cursor()

            # Debug: Check what database we're connected to
            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()

            cursor.execute(GET_UNPROCESSED_EVENTS_SQL)
            rows = cursor.fetchall()

            if rows:
                print(f"🔍 MySQL: Query returned {len(rows)} rows from {current_db}")

            event_ids = []

            for row in rows:
                # Handle both tuple and dict cursor results
                if isinstance(row, dict):
                    event_id = row['id']
                    schema = row['table_schema']
                    table = row['table_name']
                    operation = row['operation']
                    row_data_raw = row['row_data']
                    old_row_data_raw = row['old_row_data']
                    created_at = row['created_at']
                else:
                    event_id = row[0]
                    schema = row[1]
                    table = row[2]
                    operation = row[3]
                    row_data_raw = row[4]
                    old_row_data_raw = row[5]
                    created_at = row[6]

                event_ids.append(str(event_id))

                # Parse JSON data
                row_data = None
                old_row_data = None

                try:
                    if row_data_raw:
                        if isinstance(row_data_raw, str):
                            row_data = json.loads(row_data_raw)
                        elif isinstance(row_data_raw, dict):
                            row_data = row_data_raw
                        else:
                            row_data = {"raw": str(row_data_raw)}
                except:
                    row_data = {"raw": str(row_data_raw)} if row_data_raw else None

                try:
                    if old_row_data_raw:
                        if isinstance(old_row_data_raw, str):
                            old_row_data = json.loads(old_row_data_raw)
                        elif isinstance(old_row_data_raw, dict):
                            old_row_data = old_row_data_raw
                        else:
                            old_row_data = {"raw": str(old_row_data_raw)}
                except:
                    old_row_data = {"raw": str(old_row_data_raw)} if old_row_data_raw else None

                event = {
                    'id': event_id,
                    'schema': schema or self.config.get('database', ''),
                    'table': table,
                    'operation': operation,
                    'data': row_data,
                    'old_data': old_row_data,
                    'timestamp': str(created_at) if created_at else None
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
            if any(kw in error_str for kw in ['permission', 'denied', 'privilege', 'select', 'access denied']):
                print(f"""
❌ PERMISSION ERROR: Cannot read events from cdcstream_cdc_events

Your database user's permissions may have been revoked.

🔧 SOLUTION: Run in MySQL:
   GRANT SELECT, DELETE ON your_database.cdcstream_cdc_events TO 'your_user'@'%';

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
                print(f"❌ MySQL poll error: {e}")

            self._stats['errors'] += 1
            # Try to reconnect
            self._disconnect()
            time.sleep(2)
            self._connect()

        return events

    def _listen_loop(self):
        """Main polling loop."""
        print(f"🔄 MySQL Listener loop starting...")
        poll_count = 0
        try:
            while self._running:
                poll_count += 1
                try:
                    if not self._conn:
                        print(f"🔄 MySQL: No connection, attempting to connect...")
                        if not self._connect():
                            print(f"❌ MySQL: Connection failed, retrying in 5s...")
                            time.sleep(5)
                            continue
                        print(f"✅ MySQL: Connected successfully")

                    events = self._poll_events()
                    if events:
                        print(f"📥 MySQL: Found {len(events)} events (poll #{poll_count})")
                    elif poll_count % 30 == 0:
                        # Log every 30 polls to show listener is alive
                        print(f"🔄 MySQL: Listener alive, poll #{poll_count}, no new events")

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

                except Exception as e:
                    print(f"❌ MySQL poll loop error: {e}")
                    self._stats['errors'] += 1
                    self._disconnect()
                    time.sleep(2)
        except Exception as e:
            print(f"❌ MySQL Listener thread crashed: {e}")
            import traceback
            traceback.print_exc()

    def start(self):
        """Start the listener in a background thread."""
        if self._running and self._thread and self._thread.is_alive():
            return

        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True, name="MySQLListener")
        self._thread.start()
        print(f"🟢 MySQL Listener started (polling every {self.poll_interval}s)")

    def stop(self):
        """Stop the listener."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self._disconnect()
        print("🔴 MySQL Listener stopped")

    def restart(self):
        """Restart the listener."""
        print("🔄 MySQL Listener restarting...")
        self.stop()
        time.sleep(1)
        self.start()

    def ensure_running(self):
        """Check if listener thread is alive, restart if needed."""
        if not self._running:
            return False

        if self._thread is None or not self._thread.is_alive():
            print(f"⚠️ MySQL Listener thread died, restarting...")
            self._stats['reconnects'] += 1
            self._running = False  # Reset first
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


def ensure_mysql_triggers(datasource) -> dict:
    """
    Ensure CDC triggers are installed for all rules using this MySQL datasource.
    Called when an alert is created or updated.
    """
    results = {'success': [], 'failed': []}
    config = datasource.connector_config or {}

    if datasource.connector_type != 'mysql':
        return results

    try:
        conn = get_mysql_connection(config)
        manager = MySQLTriggerManager(conn)

        # Get all active rules for this datasource
        from api.models import Rule
        rules = Rule.objects.filter(datasource=datasource, is_active=True)

        for rule in rules:
            schema = rule.schema_name or config.get('database', '')
            table = rule.table_name

            if not table:
                continue

            # Always create/update triggers (DROP + CREATE handles existing triggers)
            if manager.create_triggers(schema, table):
                results['success'].append(f"{schema}.{table}")
            else:
                results['failed'].append(f"{schema}.{table}")

        conn.close()

    except Exception as e:
        print(f"❌ MySQL trigger setup error: {e}")
        results['failed'].append(str(e))

    return results


# ============================================================================
# SQL Scripts for Documentation
# ============================================================================

MYSQL_SETUP_SCRIPT = """
-- ============================================================================
-- CDC Stream - MySQL Setup Script
-- Run this script in your MySQL database to enable CDC event tracking.
-- ============================================================================

-- Step 1: Create the cdcstream_cdc_events table
-- This table stores all CDC events captured by triggers
CREATE TABLE IF NOT EXISTS cdcstream_cdc_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    table_schema VARCHAR(128) DEFAULT NULL,
    table_name VARCHAR(128) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    row_data JSON,
    old_row_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed TINYINT(1) DEFAULT 0,
    INDEX idx_processed (processed, created_at),
    INDEX idx_table (table_name, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 2: Create a user for CDC Stream (optional but recommended)
-- Replace 'your_password' with a secure password
-- CREATE USER 'cdc_user'@'%' IDENTIFIED BY 'your_password';
-- GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, TRIGGER ON your_database.* TO 'cdc_user'@'%';
-- FLUSH PRIVILEGES;

-- Step 3: Triggers will be automatically created by CDC Stream when you create an alert.
-- You can also manually create triggers for a table using the template below:

-- Example: Triggers for a 'users' table
/*
DELIMITER //

CREATE TRIGGER trg_users_insert
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO cdcstream_cdc_events (table_schema, table_name, operation, row_data)
    VALUES (DATABASE(), 'users', 'INSERT', JSON_OBJECT('id', NEW.id, 'name', NEW.name, 'email', NEW.email));
END//

CREATE TRIGGER trg_users_update
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    INSERT INTO cdcstream_cdc_events (table_schema, table_name, operation, row_data, old_row_data)
    VALUES (DATABASE(), 'users', 'UPDATE',
            JSON_OBJECT('id', NEW.id, 'name', NEW.name, 'email', NEW.email),
            JSON_OBJECT('id', OLD.id, 'name', OLD.name, 'email', OLD.email));
END//

CREATE TRIGGER trg_users_delete
AFTER DELETE ON users
FOR EACH ROW
BEGIN
    INSERT INTO cdcstream_cdc_events (table_schema, table_name, operation, old_row_data)
    VALUES (DATABASE(), 'users', 'DELETE', JSON_OBJECT('id', OLD.id, 'name', OLD.name, 'email', OLD.email));
END//

DELIMITER ;
*/

-- Step 4: Test the setup
-- INSERT INTO your_table (...) VALUES (...);
-- SELECT * FROM cdcstream_cdc_events ORDER BY id DESC LIMIT 10;
"""

