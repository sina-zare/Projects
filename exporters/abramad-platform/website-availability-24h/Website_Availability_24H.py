import numpy as np
import traceback
import requests
import time
import os
# import json
from datetime import datetime, timedelta
from requests.exceptions import RequestException
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter

# --- Configuration ---
script_name = 'website-availability'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'https://vnk-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
datacenter = 'vanak_&_miremad'
target = 'website_url'

# Create a registry for our custom metrics
registry = CollectorRegistry()

# Metrics
# General
duration_gauge = Gauge('script_exec_duration_seconds', 'Duration of my script', registry=registry)
status_gauge = Gauge('script_success', 'Whether script succeeded (1) or failed (0)', registry=registry)
total_execution_counter = Counter('script_total_execs', 'Total number of times the script has run',
                                  registry=registry)
total_failed_execution_counter = Counter('script_total_failed_execs',
                                         'Total number of times the script has failed to finish gracefully',
                                         registry=registry)
last_error_message = Gauge('script_last_error_message',
                           'The last error message encountered during script execution',
                           ['error_summary', 'error_detail'], registry=registry)

# App Specific
website_availability_24h_percent = Gauge('website_availability_24h_percent',
                             'availability of website for previous day in percent',
                             ['host', 'date'],
                             registry=registry)
website_availability_24h_samples_total = Gauge('website_availability_24h_samples_total',
                             'total samples of website status for previous day',
                             ['host', 'date'],
                             registry=registry)
website_availability_24h_samples_up = Gauge('website_availability_24h_samples_up',
                             'total up samples of website status for previous day',
                             ['host', 'date'],
                             registry=registry)


website_availability_24h_revised_percent = Gauge('website_availability_24h_revised_percent',
                                     'revised availability of website for previous day in percent',
                                     ['host', 'date'],
                                     registry=registry)
website_availability_24h_revised_samples_total = Gauge('website_availability_24h_revised_samples_total',
                             'total revised samples of website status for previous day',
                             ['host', 'date', 'chunk'],
                             registry=registry)
website_availability_24h_revised_samples_up = Gauge('website_availability_24h_revised_samples_up',
                             'total revised up samples of website status for previous day',
                             ['host', 'date', 'chunk'],
                             registry=registry)


# Simulate your script logic
start_time = time.time()
success = True
error_string_summary = ""
error_string_detail = ""


def read_value_from_file(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)  # Create the directory if it doesn't exist
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.write('0')
        return 0
    try:
        with open(file_path, 'r') as f:
            return int(f.read().strip())
    except ValueError:
        # In case of a corrupt or non-integer value
        return 0


def write_value_to_file(file_path, value):
    with open(file_path, 'w') as f:
        f.write(str(value))

def push_metrics():

    push_to_gateway(
        gateway=pushgateway_url,
        job=job_name,
        grouping_key={
            'instance': instance,
            'target': target
        },
        registry=registry
    )

