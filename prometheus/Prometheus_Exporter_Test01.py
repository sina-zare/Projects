from prometheus_client import start_http_server, Counter
import time

# Define a counter metric
REQUESTS = Counter('http_requests_total', 'Total HTTP Requests')

# Simulate a request handler
def handle_request():
    REQUESTS.inc()
    print("Handled request")
    time.sleep(1)  # simulate some work

if __name__ == '__main__':
    start_http_server(8000)  # This exposes /metrics on port 8000
    print("Metrics exposed at http://localhost:8000/metrics")

    # Simulate handling requests continuously
    while True:
        handle_request()
