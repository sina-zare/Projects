import json
import os
import threading
import time
from datetime import datetime, timedelta

import numpy as np
import requests
from prometheus_client import (
    CollectorRegistry,
    Gauge,
    Counter,
    generate_latest,
    CONTENT_TYPE_LATEST
)

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

GRAFANA_ADDR = os.getenv("GRAFANA_ADDR")
API_KEY = os.getenv("API_KEY")
CONFIG_FILE = "/config/targets.json"
COLLECTION_INTERVAL = int(os.getenv("COLLECTION_INTERVAL", "300"))

if not GRAFANA_ADDR:
    raise RuntimeError("GRAFANA_ADDR environment variable is required")

if not API_KEY:
    raise RuntimeError("API_KEY environment variable is required")

# ------------------------------------------------------------------------------
# Registry
# ------------------------------------------------------------------------------

registry = CollectorRegistry()

# ------------------------------------------------------------------------------
# Business Metrics
# ------------------------------------------------------------------------------

website_availability_current_status = Gauge(
    "website_availability_current_status",
    "Website status (-1=no data,0=down,1=up,2=disruption)",
    ["host"],
    registry=registry
)

website_availability_current_samples_total = Gauge(
    "website_availability_current_samples_total",
    "Total samples collected",
    ["host"],
    registry=registry
)

website_availability_current_samples_up = Gauge(
    "website_availability_current_samples_up",
    "Samples considered available",
    ["host"],
    registry=registry
)


website_availability_current_revised_status = Gauge(
    "website_availability_current_revised_status",
    "Revised status (-1=no data,0=down,1=up,2=disruption)",
    ["host"],
    registry=registry
)

website_availability_current_revised_samples_total = Gauge(
    "website_availability_current_revised_samples_total",
    "Total revised samples",
    ["host"],
    registry=registry
)

website_availability_current_revised_samples_up = Gauge(
    "website_availability_revised_samples_up",
    "Available revised samples",
    ["host"],
    registry=registry
)

# ------------------------------------------------------------------------------
# Exporter Metrics
# ------------------------------------------------------------------------------

exporter_last_collection_success = Gauge(
    "website_availability_exporter_last_collection_success",
    "1 if last collection succeeded",
    registry=registry
)

exporter_last_collection_duration_seconds = Gauge(
    "website_availability_exporter_last_collection_duration_seconds",
    "Collection duration",
    registry=registry
)

exporter_collection_errors_total = Counter(
    "website_availability_exporter_collection_errors_total",
    "Total collection errors",
    registry=registry
)

# ------------------------------------------------------------------------------
# Globals
# ------------------------------------------------------------------------------

session = requests.Session()

collection_lock = threading.Lock()

known_hosts = set()

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def retry(
    func,
    max_attempts=5,
    initial_delay=2,
    backoff_factor=2,
    exceptions=(Exception,)
    ):
    delay = initial_delay

    for attempt in range(1, max_attempts + 1):
        try:
            return func()

        except exceptions as e:
            if attempt == max_attempts:
                raise

            print(
                f"Attempt {attempt}/{max_attempts} failed: {e}. "
                f"Retrying in {delay}s..."
            )

            time.sleep(delay)
            delay *= backoff_factor


def load_targets():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def availability_to_status(value):
    if value is None:
        return -1

    if value == 0:
        return 0

    if value == 100:
        return 1

    return 2


