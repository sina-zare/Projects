from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from email.mime.text import MIMEText
from email.header import Header
from pyzabbix import ZabbixAPI
import traceback
import smtplib
import time
import csv
import os
import pyzipper

# --- Configuration ---
script_name = 'zabbix_problem_alerter'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'https://me-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
datacenter = 'me_vanak'
target = 'zabbix_problems'

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

error_receivers = 'abramadsysops@abramad.com'
error_cc = 'sina.z@abramad.com'
default_cc = 'abramadsysops@abramad.com,admin@abramad.com,opsassistant@abramad.com'
from_email = 'ZabbixProblems@abramad.com'

try:

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


    def decryptor(enc_env_var, key_env_var):
        # Load the key
        key = os.environ.get(key_env_var)
        encryption_key = Fernet(key)
        encrypted_password = (os.environ.get(enc_env_var)).encode()
        # Decrypt Data
        decrypted_password = encryption_key.decrypt(encrypted_password.decode())

        return decrypted_password.decode()


    def send_anonymous_email(from_email, to_email, cc_email, subject, html_message, direction,
                             mail_server='mail.abramad.com', attachments=None):
        global error_string_summary
        global error_string_detail

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
                                        .severity-High {{
                                            background-color: #f8d7da;
                                        }}
                                        .severity-Average {{
                                            background-color: #ffe3cd;
                                        }}
                                        .severity-Warning {{
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
            error_string_detail += f" Error 'email_sender' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"


    today_date = str(datetime.now().strftime('%Y-%m-%d')).replace('-', '_')
    ten_days_in_seconds = 10 * 24 * 60 * 60  # 864,000 seconds
    severity_dict = {
        '0': 'Not Classified',
        '1': 'Information',
        '2': 'Warning',
        '3': 'Average',
        '4': 'High',
        '5': 'Disaster'
    }

    email_dict = {
        'SYSOPS_Team': 'sysops@abramad.com',
        'Network_Team': 'network@abramad.com',
        'System_Team': 'system@abramad.com',
        'Platform_Team': 'ProductMGMT@abramad.com',
        'SGIS_Team': 'foroughe@systemgroup.net,ramins@systemgroup.net',
        'Development_Team': 'development@abramad.com',
        'ITSM_Team': 'itsm@abramad.com',
        'Support_Team': 'support@abramad.com',
        'CSB_Team': 'csb@abramad.com',
        'Security_Team': 'Security@abramad.com',
        'IaaS_Team': 'openstack@abramad.com',
        'Datacenter_Team': 'datacenter@abramad.com',
        'MLP_Team': 'mlplatform@abramad.com',
        'PaaS_Team': 'kubernetes@abramad.com',
        'Ceph_Team': 'sds@abramad.com',
        'SGAI_Team': '',
        'EPM_Team': 'epm@abramad.com',
        'CaaS_Team': 'caas@abramad.com',
        'Cloud_Services_Team': 'ProductDevelopment@abramad.com',
        'CRE_Team': 'cre@abramad.com',
        'Sale_Team': 'sales@abramad.com',
        'Product_Team': 'product@abramad.com',
    }

    output_dir = 'C://Temp//Zabbix_Problems'
    os.makedirs(output_dir, exist_ok=True)  # Create the directory if it doesn't exist
    # Zip file path
    zip_pass = "uS8#N@H2k(2M)8&nL]'Z;"


    zabbix_servers = {
        'VNK-Zabbix': "https://vnk-zabbix.abramad.com",
        'VNK-CustomerZabbix': 'http://172.29.6.15',
        'ME-Zabbix': 'http://172.17.234.13/zabbix/',
        'ME-CustomerZabbix': 'http://172.17.234.23'
    }

    # Zabbix credentials
    username = 'sysops-svc'
    passphrase = decryptor('sysops-svc_enc', 'sysops-svc_key')

    for zabbix_server_name, zabbix_server_address in zabbix_servers.items():
        # Connect to Zabbix API
        zapi = ZabbixAPI(zabbix_server_address)
        zapi.login(username, passphrase)
        print(f"Connected to Zabbix API Version {zapi.api_version()}")



        # Get all host groups
        host_groups = zapi.hostgroup.get(output=["groupid", "name"])

        for group in host_groups:
            if 'team' in group['name'].lower():
                print(f"\nHost Group: {group['name']}")

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


                print(zabbix_server_name)
                if problems:
                        problem_counter = 0
                        html_table_is_valid = False
                        html_tbl = f'''
                                <table>
                                <tr>
                                    <th>Host</th>
                                    <th>Problem</th>
                                    <th>Severity</th>
                                    <th>Time</th>
                                    <th>Age</th>
                                </tr>
                                '''

                        # Open CSV file for writing
                        csv_file_path = f'{output_dir}//{group['name']}_Problems_{zabbix_server_name.replace('-', '_')}_{today_date}.csv'
                        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csvfile:
                            writer = csv.writer(csvfile)
                            writer.writerow(["Host", "Problem", "Severity", "Time", "Age"])

                            for problem in problems:
                                clock = int(problem["clock"])
                                age_seconds = int(datetime.now().timestamp()) - clock

                                if age_seconds > ten_days_in_seconds:
                                    problem_counter += 1
                                    html_table_is_valid = True

                                    # Get host name
                                    triggerid = problem["objectid"]
                                    hostid = trigger_to_host.get(triggerid)
                                    host_name = host_info.get(hostid, "Unknown")

                                    time_str = datetime.fromtimestamp(clock).strftime('%Y-%m-%d %H:%M:%S')
                                    age_str = str(timedelta(seconds=age_seconds))
                                    print(f"  Host: {host_name} | Problem: {problem['name']} | Severity: {severity_dict[problem['severity']]} | Time: {time_str} | Age: {age_str}")

                                    # Write to CSV
                                    writer.writerow([host_name, problem['name'], severity_dict[problem['severity']], time_str, age_str])

                                    html_tbl += f"""
                                                <tr class="severity-{severity_dict[problem['severity']]}">
                                                    <td>{host_name}</td>
                                                    <td>{problem['name']}</td>
                                                    <td>{severity_dict[problem['severity']]}</td>
                                                    <td>{time_str}</td>
                                                    <td>{age_str}</td>
                                                </tr>
                                            """

                        html_tbl += """
                                </table>
                                """
                        html_msg = f"""
                            <h2>{group['name'].replace('_', ' ')} Problems Over 10 days</h2>
                            <p>Dear {group['name'].split('_')[0]} Team<br>Please address the issues on {zabbix_server_name}. Number of problems: {problem_counter}<br>Password of the attached file is shared with you in password manager as 'Zabbix_Scripts_ZIP_Password'</p>
                        """

                        html = html_msg + html_tbl

                        zip_file_path = f'{output_dir}//{group['name']}_Problems_{zabbix_server_name.replace('-', '_')}_{today_date}.zip'
                        # Zipping files with password
                        files = [csv_file_path]
                        make_zip(files, zip_file_path, zip_pass)

                        if html_table_is_valid:
                            send_anonymous_email(
                                from_email=from_email,
                                to_email=email_dict[group['name']],
                                cc_email=default_cc,
                                subject=f"Zabbix Problems Over 10 days | {group['name']} | {zabbix_server_name}",
                                html_message=html,
                                direction="ltr",
                                attachments=[zip_file_path]
                            )


                else:
                    print("  No current problems.")


        # Logout
        zapi.user.logout()



except Exception as err:
    print(f"Script failed: {err}")
    print(f"Body Error: {err}")
    print(f"Exception type: {type(err).__name__}")
    traceback.print_exc()
    send_anonymous_email(
        from_email='ScriptError@abramad.com',
        to_email=error_receivers,
        cc_email=error_cc,
        subject=f"Body Error in running {script_name}",
        html_message=f"Error Occurred:<br><b>{err}<br>{traceback.print_exc()}<br>Exception type: {type(err).__name__}</b>",
        direction="ltr",
        # attachments=[]
    )

    success = False
    error_string_summary += f" {type(err).__name__}: {err}"

    # Get the traceback and extract the last traceback frame
    tb = traceback.extract_tb(err.__traceback__)
    last_call = tb[-1]  # the last traceback frame, where the exception occurred
    error_string_detail += f" Error occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"



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
        gateway=pushgateway_url,
        job=job_name,
        grouping_key={'instance': instance, 'target': target, 'datacenter': datacenter},
        registry=registry
    )

    print('✅ Metrics Sent.')



