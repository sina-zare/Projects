from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter
import traceback
import random
import time
import os

# --- Configuration ---
script_name = 'prometheus_pushgw_test02'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'http://127.0.0.1:20091'
job_name = 'python_scripts'
instance = script_name
datacenter = 'vanak'
target = 'vnk_snmp_ilo'


# --- Read script run counter from file ---
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

# --- Write updated count to file ---
def write_value_to_file(file_path, value):
    with open(file_path, 'w') as f:
        f.write(str(value))




# Create a registry for our custom metrics
registry = CollectorRegistry()

# Define metrics
duration_gauge = Gauge('script_exec_duration_seconds', 'Duration of my script', registry=registry)
status_gauge = Gauge('script_success', 'Whether script succeeded (1) or failed (0)', registry=registry)
total_execution_counter = Counter('script_total_execs', 'Total number of times the script has run', registry=registry)
total_failed_execution_counter = Counter('script_total_failed_execs', 'Total number of times the script has failed to finish gracefully', registry=registry)
last_error_message = Gauge('script_last_error_message','The last error message encountered during script execution',['error_summary', 'error_detail'], registry=registry)


# Simulate your script logic
start_time = time.time()
success = True
error_string_summary = ""
error_string_detail = ""

try:
    # Your real logic would go here
    time.sleep(random.uniform(0.5, 5.0))  # simulate work
    #raise Exception("Unfortunate Something broke")
    x = 12 - time.sleep(random.uniform(0.5, 5.0))

except Exception as err:
    print(f"Script failed: {err}")
    success = False
    error_string_summary = f"{type(err).__name__}: {err}"

    # Get the traceback and extract the last traceback frame
    tb = traceback.extract_tb(err.__traceback__)
    last_call = tb[-1]  # the last traceback frame, where the exception occurred
    error_string_detail= f"Error occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"



finally:
    # Finalizing Metrics
    # Script Duration
    duration = time.time() - start_time
    duration_gauge.set(duration)

    #Script Success Status
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
    push_to_gateway(
        gateway='127.0.0.1:20091',
        job=job_name,
        grouping_key={'instance': instance, 'target': target, 'datacenter': datacenter},
        registry=registry
    )
