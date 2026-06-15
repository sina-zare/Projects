# ---------------------------------------------------------------------------------------------------
# Modules
# ---------------------------------------------------------------------------------------------------

from prometheus_client import CollectorRegistry, Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST
from datetime import datetime, timedelta
import dns.resolver
import threading
import requests
import logging
import json
import time
import sys
import os


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("pdns_exporter")

registry = CollectorRegistry()

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

GRAFANA_ADDR = os.getenv("GRAFANA_ADDR")
GRAFANA_TOKEN = os.getenv("GRAFANA_TOKEN")
GRAFANA_PROM_DS = os.getenv("GRAFANA_PROM_DS")
READ_STATUS_PROMQL = os.getenv("READ_STATUS_PROMQL", "pdns_read_current_status")
WRITE_STATUS_PROMQL = os.getenv("WRITE_STATUS_PROMQL" , "pdns_write_current_status")
READ_STATUS_COLLECTION_INTERVAL = int(os.getenv("READ_STATUS_COLLECTION_INTERVAL", "1"))
READ_AVAILABILITY_COLLECTION_INTERVAL = int(os.getenv("READ_AVAILABILITY_COLLECTION_INTERVAL", "1440"))
WRITE_STATUS_COLLECTION_INTERVAL = int(os.getenv("WRITE_STATUS_COLLECTION_INTERVAL", "15"))
WRITE_AVAILABILITY_COLLECTION_INTERVAL = int(os.getenv("WRITE_AVAILABILITY_COLLECTION_INTERVAL", "96"))
ME_DNS = os.getenv("ME_DNS")
VNK_DNS = os.getenv("VNK_DNS")
PDNS_ADDR = os.getenv("PDNS_ADDR")
PDNS_TOKEN = os.getenv("PDNS_TOKEN")
PDNS_WRITE_RECORD = os.getenv("PDNS_WRITE_RECORD")
PDNS_QUERY_RECORD = os.getenv("PDNS_QUERY_RECORD")

# ------------------------------------------------------------------------------
# Environment Existence Check
# ------------------------------------------------------------------------------

for var in (PDNS_ADDR, PDNS_TOKEN, PDNS_WRITE_RECORD, PDNS_QUERY_RECORD, GRAFANA_ADDR, GRAFANA_TOKEN, GRAFANA_PROM_DS, READ_STATUS_PROMQL, WRITE_STATUS_PROMQL, READ_STATUS_COLLECTION_INTERVAL, WRITE_STATUS_COLLECTION_INTERVAL, READ_AVAILABILITY_COLLECTION_INTERVAL, WRITE_AVAILABILITY_COLLECTION_INTERVAL, ME_DNS, VNK_DNS):
    if not var:
        raise RuntimeError(f"{var} environment variable is required")


# ------------------------------------------------------------------------------
# App Metrics
# ------------------------------------------------------------------------------

pdns_read_current_status = Gauge(
    "pdns_read_current_status",
    "powerdns name resolution success status (-1=nodata,0=down,1=up,2=disruption)",
    ["role", "miremad", "vanak"],
    registry=registry
)

pdns_write_current_status = Gauge(
    "pdns_write_current_status",
    "powerdns A record creation success status (-1=nodata,0=down,1=up,2=disruption)",
    ["role", "datacenter"],
    registry=registry
)

pdns_24h_availability_percent = Gauge(
    "pdns_24h_availability_percent",
    "aggregated powerdns name resolution(func=read) or A record creation(func=write) success availability for last 24h in percent",
    ["role", "func", "date"],
    registry=registry
)

pdns_24h_availability_samples_total = Gauge(
    "pdns_24h_availability_samples_total",
    "total samples in last 24 hour history",
    ["role", "func", "date"],
    registry=registry
)

pdns_24h_availability_samples_up = Gauge(
    "pdns_24h_availability_samples_up",
    "up samples in last 24 hour history",
    ["role", "func", "date"],
    registry=registry
)

# ------------------------------------------------------------------------------
# Exporter Metrics
# ------------------------------------------------------------------------------

exporter_last_collection_success = Gauge(
    "pdns_exporter_last_collection_success",
    "1 if last collection succeeded",
    ["role", "mode", "collection_interval", "last_error"],
    registry=registry
)

exporter_last_collection_duration_seconds = Gauge(
    "pdns_exporter_last_collection_duration_seconds",
    "Collection duration",
    ["role", "mode", "collection_interval"],
    registry=registry
)

