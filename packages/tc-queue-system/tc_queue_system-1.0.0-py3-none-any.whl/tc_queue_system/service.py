"""TC Queue Service - Simple queue with Flask API and module usage.

Use as a server:
    python -m tc_queue_system.service --port 8090

Use as a module:
    from tc_queue_system.service import QueueService

    qs = QueueService()
    qs.publish('my_queue', {'task': 'hello'})
    msg = qs.consume('my_queue')
    if msg:
        print(msg['data'])
        qs.ack(msg['id'])

API Endpoints (auth: admin/123):
    GET  /              - Service info
    GET  /stats         - Overall stats
    GET  /queues        - List all queues
    POST /queue/<name>  - Create queue
    GET  /queue/<name>  - Get queue info
    DELETE /queue/<name> - Delete queue
    POST /queue/<name>/publish  - Publish message (JSON body)
    POST /queue/<name>/consume  - Consume one message
    POST /queue/<name>/purge    - Purge all messages
    GET  /queue/<name>/size     - Get queue size
    POST /message/<id>/ack      - Acknowledge message
    POST /message/<id>/nack     - Requeue message
"""

import json
import os
import sqlite3
import threading
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Dict, List, Optional, Any

# Default database path
DB_PATH = Path(__file__).parent / 'queue.db'

# Default auth (can override via env vars or function args)
DEFAULT_AUTH_USER = os.getenv('QUEUE_AUTH_USER', 'admin')
DEFAULT_AUTH_PASS = os.getenv('QUEUE_AUTH_PASS', '123')


