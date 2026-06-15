import csv
from email.mime.application import MIMEApplication
from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import warnings
from persiantools.jdatetime import JalaliDate
from jdatetime import datetime, timedelta, date
import smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
from cryptography.fernet import Fernet
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter
import traceback
import time
import os


# --- Configuration ---
script_name = 'vm_delete_alert'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'http://me-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
datacenter = 'miremad'
target = 'me-vc01_customer_vms'


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


    # Get today's date
    today = date.today()
    # Convert to Persian date
    persian_date = JalaliDate.to_jalali(today.year, today.month, today.day)
    # Format the Persian date as "YYYY/MM/DD"
    today_persian_date = persian_date.strftime("%Y/%m/%d")



    def calculate_days_between_dates(start_date, end_date):
        date_format = "%Y/%m/%d"  # Specify the format of the dates
        start_date_obj = datetime.strptime(start_date, date_format)
        end_date_obj = datetime.strptime(end_date, date_format)
        delta = end_date_obj - start_date_obj
        return delta.days


    def decryptor(enc_env_var, key_env_var):
        # Load the key
        key = os.environ.get(key_env_var)
        encryption_key = Fernet(key)
        encrypted_password = (os.environ.get(enc_env_var)).encode()
        # Decrypt Data
        decrypted_password = encryption_key.decrypt(encrypted_password.decode())

        # print(f"Decryped Text: {decrypted_password}")
        return decrypted_password.decode()

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
                                 f"Error Occurred:<br><b>{err}<br></b> Agent: Downtime.py",
                                 'ltr')

    username = 'sysops-svc@abramad.com'
    password = decryptor('sysops-svc_enc', 'sysops-svc_key')

    error_log = ""

    # Ignore the warning
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.verify_mode = ssl.CERT_NONE

    ME_VC = connect.SmartConnect(host='me-vc01.abramad.com',user=username,pwd=password,port=443,sslContext=context)
    me_content = ME_VC.RetrieveContent()
    me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
    me_vms = [vm for vm in me_vm_view.view if (vm.name.lower().startswith("mer-") or vm.name.lower().startswith("mef-") or vm.name.lower().startswith("mes-") or vm.name.lower().startswith("mea-") or vm.name.lower().startswith("meb-") or vm.name.lower().startswith("mem-") or vm.name.lower().startswith("mei-") )]

    vms_to_be_deleted = []

    for vm in me_vms:
        # find the poweredoff vms
        if vm.runtime.powerState == "poweredOff" and not vm.name.lower() == "mer-singletemp" and not vm.name.lower() == "mei-ava-centos7-template01" and not vm.name.lower() == "mei-ava-centos7-template02":

            # Get VM Creation Date
            vm_creation_date = ""
            vm_shutdown_date = ""
            vm_persian_name = ""
            custom_attribute= vm.summary.customValue
            for i in custom_attribute:
                if i.key == 104:
                    vm_creation_date = i.value
                if i.key == 401:
                    vm_shutdown_date = i.value
                if i.key == 103:
                    vm_persian_name = i.value
            try:
                vm_dead_days = ""
                if calculate_days_between_dates(vm_shutdown_date, today_persian_date) > 31:
                    vm_dead_days = calculate_days_between_dates(vm_shutdown_date, today_persian_date)
                    vms_to_be_deleted.append([vm_persian_name, vm.name, vm_dead_days])
            except ValueError:
                error_log += f"VM <em><b>{vm.name}</b></em> has bad shutdown date format or it does not exists."

    # Send the text via email
    receiver_email = 'support@abramad.com, mehdi.a@abramad.com, alireza.ja@abramad.com'


    message = "Below VMs are powered off more than 1 month and should be deleted as soon as possible.<br><br><br><br>"
    for vm_info in vms_to_be_deleted:
        mail_vm_persian_name = vm_info[0]
        mail_vm_name = vm_info[1]
        mail_vm_off_days = vm_info[2]
        message += f"<em>{mail_vm_persian_name}</em><br><em><b>{mail_vm_name}</b></em> is powered off for <b>{mail_vm_off_days}</b> days<br><br><br>"
    message += f"<br><br>{error_log}<br><br><br></p><br><br>Agent: VM_Delete_Alert.py"

    if len(vms_to_be_deleted) > 1:
        send_anonymous_email(
            from_email="DeleteVM@abramad.com",
            to_email=receiver_email,
            cc_email='sina.z@abramad.com',
            subject=f'VMs that should be Deleted',
            html_message=message,
            direction="ltr"
            # attachments=[attachment]
        )

    Disconnect(ME_VC)


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