def query_grafana(
    datastore_uid,
    zbx_host,
    zbx_group,
    last_minutes=3
):
    time_from = int(
        (
            datetime.now() -
            timedelta(minutes=last_minutes)
        ).timestamp() * 1000
    )

    time_to = int(
        datetime.now().timestamp() * 1000
    )

    payload = {
        "queries": [
            {
                "refId": "A",
                "datasource": {
                    "type": "alexanderzobnin-zabbix-datasource",
                    "uid": datastore_uid
                },
                "queryType": "0",
                "host": {
                    "filter": zbx_host
                },
                "item": {
                    "filter": "Failed step of scenario \"Web_Check\"."
                },
                "group": {
                    "filter": zbx_group
                },
                "intervalMs": 60000,
                "options": {
                    "showDisabledItems": False,
                    "skipEmptyValues": False
                }
            }
        ],
        "from": str(time_from),
        "to": str(time_to)
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    def _request():
        r = session.post(
            f"{GRAFANA_ADDR}/api/ds/query",
            headers=headers,
            json=payload,
            timeout=30
        )
        # retry only on server-side issues
        if r.status_code >= 500:
            raise requests.exceptions.HTTPError(
                f"Grafana returned {r.status_code}"
            )

        r.raise_for_status()

        return r.json()

    return retry(
        _request,
        exceptions=(
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
        )
    )


def calculate_availability(host_cfg):
    host = host_cfg["host"]

    data = query_grafana(
        datastore_uid=host_cfg["ds_uid"],
        zbx_host=host_cfg["host"],
        zbx_group=host_cfg["group"],
        last_minutes=3
    )

    frames = (
        data.get("results", {})
        .get("A", {})
        .get("frames", [])
    )

    if not frames:
        return {
            "host": host,
            "original_availability": None,
            "revised_availability": None,
            "original_up": 0,
            "original_total": 0,
            "revised_up": 0,
            "revised_total": 0,
        }

    values = frames[0]["data"]["values"]

    metrics = values[1]

    readable_metrics = []

    for v in metrics:
        if v == 0:
            readable_metrics.append(1)
        elif v == 1:
            readable_metrics.append(0)

    if len(readable_metrics) == 0:
        return {
            "host": host,
            "original_availability": None,
            "revised_availability": None,
            "original_up": 0,
            "original_total": 0,
            "revised_up": 0,
            "revised_total": 0,
        }

    '''
                # standardize samples to chunk size

                len(readable_metrics) = 7
                chunk_size = 3

                remainder = 7 % 3 --> 1
                usable_length = 7 - 1 --> 6

                trimmed_metrics = readable_metrics[:6]
                Result:
                [1,0,0,1,1,0]

                Now reshape works:
                [[1,0,0],
                 [1,1,0]]
                '''
    chunk_size = host_cfg.get("chunk", 3)
    remainder = len(readable_metrics) % chunk_size

    if remainder:
        trimmed = readable_metrics[:-remainder]
    else:
        trimmed = readable_metrics

    if not trimmed:
        trimmed = readable_metrics

    arr = np.array(trimmed)
    chunks = arr.reshape(-1, chunk_size)

    revised_metrics = []

    for chunk in chunks:
        revised_metrics.append(
            1 if np.sum(chunk) > 0 else 0
        )

    original_up = sum(readable_metrics)
    original_total = len(readable_metrics)

    revised_up = sum(revised_metrics)
    revised_total = len(revised_metrics)

    return {
        "host": host,
        "original_availability": round((original_up / original_total) * 100, 4),
        "revised_availability": round((revised_up / revised_total) * 100, 4),
        "original_up": original_up,
        "original_total": original_total,
        "revised_up": revised_up,
        "revised_total": revised_total,
    }


def remove_host_metrics(host):
    website_availability_current_status.remove(host)
    website_availability_current_samples_total.remove(host)
    website_availability_current_samples_up.remove(host)

    website_availability_current_revised_status.remove(host)
    website_availability_current_revised_samples_total.remove(host)
    website_availability_current_revised_samples_up.remove(host)


def collect_all_targets():
    global known_hosts

    targets = load_targets()

    current_hosts = set()

    for target in targets:
        host = target["host"]
        current_hosts.add(host)

        try:
            result = calculate_availability(target)

        except Exception as e:
            print(f"Failed collecting {host}: {e}")
            exporter_collection_errors_total.inc()
            continue

        original_availability = result["original_availability"]
        revised_availability = result["revised_availability"]

        # Metric Updating
        website_availability_current_status.labels(host=host).set(availability_to_status(original_availability)        )
        website_availability_current_samples_total.labels(host=host).set(result["original_total"])
        website_availability_current_samples_up.labels(host=host).set(result["original_up"])

        website_availability_current_revised_status.labels(host=host).set(availability_to_status(revised_availability))
        website_availability_current_revised_samples_total.labels(host=host).set(result["revised_total"])
        website_availability_current_revised_samples_up.labels(host=host).set(result["revised_up"])

    stale_hosts = known_hosts - current_hosts

    for host in stale_hosts:
        try:
            remove_host_metrics(host)
        except Exception:
            pass

    known_hosts = current_hosts


def collector_loop():
    while True:

        start = time.time()

        with collection_lock:
            try:
                collect_all_targets()

                exporter_last_collection_success.set(1)

            except Exception as e:
                print(f"Collection failed: {e}")

                exporter_last_collection_success.set(0)
                exporter_collection_errors_total.inc()

            finally:
                exporter_last_collection_duration_seconds.set(time.time() - start)

        time.sleep(COLLECTION_INTERVAL)

# ------------------------------------------------------------------------------
# Initial collection
# ------------------------------------------------------------------------------

# Run manually for first time so we don't wait for {COLLECTION_INTERVAL} seconds
try:
    collect_all_targets()
    exporter_last_collection_success.set(1)
except Exception as e:
    print(f"Initial collection failed: {e}")
    exporter_last_collection_success.set(0)

collector_thread = threading.Thread(
    target=collector_loop,
    daemon=True
)

collector_thread.start()

# ------------------------------------------------------------------------------
# WSGI Application
# ------------------------------------------------------------------------------

def app(environ, start_response):
    path = environ.get("PATH_INFO")
    if path != "/metrics":
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b"Not Found"]

    with collection_lock:
        output = generate_latest(registry)

    start_response("200 OK", [("Content-Type", CONTENT_TYPE_LATEST)])
    return [output]

# gunicorn -w 1 --threads 2 --timeout 10 -b 0.0.0.0:9779 file_name:app