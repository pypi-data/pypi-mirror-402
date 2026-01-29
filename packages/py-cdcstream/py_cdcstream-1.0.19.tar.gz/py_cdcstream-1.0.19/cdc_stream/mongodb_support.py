"""
CDC Stream - MongoDB Support
Provides Change Stream listener for MongoDB.
Uses MongoDB's native Change Streams API (requires Replica Set or Sharded Cluster).
"""

import json
import threading
import time
from typing import Optional, Callable, List, Dict, Any
from queue import Queue
from datetime import datetime

try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
    from bson import ObjectId
    from bson.json_util import dumps as bson_dumps
    HAS_PYMONGO = True
except ImportError:
    HAS_PYMONGO = False


def get_mongodb_connection(config: dict) -> 'MongoClient':
    """
    Create MongoDB connection.
    Supports connection string or host/port configuration.
    """
    if not HAS_PYMONGO:
        raise ImportError("pymongo is not installed! Install with: pip install pymongo")

    connection_string = config.get('connection_string')

    if connection_string:
        # Use connection string directly
        client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
    else:
        # Build connection from individual params
        host = config.get('host', 'localhost')
        port = int(config.get('port', 27017))
        user = config.get('user', '')
        password = config.get('password', '')
        database = config.get('database', 'admin')  # Auth database

        if user and password:
            client = MongoClient(
                host=host,
                port=port,
                username=user,
                password=password,
                authSource=database,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
        else:
            client = MongoClient(
                host=host,
                port=port,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )

    # Test connection
    client.admin.command('ping')
    return client


def serialize_bson(obj: Any) -> Any:
    """Convert BSON types to JSON-serializable types."""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, bytes):
        return obj.hex()
    elif isinstance(obj, dict):
        return {k: serialize_bson(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_bson(item) for item in obj]
    else:
        return obj


class MongoDBListener:
    """
    Listens to MongoDB Change Streams for real-time CDC events.

    Requirements:
    - MongoDB 3.6+ with Replica Set or Sharded Cluster
    - Standalone MongoDB does NOT support Change Streams

    Change Streams provide:
    - Real-time notifications (no polling needed)
    - Resume tokens for fault tolerance
    - Full document lookup option
    """

    def __init__(
        self,
        connection_config: dict,
        event_queue: Queue,
        on_event: Optional[Callable] = None,
        poll_interval: float = 1.0,  # Not used for Change Streams, kept for compatibility
        datasource_id: int = None,
        watch_database: str = None,
        watch_collections: List[str] = None
    ):
        self.config = connection_config
        self.queue = event_queue
        self.on_event = on_event
        self.poll_interval = poll_interval
        self.datasource_id = datasource_id

        # MongoDB specific
        self.watch_database = watch_database or connection_config.get('database', '')
        self.watch_collections = watch_collections or []

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._client: Optional[MongoClient] = None
        self._resume_token = None
        self._stats = {
            'events_received': 0,
            'errors': 0,
            'reconnects': 0,
            'last_event_time': None
        }

    def _connect(self) -> bool:
        """Establish connection to MongoDB."""
        try:
            self._client = get_mongodb_connection(self.config)
            print(f"✅ MongoDB connected to {self.config.get('host', 'localhost')}")
            return True
        except ServerSelectionTimeoutError as e:
            print(f"""
❌ CONNECTION ERROR: MongoDB connection failed

Could not connect to MongoDB server.

🔧 SOLUTIONS:
   1. Check if MongoDB is running
   2. Verify host and port
   3. Ensure firewall allows connection

Original error: {e}
""")
            self._stats['errors'] += 1
            return False
        except PyMongoError as e:
            error_str = str(e).lower()
            if 'authentication' in error_str or 'auth' in error_str:
                print(f"""
❌ AUTHENTICATION ERROR: MongoDB connection failed

Invalid username or password.

🔧 SOLUTIONS:
   1. Verify username and password
   2. Check authentication database (authSource)
   3. Ensure user has appropriate roles

Original error: {e}
""")
            else:
                print(f"❌ MongoDB connection failed: {e}")
            self._stats['errors'] += 1
            return False

    def _disconnect(self):
        """Close the MongoDB connection."""
        if self._client:
            try:
                self._client.close()
            except:
                pass
            self._client = None

    def _process_change_event(self, change: dict) -> Optional[dict]:
        """Process a Change Stream event and convert to standard format."""
        try:
            operation_map = {
                'insert': 'INSERT',
                'update': 'UPDATE',
                'replace': 'UPDATE',  # Treat replace as update
                'delete': 'DELETE'
            }

            op_type = change.get('operationType', '')
            operation = operation_map.get(op_type)

            if not operation:
                # Skip non-CRUD operations (drop, rename, etc.)
                return None

            # Extract namespace
            ns = change.get('ns', {})
            database = ns.get('db', self.watch_database)
            collection = ns.get('coll', '')

            # Extract document data
            full_document = change.get('fullDocument') or {}
            document_key = change.get('documentKey', {})

            # For updates, try to get update description
            update_description = change.get('updateDescription', {})

            # Build row data
            if operation == 'INSERT':
                data = serialize_bson(full_document)
                old_data = None
            elif operation == 'UPDATE':
                data = serialize_bson(full_document) if full_document else serialize_bson(update_description)
                old_data = None  # MongoDB Change Streams don't provide old document by default
            elif operation == 'DELETE':
                data = None
                old_data = serialize_bson(document_key)
            else:
                data = serialize_bson(full_document) if full_document else serialize_bson(document_key)
                old_data = None

            # Ensure we have the document ID
            if data and '_id' not in data and document_key.get('_id'):
                data['_id'] = serialize_bson(document_key['_id'])

            event = {
                'id': str(change.get('_id', {}).get('_data', '')),
                'schema': database,  # MongoDB database = schema
                'table': collection,  # MongoDB collection = table
                'operation': operation,
                'data': data,
                'old_data': old_data,
                'timestamp': change.get('clusterTime').as_datetime().isoformat() if change.get('clusterTime') else datetime.now().isoformat()
            }

            return event

        except Exception as e:
            print(f"⚠️ Error processing MongoDB change event: {e}")
            return None

    def _watch_loop(self):
        """Main Change Stream watch loop."""
        print(f"🔄 MongoDB Change Stream starting...")

        while self._running:
            try:
                if not self._client:
                    print(f"🔄 MongoDB: No connection, attempting to connect...")
                    if not self._connect():
                        print(f"❌ MongoDB: Connection failed, retrying in 5s...")
                        time.sleep(5)
                        continue

                # Get database
                db = self._client[self.watch_database] if self.watch_database else self._client.get_default_database()

                # Build pipeline for filtering (optional)
                pipeline = []

                # Watch options
                watch_options = {
                    'full_document': 'updateLookup',  # Get full document on updates
                }

                if self._resume_token:
                    watch_options['resume_after'] = self._resume_token

                # Determine what to watch
                if self.watch_collections:
                    # Watch specific collections
                    for coll_name in self.watch_collections:
                        self._watch_collection(db[coll_name], pipeline, watch_options)
                else:
                    # Watch entire database
                    print(f"👁️ MongoDB: Watching database '{db.name}' for changes...")

                    try:
                        with db.watch(pipeline, **watch_options) as stream:
                            for change in stream:
                                if not self._running:
                                    break

                                # Save resume token
                                self._resume_token = change.get('_id')

                                # Process event
                                event = self._process_change_event(change)
                                if event:
                                    self._stats['events_received'] += 1
                                    self._stats['last_event_time'] = time.time()

                                    print(f"📥 MongoDB: {event['operation']} on {event['schema']}.{event['table']}")

                                    # Push to queue
                                    self.queue.put(event)

                                    # Callback if provided
                                    if self.on_event:
                                        try:
                                            self.on_event(event)
                                        except Exception as e:
                                            print(f"❌ Event callback error: {e}")

                    except PyMongoError as e:
                        error_str = str(e).lower()
                        if 'not supported' in error_str or 'change stream' in error_str or 'replica set' in error_str:
                            print(f"""
❌ CHANGE STREAMS NOT AVAILABLE

MongoDB Change Streams require a Replica Set or Sharded Cluster.
Standalone MongoDB does NOT support Change Streams.

🔧 SOLUTIONS:
   1. Convert to Replica Set (even single-node):
      mongod --replSet rs0
      rs.initiate()

   2. Use MongoDB Atlas (free tier supports Change Streams)

   3. Use a containerized Replica Set for development

Original error: {e}
""")
                            # Don't spam - wait longer before retry
                            time.sleep(30)
                        else:
                            raise

            except PyMongoError as e:
                print(f"❌ MongoDB Change Stream error: {e}")
                self._stats['errors'] += 1
                self._disconnect()
                time.sleep(5)
                self._stats['reconnects'] += 1
            except Exception as e:
                print(f"❌ MongoDB unexpected error: {e}")
                import traceback
                traceback.print_exc()
                self._stats['errors'] += 1
                time.sleep(5)

    def _watch_collection(self, collection, pipeline: list, watch_options: dict):
        """Watch a specific collection for changes."""
        print(f"👁️ MongoDB: Watching collection '{collection.name}' for changes...")

        try:
            with collection.watch(pipeline, **watch_options) as stream:
                for change in stream:
                    if not self._running:
                        break

                    # Save resume token
                    self._resume_token = change.get('_id')

                    # Process event
                    event = self._process_change_event(change)
                    if event:
                        self._stats['events_received'] += 1
                        self._stats['last_event_time'] = time.time()

                        print(f"📥 MongoDB: {event['operation']} on {event['schema']}.{event['table']}")

                        # Push to queue
                        self.queue.put(event)

                        # Callback if provided
                        if self.on_event:
                            try:
                                self.on_event(event)
                            except Exception as e:
                                print(f"❌ Event callback error: {e}")

        except PyMongoError as e:
            raise

    def start(self):
        """Start the Change Stream listener in a background thread."""
        if self._running and self._thread and self._thread.is_alive():
            return

        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True, name="MongoDBListener")
        self._thread.start()
        print(f"🟢 MongoDB Change Stream listener started")

    def stop(self):
        """Stop the listener."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self._disconnect()
        print("🔴 MongoDB listener stopped")

    def restart(self):
        """Restart the listener."""
        print("🔄 MongoDB listener restarting...")
        self.stop()
        time.sleep(1)
        self._resume_token = None  # Clear resume token on restart
        self.start()

    def ensure_running(self):
        """Check if listener thread is alive, restart if needed."""
        if not self._running:
            return False

        if self._thread is None or not self._thread.is_alive():
            print(f"⚠️ MongoDB listener thread died, restarting...")
            self._stats['reconnects'] += 1
            self._running = False
            time.sleep(1)
            self.start()
            return True
        return True

    def is_running(self) -> bool:
        """Check if listener is running."""
        if self._running and self._thread and not self._thread.is_alive():
            return False
        return self._running

    def get_stats(self) -> dict:
        """Get listener statistics."""
        return self._stats.copy()

    @property
    def running(self) -> bool:
        return self.is_running()

    @property
    def stats(self) -> dict:
        return self._stats.copy()


def list_databases(config: dict) -> List[str]:
    """List all databases in MongoDB."""
    try:
        client = get_mongodb_connection(config)
        databases = client.list_database_names()
        # Filter out system databases
        databases = [db for db in databases if db not in ('admin', 'config', 'local')]
        client.close()
        return databases
    except Exception as e:
        print(f"❌ Failed to list databases: {e}")
        return []


def list_collections(config: dict, database: str) -> List[str]:
    """List all collections in a database."""
    try:
        client = get_mongodb_connection(config)
        db = client[database]
        collections = db.list_collection_names()
        # Filter out system collections
        collections = [c for c in collections if not c.startswith('system.')]
        client.close()
        return collections
    except Exception as e:
        print(f"❌ Failed to list collections: {e}")
        return []


def check_replica_set(config: dict) -> dict:
    """Check if MongoDB is running as a Replica Set."""
    try:
        client = get_mongodb_connection(config)

        # Try to get replica set status
        try:
            rs_status = client.admin.command('replSetGetStatus')
            return {
                'is_replica_set': True,
                'set_name': rs_status.get('set', ''),
                'members': len(rs_status.get('members', [])),
                'ok': True
            }
        except PyMongoError as e:
            if 'not running with --replSet' in str(e) or 'no replset config' in str(e).lower():
                return {
                    'is_replica_set': False,
                    'error': 'MongoDB is running in standalone mode. Change Streams require Replica Set.',
                    'ok': False
                }
            raise
        finally:
            client.close()

    except Exception as e:
        return {
            'is_replica_set': False,
            'error': str(e),
            'ok': False
        }


# ============================================================================
# MongoDB Setup Instructions
# ============================================================================

MONGODB_SETUP_INSTRUCTIONS = """
# ============================================================================
# CDC Stream - MongoDB Setup Instructions
# ============================================================================

MongoDB Change Streams require a Replica Set or Sharded Cluster.
Standalone MongoDB does NOT support Change Streams.

## Option 1: Convert Standalone to Single-Node Replica Set

1. Stop MongoDB
2. Edit mongod.conf or add command line flag:

   mongod --replSet rs0

3. Start MongoDB and initialize replica set:

   mongo
   > rs.initiate()

## Option 2: Use MongoDB Atlas (Recommended for Production)

MongoDB Atlas free tier (M0) supports Change Streams.
https://www.mongodb.com/cloud/atlas

## Option 3: Docker Compose for Development

```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:6.0
    command: ["--replSet", "rs0", "--bind_ip_all"]
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

After starting:
```bash
docker exec -it <container> mongosh
> rs.initiate()
```

## Verifying Replica Set Status

```javascript
rs.status()
```

Should show:
- "set" : "rs0"
- "members" with at least one PRIMARY

## Required Permissions

For Change Streams, user needs:
- read role on the database
- changeStream action

```javascript
db.createUser({
  user: "cdcstream",
  pwd: "your_password",
  roles: [
    { role: "read", db: "your_database" },
    { role: "changeStream", db: "your_database" }
  ]
})
```

Or simply use admin/root access for development.
"""


