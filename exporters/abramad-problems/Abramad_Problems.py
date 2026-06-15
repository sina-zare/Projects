from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter
from datetime import datetime, timezone, timedelta
from cryptography.fernet import Fernet
from collections import defaultdict
from pyzabbix import ZabbixAPI
from tabulate import tabulate
import pprint as pp
import traceback
import requests
import json
import time
import os


# --- Configuration ---
script_name = 'abramad_problems'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'https://me-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
datacenter = 'vanak_&_miremad'
target = 'team_alerts'

# Create a registry for our custom metrics
registry = CollectorRegistry()

# Define metrics
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

# Simulate your script logic
start_time = time.time()
success = True
error_string_summary = ""
error_string_detail = ""


def decryptor(enc_env_var, key_env_var):
    # Load the key
    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = (os.environ.get(enc_env_var)).encode()
    # Decrypt Data
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())

    return decrypted_password.decode()


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


def get_alertmanager_alerts(alertmanager_url, overdue_days=0):
    global error_string_summary
    global error_string_detail
    global success

    try:
        print(f'Connecting to {alertmanager_url}')
        target_timezone = timezone(timedelta(hours=3, minutes=30))
        response = requests.get(alertmanager_url, timeout=10)
        response.raise_for_status()
        alerts = response.json()
        # print(f'Response: {response}\nAlerts: {alerts}')
        if not alerts:
            print("✅ No active alerts")
        else:
            overdue_flag = 0
            alert_dict = {}
            for alert in alerts:
                # if alert['labels'].get('team') == 'mlp':
                #     pp.pp(alert)
                #     print(90 * '#' + '\n')
                starts_at_str = alert.get("startsAt")
                age_str = "N/A"
                starts_at_localized = "N/A"

                if starts_at_str:
                    starts_at = datetime.fromisoformat(starts_at_str.replace("Z", "+00:00"))
                    starts_at_localized = \
                    starts_at.replace(tzinfo=timezone.utc).astimezone(target_timezone).isoformat(timespec='seconds',
                                                                                                 sep=' ').split('+')[
                        0]  # Important!

                    now = datetime.now(timezone.utc)
                    # now_localized = now.astimezone(target_timezone)

                    age = now - starts_at
                    # age = now_localized - starts_at_localized

                    if age.days >= overdue_days:
                        overdue_flag += 1
                        # Format nicely: days, hours, minutes
                        days = age.days
                        hours, remainder = divmod(age.seconds, 3600)
                        minutes, _ = divmod(remainder, 60)

                        parts = []
                        if days: parts.append(f"{days}d")
                        if hours: parts.append(f"{hours}h")
                        if minutes: parts.append(f"{minutes}m")
                        if not parts: parts.append("just now")
                        age_str = " ".join(parts)

                        if alert.get('labels').get('vm_name'):
                            instance = alert.get('labels', {}).get('vm_name')
                        elif alert.get('labels').get('exported_instance'):
                            instance = alert.get('labels', {}).get('exported_instance')
                        else:
                            instance = alert.get('labels', {}).get('instance')

                        alert_name = alert.get('labels', {}).get('alertname', 'Unknown')
                        alert_sum = alert.get('annotations', {}).get('summary', 'No_Summary')
                        team_name = alert.get('labels', {}).get('team', 'no_name')
                        environment = alert.get('labels', {}).get('type', 'N/A')
                        severity = alert.get('labels', {}).get('severity', 'N/A')

                        # create empty team name element, if existed append it
                        alert_dict.setdefault(team_name, []).append({
                            'instance': instance,
                            'alert': alert_name,#alert_sum,#alert_name,
                            'severity': severity.lower(),
                            'time': starts_at_localized,
                            'age': age_str,
                            'env': environment
                        })

                        # print(f"- Alert: {alert_name}")
                        # print(f"  Severity: {severity}")
                        # print(f"  Instance: {instance}")
                        # print(f"  Team: {team}")
                        # print(f"  Environment: {environment}")
                        # print(f"  Status: {alert.get('status', {}).get('state', 'N/A')}")
                        # print(f"  StartsAt: {starts_at_localized}")
                        # print(f"  Age: {age_str}")
                        # print("-" * 40)

            alert_str = [[len(alerts), overdue_flag]]
            pp.pp(alert_dict)
            print(tabulate(alert_str, headers=["Total", f"Over {overdue_days} Days"], tablefmt="rounded_outline"))

            return alert_dict

    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        success = False
        error_string_summary += f"{type(e).__name__}: {e}"

        # Get the traceback and extract the last traceback frame
        tb = traceback.extract_tb(e.__traceback__)
        last_call = tb[-1]  # the last traceback frame, where the exception occurred
        error_string_detail += f"Error occurred in line {last_call.lineno}: {last_call.line}"
        print(f"Script failed: {error_string_summary}\n{error_string_detail}")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        success = False
        error_string_summary += f"{type(e).__name__}: {e}"

        # Get the traceback and extract the last traceback frame
        tb = traceback.extract_tb(e.__traceback__)
        last_call = tb[-1]  # the last traceback frame, where the exception occurred
        error_string_detail += f"Error occurred in line {last_call.lineno}: {last_call.line}"
        print(f"Script failed: {error_string_summary}\n{error_string_detail}")

    except KeyError as e:
        print(f"Error: Missing key in alert data: {e}")  # Handle missing keys
        success = False
        error_string_summary += f"{type(e).__name__}: {e}"

        # Get the traceback and extract the last traceback frame
        tb = traceback.extract_tb(e.__traceback__)
        last_call = tb[-1]  # the last traceback frame, where the exception occurred
        error_string_detail += f"Error occurred in line {last_call.lineno}: {last_call.line}"
        print(f"Script failed: {error_string_summary}\n{error_string_detail}")