exporter_collection_errors_total = Counter(
    "pdns_exporter_collection_errors_total",
    "Total collection errors",
    ["role", "mode", "collection_interval"],
    registry=registry
)


# --------------------------------------------
# Global Variables
# --------------------------------------------

session = requests.Session()
collection_lock = threading.Lock()

me_status_read_error = 'N/A'
me_status_write_error = 'N/A'

vnk_status_read_error = 'N/A'
vnk_status_write_error = 'N/A'

avail_read_error = 'N/A'
avail_write_error = 'N/A'


# --------------------------------------------
# Function Definition
# --------------------------------------------

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

            logger.warning(
                "Attempt %s/%s failed: %s. Retrying in %ss",
                attempt,
                max_attempts,
                e,
                delay
            )

            time.sleep(delay)
            delay *= backoff_factor


def query_grafana(datastore_uid, promql, last_minutes=0):

    time_from = int((datetime.now() - timedelta(minutes=last_minutes)).timestamp() * 1000)  # in ms
    time_to = int(datetime.now().timestamp() * 1000)

    payload = {
        "queries": [
            {
                "refId": "A",
                "datasource": {
                    "type": "prometheus",
                    "uid": datastore_uid
                },
                "expr": promql,
                "instant": False,
                "range": True,
                "intervalMs": 60000,
                "maxDataPoints": last_minutes,
                "step": "60s"
            }
        ],
        "from": str(time_from),
        "to": str(time_to)
    }

    headers = {
        "Authorization": f"Bearer {GRAFANA_TOKEN}",
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

    return retry(_request)


def resolve_fqdn(hostname: str, dns_server: str):
    """
    :param hostname: hostname to resolve
    :param dns_server: DNS server(s), comma-separated
    :return: (success, ip, error)
    """

    resolver = dns.resolver.Resolver()
    resolver.nameservers = dns_server.split(',')

    answer = resolver.resolve(hostname, "A")
    ip = answer[0].to_text()

    return True, ip


def pdns_write_test(
        server_url,
        api_key,
        record_name,
        record_ip="127.0.0.1"
):

    record_parts = record_name.split(".")

    subdomain = record_parts[0]
    zone_name = record_parts[-2] + "." + record_parts[-1]
    record_name_final = f"{subdomain}-{int(time.time())}.{zone_name}."

    logger.info(
        "A record info | parts=%s subdomain=%s zone=%s final=%s",
        record_parts,
        subdomain,
        zone_name,
        record_name_final
    )

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    zone_url = (
        f"{server_url}/api/v1/servers/localhost/zones/{zone_name}"
    )

    try:
        # ------------------------------------------------------------------
        # Create record
        # ------------------------------------------------------------------
        create_payload = {
            "rrsets": [
                {
                    "name": record_name_final,
                    "type": "A",
                    "ttl": 60,
                    "changetype": "REPLACE",
                    "records": [
                        {
                            "content": record_ip,
                            "disabled": False
                        }
                    ]
                }
            ]
        }

        create_response = requests.patch(
            zone_url,
            headers=headers,
            json=create_payload,
            timeout=5
        )

        create_response.raise_for_status()
        logger.info(f'Success: A record created - {record_name_final}\n')

        # ------------------------------------------------------------------
        # Delete record
        # ------------------------------------------------------------------

        delete_payload = {
            "rrsets": [
                {
                    "name": record_name_final,
                    "type": "A",
                    "changetype": "DELETE"
                }
            ]
        }

        delete_response = requests.patch(
            zone_url,
            headers=headers,
            json=delete_payload,
            timeout=5
        )

        delete_response.raise_for_status()
        logger.info(f'Success: A record deleted - {record_name_final}\n')

        return True, None

    except Exception as e:
        return False, str(e)


def collector_loop(collect_func, interval, role, mode):
    # global me_status_read_error
    # global me_status_write_error
    #
    # global vnk_status_read_error
    # global vnk_status_write_error
    #
    # global avail_read_error
    # global avail_write_error

    interval_seconds = interval * 60

    collector_error = 'N/A'
    next_run = time.time()

    while True:
        start = time.time()

        try:
            with collection_lock:
                collect_func()

            exporter_last_collection_success.labels(
                role=role,
                mode=mode,
                collection_interval=f"{str(interval)}m",
                last_error='N/A'
            ).set(1)

        except Exception as e:
            logger.error(f"Collection failed: {e}\n")


            if role == 'secondary':
                if mode == 'status':
                    if me_status_read_error == 'N/A' and vnk_status_read_error == 'N/A':
                        collector_error = 'N/A'
                    elif me_status_read_error != 'N/A' and vnk_status_read_error == 'N/A':
                        collector_error = f'Miremad: {me_status_read_error}'
                    elif me_status_read_error == 'N/A' and vnk_status_read_error != 'N/A':
                        collector_error = f'Vanak: {vnk_status_read_error}'
                    elif me_status_read_error != 'N/A' and vnk_status_read_error != 'N/A':
                        collector_error = f'Miremad: {me_status_read_error} - Vanak: {vnk_status_read_error}'
                    else:
                        collector_error = e

                elif mode == 'availability':
                    if avail_read_error == 'N/A':
                        collector_error = 'N/A'
                    elif avail_read_error != 'N/A':
                        collector_error = f'{avail_read_error}'
                    else:
                        collector_error = e

            if role == 'primary':
                if mode == 'status':
                    if me_status_write_error == 'N/A' and vnk_status_write_error == 'N/A':
                        collector_error = 'N/A'
                    elif me_status_write_error != 'N/A' and vnk_status_write_error == 'N/A':
                        collector_error = f'Miremad: {me_status_write_error}'
                    elif me_status_write_error == 'N/A' and vnk_status_write_error != 'N/A':
                        collector_error = f'Vanak: {vnk_status_write_error}'
                    elif me_status_write_error != 'N/A' and vnk_status_write_error != 'N/A':
                        collector_error = f'Miremad: {me_status_write_error} - Vanak: {vnk_status_write_error}'
                    else:
                        collector_error = e

                elif mode == 'availability':
                    if avail_write_error == 'N/A':
                        collector_error = 'N/A'
                    elif avail_write_error != 'N/A':
                        collector_error = f'{avail_write_error}'
                    else:
                        collector_error = e


            exporter_last_collection_success.labels(
                role=role,
                mode=mode,
                collection_interval=f"{str(interval)}m",
                last_error=collector_error
            ).set(0)

            exporter_collection_errors_total.labels(
                role=role,
                mode=mode,
                collection_interval=f"{str(interval)}m"
            ).inc()

        finally:
            exporter_last_collection_duration_seconds.labels(
                role=role,
                mode=mode,
                collection_interval=f"{str(interval)}m"
            ).set(time.time() - start)

        next_run += interval_seconds

        sleep_time = next_run - time.time()

        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            logger.warning(f"{role} {mode} collector is behind schedule by {-sleep_time:.2f} seconds\n")


def collect_read_status():

    global me_status_read_error
    global vnk_status_read_error

    logger.info(f">>> collect_read_status() starting")
    json_data_read = {}

    for dns_name, dns_srv in {
        "me-sec-pdns": ME_DNS,
        "vnk-sec-pdns": VNK_DNS,
    }.items():

        try:
            success, resolved_ip = retry(
                lambda: resolve_fqdn(PDNS_QUERY_RECORD, dns_srv),
                max_attempts=2
            )
            error = 'N/A'

        except Exception as err:
            success = False
            resolved_ip = 'N/A'
            error = f"{type(err).__name__}: {err}"

        json_data_read[dns_name] = {
            "success": success,
            "resolved_ip": resolved_ip,
            "error": error
        }

    logger.info("DNS resolution result: %s", json.dumps(json_data_read, indent=4))

    me_read_success = json_data_read["me-sec-pdns"]["success"]
    vnk_read_success = json_data_read["vnk-sec-pdns"]["success"]
    #me_read_resolved_ip = json_data_read["me-sec-pdns"]["resolved_ip"]
    #vnk_read_resolved_ip = json_data_read["vnk-sec-pdns"]["resolved_ip"]
    me_status_read_error = json_data_read["me-sec-pdns"]["error"]
    vnk_status_read_error = json_data_read["vnk-sec-pdns"]["error"]


    # No Data
    if me_read_success is None or vnk_read_success is None:
        pdns_read_current_status.labels(role="secondary",
                                        miremad="N/A",
                                        vanak="N/A").set(-1)
        raise RuntimeError(
            f"All DNS resolvers returned None for {PDNS_QUERY_RECORD}. "
            f"ME error: {me_status_read_error}, VNK error: {vnk_status_read_error}"
        )

    # ME & VNK UP
    if me_read_success and vnk_read_success:
        pdns_read_current_status.labels(role="secondary",
                                        miremad="UP",
                                        vanak="UP").set(1)
        return

    # ME UP & VNK DOWN
    elif me_read_success and not vnk_read_success:
        pdns_read_current_status.labels(role="secondary",
                                        miremad="UP",
                                        vanak="DOWN").set(1)
        return

    # ME DOWN & VNK UP
    elif not me_read_success and vnk_read_success:
        pdns_read_current_status.labels(role="secondary",
                                        miremad="DOWN",
                                        vanak="UP").set(1)
        return

    # ME DOWN & VNK DOWN
    elif not me_read_success and not vnk_read_success:
        pdns_read_current_status.labels(role="secondary",
                                        miremad="DOWN",
                                        vanak="DOWN").set(0)
        raise RuntimeError(
            f"All DNS resolvers failed for {PDNS_QUERY_RECORD}. "
            f"ME error: {me_status_read_error}, VNK error: {vnk_status_read_error}"
        )


def collect_read_availability():

    global avail_read_error

    logger.info(f">>> collect_read_availability() starting")
    today_date = datetime.now().strftime("%Y/%m/%d")
    data = retry(
            lambda: query_grafana(
                datastore_uid=GRAFANA_PROM_DS,
                promql=READ_STATUS_PROMQL,
                last_minutes=READ_AVAILABILITY_COLLECTION_INTERVAL
            ),
            max_attempts=5
        )

    frames = (
        data.get("results", {})
        .get("A", {})
        .get("frames", [])
    )

    if not frames:
        avail_read_error = f'no data returned after querying grafana for {READ_STATUS_PROMQL}'
        pdns_24h_availability_percent.labels(
            role="secondary",
            func="read",
            date=today_date
        ).set(-1)

        raise RuntimeError(avail_read_error)

    values = frames[0].get("data", {}).get("values", [])
    if len(values) < 2:
        avail_read_error = f"unexpected Grafana response structure: {frames[0]}"
        pdns_24h_availability_percent.labels(
            role="secondary",
            func="read",
            date=today_date
        ).set(-1)

        raise RuntimeError(avail_read_error)

    metrics = values[1]

    if len(metrics) < READ_AVAILABILITY_COLLECTION_INTERVAL:
        avail_read_error = f"expected {READ_AVAILABILITY_COLLECTION_INTERVAL} samples, got {len(metrics)}"

        pdns_24h_availability_percent.labels(
            role="secondary",
            func="read",
            date=today_date
        ).set(-1)

        raise RuntimeError(avail_read_error)

    original_up = sum(metrics)
    original_total = len(metrics)
    original_availability = round((original_up / original_total) * 100, 4)


    logger.info(
        "Read Availability | total samples=%s up samples=%s availability=%s",
        original_total,
        original_up,
        original_availability
    )

    pdns_24h_availability_percent.labels(
        role="secondary",
        func="read",
        date=today_date
    ).set(original_availability)

    pdns_24h_availability_samples_up.labels(
        role="secondary",
        func="read",
        date=today_date
    ).set(original_up)

    pdns_24h_availability_samples_total.labels(
        role="secondary",
        func="read",
        date=today_date
    ).set(original_total)


def collect_write_status():

    global me_status_write_error
    global vnk_status_write_error

    logger.info(f">>> collect_write_status() starting")
    json_data_write = {}

    for dns_name in ["me-pri-pdns"]:

        try:
            success, _ = retry(
                lambda: pdns_write_test(PDNS_ADDR, PDNS_TOKEN, PDNS_WRITE_RECORD, "127.0.0.127"),
                max_attempts=2
            )
            error = 'N/A'

        except Exception as err:
            success = False
            error = f"{type(err).__name__}: {err}"

        json_data_write[dns_name] = {
            "success": success,
            "error": error
        }

    logger.info("DNS record creation and deletion: %s", json.dumps(json_data_write, indent=4))

    me_write_success = json_data_write["me-pri-pdns"]["success"]
    #vnk_write_success = json_data_write["vnk-pri-pdns"]["success"]

    me_status_write_error = json_data_write["me-pri-pdns"]["error"]
    #vnk_status_write_error = json_data_write["vnk-pri-pdns"]["error"]


    # No Data
    if me_write_success is None:# or vnk_write_success is None:
        pdns_write_current_status.labels(role="primary",
                                        datacenter="Miremad"
                                        ).set(-1)
        raise RuntimeError(
            f"No data returned for pdns_write_test() "
            f"ME error: {me_status_write_error}"#, VNK error: {vnk_status_read_error}"
        )

    # ME & VNK UP
    if me_write_success:# and vnk_read_success:
        pdns_write_current_status.labels(role="primary",
                                        datacenter="Miremad"
                                        ).set(1)
        return

    # ME UP & VNK DOWN
    # elif me_write_success and not vnk_write_success:
    #     pdns_write_current_status.labels(role="primary",
    #                                     datacenter="Miremad"
    #                                     ).set(1)
    #     return

    # ME DOWN & VNK UP
    # elif not me_write_success and vnk_write_success:
    #     pdns_write_current_status.labels(role="primary",
    #                                     datacenter="Miremad"
    #                                     ).set(1)
    #     return

    # ME DOWN & VNK DOWN
    elif not me_write_success:# and not vnk_write_success:
        pdns_write_current_status.labels(role="primary",
                                        datacenter="Miremad"
                                        ).set(0)
        raise RuntimeError(
            f"Primary DNS servers failed to create and delete {PDNS_WRITE_RECORD}. "
            f"ME error: {me_status_write_error}"#, VNK error: {vnk_status_read_error}"
        )


def collect_write_availability():

    global avail_write_error

    logger.info(f">>> collect_write_availability() starting")
    today_date = datetime.now().strftime("%Y/%m/%d")
    data = retry(
            lambda: query_grafana(
                datastore_uid=GRAFANA_PROM_DS,
                promql=WRITE_STATUS_PROMQL,
                last_minutes=WRITE_AVAILABILITY_COLLECTION_INTERVAL
            ),
            max_attempts=5
        )

    frames = (
        data.get("results", {})
        .get("A", {})
        .get("frames", [])
    )

    if not frames:
        avail_write_error = f'no data returned after querying grafana for {WRITE_STATUS_PROMQL}'
        pdns_24h_availability_percent.labels(
            role="primary",
            func="write",
            date=today_date
        ).set(-1)

        raise RuntimeError(avail_write_error)

    values = frames[0].get("data", {}).get("values", [])
    if len(values) < 2:
        avail_write_error = f"unexpected Grafana response structure: {frames[0]}"
        pdns_24h_availability_percent.labels(
            role="primary",
            func="write",
            date=today_date
        ).set(-1)

        raise RuntimeError(avail_write_error)

    metrics = values[1]

    if len(metrics) < WRITE_AVAILABILITY_COLLECTION_INTERVAL:
        avail_write_error = f"expected {WRITE_AVAILABILITY_COLLECTION_INTERVAL} samples, got {len(metrics)}"

        pdns_24h_availability_percent.labels(
            role="primary",
            func="write",
            date=today_date
        ).set(-1)

        raise RuntimeError(avail_write_error)

    original_up = sum(metrics)
    original_total = len(metrics)
    original_availability = round((original_up / original_total) * 100, 4)

    logger.info(
        "Write Availability | total samples=%s up samples=%s availability=%s",
        original_total,
        original_up,
        original_availability
    )

    pdns_24h_availability_percent.labels(
        role="primary",
        func="write",
        date=today_date
    ).set(original_availability)

    pdns_24h_availability_samples_up.labels(
        role="primary",
        func="write",
        date=today_date
    ).set(original_up)

    pdns_24h_availability_samples_total.labels(
        role="primary",
        func="write",
        date=today_date
    ).set(original_total)



# --------------------------------------------
# Threads
# --------------------------------------------

# Collect PowerDNS Read Status
threading.Thread(
    target=collector_loop,
    args=(
        collect_read_status,
        READ_STATUS_COLLECTION_INTERVAL,
        "secondary",
        "status"
    ),
    daemon=True,
    name="pdns-read-status-thread"
).start()

# Collect PowerDNS Read Availability
threading.Thread(
    target=collector_loop,
    args=(
        collect_read_availability,
        READ_AVAILABILITY_COLLECTION_INTERVAL,
        "secondary",
        "availability"
    ),
    daemon=True,
    name="pdns-read-availability-thread"
).start()

# Collect PowerDNS Write Status
threading.Thread(
    target=collector_loop,
    args=(
        collect_write_status,
        WRITE_STATUS_COLLECTION_INTERVAL,
        "primary",
        "status"
    ),
    daemon=True,
    name="pdns-write-status-thread"
).start()

# Collect PowerDNS Write Availability
threading.Thread(
    target=collector_loop,
    args=(
        collect_write_availability,
        WRITE_AVAILABILITY_COLLECTION_INTERVAL,
        "primary",
        "availability"
    ),
    daemon=True,
    name="pdns-write-availability-thread"
).start()



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

# gunicorn -w 1 --threads 2 --timeout 10 -b 0.0.0.0:5335 file_name:app