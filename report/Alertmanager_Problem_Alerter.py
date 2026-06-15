from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter
from datetime import datetime, timezone, timedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from tabulate import tabulate
import pprint as pp
import traceback
import pyzipper
import requests
import smtplib
import json
import time
import csv
import os


# --- Configuration ---
script_name = 'alertmanager_problem_alerter'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'https://vnk-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
datacenter = 'me_vanak'
target = 'alertmanager'

# Create a registry for our custom metrics
registry = CollectorRegistry()

# Define metrics
duration_gauge = Gauge('script_exec_duration_seconds', 'Duration of my script', registry=registry)
status_gauge = Gauge('script_success', 'Whether script succeeded (1) or failed (0)', registry=registry)
total_execution_counter = Counter('script_total_execs', 'Total number of times the script has run',registry=registry)
total_failed_execution_counter = Counter('script_total_failed_execs', 'Total number of times the script has failed to finish gracefully',registry=registry)
last_error_message = Gauge('script_last_error_message', 'The last error message encountered during script execution', ['error_summary', 'error_detail'], registry=registry)

# Simulate your script logic
start_time = time.time()
success = True
error_string_summary = ""
error_string_detail = ""

# Zipper function
def make_zip(files, zip_name, password):
    with pyzipper.AESZipFile(zip_name, 'w', compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES) as zf:
        zf.setpassword(password.encode())

        for file_path in files:
            file_name = os.path.basename(file_path)  # <- keeps only filename
            zf.write(file_path, arcname=file_name)  # <- overrides path inside ZIP


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


def send_anonymous_email(from_email, to_email, cc_email, subject, html_message, direction,
                         mail_server='mail.abramad.com', attachments=None):
    global error_string_summary
    global error_string_detail
    global success

    try:
        ##############################################
        ######### HTML Body Begin For Email ##########
        html_line_break = '''
                                <p><br></p>
                            '''
        html_msg_1 = f'''
                            <html dir={direction}>
                              <head>
                                <style>
                                    table {{
                                        width: 100%;
                                        border-collapse: collapse;
                                        font-family: Arial, sans-serif;
                                    }}
                                    th, td {{
                                        border: 1px solid #dddddd;
                                        text-align: left;
                                        padding: 8px;
                                    }}
                                    th {{
                                        background-color: #f2f2f2;
                                    }}
                                    .severity-critical {{
                                        background-color: #f8d7da;
                                    }}
                                    .severity-average {{
                                        background-color: #ffe3cd;
                                    }}
                                    .severity-warning {{
                                        background-color: #fff3cd;
                                    }}
                                </style>
                              </head>
                              <body>
                            '''
        html_msg_2 = f'''
                                <p  style="font-family: DiodrumArabic-Regular">{html_message}</p>
                            '''
        html_msg_3 = f'''
                                '''
        html_msg_4 = '''
                              </body>
                            </html>
                            '''
        ######### HTML Body End For Email ##########
        ############################################

        email_body = html_msg_1 + html_msg_2 + html_line_break + html_line_break + html_msg_3 + html_msg_4

        # Split email addresses into lists
        to_email_list = to_email.split(",") if to_email else []
        cc_email_list = cc_email.split(",") if cc_email else []
        all_recipients = to_email_list + cc_email_list

        # Create the email message
        msg = MIMEMultipart()
        msg["From"] = Header(from_email, "utf-8")
        msg["To"] = Header(", ".join(to_email_list), "utf-8")
        msg["CC"] = Header(", ".join(cc_email_list), "utf-8")
        msg["Subject"] = Header(subject, "utf-8")

        # Attach HTML body
        msg.attach(MIMEText(email_body, "html", "utf-8"))

        # Attach files if any
        if attachments:
            for attachment in attachments:
                if os.path.exists(attachment):
                    with open(attachment, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(attachment))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment)}"'
                        msg.attach(part)
                else:
                    print(f"Warning: Attachment {attachment} not found.")

        # Connect to the mail server and send the email
        with smtplib.SMTP(mail_server, 25) as server:
            server.sendmail(from_email, all_recipients, msg.as_string())
            print("Email sent successfully.")

    except Exception as err:
        print(f"email_sender Function Error: {err}")
        print(f"Exception type: {type(err).__name__}")

        print(f"Script failed: {err}")
        success = False
        error_string_summary += f" {type(err).__name__}: {err}"

        # Get the traceback and extract the last traceback frame
        tb = traceback.extract_tb(err.__traceback__)
        last_call = tb[-1]  # the last traceback frame, where the exception occurred
        error_string_detail += f" Error 'email_sender' in line {last_call.lineno}: {last_call.line}"