def get_zabbix_alerts(zbx_url, zbx_username, zbx_password, overdue_days=0):
    global error_string_summary
    global error_string_detail
    global success

    try:
        alert_dict = {}
        overdue_days_seconds = overdue_days * 24 * 60 * 60  # 864,000 seconds
        severity_dict = {
            '0': 'not_classified',
            '1': 'info',
            '2': 'warning',
            '3': 'average',
            '4': 'critical',
            '5': 'disaster'
        }

        # Connect to Zabbix API
        zapi = ZabbixAPI(zbx_url)
        zapi.login(zbx_username, zbx_password)
        print(f"Connected to {zbx_url}\nAPI Version: {zapi.api_version()}")

        # Get all host groups
        host_groups = zapi.hostgroup.get(output=["groupid", "name"])

        for group in host_groups:
            if 'team' in group['name'].lower():
                # print(f"\nHost Group: {group['name']}")

                # Get all triggers for the host group
                triggers = zapi.trigger.get(
                    output=["triggerid", "description"],
                    groupids=group["groupid"],
                    selectHosts=["hostid"],
                    monitored=True
                )

                # Create mapping from triggerid to hostid
                trigger_to_host = {}
                host_ids = set()
                for trigger in triggers:
                    if "hosts" in trigger and trigger["hosts"]:
                        trigger_to_host[trigger["triggerid"]] = trigger["hosts"][0]["hostid"]
                        host_ids.add(trigger["hosts"][0]["hostid"])

                # Get host information
                host_info = {host["hostid"]: host["host"] for host in zapi.host.get(
                    hostids=list(host_ids),
                    output=["hostid", "host"]
                )}

                # Get problems for these triggers
                problems = zapi.problem.get(
                    output=["eventid", "severity", "acknowledged", "name", "clock", "objectid"],
                    objectids=list(trigger_to_host.keys()),
                    sortfield=["eventid"],
                    sortorder="DESC"
                )

                if problems:
                    problem_counter = 0
                    for problem in problems:
                        clock = int(problem["clock"])
                        age_seconds = int(datetime.now().timestamp()) - clock

                        if age_seconds > overdue_days_seconds:
                            problem_counter += 1
                            # Get host name
                            triggerid = problem["objectid"]
                            hostid = trigger_to_host.get(triggerid)
                            host_name = host_info.get(hostid, "Unknown")
                            team_name = group['name'].lower().split('_')[0]
                            alert_name = problem['name']

                            time_str = datetime.fromtimestamp(clock).strftime('%Y-%m-%d %H:%M:%S')
                            age_str = str(timedelta(seconds=age_seconds))
                            severity = severity_dict[problem['severity']]

                            # print(f"""
                            # Host: {host_name}
                            # Problem: {problem['name']}
                            # Severity: {severity_dict[problem['severity']]}
                            # Time: {time_str}
                            # Age: {age_str}
                            # """)

                            # create empty team name element, if existed append it
                            alert_dict.setdefault(team_name, []).append({
                                'instance': host_name,
                                'alert': alert_name,
                                'severity': severity.lower(),
                                'time': time_str,
                                'age': age_str,
                            })

                    alert_str = [[{group['name']}, len(problems), problem_counter]]
                    print(tabulate(alert_str, headers=["Team", "Total", f"Over {overdue_days} Days"], tablefmt="rounded_outline"))

                else:
                    print(f"{group['name']} has No problems.")

        pp.pp(alert_dict)
        return alert_dict

    except Exception as e:
        print(f"Error: Missing key in alert data: {e}")  # Handle missing keys
        success = False
        error_string_summary += f"{type(e).__name__}: {e}"

        # Get the traceback and extract the last traceback frame
        tb = traceback.extract_tb(e.__traceback__)
        last_call = tb[-1]  # the last traceback frame, where the exception occurred
        error_string_detail += f"Error occurred in line {last_call.lineno}: {last_call.line}"
        print(f"Script failed: {error_string_summary}\n{error_string_detail}")




