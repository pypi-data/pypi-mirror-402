"""tc-queue-system - A simple message queue system.

Use as module (no Flask required):
    from tc_queue_system import QueueService

    qs = QueueService()
    qs.publish('my_queue', {'task': 'hello'})
    msg = qs.consume('my_queue')
    if msg:
        print(msg['data'])
        qs.ack(msg['id'])

Use as server (requires Flask):
    python -m tc_queue_system.service --port 8090

    # Or in code:
    from tc_queue_system import run_server
    run_server(port=8090)

API Endpoints (auth: admin/123):
    GET  /stats              - Get stats
    GET  /queues             - List queues
    POST /queue/<name>       - Create queue
    GET  /queue/<name>       - Get queue info
    DELETE /queue/<name>     - Delete queue
    POST /queue/<name>/publish - Publish message
    POST /queue/<name>/consume - Consume message
    POST /queue/<name>/purge   - Purge queue
    GET  /queue/<name>/size    - Get queue size
    POST /message/<id>/ack     - Ack message
    POST /message/<id>/nack    - Nack message
"""

__version__ = '1.0.0'

# Core module (no Flask required)
from tc_queue_system.service import QueueService


def create_app(*args, **kwargs):
    """Create Flask app (lazy import to avoid requiring Flask for module usage)."""
    from tc_queue_system.service import create_app as _create_app
    return _create_app(*args, **kwargs)


def run_server(*args, **kwargs):
    """Run Flask server (lazy import to avoid requiring Flask for module usage)."""
    from tc_queue_system.service import run_server as _run_server
    return _run_server(*args, **kwargs)


__all__ = [
    '__version__',
    'QueueService',
    'create_app',
    'run_server',
]

