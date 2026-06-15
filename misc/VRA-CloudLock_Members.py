from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import warnings
import os
import csv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from cryptography.fernet import Fernet
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter
import traceback
import random
import time
import os

# --- Configuration ---
script_name = 'vra_cloudlock_members'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'http://me-prometheus.abramad.com:9091'
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
total_failed_execution_counter = Counter('script_total_failed_execs',
                                         'Total number of times the script has failed to finish gracefully',
                                         registry=registry)
last_error_message = Gauge('script_last_error_message', 'The last error message encountered during script execution',
                           ['error_summary', 'error_detail'], registry=registry)

# Simulate your script logic
start_time = time.time()
success = True
error_string_summary = ""
error_string_detail = ""

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
                             mail_server='mail.abramad.com', attachments=None):
        try:
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

            # Create the email message
            msg = MIMEMultipart()
            msg["From"] = Header(from_email, "utf-8")
            msg["To"] = Header(", ".join(to_email_list), "utf-8")  # For display purposes
            msg["CC"] = Header(", ".join(cc_email_list), "utf-8")  # For display purposes
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
            send_anonymous_email('ScriptErrors@abramad.com', 'abramadsysops@abramad.com', 'sina.z@abramad.com',
                                 f"email_sender Function Error in running All_VMs_Info.py",
                                 f"Error Occurred:<br><b>{err}<br></b> Agent: VRA_CloudLock_Members.py",
                                 'ltr')


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


    username = 'sysops-svc@abramad.com'
    password = decryptor('sysops-svc_enc', 'sysops-svc_key')
    receiver_email = 'support@abramad.com'
    cc_email = 'mehdi.a@abramad.com, alireza.ja@abramad.com, AbramadSysOps@abramad.com'

    # *** Connecting to ME-VC01.Abramad.Com to get the Report ***
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.verify_mode = ssl.CERT_NONE

    # Connecting to vCenter
    MRA_VC = connect.SmartConnect(host='vra-vc01.abramad.com', user=username, pwd=password, port=443,
                                  sslContext=context)
    mra_content = MRA_VC.RetrieveContent()
    mra_vm_view = mra_content.viewManager.CreateContainerView(mra_content.rootFolder, [vim.VirtualMachine], True)
    mra_vms = [vm for vm in mra_vm_view.view if
               (vm.name.startswith("VRA-") or vm.name.startswith("VRF-") or vm.name.startswith("VRT-"))]
    sorted_vms = sorted(mra_vms, key=lambda vm: vm.name.lower())

    cloudlock_servers = []

    for vm in sorted_vms:
        if (vm.name.lower().startswith("vra-cloudlock")):

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
    # test = [cloudlock_servers[1], cloudlock_servers[2]]
    for lock_server in cloudlock_servers:
        try:
            # Define the URL of the web page you want to fetch
            url = f"http://{lock_server[1]}:22352/license_monitoring/sessions.html"

            # create a variable for that cloudlock
            temp = lock_server[0].split(".")
            cloudlock_variable_name = temp[0][4:].lower()
            # print(cloudlock_variable_name)

            # Send a GET request to the URL
            response = requests.get(url)

            # Check if the request was successful
            if response.status_code == 200:
                # Extract the text content from the response
                page_content = response.text

                # Use regular expressions to find all strings starting with "10.X.X.X"
                ip_pattern = r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}"  # Regex pattern to match IP addresses
                cloud_pattern = r">(.*?cloud\.local)<"  # Regex pattern to match strings starting after > and before < and ending with "cloud.local"

                cm_client_ips = re.findall(ip_pattern, page_content)
                # ip_matches.remove(lock_server[1])
                cm_client_fqdns = re.findall(cloud_pattern, page_content)
                # Combine the matched IP addresses and cloud.local strings
                matched_strings = cm_client_ips + cm_client_fqdns

                # Remove duplicates using set and convert to a list
                matched_strings = list(set(matched_strings))

                # making exec variable global so eval() can retrieve it
                # exec(f"global me_{rahlock_variable_name}_customers")
                # creating list for each rahlock
                # exec(f"me_{rahlock_variable_name}_customers = []")
                # take the matched strings and append them to their corresponding list. runs all that comes between " "
                # exec(f"me_{rahlock_variable_name}_customers.append(matched_strings)")
                # append list using eval() to retrieve it
                # rahlock_customers.append(eval(f"me_{rahlock_variable_name}_customers"))

                cloudlock_customers[f"vra_{cloudlock_variable_name}_customers"] = matched_strings

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
            body_err = 'Error description:<br><br>' + f'Host: {lock_server[0].split(".")[0]}<br>' + f'{type(err).__name__}: {err}<br><br>' + f'Error occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}'
            send_anonymous_email(
                from_email="CloudLockMembers@abramad.com",
                to_email=receiver_email,
                cc_email=cc_email,
                subject=f'Error in data gathering of CloudLock server {lock_server[0].split(".")[0]}',
                html_message=body_err,
                direction="ltr"
                # attachments=[attachment]
            )
            continue

    '''
    for key, value in cloudlock_customers.items():
        print(f"Key: {key}")
        for i in value:

            print(f"Value: {i}")
        print("****************")

    #print( 2 / 0)
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

    # Getting cloudlock server members count
    # last_cloudlock_server_name = list(cloudlock_customers.keys())[-1]
    endangered_locks = []

    for cld_lk in cloudlock_customers:
        count_of_items_per_lock_server = len(cloudlock_customers[cld_lk])
        if count_of_items_per_lock_server > 750:
            endangered_locks.append([cld_lk, count_of_items_per_lock_server])

    # print(endangered_locks)
    for srv in endangered_locks:
        # Sending Email

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

    Disconnect(MRA_VC)

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
        grouping_key={'instance': instance, 'target': target, 'datacenter': datacenter},
        registry=registry
    )

    print('✅ Metrics Sent.')