class QueueService:
    """Simple queue service with SQLite backend.

    Thread-safe singleton that manages queues and messages using SQLite.
    Supports priority queues, message acknowledgment, and basic operations.
    """

    _instance: Optional['QueueService'] = None
    _lock = threading.Lock()

    def __new__(cls, db_path: str = None) -> 'QueueService':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._init_db(db_path or str(DB_PATH))
                    cls._instance = instance
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset singleton instance (for testing)."""
        with cls._lock:
            cls._instance = None

    def _init_db(self, db_path: str):
        """Initialize database."""
        self.db_path = db_path
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # Messages table
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                queue TEXT NOT NULL,
                data TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                processed_at TEXT
            )
        ''')

        # Queues table
        c.execute('''
            CREATE TABLE IF NOT EXISTS queues (
                name TEXT PRIMARY KEY,
                created_at TEXT
            )
        ''')

        c.execute('CREATE INDEX IF NOT EXISTS idx_queue_status ON messages(queue, status)')
        conn.commit()
        conn.close()

    def _get_conn(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ==================== Queue Operations ====================

    def create_queue(self, name: str) -> bool:
        """Create a queue.

        Args:
            name: Queue name

        Returns:
            True if created successfully
        """
        conn = self._get_conn()
        try:
            conn.execute(
                'INSERT OR IGNORE INTO queues (name, created_at) VALUES (?, ?)',
                (name, datetime.now().isoformat())
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def delete_queue(self, name: str) -> bool:
        """Delete a queue and all its messages.

        Args:
            name: Queue name

        Returns:
            True if deleted successfully
        """
        conn = self._get_conn()
        try:
            conn.execute('DELETE FROM messages WHERE queue = ?', (name,))
            conn.execute('DELETE FROM queues WHERE name = ?', (name,))
            conn.commit()
            return True
        finally:
            conn.close()

    def list_queues(self) -> List[Dict[str, Any]]:
        """List all queues with their stats.

        Returns:
            List of queue dicts with name, created_at, pending, processing
        """
        conn = self._get_conn()
        try:
            c = conn.cursor()
            c.execute('''
                SELECT q.name, q.created_at,
                    (SELECT COUNT(*) FROM messages WHERE queue = q.name AND status = 'pending') as pending,
                    (SELECT COUNT(*) FROM messages WHERE queue = q.name AND status = 'processing') as processing
                FROM queues q
                ORDER BY q.name
            ''')
            return [dict(row) for row in c.fetchall()]
        finally:
            conn.close()

    def get_queue(self, name: str) -> Dict[str, Any]:
        """Get queue stats.

        Args:
            name: Queue name

        Returns:
            Dict with name, pending, processing counts
        """
        conn = self._get_conn()
        try:
            c = conn.cursor()
            c.execute('SELECT COUNT(*) as pending FROM messages WHERE queue = ? AND status = ?', (name, 'pending'))
            pending = c.fetchone()['pending']
            c.execute('SELECT COUNT(*) as processing FROM messages WHERE queue = ? AND status = ?', (name, 'processing'))
            processing = c.fetchone()['processing']
            return {'name': name, 'pending': pending, 'processing': processing}
        finally:
            conn.close()

    # ==================== Message Operations ====================

    def publish(self, queue: str, data: Dict[str, Any], priority: int = 0) -> int:
        """Publish message to queue.

        Args:
            queue: Queue name (auto-created if not exists)
            data: Message data (dict)
            priority: Message priority (higher = processed first)

        Returns:
            Message ID
        """
        self.create_queue(queue)
        conn = self._get_conn()
        try:
            c = conn.cursor()
            c.execute(
                'INSERT INTO messages (queue, data, priority, status, created_at) VALUES (?, ?, ?, ?, ?)',
                (queue, json.dumps(data), priority, 'pending', datetime.now().isoformat())
            )
            conn.commit()
            return c.lastrowid
        finally:
            conn.close()

    def consume(self, queue: str) -> Optional[Dict[str, Any]]:
        """Consume one message from queue.

        Args:
            queue: Queue name

        Returns:
            Message dict with id, data, priority, created_at or None if empty
        """
        conn = self._get_conn()
        try:
            c = conn.cursor()
            c.execute('''
                SELECT id, data, priority, created_at FROM messages 
                WHERE queue = ? AND status = 'pending'
                ORDER BY priority DESC, id ASC
                LIMIT 1
            ''', (queue,))
            row = c.fetchone()

            if row:
                # Mark as processing
                c.execute(
                    'UPDATE messages SET status = ?, processed_at = ? WHERE id = ?',
                    ('processing', datetime.now().isoformat(), row['id'])
                )
                conn.commit()
                return {
                    'id': row['id'],
                    'data': json.loads(row['data']),
                    'priority': row['priority'],
                    'created_at': row['created_at']
                }
            return None
        finally:
            conn.close()

    def ack(self, message_id: int) -> bool:
        """Acknowledge message (mark as processed and delete).

        Args:
            message_id: Message ID from consume()

        Returns:
            True if acknowledged
        """
        conn = self._get_conn()
        try:
            conn.execute('DELETE FROM messages WHERE id = ?', (message_id,))
            conn.commit()
            return True
        finally:
            conn.close()

    def nack(self, message_id: int) -> bool:
        """Negative acknowledge (requeue message for retry).

        Args:
            message_id: Message ID from consume()

        Returns:
            True if requeued
        """
        conn = self._get_conn()
        try:
            conn.execute('UPDATE messages SET status = ? WHERE id = ?', ('pending', message_id))
            conn.commit()
            return True
        finally:
            conn.close()

    def purge(self, queue: str) -> int:
        """Purge all messages from queue.

        Args:
            queue: Queue name

        Returns:
            Number of messages deleted
        """
        conn = self._get_conn()
        try:
            c = conn.cursor()
            c.execute('DELETE FROM messages WHERE queue = ?', (queue,))
            conn.commit()
            return c.rowcount
        finally:
            conn.close()

    def size(self, queue: str) -> int:
        """Get number of pending messages in queue.

        Args:
            queue: Queue name

        Returns:
            Number of pending messages
        """
        conn = self._get_conn()
        try:
            c = conn.cursor()
            c.execute('SELECT COUNT(*) as cnt FROM messages WHERE queue = ? AND status = ?', (queue, 'pending'))
            return c.fetchone()['cnt']
        finally:
            conn.close()

    def stats(self) -> Dict[str, Any]:
        """Get overall service statistics.

        Returns:
            Dict with queues, pending, processing counts and timestamp
        """
        conn = self._get_conn()
        try:
            c = conn.cursor()
            c.execute('SELECT COUNT(*) as cnt FROM queues')
            total_queues = c.fetchone()['cnt']
            c.execute('SELECT COUNT(*) as cnt FROM messages WHERE status = ?', ('pending',))
            total_pending = c.fetchone()['cnt']
            c.execute('SELECT COUNT(*) as cnt FROM messages WHERE status = ?', ('processing',))
            total_processing = c.fetchone()['cnt']
            return {
                'queues': total_queues,
                'pending': total_pending,
                'processing': total_processing,
                'timestamp': datetime.now().isoformat()
            }
        finally:
            conn.close()


# ==================== Flask API ====================

def create_app(auth_user: str = None, auth_pass: str = None):
    """Create Flask app with queue API.

    Args:
        auth_user: Basic auth username (default: env QUEUE_AUTH_USER or 'admin')
        auth_pass: Basic auth password (default: env QUEUE_AUTH_PASS or '123')

    Returns:
        Flask application
    """
    from flask import Flask, jsonify, request, Response

    app = Flask(__name__)
    qs = QueueService()

    # Use provided or default from env
    _auth_user = auth_user or DEFAULT_AUTH_USER
    _auth_pass = auth_pass or DEFAULT_AUTH_PASS

    def check_auth(u: str, p: str) -> bool:
        return u == _auth_user and p == _auth_pass

    def requires_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if not auth or not check_auth(auth.username, auth.password):
                return Response('Auth required', 401, {'WWW-Authenticate': 'Basic realm="TC Queue"'})
            return f(*args, **kwargs)
        return decorated

    @app.route('/')
    @requires_auth
    def index():
        """Service info."""
        return jsonify({'service': 'tc-queue-system', 'version': '1.0.1', 'status': 'ok'})

    @app.route('/stats')
    @requires_auth
    def api_stats():
        """Get overall stats."""
        return jsonify(qs.stats())

    @app.route('/queues')
    @requires_auth
    def api_list_queues():
        """List all queues."""
        return jsonify(qs.list_queues())

    @app.route('/queue/<name>', methods=['GET'])
    @requires_auth
    def api_get_queue(name):
        """Get queue info."""
        return jsonify(qs.get_queue(name))

    @app.route('/queue/<name>', methods=['POST'])
    @requires_auth
    def api_create_queue(name):
        """Create a queue."""
        qs.create_queue(name)
        return jsonify({'success': True, 'queue': name})

    @app.route('/queue/<name>', methods=['DELETE'])
    @requires_auth
    def api_delete_queue(name):
        """Delete a queue."""
        qs.delete_queue(name)
        return jsonify({'success': True, 'queue': name})

    @app.route('/queue/<name>/publish', methods=['POST'])
    @requires_auth
    def api_publish(name):
        """Publish message to queue."""
        data = request.get_json() or {}
        priority = data.pop('_priority', 0) if isinstance(data, dict) else 0
        msg_id = qs.publish(name, data, priority)
        return jsonify({'success': True, 'id': msg_id, 'queue': name})

    @app.route('/queue/<name>/consume', methods=['POST'])
    @requires_auth
    def api_consume(name):
        """Consume message from queue."""
        msg = qs.consume(name)
        if msg:
            return jsonify({'success': True, 'message': msg})
        return jsonify({'success': False, 'message': None})

    @app.route('/queue/<name>/purge', methods=['POST'])
    @requires_auth
    def api_purge(name):
        """Purge all messages from queue."""
        count = qs.purge(name)
        return jsonify({'success': True, 'deleted': count})

    @app.route('/queue/<name>/size')
    @requires_auth
    def api_size(name):
        """Get queue size."""
        return jsonify({'queue': name, 'size': qs.size(name)})

    @app.route('/message/<int:msg_id>/ack', methods=['POST'])
    @requires_auth
    def api_ack(msg_id):
        """Acknowledge message."""
        qs.ack(msg_id)
        return jsonify({'success': True})

    @app.route('/message/<int:msg_id>/nack', methods=['POST'])
    @requires_auth
    def api_nack(msg_id):
        """Requeue message."""
        qs.nack(msg_id)
        return jsonify({'success': True})

    return app


def run_server(host: str = '0.0.0.0', port: int = 8090, auth_user: str = None, auth_pass: str = None):
    """Run the queue server.

    Args:
        host: Host to bind (default: 0.0.0.0)
        port: Port to listen (default: 8090)
        auth_user: Basic auth username (default: env QUEUE_AUTH_USER or 'admin')
        auth_pass: Basic auth password (default: env QUEUE_AUTH_PASS or '123')
    """
    _user = auth_user or DEFAULT_AUTH_USER
    _pass = auth_pass or DEFAULT_AUTH_PASS

    print(f'''
╔════════════════════════════════════════════╗
║         TC Queue Service                   ║
╠════════════════════════════════════════════╣
║  URL:   http://localhost:{port:<18}║
║  Auth:  {_user} / {_pass:<25}║
╚════════════════════════════════════════════╝
''')
    app = create_app(_user, _pass)
    app.run(host=host, port=port)


def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description='TC Queue Service')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8090, help='Port to listen (default: 8090)')
    parser.add_argument('--user', default=None, help='Auth username (default: env or admin)')
    parser.add_argument('--pass', dest='password', default=None, help='Auth password (default: env or 123)')
    args = parser.parse_args()
    run_server(args.host, args.port, args.user, args.password)


if __name__ == '__main__':
    main()