### Main App ###
try:
    # Zabbix credentials
    username = 'sysops-svc'
    passphrase = decryptor('sysops-svc_enc', 'sysops-svc_key')

    zabbix_urls = {
            'VNK-Zabbix': "https://vnk-zabbix.abramad.com",
            'VNK-CustomerZabbix': 'http://172.29.6.15',
            'ME-Zabbix': 'http://172.17.234.13/zabbix/',
            'ME-CustomerZabbix': 'http://172.17.234.23'
        }

    alertmanager_urls = {
            'VNK-Alertmanager': 'http://172.29.6.16:9093/api/v2/alerts',
            'ME-Alertmanager': 'http://172.17.234.37:9093/api/v2/alerts',
                             }

    # Metric Definition
    abramad_team_alerts = Gauge(
                'abramad_team_alerts',
                'returns total number of team alerts per monitoring server',
                ['monitoring_server', 'monitoring_type', 'team', 'severity', 'datacenter'],
                registry=registry
            )

    #today_date = str(datetime.now().strftime('%Y-%m-%d')).replace('-', '_')
    days_over = 0

    # Zabbix
    for zbx_name, zbx_url in zabbix_urls.items():

        if zbx_name.lower().startswith('me-'):
            datacenter = 'Miremad - Asiatech'
        elif zbx_name.lower().startswith('vnk-'):
            datacenter = 'Vanak - P73'

        zbx_problems = get_zabbix_alerts(zbx_url, username, passphrase, days_over)
        for team, alert_list in zbx_problems.items():
            # defaultdict(int) creates a special kind of dictionary where missing keys automatically get the value returned by int(), which is 0.
            severity_dict = defaultdict(int)
            for alert in alert_list:
                severity = alert.get('severity', 'N/A')
                severity_dict[severity] += 1
            for key, value in severity_dict.items():
                #print(f"{key}: {value}")

                abramad_team_alerts.labels(
                    monitoring_server=zbx_name.lower(),
                    monitoring_type='zabbix',
                    team=team,
                    severity=key,
                    datacenter=datacenter,
                ).set(value)


    # Alert Manager
    for alertmanager_name, alertmanager_url in alertmanager_urls.items():

        if alertmanager_name.lower().startswith('me-'):
            datacenter = 'Miremad - Asiatech'
        elif alertmanager_name.lower().startswith('vnk-'):
            datacenter = 'Vanak - P73'

        prometheus_problems = get_alertmanager_alerts(alertmanager_url, days_over)
        for team, alert_list in prometheus_problems.items():
            # defaultdict(int) creates a special kind of dictionary where missing keys automatically get the value returned by int(), which is 0.
            severity_dict = defaultdict(int)
            for alert in alert_list:
                severity = alert.get('severity', 'N/A')
                severity_dict[severity] += 1
            for key, value in severity_dict.items():
                #print(f"{key}: {value}")

                abramad_team_alerts.labels(
                    monitoring_server=alertmanager_name.lower(),
                    monitoring_type='prometheus',
                    team=team,
                    severity=key,
                    datacenter=datacenter,
                ).set(value)


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
    push_to_gateway(
        gateway=pushgateway_url,
        job=job_name,
        grouping_key={'instance': instance, 'target': target},
        registry=registry
    )
    print(f'✅ Metrics sent to {pushgateway_url}')