def get_alerts(alertmanager_url, overdue=0):
    global error_string_summary
    global error_string_detail
    global success

    try:
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

                    if age.days >= overdue:
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
                            'severity': severity,
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
            print(tabulate(alert_str, headers=["Total", f"Over {overdue} Days"], tablefmt="rounded_outline"))

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



# Main App
try:
    today_date = str(datetime.now().strftime('%Y-%m-%d')).replace('-', '_')
    output_dir = 'C://Temp//Alertmanager_Alerts'
    os.makedirs(output_dir, exist_ok=True)
    zip_pass = 'iUJ18dE^kar^)D-<<*$@>*'

    error_receivers = 'sysops@abramad.com'
    error_cc = 'sina.z@abramad.com'
    default_cc = 'sysops@abramad.com,admin@abramad.com,opsassistant@abramad.com'
    from_email = 'AlertManager@abramad.com'

    alertmanager_urls = {
        'VNK-Alertmanager': 'http://172.29.6.16:9093/api/v2/alerts',
        'ME-Alertmanager': 'http://172.17.234.37:9093/api/v2/alerts',
                         }

    email_dict = {
        'sysops': 'sysops@abramad.com',
        'network': 'network@abramad.com',
        'system': 'system@abramad.com',
        'development': 'development@abramad.com',
        'support': 'support@abramad.com',
        'csb': 'csb@abramad.com',
        'csb_storage_sds': 'sds@abramad.com',
        'security': 'Security@abramad.com',
        'iaas': 'openstack@abramad.com',
        'mlp': 'mlplatform@abramad.com',
        'paas': 'kubernetes@abramad.com',
        'ceph': 'sds@abramad.com',
        'noc': 'noc@abramad.com',
        'caas': 'caas@abramad.com',
        'datacenter': 'datacenter@abramad.com',
        'no_name': 'sysops@abramad.com',
        # 'Platform_Team': 'ProductMGMT@abramad.com',
        # 'SGIS_Team': 'foroughe@systemgroup.net,ramins@systemgroup.net',
        # 'Cloud_Services_Team': 'ProductDevelopment@abramad.com',
        # 'EPM_Team': 'epm@abramad.com',
        # 'ITSM_Team': 'itsm@abramad.com',
    }

    days_over = 10

    for alertmanager_name, alertmanager_url in alertmanager_urls.items():
        print(f'Connecting to {alertmanager_name}')

        problems = get_alerts(alertmanager_url, days_over)
        for team, alert_list in problems.items():
            print(f'*** {team} ***')
            html_tbl = f'''
                <table>
                <tr>
                    <th>Instance</th>
                    <th>Problem</th>
                    <th>Severity</th>
                    <th>Time</th>
                    <th>Age</th>
                </tr>
                '''

            # Open CSV file for writing
            csv_file_path = f'{output_dir}//{team.upper()}_Alerts_{alertmanager_name.replace('-', '_')}_{today_date}.csv'
            with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Instance", "Problem", "Severity", "Time", "Age"])

                for alert in alert_list:

                    # Write to CSV
                    writer.writerow([alert.get('instance', 'N/A'),
                                     f'{alert.get('alert', 'N/A')} | Env: {alert.get('env', 'N/A')}',
                                     alert.get('severity', 'N/A'),
                                     alert.get('time', 'N/A'),
                                     alert.get('age', 'N/A')])

                    html_tbl += f"""
                            <tr class="severity-{alert.get('severity', 'N/A')}">
                                <td>{alert.get('instance', 'N/A')}</td>
                                <td>Name: {alert.get('alert', 'N/A')} | Env: {alert.get('env', 'N/A')}</td>
                                <td>{alert.get('severity', 'N/A')}</td>
                                <td>{alert.get('time', 'N/A')}</td>
                                <td>{alert.get('age', 'N/A')}</td>
                            </tr>
                        """

            html_tbl += """
                        </table>
                        """

            html_msg = f"""
                        <h2>{team.upper()} alerts over {days_over} days</h2>
                        <p>Dear {team.upper()} Team<br>Please address the issues on {alertmanager_name}. Number of alerts: {len(alert_list)}<br>Password of the attached file is shared with you in password manager as 'AlertManager_Scripts_ZIP_Password'</p>
                    """

            html = html_msg + html_tbl

            zip_file_path = f'{output_dir}//{team.upper()}_Alerts_{alertmanager_name.replace('-', '_')}_{today_date}.zip'

            # Zipping files with password
            files = [csv_file_path]
            make_zip(files, zip_file_path, zip_pass)


            send_anonymous_email(
                from_email=from_email,
                to_email='sina.z@abramad.com',#email_dict[team],
                cc_email='sina.z@abramad.com',#default_cc,
                subject=f"Alertmanager Alerts Over {days_over} days | {team} | {alertmanager_name}",
                html_message=html,
                direction="ltr",
                attachments=[zip_file_path]
            )

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

