#import sys
from collections import defaultdict
from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import warnings
#import os
#import csv
#from email.mime.multipart import MIMEMultipart
#from email.mime.text import MIMEText
from cryptography.fernet import Fernet
import smtplib
from email.mime.text import MIMEText
#from email.mime.multipart import MIMEMultipart
#from email.mime.application import MIMEApplication
from email.header import Header
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter
import traceback
import time
import os


# --- Configuration ---
script_name = 'vra_cloudlock_members_monitoring'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'http://vnk-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
datacenter = 'vanak'
target = 'vnk_abri_lock_servers'


# Create a registry for our custom metrics
registry = CollectorRegistry()

# Define metrics
duration_gauge = Gauge('script_exec_duration_seconds', 'Duration of my script', registry=registry)
status_gauge = Gauge('script_success', 'Whether script succeeded (1) or failed (0)', registry=registry)
total_execution_counter = Counter('script_total_execs', 'Total number of times the script has run', registry=registry)
total_failed_execution_counter = Counter('script_total_failed_execs', 'Total number of times the script has failed to finish gracefully', registry=registry)
last_error_message = Gauge('script_last_error_message','The last error message encountered during script execution',['error_summary', 'error_detail'], registry=registry)

# Service Specific Metrics
lock_server_clients_total = Gauge(
    'lock_server_clients_total',
    'The total number of clients connected to a Code Meter server',
    ['lock_server_name', 'lock_server_dongle_count', 'lock_server_dongle_sn'],
    registry=registry
)

lock_server_clients_per_serial = Gauge(
    'lock_server_clients_per_serial',
    'Number of clients per dongle serial number',
    ['lock_server_name', 'dongle_serial_number'],
    registry=registry
)



start_time = time.time()
success = True
error_string_summary = ""
error_string_detail = ""

error_receivers = 'abramadsysops@abramad.com, support@abramad.com'
default_receivers = 'support@abramad.com'
default_cc = 'sina.z@abramad.com'