def retry(
    func,
    max_attempts=5,
    initial_delay=2,
    backoff_factor=2,
    exceptions=(Exception,),
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


def query_grafana(grafana_url, datastore_uid, zbx_host, zbx_group, last_days=0, last_hours=0, last_minutes=0):
    time_from = int((datetime.now() - timedelta(days=last_days, hours=last_hours,
                                                minutes=last_minutes)).timestamp() * 1000)  # in ms
    time_to = int(datetime.now().timestamp() * 1000)

    payload = {
        "queries": [
            {
                "refId": "A",
                "datasource": {
                    "type": "alexanderzobnin-zabbix-datasource",
                    "uid": f"{datastore_uid}"
                },
                "queryType": "0",
                "host": {"filter": f"{zbx_host}"},
                "item": {"filter": "Failed step of scenario \"Web_Check\"."},
                "group": {"filter": f"{zbx_group}"},

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
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    def _request():
        r = requests.post(
            f"{grafana_url}/api/ds/query",
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
        max_attempts=5,
        initial_delay=2,
        exceptions=(
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
        )
    )


def site_availability(host_iterable, duration_days=0, duration_hours=0, duration_minutes=0):
    results = []

    for host in host_iterable:
        try:
            today_date = datetime.now().strftime("%Y/%m/%d")
            data = query_grafana(grafana_url=grafana_addr,
                                 datastore_uid=host["ds_uid"],
                                 zbx_host=host["host"],
                                 zbx_group=host["group"],
                                 last_days=duration_days,
                                 last_hours=duration_hours,
                                 last_minutes=duration_minutes)
        except Exception as e:
            print(f"Failed collecting {host['host']}: {e}")
            continue

        frames = data.get("results", {}).get("A", {}).get("frames", [])
        if not frames:
            results.append({
                "host": host["host"],
                "availability": None,
                "error": "No data returned"
            })
            continue

        values = frames[0]["data"]["values"]

        # timestamps = values[0]
        metrics = values[1]

        readable_metrics = []
        for v in metrics:
            if v == 0:
                readable_metrics.append(v + 1)
            elif v == 1:
                readable_metrics.append(v - 1)

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
        chunk_size = host.get("chunk", 3)
        remainder = len(readable_metrics) % chunk_size

        if remainder != 0:
            trimmed_metrics = readable_metrics[:-remainder]
        else:
            trimmed_metrics = readable_metrics

        if len(trimmed_metrics) == 0:
            print("Not enough samples")
            continue

        arr = np.array(trimmed_metrics)
        chunks = arr.reshape(-1, chunk_size)

        # print(f'Original Metrics')
        # for t, v in zip(timestamps, readable_metrics):
        #     print(f'\t{t} {v}')
        #
        # print(f'\n{chunks}')
        # print(f'\nOriginal Availability)\n\tSamples: {sum(readable_metrics)}/{len(readable_metrics)}\n\tResult: {res} %')

        revised_metrics = []
        for chunk_list in chunks:
            # print(f'Chunk: {chunk_list} | Sum: {sum(chunk_list)}')
            if sum(chunk_list) > 0:
                revised_metrics.append(1)
            else:
                revised_metrics.append(0)

        original_result = round((sum(readable_metrics) / len(readable_metrics) * 100), 4)
        revised_result = round((sum(revised_metrics) / len(revised_metrics) * 100), 4)
        print(
            f'{host["host"]})\nRevised Availability\n\tSamples: {sum(revised_metrics)}/{len(revised_metrics)}\n\tDate: {today_date}\n\tResult: {revised_result} %\n\n')

        results.append({
            "host": host["host"],
            "original_availability": original_result,
            "revised_availability": revised_result,
            "original_total_samples": len(readable_metrics),
            "original_up_samples": sum(readable_metrics),
            "revised_total_samples": len(revised_metrics),
            "revised_up_samples": sum(revised_metrics),
            "chunk_size": chunk_size,
            "date": today_date,
        })

    return results


try:
    grafana_addr = "https://vnk-grafana.abramad.com"
    api_key = "xyz"

    host_dict = [
        {'host': 'Abramad-Website', 'group': 'Internal_Services', 'ds_uid': 'ffmenurs6lts0a', 'chunk': 3},
        {'host': 'Abramad-CloudWebsite', 'group': 'Cloud_Internal_Services', 'ds_uid': 'ffmenurs6lts0a', 'chunk': 3},
        {'host': 'AbramadCloud-Shahkar', 'group': 'Cloud_Internal_Services', 'ds_uid': 'dfmenqykyvrpcf', 'chunk': 3},
        {'host': 'AbramadCloud-ECS01', 'group': 'Cloud_Internal_Services', 'ds_uid': 'ffmenurs6lts0a', 'chunk': 3},
        {'host': 'AbramadCloud-ECS02', 'group': 'Cloud_Internal_Services', 'ds_uid': 'ffmenurs6lts0a', 'chunk': 3},
    ]

    availability_results_24h = site_availability(host_dict, duration_days=1)

    # Last 24 Hour
    for r_24 in availability_results_24h:
        print(f'Last 24 Hour:\n\t{r_24}')

        website_availability_24h_percent.labels(
            host=r_24.get("host", "N/A"),
            date=r_24.get("date", "N/A"),
        ).set(r_24.get("original_availability", -1))

        website_availability_24h_samples_total.labels(
            host=r_24.get("host", "N/A"),
            date=r_24.get("date", "N/A"),
        ).set(r_24.get("original_total_samples", 0))

        website_availability_24h_samples_up.labels(
            host=r_24.get("host", "N/A"),
            date=r_24.get("date", "N/A"),
        ).set(r_24.get("original_up_samples", 0))



        website_availability_24h_revised_percent.labels(
            host=r_24.get("host", "N/A"),
            date=r_24.get("date", "N/A"),
        ).set(r_24.get("revised_availability", -1))

        website_availability_24h_revised_samples_total.labels(
            host=r_24.get("host", "N/A"),
            date=r_24.get("date", "N/A"),
            chunk=r_24.get("chunk", "N/A"),
        ).set(r_24.get("revised_total_samples", 0))

        website_availability_24h_revised_samples_up.labels(
            host=r_24.get("host", "N/A"),
            date=r_24.get("date", "N/A"),
            chunk=r_24.get("chunk", "N/A"),
        ).set(r_24.get("revised_up_samples", 0))

        # if r_24.get("revised_availability", -1) == -1: # No data
        #     website_availability_24h.labels(host=r_24.get("host", "N/A")).set(4)
        # elif 0 <= r_24.get("revised_availability", -1) <= 91.6667: # Over 2h downtime per 24 hour
        #     website_availability_24h.labels(host=r_24.get("host", "N/A")).set(1)
        # elif 91.6668 <= r_24.get("revised_availability", -1) <= 97.9: # Less than 30m downtime per 24 hour
        #     website_availability_24h.labels(host=r_24.get("host", "N/A")).set(2)
        # elif 97.91 <= r_24.get("revised_availability", -1) <= 100: # Almost no downtime
        #     website_availability_24h.labels(host=r_24.get("host", "N/A")).set(0)


except Exception as e:
    success = False
    error_string_summary += f"{type(e).__name__}: {e}"

    # Get the traceback and extract the last traceback frame
    tb = traceback.extract_tb(e.__traceback__)
    last_call = tb[-1]  # the last traceback frame, where the exception occurred
    error_string_detail += f"Error occurred in line {last_call.lineno}: {last_call.line}"
    print(f"Script failed: {error_string_summary}\n{error_string_detail}")


finally:
    # Finalizing Metrics
    # Script Duration
    duration = time.time() - start_time
    duration_gauge.set(duration)

    # Script Success Status
    status_gauge.set(1 if success else 0)

    # Script Total Executions
    total_exec_counts = read_value_from_file(total_exec_counter_file) + 1
    write_value_to_file(total_exec_counter_file, total_exec_counts)
    total_execution_counter.inc(total_exec_counts)

    if not success:
        # Script Total Failed Executions
        total_failed_exec_counts = read_value_from_file(total_failed_exec_counter_file) + 1
        write_value_to_file(total_failed_exec_counter_file, total_failed_exec_counts)
        total_failed_execution_counter.inc(total_failed_exec_counts)

        # Script Last Error Message
        last_error_message.labels(error_summary=error_string_summary, error_detail=error_string_detail).set(1)

    elif success:
        # Script Total Failed Executions
        total_failed_exec_counts = read_value_from_file(total_failed_exec_counter_file)
        total_failed_execution_counter.inc(total_failed_exec_counts)

        # Script Last Error Message
        last_error_message.labels(error_summary="None", error_detail="None").set(0)

    # Push metrics to Pushgateway
    retry(
        push_metrics,
        max_attempts=5,
        initial_delay=5,
        exceptions=(Exception,)
    )
    print(f'Metrics sent to {pushgateway_url}')
