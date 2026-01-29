"""Basic usage example for tc-queue-system."""

from tc_queue_system import QueueService


def main():
    print("=" * 60)
    print("TC-QUEUE-SYSTEM EXAMPLE")
    print("=" * 60)

    # Get singleton instance (uses SQLite backend)
    qs = QueueService()
    print("\nQueueService initialized (SQLite backend)")

    # ==========================================================================
    # Queue Operations
    # ==========================================================================

    print("\n--- Queue Operations ---")

    # Create queue
    qs.create_queue('tasks')
    print("Created queue: tasks")

    # List queues
    queues = qs.list_queues()
    print(f"Queues: {queues}")

    # ==========================================================================
    # Publishing Messages
    # ==========================================================================

    print("\n--- Publishing Messages ---")

    # Simple publish
    msg_id = qs.publish('tasks', {'action': 'send_email', 'to': 'user@example.com'})
    print(f"Published message id: {msg_id}")

    # Publish with priority (higher = processed first)
    msg_id = qs.publish('tasks', {'action': 'urgent_task'}, priority=10)
    print(f"Published HIGH priority message id: {msg_id}")

    # Publish more messages
    for i in range(3):
        qs.publish('tasks', {'action': f'task_{i}'})
    print("Published 3 more messages")

    # Check queue size
    size = qs.size('tasks')
    print(f"Queue size: {size}")

    # ==========================================================================
    # Consuming Messages
    # ==========================================================================

    print("\n--- Consuming Messages ---")

    # Consume messages (highest priority first)
    while True:
        msg = qs.consume('tasks')
        if not msg:
            print("No more messages")
            break

        print(f"Consumed: {msg['data']} (id={msg['id']}, priority={msg['priority']})")

        # Acknowledge the message
        qs.ack(msg['id'])
        print(f"  Acknowledged message {msg['id']}")

    # ==========================================================================
    # Stats
    # ==========================================================================

    print("\n--- Stats ---")
    stats = qs.stats()
    print(f"Stats: {stats}")

    # ==========================================================================
    # Cleanup
    # ==========================================================================

    print("\n--- Cleanup ---")
    qs.delete_queue('tasks')
    print("Deleted queue: tasks")

    print("\n" + "=" * 60)
    print("EXAMPLE COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    main()