try:

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
                             mail_server='mail.abramad.com'):
        try:
            global success
            global error_string_summary
            global error_string_detail

            ##############################################
            ######### HTML Body Begin For Email ##########
            html_line_break = '''
                                    <p><br></p>
                                '''
            html_msg_1 = f'''
                                <html dir={direction}>
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

            # Create the MIME email object with HTML content
            msg = MIMEText(email_body, "html", "utf-8")
            msg["From"] = Header(from_email, "utf-8")
            msg["To"] = Header(", ".join(to_email_list), "utf-8")  # For display purposes
            msg["CC"] = Header(", ".join(cc_email_list), "utf-8")  # For display purposes
            msg["Subject"] = Header(subject, "utf-8")

            # Connect to the mail server and send the email
            with smtplib.SMTP(mail_server, 25) as server:
                server.sendmail(from_email, all_recipients, msg.as_string())
                print("Email sent successfully.")


        except Exception as err:
            print(f"email_sender Function Error: {err}")
            print(f"Exception type: {type(err).__name__}")
            traceback.print_exc()
            send_anonymous_email('ScriptError@abramad.com', error_receivers, default_cc,
                                 f"email_sender Function Error in running Zabbix_Add_vCenter_ICMP_Fully_Automated.py",
                                 f"Error Occurred:<br><b>{err}<br>{traceback.print_exc()}<br>Exception type: {type(err).__name__}</b> Agent: Zabbix_Add_vCenter_ICMP_Fully_Automated.py",
                                 'ltr')

            print(f"Script failed: {err}")
            success = False
            error_string_summary += f" {type(err).__name__}: {err}"

            # Get the traceback and extract the last traceback frame
            tb = traceback.extract_tb(err.__traceback__)
            last_call = tb[-1]  # the last traceback frame, where the exception occurred
            error_string_detail += f" Error 'email_sender' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"

    # Credentials
    def decryptor(enc_env_var, key_env_var):
        # Load the key
        key = os.environ.get(key_env_var)
        encryption_key = Fernet(key)
        encrypted_password = (os.environ.get(enc_env_var)).encode()
        # Decrypt Data
        decrypted_password = encryption_key.decrypt(encrypted_password.decode())

        # print(f"Decryped Text: {decrypted_password}")
        return decrypted_password.decode()


    #username = 'support@abramad.com'
    #password = decryptor('support-svc_enc', 'support-svc_key')

    username = 'sysops-svc@abramad.com'
    password = decryptor('sysops-svc_enc', 'sysops-svc_key')

    # *** Connecting to vCenter to get the Report ***
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.verify_mode = ssl.CERT_NONE

    # Connecting to vCenter
    vra_vc = connect.SmartConnect(host='vra-vc01.abramad.com', user=username, pwd=password, port=443, sslContext=context)
    vra_content = vra_vc.RetrieveContent()
    vra_vm_view = vra_content.viewManager.CreateContainerView(vra_content.rootFolder, [vim.VirtualMachine], True)
    vra_vms = [vm for vm in vra_vm_view.view if vm.name.lower().startswith("vra-cloudlock")]
    sorted_vms = sorted(vra_vms, key=lambda vm: vm.name.lower())

    cloudlock_servers = []

    for vm in sorted_vms:

        # retrieve vm IP address
        vm_ip = ""
        if vm.guest is not None:
            for nic in vm.guest.net:
                if nic.ipConfig is not None:
                    for ip in nic.ipConfig.ipAddress:
                        if not ip.ipAddress.startswith('169.254') and not ip.ipAddress.startswith('fe80'):
                            vm_ip = ip.ipAddress

        # retrieve vm Hostname
        vm_hostname = vm.summary.guest.hostName

        cloudlock_servers.append([vm_hostname, vm_ip])


    # ================================================================================
    import requests
    import re

    cloudlock_customers = {}
    for lock_server in cloudlock_servers:
        try:
            # Define the URL of the web page you want to fetch
            url = f"http://{lock_server[1]}:22352/license_monitoring/sessions.html"

            # create a variable for that cloudlock
            cloudlock_hostname = (lock_server[0].split("."))[0]
            #cloudlock_variable_name = cloudlock_hostname[0][4:].lower()
            #print(cloudlock_variable_name)

            # Send a GET request to the URL
            response = requests.get(url)

            # Check if the request was successful
            if response.status_code == 200:
                # Extract the text content from the response
                page_content = response.text

                # Match rows with IPs and serial numbers
                pattern = re.compile(
                    r'<td class="text_left">(?P<ip>\d+\.\d+\.\d+\.\d+)</td>\s*'
                    r'<td class="text_left word_break">\s*\((?P<serial>\d-\d+)\)</td>',
                    re.MULTILINE
                )

                ip_pattern = r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}"  # Regex pattern to match IP addresses starting with "10.X.X.X"
                sn_pattern = r"\(\d-\d+\)"
                cloud_pattern = r">(.*?cloud\.local)<"  # Regex pattern to match strings starting after > and before < and ending with "cloud.local"

                cm_client_ips = list(set(re.findall(ip_pattern, page_content)))

                cm_client_fqdns = list(set(re.findall(cloud_pattern, page_content)))

                cm_sn = set(re.findall(sn_pattern, page_content))
                cm_serial_numbers = [sn.strip("()") for sn in cm_sn]
                if not cm_serial_numbers:
                    cm_serial_numbers = ['No Dongle']

                # Store results in a dictionary
                serial_to_ips = defaultdict(list)
                # Iterate over matches
                for match in pattern.finditer(page_content):
                    serial = match.group("serial")
                    ip = match.group("ip")
                    serial_to_ips[serial].append(ip)

                cloudlock_customers[f"{cloudlock_hostname}"] = {
                    "lock_server_name": cloudlock_hostname,
                    "lock_server_clients_total": (cm_client_ips + cm_client_fqdns),
                    "lock_server_clients_total_count": (len(cm_client_ips) + len(cm_client_fqdns)),
                    "lock_server_dongle_count": len(cm_serial_numbers),
                    "lock_server_dongle_sn": cm_serial_numbers,

                }


                # Adding clients per Serial number
                cloudlock_customers[cloudlock_hostname]['lock_server_clients_by_serial'] = {}
                for serial_number, ip_list in serial_to_ips.items():
                    unique_ips = list(set(ip_list))

                    cloudlock_customers[cloudlock_hostname]['lock_server_clients_by_serial'][serial_number] = {
                        'clients': unique_ips,
                        'client_count': len(unique_ips)
                    }

                if not cloudlock_customers[cloudlock_hostname]['lock_server_clients_by_serial']:
                    cloudlock_customers[cloudlock_hostname]['lock_server_clients_by_serial'][None] = {
                        'clients': [],
                        'client_count': 0
                    }

                # Building Lock Specific metrics
                for key, value in cloudlock_customers.items():
                   print(f"lock_server_name: {value["lock_server_name"]}")
                   print(f"lock_server_clients_total: {value["lock_server_clients_total"]}")
                   print(f"lock_server_clients_total_count: {value["lock_server_clients_total_count"]}")
                   print(f"lock_server_dongle_count: {value["lock_server_dongle_count"]}")
                   print(f"lock_server_dongle_sn: {value["lock_server_dongle_sn"]}")

                   lock_server_clients_total.labels(
                       lock_server_name=value["lock_server_name"],
                       lock_server_dongle_count=value["lock_server_dongle_count"],
                       lock_server_dongle_sn=",".join(value["lock_server_dongle_sn"])
                   ).set(value["lock_server_clients_total_count"])


                   print('lock_server_clients_by_serial:')
                   for serial_number, serial_data in value["lock_server_clients_by_serial"].items():
                       print(f"  Serial Number: {serial_number}")
                       print(f"    Clients: {serial_data['clients']}")
                       print(f"    Client Count: {serial_data['client_count']}")

                       lock_server_clients_per_serial.labels(
                           lock_server_name=value["lock_server_name"],
                           dongle_serial_number=serial_number
                       ).set(serial_data['client_count'])

                print(50 * '#')
            else:
                print("Failed to fetch the web page.")

        except Exception as err:
            print(f"Data gathering error: {err}")
            success = False
            error_string_summary = f"{type(err).__name__}: {err}"

            # Get the traceback and extract the last traceback frame
            tb = traceback.extract_tb(err.__traceback__)
            last_call = tb[-1]  # the last traceback frame, where the exception occurred
            error_string_detail = f"Error occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"
            print(50 * '#')
            continue

    '''
    for key, value in cloudlock_customers.items():
        print(f"Key: {key}")
        for i in value:
    
            print(f"Value: {i}")
        print("****************")
    
    for key, value in cloudlock_customers.items():
    
        # Open CSV file
        with open(f'C:/Users/sina.z/Desktop/Automation_Reports/CloudLock_Members/{key}.csv', 'w', encoding='utf-8_sig',
                  newline='') as f:
    
            # Write header
            writer = csv.writer(f)
            writer.writerow(["VM Names"])
    
            # Write rows from value list
            for data in value:
                writer.writerow([data])
    '''
    """
    # Getting cloudlock server members count
    #last_cloudlock_server_name = list(cloudlock_customers.keys())[-1]
    endangered_locks = []

    for cld_lk in cloudlock_customers:
        count_of_items_per_lock_server = len(cloudlock_customers[cld_lk])
        if count_of_items_per_lock_server > 750:
            endangered_locks.append([cld_lk, count_of_items_per_lock_server])

    #print(endangered_locks)
    for srv in endangered_locks:
        # Sending Email

        receiver_email = 'support@abramad.com'
        error_receivers = 'abramadsysops@abramad.com, support@abramad.com'
        default_cc = 'sina.z@abramad.com'


        ##############################################
        ######### HTML Body Begin For Email ##########
        html_line_break = '''
                                <p><br></p>
                            '''
        html_msg_1s = '''
                            <html dir="rtl">
                            <head>
                                <style>
                                .numeric_class {
                                    direction: ltr;
    
                                </style>
                              </head>
                              <body>
                            '''
        html_msg_2s = '''
                            <p  style="font-family: DiodrumArabic-Regular">با سلام و احترام</p>
                        '''
        html_msg_3s = f'''
                            <p  style="font-family: DiodrumArabic-Regular">با توجه به گسترش فروش و افزایش تعداد سرور های راهکاران ابری و نزدیک شدن به limit تعداد مشترکین ساپورت شده روی هر سرور قفل، نیازمند ایجاد سرور جدیدی در زیرساخت VRA میباشیم.</p>
                        '''
        html_msg_4s = f'''
                            <p  style="font-family: DiodrumArabic-Regular">تعداد سرور هایی که از <b>{(srv[0].replace('_', '-'))[:15]}</b> سرویس میگیرند، <b>{srv[1]}</b> سرور میباشد.</p>
                        '''

        html_msg_8s = f'''
                            <p style="font-family: DiodrumArabic-Regular"></p>
                        '''
        html_msg_9s = '''
                              </body>
                            </html>
                            '''

        ######### HTML Body End For Email ##########
        ############################################

        inform_email_body = html_msg_1s + html_msg_2s + html_msg_3s + html_msg_4s + html_line_break + html_msg_8s + html_line_break + html_msg_9s

        send_anonymous_email(
            from_email="CloudLockMembers@abramad.com",
            to_email=receiver_email,
            cc_email=cc_email,
            subject=f'هشدار ایجاد سرور قفل ابری جدید برای زیرساخت ونک',
            html_message=inform_email_body,
            direction="rtl"
            # attachments=[attachment]
        )

    """
    Disconnect(vra_vc)


except Exception as err:
    print(f"Script failed: {err}")
    success = False
    error_string_summary = f"{type(err).__name__}: {err}"

    # Get the traceback and extract the last traceback frame
    tb = traceback.extract_tb(err.__traceback__)
    last_call = tb[-1]  # the last traceback frame, where the exception occurred
    error_string_detail = f"Error occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"



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

