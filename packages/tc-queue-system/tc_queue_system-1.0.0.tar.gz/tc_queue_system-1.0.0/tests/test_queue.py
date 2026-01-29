"""Tests for tc_queue_system.QueueService."""

import os
import pytest
import tempfile
from tc_queue_system import QueueService


@pytest.fixture
def qs():
    """Create QueueService with temp database."""
    # Reset singleton
    QueueService.reset()

    # Use temp database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    service = QueueService(db_path=db_path)
    yield service

    # Cleanup
    QueueService.reset()
    try:
        os.unlink(db_path)
    except:
        pass


class TestQueueService:
    """Test QueueService class."""

    def test_create_queue(self, qs):
        result = qs.create_queue('test_queue')
        assert result is True

        queues = qs.list_queues()
        assert len(queues) == 1
        assert queues[0]['name'] == 'test_queue'

    def test_delete_queue(self, qs):
        qs.create_queue('test_queue')
        qs.delete_queue('test_queue')

        queues = qs.list_queues()
        assert len(queues) == 0

    def test_publish(self, qs):
        msg_id = qs.publish('test_queue', {'key': 'value'})

        assert msg_id is not None
        assert msg_id > 0
        assert qs.size('test_queue') == 1

    def test_publish_with_priority(self, qs):
        qs.publish('test_queue', {'task': 'low'}, priority=1)
        qs.publish('test_queue', {'task': 'high'}, priority=10)
        qs.publish('test_queue', {'task': 'medium'}, priority=5)

        # Should consume in priority order (highest first)
        msg = qs.consume('test_queue')
        assert msg['data']['task'] == 'high'
        qs.ack(msg['id'])

        msg = qs.consume('test_queue')
        assert msg['data']['task'] == 'medium'
        qs.ack(msg['id'])

        msg = qs.consume('test_queue')
        assert msg['data']['task'] == 'low'
        qs.ack(msg['id'])

    def test_consume_empty(self, qs):
        qs.create_queue('empty_queue')
        msg = qs.consume('empty_queue')
        assert msg is None

    def test_consume(self, qs):
        qs.publish('test_queue', {'key': 'value'})

        msg = qs.consume('test_queue')

        assert msg is not None
        assert msg['data'] == {'key': 'value'}
        assert 'id' in msg
        assert 'created_at' in msg

    def test_ack(self, qs):
        msg_id = qs.publish('test_queue', {'key': 'value'})
        msg = qs.consume('test_queue')

        result = qs.ack(msg['id'])

        assert result is True
        assert qs.size('test_queue') == 0

    def test_nack(self, qs):
        qs.publish('test_queue', {'key': 'value'})
        msg = qs.consume('test_queue')

        # Message is in processing, queue shows 0 pending
        assert qs.size('test_queue') == 0

        # Nack requeues it
        result = qs.nack(msg['id'])

        assert result is True
        assert qs.size('test_queue') == 1

    def test_purge(self, qs):
        qs.publish('test_queue', {'key': '1'})
        qs.publish('test_queue', {'key': '2'})
        qs.publish('test_queue', {'key': '3'})

        assert qs.size('test_queue') == 3

        deleted = qs.purge('test_queue')

        assert deleted == 3
        assert qs.size('test_queue') == 0

    def test_size(self, qs):
        assert qs.size('test_queue') == 0

        qs.publish('test_queue', {'key': '1'})
        assert qs.size('test_queue') == 1

        qs.publish('test_queue', {'key': '2'})
        assert qs.size('test_queue') == 2

    def test_stats(self, qs):
        qs.create_queue('queue1')
        qs.create_queue('queue2')
        qs.publish('queue1', {'key': '1'})
        qs.publish('queue1', {'key': '2'})
        qs.publish('queue2', {'key': '3'})

        stats = qs.stats()

        assert stats['queues'] == 2
        assert stats['pending'] == 3
        assert stats['processing'] == 0
        assert 'timestamp' in stats

    def test_get_queue(self, qs):
        qs.publish('test_queue', {'key': '1'})
        qs.publish('test_queue', {'key': '2'})
        qs.consume('test_queue')  # One in processing

        info = qs.get_queue('test_queue')

        assert info['name'] == 'test_queue'
        assert info['pending'] == 1
        assert info['processing'] == 1

    def test_list_queues(self, qs):
        qs.create_queue('queue_a')
        qs.create_queue('queue_b')
        qs.publish('queue_a', {'key': '1'})

        queues = qs.list_queues()

        assert len(queues) == 2
        names = [q['name'] for q in queues]
        assert 'queue_a' in names
        assert 'queue_b' in names

