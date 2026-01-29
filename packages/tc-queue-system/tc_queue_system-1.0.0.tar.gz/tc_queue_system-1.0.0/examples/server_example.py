"""Server example for tc-queue-system.

Run: python server_example.py

Then test with curl:
    curl -u admin:123 http://localhost:8090/stats
    curl -u admin:123 -X POST http://localhost:8090/queue/test/publish \
         -H "Content-Type: application/json" -d '{"hello": "world"}'
"""

from tc_queue_system import run_server


if __name__ == '__main__':
    # Start server with default auth (admin/123)
    run_server(port=8090)

    # Or with custom auth:
    # run_server(port=8090, auth_user='myuser', auth_pass='mypassword')

