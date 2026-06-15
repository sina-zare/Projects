import os
import time
import requests
import urllib3
from urllib.parse import parse_qs
from requests.auth import HTTPBasicAuth
from prometheus_client import (
    CollectorRegistry,
    Gauge,
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================================
# Configuration
# ==========================================================
USERNAME = os.getenv("UNITY_USERNAME")
PASSWORD = os.getenv("UNITY_PASSWORD")

if not USERNAME or not PASSWORD:
    raise RuntimeError("UNITY_USERNAME and UNITY_PASSWORD must be set")


# ==========================================================
# Reusable HTTP Session (per process)
# ==========================================================
session = requests.Session()
session.verify = False
session.auth = HTTPBasicAuth(USERNAME, PASSWORD)
session.headers.update({
    "X-EMC-REST-CLIENT": "true",
    "Accept": "application/json"
})


def fetch_cpu(target, registry):
    # Main metric
    unity_cpu_util = Gauge(
        "dellemc_unity_cpu_utilization_percent",
        "Dell EMC Unity CPU utilization percentage",
        ["target", "sp"],
        registry=registry,
    )

    # Standard exporter health metric (per target)
    unity_up = Gauge(
        "dellemc_unity_up",
        "Whether the Unity target is reachable (1=up, 0=down)",
        ["target", "problem"],
        registry=registry,
    )

    # Request duration metric
    # unity_request_duration = Histogram(
    #     "dellemc_unity_request_duration_seconds",
    #     "Time spent querying Unity REST API",
    #     ["target"],
    #     registry=registry,
    # )

    # # Request error counter
    # unity_request_errors = Counter(
    #     "dellemc_unity_request_errors_total",
    #     "Total Unity API request errors",
    #     ["target"],
    #     registry=registry,
    # )


    url = (
        f"https://{target}/api/types/metricValue/instances"
        '?filter=path EQ "sp.*.cpu.summary.utilization"&per_page=1'
    )

    #start_time = time.time()

    try:
        response = session.get(url, timeout=10)
        #duration = time.time() - start_time
        #unity_request_duration.labels(target=target).observe(duration)

        if response.status_code != 200:
            unity_up.labels(target=target,problem=f'failed to get response from url with status {response.status_code}').set(0)
            #unity_request_errors.labels(target=target).inc()
            return

        entries = response.json().get("entries", [])
        if not entries:
            unity_up.labels(target=target,problem=f'empty response-json-get-entries for cpu utilization').set(0)
            return

        values = entries[0]["content"].get("values", {})

        for sp in ["spa", "spb"]:
            if sp in values:
                unity_cpu_util.labels(target=target, sp=sp).set(float(values[sp]))

        unity_up.labels(target=target,problem='none').set(1)

    except Exception as e:
        unity_up.labels(target=target,problem=f'type: {type(e).__name__} - error:{e}').set(0)
        #unity_request_errors.labels(target=target).inc()


# ==========================================================
# WSGI Application
# ==========================================================
def app(environ, start_response):
    path = environ.get("PATH_INFO", "")

    # Health endpoint
    if path == "/health":
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"OK"]

    if path != "/metrics":
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b"Not Found"]

    params = parse_qs(environ.get("QUERY_STRING", ""))
    target = params.get("target", [None])[0]

    if not target:
        start_response("400 Bad Request", [("Content-Type", "text/plain")])
        return [b"Missing target parameter"]

    # new registry per request
    registry = CollectorRegistry()

    try:
        fetch_cpu(target, registry)
    except Exception as e:
        start_response("500 Internal Server Error", [("Content-Type", "text/plain")])
        return [f"Error: {str(e)}".encode()]

    output = generate_latest(registry)

    start_response("200 OK", [("Content-Type", CONTENT_TYPE_LATEST)])
    return [output]

# gunicorn -w 2 --threads 4 --timeout 10 -b 0.0.0.0:9105 file_name:app