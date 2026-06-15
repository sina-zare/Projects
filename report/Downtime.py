import csv
from email.mime.application import MIMEApplication
from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import warnings
from persiantools.jdatetime import JalaliDate
from jdatetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from icalendar import Calendar, Event
import smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter
import traceback
import random
import time
import os
import pyzipper

# --- Configuration ---
script_name = 'downtime'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'https://me-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
datacenter = 'miremad'
target = 'me_onprem_customers'


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


    month_dict = {
        "01": "فروردین",
        "02": "اردیبهشت",
        "03": "خرداد",
        "04": "تیر",
        "05": "مرداد",
        "06": "شهریور",
        "07": "مهر",
        "08": "آبان",
        "09": "آذر",
        "10": "دی",
        "11": "بهمن",
        "12": "اسفند"
    }

    week_dict = {
        "Sat": "شنبه",
        "Sun": "یکشنبه",
        "Mon": "دوشنبه",
        "Tue": "سه شنبه",
        "Wed": "چهارشنبه",
        "Thu": "پنجشنبه",
        "Fri": "جمعه"
    }


    # Decryption function
    def decrypt(cipher_text, key):
        plain_text = ""
        for i in range(len(cipher_text)):
            char = cipher_text[i]
            plain_int = ord(char) - key
            plain_text += chr(plain_int)
        return plain_text


    # Credentials
    from cryptography.fernet import Fernet


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

    # Read the existing Mediocre flag from the file
    mediocre_path = "C:/Users/sina.z/Desktop/Automation_Reports/Downtime/Mediocre.txt"
    mediocre_flag = ""
    with open(mediocre_path, "r") as file:
        mediocre_flag = file.read()

    # Read the existing VIP flag from the file
    vip_path = "C:/Users/sina.z/Desktop/Automation_Reports/Downtime/VIP.txt"
    vip_flag = ""
    with open(vip_path, "r") as file:
        vip_flag = file.read()

    # Read the existing last ticket No created from the file
    version_no_path = "C:/Users/sina.z/Desktop/Automation_Reports/Downtime/Version.txt"
    with open(version_no_path, "r") as file:
        version_no = file.read()

        # Convert the file contents to an integer

        if version_no.isnumeric():
            int_version_no = int(version_no)
            print("File contents type check good, Value:", int_version_no, "\n\n")

        else:

            send_anonymous_email(
                from_email="ScriptErrors@abramad.com",
                to_email='abramadsysops@abramad.com',
                cc_email='sina.z@abramad.com',
                subject=f'Error in Version Data',
                html_message=f"<p><b>Version File does not contain valid integer data<br><br>Wrong Value: {version_no}</p><br><br>Agent: Downtime.py",
                direction="rtl"
                # attachments=[attachment]
            )

    # Get today's Jalali date
    today = datetime.now().date()
    day_name = today.strftime('%a')
    # Add three days to today's date
    downtime_date = today + timedelta(days=3)

    downtime_year = str(downtime_date)[:4]
    downtime_month = str(downtime_date)[5:7]
    downtime_day = str(downtime_date)[8:10]
    downtime_month_label = month_dict[downtime_month]
    downtime_day_label = downtime_date.strftime('%a')
    downtime_day_label_fa = week_dict[downtime_day_label]

    from datetime import datetime, timedelta, date

    # Get today's date
    miladi_today = date.today()
    miladi_current_day = str(miladi_today)[-2:]

    # Ignore the warning
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    # *** Connecting to ME-VC01.Abramad.Com to get the Report ***
    # Create an SSL context with no certificate verification
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.verify_mode = ssl.CERT_NONE

    # Connecting to vCenter
    ME_VC = connect.SmartConnect(host='me-vc01.abramad.com', user=username, pwd=password, port=443, sslContext=context)
    me_content = ME_VC.RetrieveContent()
    me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
    me_vms = [vm for vm in me_vm_view.view if (
                vm.name.startswith("MER-") or vm.name.startswith("MERD-") or vm.name.startswith(
            "MEF-") or vm.name.startswith("MES-") or vm.name.startswith("MEA-") or vm.name.startswith(
            "MEB-") or vm.name.startswith("MEM-") or vm.name.startswith("MEI-"))]
    # Sort the me_vms list based on VM names
    sorted_vms = sorted(me_vms, key=lambda vm: vm.name.lower())

    # Zip file path
    zip_path = "C:/Users/sina.z/Desktop/Automation_Reports/Downtime/Update_Files.zip"
    zip_pass = "wzo}e!H32u}8}Dln'[k;"

    # CSV File Paths
    mer_total_vms_path = f"C:/Users/sina.z/Desktop/Automation_Reports/Downtime/MER/MER-Total-VMs.csv"
    mer_vip_ramak_total_vms_path = f"C:/Users/sina.z/Desktop/Automation_Reports/Downtime/MER/MER-VIP-Ramak-Total-VMs.csv"
    mer_vip_alaziz_total_vms_path = f"C:/Users/sina.z/Desktop/Automation_Reports/Downtime/MER/MER-VIP-ALaziz-Total-VMs.csv"
    mer_vip_domino_total_vms_path = f"C:/Users/sina.z/Desktop/Automation_Reports/Downtime/MER/MER-VIP-Domino-Total-VMs.csv"
    mer_vip_tatpsa_total_vms_path = f"C:/Users/sina.z/Desktop/Automation_Reports/Downtime/MER/MER-VIP-TatPSA-Total-VMs.csv"
    mes_total_vms_path = f"C:/Users/sina.z/Desktop/Automation_Reports/Downtime/MES/MES-Total-VMs.csv"
    meb_total_vms_path = f"C:/Users/sina.z/Desktop/Automation_Reports/Downtime/MEB/MEB-Total-VMs.csv"
    mea_total_vms_path = f"C:/Users/sina.z/Desktop/Automation_Reports/Downtime/MEA/MEA-Total-VMs.csv"
    mem_total_vms_path = f"C:/Users/sina.z/Desktop/Automation_Reports/Downtime/MEM/MEM-Total-VMs.csv"
    mef_total_vms_path = f"C:/Users/sina.z/Desktop/Automation_Reports/Downtime/MEF/MEF-Total-VMs.csv"
    planned_for_update_system_path = f"C:/Users/sina.z/Desktop/Automation_Reports/Downtime/Planned_For_Update_System.csv"
    planned_for_update_sms_path = f"C:/Users/sina.z/Desktop/Automation_Reports/Downtime/Planned_For_Update_SMS.csv"
    raw_sms_data_path = f"C:/Users/sina.z/Desktop/Automation_Reports/Downtime/raw.xlsx"
    # take out updated vms and store 'Em in a list
    updated_vms_csv_path = "C:/Users/sina.z/Desktop/Automation_Reports/Downtime/Updated_VMs.csv"
    updated_vms = []

    # Email Recipients
    #reciever_email = 'support@abramad.com,noc@abramad.com,system@abramad.com,farnaz.sh@abramad.com,SaharP@systemgroup.net,JavadK@systemgroup.net,HesamR@systemgroup.net,NedaPo@systemgroup.net,MozhganFA@systemgroup.net,YahyaM@systemgroup.net,fahimegh@systemgroup.net,ArashP@systemgroup.net,MohammadRam@systemgroup.net,abbasas@systemgroup.net,itsm@abramad.com'
    reciever_email = 'support@abramad.com,system@abramad.com'
    cc_email = 'sina.z@abramad.com'
    finished_email_list = reciever_email

    if miladi_current_day == "20":

        ##########################
        ###### Begin of MER ######

        # Rahkaran
        with open(mer_total_vms_path, 'w', newline='', encoding='utf-8_sig') as csv_file:
            writer = csv.writer(csv_file)

            writer.writerow(["VM Name", "National ID", "Persian Name"])

            for vm in sorted_vms:

                # Get VIP Status
                vm_vip_state = "not_vip"
                custom_value_n = vm.summary.customValue
                for i in custom_value_n:
                    if i.key == 705:
                        vm_vip_state = i.value

                if (vm.name.lower().startswith(
                        "mer-") and vm_vip_state == "not_vip" and vm.runtime.powerState.lower() == "poweredon") or (
                        vm.name.lower().startswith(
                                "merd-") and vm_vip_state == "not_vip" and vm.runtime.powerState.lower() == "poweredon"):
                    # Get National ID Status
                    vm_national_id = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 611:
                            vm_national_id = i.value

                    # Get VM Persian Name
                    vm_persian_name = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 103:
                            vm_persian_name = i.value

                    writer.writerow([vm.name, f"\t{str(vm_national_id)}", vm_persian_name])

        # Rahkaran VIP
        # Ramak
        with open(mer_vip_ramak_total_vms_path, 'w', newline='', encoding='utf-8_sig') as csv_file:
            writer = csv.writer(csv_file)

            writer.writerow(["VM Name", "National ID", "Persian Name"])

            for vm in sorted_vms:

                if vm.name.lower().startswith("mer-ramak") and vm.runtime.powerState.lower() == "poweredon":
                    # Get National ID Status
                    vm_national_id = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 611:
                            vm_national_id = i.value

                    # Get VM Persian Name
                    vm_persian_name = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 103:
                            vm_persian_name = i.value

                    writer.writerow([vm.name, f"\t{str(vm_national_id)}", vm_persian_name])

        # ALaziz
        with open(mer_vip_alaziz_total_vms_path, 'w', newline='', encoding='utf-8_sig') as csv_file:
            writer = csv.writer(csv_file)

            writer.writerow(["VM Name", "National ID", "Persian Name"])

            for vm in sorted_vms:

                if vm.name.lower().startswith("mer-alaziz") and vm.runtime.powerState.lower() == "poweredon":
                    # Get National ID Status
                    vm_national_id = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 611:
                            vm_national_id = i.value

                    # Get VM Persian Name
                    vm_persian_name = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 103:
                            vm_persian_name = i.value

                    writer.writerow([vm.name, f"\t{str(vm_national_id)}", vm_persian_name])

        # Domino
        with open(mer_vip_domino_total_vms_path, 'w', newline='', encoding='utf-8_sig') as csv_file:
            writer = csv.writer(csv_file)

            writer.writerow(["VM Name", "National ID", "Persian Name"])

            for vm in sorted_vms:

                if vm.name.lower().startswith("mer-domino") and vm.runtime.powerState.lower() == "poweredon":
                    # Get National ID Status
                    vm_national_id = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 611:
                            vm_national_id = i.value

                    # Get VM Persian Name
                    vm_persian_name = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 103:
                            vm_persian_name = i.value

                    writer.writerow([vm.name, f"\t{str(vm_national_id)}", vm_persian_name])

        # TatPSA
        with open(mer_vip_tatpsa_total_vms_path, 'w', newline='', encoding='utf-8_sig') as csv_file:
            writer = csv.writer(csv_file)

            writer.writerow(["VM Name", "National ID", "Persian Name"])

            for vm in sorted_vms:

                if vm.name.lower().startswith("mer-tatpsa") and vm.runtime.powerState.lower() == "poweredon":
                    # Get National ID Status
                    vm_national_id = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 611:
                            vm_national_id = i.value

                    # Get VM Persian Name
                    vm_persian_name = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 103:
                            vm_persian_name = i.value

                    writer.writerow([vm.name, f"\t{str(vm_national_id)}", vm_persian_name])

        ####### End of MER #######
        ##########################

        ##########################
        ###### Begin of MES ######

        # Sepidar
        with open(mes_total_vms_path, 'w', newline='', encoding='utf-8_sig') as csv_file:
            writer = csv.writer(csv_file)

            writer.writerow(["VM Name", "National ID", "Persian Name"])

            for vm in sorted_vms:

                if vm.name.lower().startswith("mes-") and vm.runtime.powerState.lower() == "poweredon":
                    # Get National ID Status
                    vm_national_id = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 611:
                            vm_national_id = i.value

                    # Get VM Persian Name
                    vm_persian_name = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 103:
                            vm_persian_name = i.value

                    writer.writerow([vm.name, f"\t{str(vm_national_id)}", vm_persian_name])

        ####### End of MES #######
        ##########################

        ##########################
        ###### Begin of MEB ######

        # Business Intelligence
        with open(meb_total_vms_path, 'w', newline='', encoding='utf-8_sig') as csv_file:
            writer = csv.writer(csv_file)

            writer.writerow(["VM Name", "National ID", "Persian Name"])

            for vm in sorted_vms:

                if vm.name.lower().startswith("meb-") and vm.runtime.powerState.lower() == "poweredon":
                    # Get National ID Status
                    vm_national_id = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 611:
                            vm_national_id = i.value

                    # Get VM Persian Name
                    vm_persian_name = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 103:
                            vm_persian_name = i.value

                    writer.writerow([vm.name, f"\t{str(vm_national_id)}", vm_persian_name])

        ####### End of MEB #######
        ##########################

        ##########################
        ###### Begin of MEA ######

        # Automation
        with open(mea_total_vms_path, 'w', newline='', encoding='utf-8_sig') as csv_file:
            writer = csv.writer(csv_file)

            writer.writerow(["VM Name", "National ID", "Persian Name"])

            for vm in sorted_vms:

                if vm.name.lower().startswith(
                        "mea-") and vm.runtime.powerState.lower() == "poweredon" and vm.guest.guestFullName.startswith(
                        "Microsoft"):

                    # Get National ID Status
                    vm_national_id = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 611:
                            vm_national_id = i.value

                    # Get VM Persian Name
                    vm_persian_name = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 103:
                            vm_persian_name = i.value

                    writer.writerow([vm.name, f"\t{str(vm_national_id)}", vm_persian_name])

        ####### End of MEA #######
        ##########################

        ##########################
        ###### Begin of MEM ######

        # MIaaS
        with open(mem_total_vms_path, 'w', newline='', encoding='utf-8_sig') as csv_file:
            writer = csv.writer(csv_file)

            writer.writerow(["VM Name", "National ID", "Persian Name"])

            for vm in sorted_vms:

                if vm.name.lower().startswith("mem-") and vm.runtime.powerState.lower() == "poweredon":
                    # Get National ID Status
                    vm_national_id = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 611:
                            vm_national_id = i.value

                    # Get VM Persian Name
                    vm_persian_name = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 103:
                            vm_persian_name = i.value

                    writer.writerow([vm.name, f"\t{str(vm_national_id)}", vm_persian_name])

        ####### End of MEM #######
        ##########################

        ##########################
        ###### Begin of MEF ######

        # Saham Fasl
        with open(mef_total_vms_path, 'w', newline='', encoding='utf-8_sig') as csv_file:
            writer = csv.writer(csv_file)

            writer.writerow(["VM Name", "National ID", "Persian Name"])

            for vm in sorted_vms:

                if vm.name.lower().startswith("mef-") and vm.runtime.powerState.lower() == "poweredon":
                    # Get National ID Status
                    vm_national_id = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 611:
                            vm_national_id = i.value

                    # Get VM Persian Name
                    vm_persian_name = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 103:
                            vm_persian_name = i.value

                    writer.writerow([vm.name, f"\t{str(vm_national_id)}", vm_persian_name])

        ####### End of MEF #######
        ##########################

        # Assign Version No to 1
        int_version_no = 1
        # Overwrite the file with the new data
        with open(version_no_path, "w") as file:
            file.write(str(int_version_no))

        # Empty the updated_vms csv file
        with open(updated_vms_csv_path, "w") as file:
            file.truncate()

        # Assign Mediocre Flag to 0
        with open(mediocre_path, "w") as file:
            file.write("0")

        # Assign VIP Flag to 0
        with open(vip_path, "w") as file:
            file.write("0")

        # Disconnect vCenter
        Disconnect(ME_VC)

    else:
        print(f"No new VM taking for today: {miladi_current_day}th day of month.\n")

    vms_to_be_updated = []
    data_csv = [mer_total_vms_path, mer_vip_ramak_total_vms_path, mer_vip_alaziz_total_vms_path,
                mer_vip_domino_total_vms_path, mer_vip_tatpsa_total_vms_path, mes_total_vms_path, meb_total_vms_path,
                mea_total_vms_path, mem_total_vms_path, mef_total_vms_path]

    # Create a list to store the data
    mer_data_list = []
    mer_vip_ramak_data_list = []
    mer_vip_alaziz_data_list = []
    mer_vip_domino_data_list = []
    mer_vip_tatpsa_data_list = []
    mes_data_list = []
    meb_data_list = []
    mea_data_list = []
    mem_data_list = []
    mef_data_list = []

    for datum in data_csv:

        if datum == mer_total_vms_path:
            # Read Data from CSV files
            with open(datum, 'r', encoding='utf-8-sig') as read_file:
                reader = csv.reader(read_file)
                # Skip header
                next(reader)

                # Iterate over the remaining rows
                for row in reader:
                    # Create a tuple or data structure to store the row data
                    data = (row[0], row[1].replace(f"\t", ""), row[2])
                    # Add the data to the list
                    mer_data_list.append(data)

        if datum == mer_vip_ramak_total_vms_path:
            # Read Data from CSV files
            with open(datum, 'r', encoding='utf-8-sig') as read_file:
                reader = csv.reader(read_file)
                # Skip header
                next(reader)

                # Iterate over the remaining rows
                for row in reader:
                    # Create a tuple or data structure to store the row data
                    data = (row[0], row[1].replace(f"\t", ""), row[2])
                    # Add the data to the list
                    mer_vip_ramak_data_list.append(data)

        if datum == mer_vip_alaziz_total_vms_path:
            # Read Data from CSV files
            with open(datum, 'r', encoding='utf-8-sig') as read_file:
                reader = csv.reader(read_file)
                # Skip header
                next(reader)

                # Iterate over the remaining rows
                for row in reader:
                    # Create a tuple or data structure to store the row data
                    data = (row[0], row[1].replace(f"\t", ""), row[2])
                    # Add the data to the list
                    mer_vip_alaziz_data_list.append(data)

        if datum == mer_vip_domino_total_vms_path:
            # Read Data from CSV files
            with open(datum, 'r', encoding='utf-8-sig') as read_file:
                reader = csv.reader(read_file)
                # Skip header
                next(reader)

                # Iterate over the remaining rows
                for row in reader:
                    # Create a tuple or data structure to store the row data
                    data = (row[0], row[1].replace(f"\t", ""), row[2])
                    # Add the data to the list
                    mer_vip_domino_data_list.append(data)

        if datum == mer_vip_tatpsa_total_vms_path:
            # Read Data from CSV files
            with open(datum, 'r', encoding='utf-8-sig') as read_file:
                reader = csv.reader(read_file)
                # Skip header
                next(reader)

                # Iterate over the remaining rows
                for row in reader:
                    # Create a tuple or data structure to store the row data
                    data = (row[0], row[1].replace(f"\t", ""), row[2])
                    # Add the data to the list
                    mer_vip_tatpsa_data_list.append(data)

        if datum == mes_total_vms_path:
            # Read Data from CSV files
            with open(datum, 'r', encoding='utf-8-sig') as read_file:
                reader = csv.reader(read_file)
                # Skip header
                next(reader)

                # Iterate over the remaining rows
                for row in reader:
                    # Create a tuple or data structure to store the row data
                    data = (row[0], row[1].replace(f"\t", ""), row[2])
                    # Add the data to the list
                    mes_data_list.append(data)

        if datum == meb_total_vms_path:
            # Read Data from CSV files
            with open(datum, 'r', encoding='utf-8-sig') as read_file:
                reader = csv.reader(read_file)
                # Skip header
                next(reader)

                # Iterate over the remaining rows
                for row in reader:
                    # Create a tuple or data structure to store the row data
                    data = (row[0], row[1].replace(f"\t", ""), row[2])
                    # Add the data to the list
                    meb_data_list.append(data)

        if datum == mea_total_vms_path:
            # Read Data from CSV files
            with open(datum, 'r', encoding='utf-8-sig') as read_file:
                reader = csv.reader(read_file)
                # Skip header
                next(reader)

                # Iterate over the remaining rows
                for row in reader:
                    # Create a tuple or data structure to store the row data
                    data = (row[0], row[1].replace(f"\t", ""), row[2])
                    # Add the data to the list
                    mea_data_list.append(data)

        if datum == mem_total_vms_path:
            # Read Data from CSV files
            with open(datum, 'r', encoding='utf-8-sig') as read_file:
                reader = csv.reader(read_file)
                # Skip header
                next(reader)

                # Iterate over the remaining rows
                for row in reader:
                    # Create a tuple or data structure to store the row data
                    data = (row[0], row[1].replace(f"\t", ""), row[2])
                    # Add the data to the list
                    mem_data_list.append(data)

        if datum == mef_total_vms_path:
            # Read Data from CSV files
            with open(datum, 'r', encoding='utf-8-sig') as read_file:
                reader = csv.reader(read_file)
                # Skip header
                next(reader)

                # Iterate over the remaining rows
                for row in reader:
                    # Create a tuple or data structure to store the row data
                    data = (row[0], row[1].replace(f"\t", ""), row[2])
                    # Add the data to the list
                    mef_data_list.append(data)

    vm_data = [mer_data_list, mes_data_list, meb_data_list, mea_data_list, mem_data_list, mef_data_list]
    vm_data_vip = [mer_vip_ramak_data_list, mer_vip_alaziz_data_list, mer_vip_domino_data_list, mer_vip_tatpsa_data_list]

    with open(updated_vms_csv_path, 'r', encoding='utf-8-sig') as read_file:
        reader = csv.reader(read_file)

        # Iterate over the remaining rows
        for row in reader:
            # Create a tuple or data structure to store the row data
            # data = (row[0], row[1].replace(f"\t", ""), row[2])
            # Convert each element of the row list to lowercase and append to updated_vms
            updated_vms.append([item.lower() for item in row])

    to_be_updated_schedule_table = ''
    planned_for_update_vms = []
    counter = 0
    ramak_counter = 0
    alaziz_counter = 0
    domino_counter = 0
    tatpsa_counter = 0
    gate_is_locked = False

    # Flatten List
    updated_vms = [item for sublist in updated_vms for item in sublist]

    # Word Files
    ticket_path = "C:/Users/sina.z/Desktop/Automation_Reports/Downtime/EtelaResani-General-Ticket.txt"
    with open(ticket_path, "w", encoding="utf-8") as file:
        ticket = "مشترک گرامی ابرآمد\n"
        ticket += f"با توجه به اقدامات مورد نیاز برای بهبود و افزایش سطح کیفیت خدمات، در تاریخ {downtime_day_label_fa} {downtime_day} {downtime_month_label} ماه {downtime_year} بین ساعت 1:00 تا 5:00 بامداد بدلیل بروز رسانی سیستم عامل سرور احتمال اختلال در سرویس‌های شما وجود دارد. لطفا پس از پایان ساعت مذکور سرویس‌های خود را بررسی کنید. در صورتی که سرویس شما با اختلال مواجه شد، تیم پشتیبانی ابرآمد همواره پاسخگوی شما همراهان گرامی خواهد بود."

        file.write(ticket)

    sms_path = "C:/Users/sina.z/Desktop/Automation_Reports/Downtime/EtelaResani-General-SMS.txt"
    with open(sms_path, "w", encoding="utf-8") as file:
        sms = "مشترک گرامی ابرآمد\n"
        sms += f"با توجه به اقدامات مورد نیاز برای بهبود و افزایش سطح کیفیت خدمات، در تاریخ {downtime_day_label_fa} {downtime_day} {downtime_month_label} ماه {downtime_year} بین ساعت 1:00 تا 5:00 بامداد بدلیل بروز رسانی سیستم عامل سرور احتمال اختلال در سرویس‌های شما وجود دارد. لطفا پس از پایان ساعت مذکور سرویس‌های خود را بررسی کنید. در صورتی که سرویس شما با اختلال مواجه شد، تیم پشتیبانی ابرآمد همواره پاسخگوی شما همراهان گرامی خواهد بود."
        sms += f"\nلغو 11"
        sms += f"\nدریافت 12"

        file.write(sms)

    # Initializing Tables
    to_be_updated_schedule_table += """
                                    <table>
                                    <tr>
                                        <td><b>VM Name</b></td>
                                        <td><b>National ID</b></td>
                                        <td><b>Persian Name</b></td>
                                    </tr>
                                    """

    if ((day_name.lower() == "sat") or (day_name.lower() == "sun") or (day_name.lower() == "mon") or (
            day_name.lower() == "wed")):

        for vm_info in vm_data:

            # Get track of Numbers
            if counter >= 120:
                break

            for vm_deeper_data in vm_info:

                if vm_deeper_data[0].lower() in updated_vms:
                    continue
                else:
                    # Get track of Numbers
                    if counter >= 120:
                        break
                    # Fill the Table for email sending
                    to_be_updated_schedule_table += f"""
                            <tr>
                                <td>{vm_deeper_data[0]}</td>
                                <td>{vm_deeper_data[1]}</td>
                                <td>{vm_deeper_data[2]}</td>
                            </tr>
    
                        """

                    # Append Planned_for_update_vms (Name and National ID)
                    planned_for_update_vms.append([vm_deeper_data[0], vm_deeper_data[1]])

                    # Append Updated_VMs csv
                    with open(updated_vms_csv_path, 'a', newline='', encoding='utf-8_sig') as csv_file:
                        writer = csv.writer(csv_file)

                        writer.writerow([vm_deeper_data[0]])
                    counter += 1

        to_be_updated_schedule_table += "</table>"

        # Filling VM Names for system team
        with open(planned_for_update_system_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)

            writer.writerow(["VM Names"])
            for vm_data in planned_for_update_vms:
                writer.writerow([vm_data[0]])

        # Filling SMS Data for Ehsan

        raw_sms_data = pd.read_excel(raw_sms_data_path, dtype=str)

        # Specify the column indices you want to extract (0-based index)
        columns_indices = [1, 3, 5, 6, 8]

        # Extract the specified columns from each row and store them in a list
        extracted_data = [list(row.iloc[columns_indices]) for index, row in raw_sms_data.iterrows()]

        with open(planned_for_update_sms_path, 'w', newline='', encoding='utf-8_sig') as csv_file:
            writer = csv.writer(csv_file)

            writer.writerow(["نام", "شماره همراه", "پست الکترونیک"])

            for id in planned_for_update_vms:
                for raw_info in extracted_data:

                    column1 = ""
                    column2 = ""
                    column3 = ""

                    if id[1].strip() == str(raw_info[0]).strip():
                        column1 = raw_info[1]
                        column2 = raw_info[4]
                        column3 = f"{raw_info[3]}({raw_info[2]})"

                        writer.writerow([column1, column2, column3])

        # End of SMS Calculations

        # Filling Ticket HID for Abramad Support

        sarv_data = []

        sarv_csv_file = "C:/Users/sina.z/Desktop/Automation_Reports/Downtime/rawt.csv"
        with open(sarv_csv_file, 'r', encoding='utf-8-sig') as read_file:
            reader = csv.reader(read_file)

            # Skip the first 8 lines
            for _ in range(8):
                next(reader)

            for row in reader:
                sarv_data.append([row[0], row[4]])

        ####################################################

        sms_email_data = []

        sms_email_csv_file = "C:/Users/sina.z/Desktop/Automation_Reports/Downtime/Planned_For_Update_SMS.csv"
        with open(sms_email_csv_file, 'r', encoding='utf-8-sig') as read_file:
            reader = csv.reader(read_file)

            # Skip the first 1 lines
            for _ in range(1):
                next(reader)

            for row in reader:
                temp_mail = row[2].split("(")
                customer_name = row[0]
                sms_email_data.append([temp_mail[0].lower(), customer_name])

        final_data_hid = []
        final_data_email = []

        for hid in sarv_data:

            for email in sms_email_data:

                if email[0].lower().strip() == hid[0].lower().strip():
                    final_data_hid.append(hid[1])
                    final_data_email.append(hid[0].lower())
                    print(f"Matched: {hid[0].lower()}")

        email_data = []
        for i in sms_email_data:
            email_data.append(i[0])

        remainder_data = set(email_data) - set(final_data_email)
        remainder_amount = len(set(email_data)) - len(set(final_data_email))

        remainder_customers = []
        for i in remainder_data:
            for j in sms_email_data:
                if i.lower() == j[0].lower():
                    remainder_customers.append(j[1])

        print("\n")
        print(set(email_data))
        print(len(set(email_data)))
        print("\n")
        print(set(final_data_hid))
        print(len(set(final_data_hid)))
        print("\n")
        print(remainder_data)
        print(set(remainder_customers))
        print(remainder_amount)

        hid_csv_file = "C:/Users/sina.z/Desktop/Automation_Reports/Downtime/Planned_For_Update_HID.csv"

        with open(hid_csv_file, mode='w', newline='', encoding='utf-8_sig') as file:

            # Create a CSV writer object
            writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for k in set(final_data_hid):
                writer.writerow([k])

            for z in set(remainder_customers):
                writer.writerow([z])

        # End of Ticket HID Calculations

        # Check Table Emptiness then send Email
        empty_schedule_table = """
                                    <table>
                                    <tr>
                                        <td><b>VM Name</b></td>
                                        <td><b>National ID</b></td>
                                        <td><b>Persian Name</b></td>
                                    </tr>
                                    </table>"""

        if to_be_updated_schedule_table == empty_schedule_table and int(mediocre_flag) == 0:

            # Normal Customers are all updated

            html_line_break = '''
                                <p><br></p>
                            '''
            html_msg_1s = '''
                            <html dir="rtl">
                            <head>
                                <style>
                                .numeric_class {
                                    direction: ltr;
                                    font-family: Calibri;
                                    text-align: right;
                                }
    
                                </style>
                              </head>
                              <body>
                            '''
            html_msg_2s = '''
                                <p  style="font-family: DiodrumArabic-Regular">با سلام و احترام</p>
                            '''
            html_msg_3s = f'''
                                <p  style="font-family: DiodrumArabic-Regular">به اطلاع میرساندبروزرسانی سیستم عامل و نرم افزار های مشترکین ابرآمد، شامل سرویس های اتوماسیون، راهکاران، سهام فصل، سپیدار، BI و مدیریت شده به غیر از مشترکین VIP راهکاران برای تاریخ {downtime_month_label} {downtime_year} به اتمام رسید.</p>
                            '''
            html_msg_4s = f'''
                                <p  style="font-family: DiodrumArabic-Regular">سپاس از همکاری و همراهی تمام دوستان</p>
                            '''
            html_msg_5s = f'''
                                <p style="font-family: DiodrumArabic-Regular"></p>
                            '''
            html_msg_6s = '''
                              </body>
                            </html>
                            '''

            mediocre_email_body = html_msg_1s + html_msg_2s + html_msg_3s + html_line_break + html_msg_4s + html_line_break + html_msg_5s + html_msg_6s

            send_anonymous_email(
                from_email="Downtime@abramad.com",
                to_email=finished_email_list,
                cc_email='',
                subject=f'اتمام بروزرسانی OS و نرم افزار های مشترکین | {downtime_month_label} {downtime_year}',
                html_message=mediocre_email_body,
                direction="rtl"
                # attachments=[attachment]
            )

            # Bring up mediocre flag
            with open(mediocre_path, "w", encoding="utf-8") as file:

                file.write("1")

            print("All Mediocre customers Updated Successfully")

        elif to_be_updated_schedule_table == empty_schedule_table and int(mediocre_flag) == 1:
            print("All Mediocre are updated and flag is 1")

        else:
            # Send Email to King

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
                            font-family: Calibri;
                            text-align: right;
                        }
    
                        table {
                            font-family: DiodrumArabic-Regular;
                            border-collapse: collapse;
                            margin-left: 0;
                            direction: rtl;
                        }
    
                        table td {
                            border: 1px solid black;
                            padding: 8px;
                            width: 250px;
                            text-align: right;
                            direction: rtl; 
                        }
                        </style>
                      </head>
                      <body>
                    '''
            html_msg_2s = '''
                        <p  style="font-family: DiodrumArabic-Regular">با سلام و احترام</p>
                    '''
            html_msg_3s = f'''
                        <p  style="font-family: DiodrumArabic-Regular">در راستای بروزرسانی سیستم عامل مشترکین مدیریت شده ی ابرآمد به جهت نصب آخرین آپدیت های مایکروسافت در {downtime_month_label} ماه مشترکین زیر در تاریخ {downtime_day_label_fa} {downtime_day} {downtime_month_label} {downtime_year} از ساعت 01:00 الی 05:00 بامداد آپدیت میگردند.</p>
                    '''
            html_msg_4s = f'''
                        <p  style="font-family: DiodrumArabic-Regular"><b>{to_be_updated_schedule_table}</b></p>
                    '''
            html_msg_5s = f'''
                        <p  style="font-family: DiodrumArabic-Regular">@AbramadSystem لطفا کالکشنی برای مشترکین قرار گرفته شده در فایل Planned_For_Update_System قرار گرفته در پیوست برای بروزرسانی OS و اپلیکیشن ها در تاریخ مذکور ایجاد فرمایید.</p>
                    '''
            html_msg_6s = f'''
                        <p  style="font-family: DiodrumArabic-Regular">@AbramadSupport لطفا اطلاع رسانی به مشترکین به صورت تیکت، با استفاده از متن درون فایل EtelaResani-General–Ticket قرار گرفته به پیوست را انجام دهید.</p>
                    '''
            html_msg_7s = f'''
                        <p  style="font-family: DiodrumArabic-Regular">@Ehsan Hojjat لطفا در اطلاع رسانی به مشترکین به صورت SMS، با توجه به فایل های EtelaResani-General–SMS  و Planned_For_Update_SMS قرار گرفته به پیوست، تیم ساپورت را از یاری خود بهره مند سازید.</p>
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

            inform_email_body = html_msg_1s + html_msg_2s + html_msg_3s + html_line_break + html_msg_4s + html_line_break + html_msg_5s + html_msg_6s + html_msg_7s + html_msg_8s + html_line_break + html_msg_9s

            # Zipping files with password
            files = [ticket_path, sms_path, planned_for_update_sms_path, planned_for_update_system_path,
                             hid_csv_file]
            make_zip(files, zip_path, zip_pass)

            send_anonymous_email(
                from_email="Downtime@abramad.com",
                to_email=reciever_email,
                cc_email=cc_email,
                subject=f'اطلاعیه بروزرسانی مشترکین مدیریت شده ابرآمد | سری {int_version_no} | {downtime_day} {downtime_month_label} {downtime_year}',
                html_message=inform_email_body,
                direction="rtl",
                attachments=[zip_path]
            )

            '''
            ##############################
            # Create and Attach Calendar #
            ##############################
    
    
            # Calculate Date for Calendar
            # Get today's Jalali date
            khareji_today = datetime.now().date()
    
            # Add two days to today's date
            khareji_downtime_date = khareji_today + timedelta(days=3)
    
            khareji_downtime_day = int(str(khareji_downtime_date)[8:10])
            khareji_downtime_month = int(str(khareji_downtime_date)[5:7])
            khareji_downtime_year = int(str(khareji_downtime_date)[:4])
    
    
            # Calendar Text
            text_cal = f"متن مربوط به ایمیل اطلاع رسانی سری {int_version_no}ام\nبرای {downtime_month_label} ماه {downtime_year}  را بررسی فرمایید\nبا سپاس"
    
    
            # Meeting details
            subject = f'اطلاعیه بروزرسانی مشترکین مدیریت شده ابرآمد | سری {int_version_no}  | {downtime_day} {downtime_month_label} {downtime_year}'
            start = datetime(khareji_downtime_year, khareji_downtime_month, khareji_downtime_day, 1, 0)  # Meeting start time
            end = start + timedelta(hours=4)  # Meeting end time
            location = 'سرور های مشترکین مربوطه'
            attendees = ['abramadops@systemgroup.net']
            organizer = 'sina.z@abramad.com'
    
            # Create iCalendar event
            event = Event()
            event.add('summary', subject)
            event.add('dtstart', start)
            event.add('dtend', end)
            event.add('location', location)
            event.add('organizer', organizer)
            event.add('description', text_cal)
            event.add('status', 'CONFIRMED')
    
            for attendee in attendees:
                event.add('attendee', attendee)
    
            # Create iCalendar calendar and add the event
            cal = Calendar()
            cal.add_component(event)
    
            # Generate the iCalendar content as a string
            ical_content = cal.to_ical()
    
            calendar_part = MIMEBase('text', 'calendar', method='REQUEST')
            calendar_part.set_payload(ical_content)
            encoders.encode_base64(calendar_part)
            calendar_part.add_header('Content-Disposition', 'attachment; filename="meeting.ics"')
    
            # Attach Calendar file
            msg.attach(calendar_part)
    
    
            # Attach Text to email
            msg.attach(MIMEText(inform_email_body, 'html'))
    
            # Connect to the SMTP server and send the email 465,*587*,25 (mail.systemgroup.net)
            # Send email info
            smtp_server = 'mail.systemgroup.net'
            smtp_port = 587
            smtp_username = username
            smtp_password = password
    
            # Send email function
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail('sina.z@abramad.com', reciever_email.split(",") + cc_email.split(','), msg.as_string())
    '''

            # Increment Version No by one
            int_version_no += 1
            # Overwrite the file with the new data
            with open(version_no_path, "w") as file:
                file.write(str(int_version_no))




    elif (day_name.lower() == "tue"):

        # Initialize Schedule Table
        to_be_updated_schedule_table = """
                                        <table>
                                        <tr>
                                            <td><b>==============</b></td>
                                            <td><b>VIP Customers</b></td>
                                            <td><b>==============</b></td>
                                        </tr>
                                        <tr>
                                            <td><b>VM Name</b></td>
                                            <td><b>National ID</b></td>
                                            <td><b>Persian Name</b></td>
                                        </tr>
                                        """

        for vm_info in vm_data_vip:

            # check if we are still on the current csv file
            # Ramak
            if vm_info == mer_vip_ramak_data_list:
                # Check if we should stop
                if gate_is_locked:
                    break

                for vm_deeper_data in vm_info:

                    if vm_deeper_data[0].lower() in updated_vms:
                        continue
                    else:

                        # Fill the Table for email sending
                        to_be_updated_schedule_table += f"""
                                                    <tr>
                                                        <td>{vm_deeper_data[0]}</td>
                                                        <td>{vm_deeper_data[1]}</td>
                                                        <td>{vm_deeper_data[2]}</td>
                                                    </tr>
                                                    """

                        # Append Planned_for_update_vms (Name and National ID)
                        planned_for_update_vms.append([vm_deeper_data[0], vm_deeper_data[1]])

                        with open(updated_vms_csv_path, 'a', newline='', encoding='utf-8_sig') as csv_file:
                            writer = csv.writer(csv_file)
                            writer.writerow([vm_deeper_data[0]])

                        ramak_counter += 1

                        # Get track of Numbers
                        if ramak_counter >= len(mer_vip_ramak_data_list):
                            gate_is_locked = True
                            break

            # ALaziz
            if vm_info == mer_vip_alaziz_data_list:
                if gate_is_locked:
                    break

                for vm_deeper_data in vm_info:

                    if vm_deeper_data[0].lower() in updated_vms:
                        continue
                    else:

                        # Fill the Table for email sending
                        to_be_updated_schedule_table += f"""
                                                    <tr>
                                                        <td>{vm_deeper_data[0]}</td>
                                                        <td>{vm_deeper_data[1]}</td>
                                                        <td>{vm_deeper_data[2]}</td>
                                                    </tr>
                                                    """

                        # Append Planned_for_update_vms (Name and National ID)
                        planned_for_update_vms.append([vm_deeper_data[0], vm_deeper_data[1]])

                        with open(updated_vms_csv_path, 'a', newline='', encoding='utf-8_sig') as csv_file:
                            writer = csv.writer(csv_file)
                            writer.writerow([vm_deeper_data[0]])

                        alaziz_counter += 1

                        # Get track of Numbers
                        if alaziz_counter >= len(mer_vip_alaziz_data_list):
                            gate_is_locked = True
                            break

            # Domino
            if vm_info == mer_vip_domino_data_list:
                if gate_is_locked:
                    break

                for vm_deeper_data in vm_info:

                    if vm_deeper_data[0].lower() in updated_vms:
                        continue
                    else:

                        # Fill the Table for email sending
                        to_be_updated_schedule_table += f"""
                                                    <tr>
                                                        <td>{vm_deeper_data[0]}</td> 
                                                        <td>{vm_deeper_data[1]}</td>
                                                        <td>{vm_deeper_data[2]}</td>
                                                    </tr>
                                                    """

                        # Append Planned_for_update_vms (Name and National ID)
                        planned_for_update_vms.append([vm_deeper_data[0], vm_deeper_data[1]])

                        with open(updated_vms_csv_path, 'a', newline='', encoding='utf-8_sig') as csv_file:
                            writer = csv.writer(csv_file)
                            writer.writerow([vm_deeper_data[0]])

                        domino_counter += 1

                        # Get track of Numbers
                        if domino_counter >= len(mer_vip_domino_data_list):
                            gate_is_locked = True
                            break

            # TatPSA
            if vm_info == mer_vip_tatpsa_data_list:
                if gate_is_locked:
                    break

                for vm_deeper_data in vm_info:

                    if vm_deeper_data[0].lower() in updated_vms:
                        continue
                    else:

                        # Fill the Table for email sending
                        to_be_updated_schedule_table += f"""
                                                    <tr>
                                                        <td>{vm_deeper_data[0]}</td>
                                                        <td>{vm_deeper_data[1]}</td>
                                                        <td>{vm_deeper_data[2]}</td>
                                                    </tr>
                                                    """

                        # Append Planned_for_update_vms (Name and National ID)
                        planned_for_update_vms.append([vm_deeper_data[0], vm_deeper_data[1]])

                        with open(updated_vms_csv_path, 'a', newline='', encoding='utf-8_sig') as csv_file:
                            writer = csv.writer(csv_file)
                            writer.writerow([vm_deeper_data[0]])

                        tatpsa_counter += 1

                        # Get track of Numbers
                        if tatpsa_counter >= len(mer_vip_tatpsa_data_list):
                            gate_is_locked = True
                            break

        # Filling VM Names for system team
        with open(planned_for_update_system_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)

            writer.writerow(["VM Names"])
            for vm_data in planned_for_update_vms:
                writer.writerow([vm_data[0]])

        # Filling SMS Data for Ehsan

        raw_sms_data = pd.read_excel(raw_sms_data_path, dtype=str)

        # Specify the column indices you want to extract (0-based index)
        columns_indices = [1, 3, 5, 6, 8]

        # Extract the specified columns from each row and store them in a list
        extracted_data = [list(row.iloc[columns_indices]) for index, row in raw_sms_data.iterrows()]

        with open(planned_for_update_sms_path, 'w', newline='', encoding='utf-8_sig') as csv_file:
            writer = csv.writer(csv_file)

            writer.writerow(["نام", "شماره همراه", "پست الکترونیک"])

            for id in planned_for_update_vms:
                for raw_info in extracted_data:

                    column1 = ""
                    column2 = ""
                    column3 = ""

                    if id[1].strip() == str(raw_info[0]).strip():
                        column1 = raw_info[1]
                        column2 = raw_info[4]
                        column3 = f"{raw_info[3]}({raw_info[2]})"

                        writer.writerow([column1, column2, column3])

        # End of SMS Calculation

        # Filling Ticket HID for Abramad Support

        sarv_data = []

        sarv_csv_file = "C:/Users/sina.z/Desktop/Automation_Reports/Downtime/rawt.csv"
        with open(sarv_csv_file, 'r', encoding='utf-8-sig') as read_file:
            reader = csv.reader(read_file)

            # Skip the first 8 lines
            for _ in range(8):
                next(reader)

            for row in reader:
                sarv_data.append([row[0], row[4]])

        ####################################################

        sms_email_data = []

        sms_email_csv_file = "C:/Users/sina.z/Desktop/Automation_Reports/Downtime/Planned_For_Update_SMS.csv"
        with open(sms_email_csv_file, 'r', encoding='utf-8-sig') as read_file:
            reader = csv.reader(read_file)

            # Skip the first 1 lines
            for _ in range(1):
                next(reader)

            for row in reader:
                temp_mail = row[2].split("(")
                customer_name = row[0]
                sms_email_data.append([temp_mail[0].lower(), customer_name])

        final_data_hid = []
        final_data_email = []

        for hid in sarv_data:

            for email in sms_email_data:

                if email[0].lower().strip() == hid[0].lower().strip():
                    final_data_hid.append(hid[1])
                    final_data_email.append(hid[0].lower())
                    print(f"Matched: {hid[0].lower()}")

        email_data = []
        for i in sms_email_data:
            email_data.append(i[0])

        remainder_data = set(email_data) - set(final_data_email)
        remainder_amount = len(set(email_data)) - len(set(final_data_email))

        remainder_customers = []
        for i in remainder_data:
            for j in sms_email_data:
                if i.lower() == j[0].lower():
                    remainder_customers.append(j[1])

        print("\n")
        print(set(email_data))
        print(len(set(email_data)))
        print("\n")
        print(set(final_data_hid))
        print(len(set(final_data_hid)))
        print("\n")
        print(remainder_data)
        print(set(remainder_customers))
        print(remainder_amount)

        hid_csv_file = "C:/Users/sina.z/Desktop/Automation_Reports/Downtime/Planned_For_Update_HID.csv"

        with open(hid_csv_file, mode='w', newline='', encoding='utf-8_sig') as file:

            # Create a CSV writer object
            writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for k in set(final_data_hid):
                writer.writerow([k])

            for z in set(remainder_customers):
                writer.writerow([z])

        # End of Ticket HID Calculations

        to_be_updated_schedule_table += "</table>"

        # Check Table Emptiness then send Email
        empty_schedule_table_vip = """
                                        <table>
                                        <tr>
                                            <td><b>==============</b></td>
                                            <td><b>VIP Customers</b></td>
                                            <td><b>==============</b></td>
                                        </tr>
                                        <tr>
                                            <td><b>VM Name</b></td>
                                            <td><b>National ID</b></td>
                                            <td><b>Persian Name</b></td>
                                        </tr>
                                        </table>"""

        if to_be_updated_schedule_table == empty_schedule_table_vip and int(mediocre_flag) == 1 and int(vip_flag) == 0:

            # VIP Customers are all updated

            html_line_break = '''
                                <p><br></p>
                            '''
            html_msg_1s = '''
                        <html dir="rtl">
                        <head>
                            <style>
                            .numeric_class {
                                direction: ltr;
                                font-family: Calibri;
                                text-align: right;
                            }
    
                            </style>
                          </head>
                          <body>
                        '''
            html_msg_2s = '''
                            <p  style="font-family: DiodrumArabic-Regular">با سلام و احترام</p>
                        '''
            html_msg_3s = f'''
                            <p  style="font-family: DiodrumArabic-Regular">به اطلاع میرساندبروزرسانی سیستم عامل و نرم افزار های مشترکین ابرآمد، شامل سرویس های اتوماسیون، راهکاران، سهام فصل، سپیدار، BI و مدیریت شده به انضمام مشترکین VIP راهکاران برای تاریخ {downtime_month_label} {downtime_year} به اتمام رسید.</p>
                        '''
            html_msg_4s = f'''
                            <p  style="font-family: DiodrumArabic-Regular">سپاس از همکاری و همراهی تمام دوستان</p>
                        '''
            html_msg_5s = f'''
                            <p style="font-family: DiodrumArabic-Regular"></p>
                        '''
            html_msg_6s = '''
                          </body>
                        </html>
                        '''

            vip_email_body = html_msg_1s + html_msg_2s + html_msg_3s + html_line_break + html_msg_4s + html_line_break + html_msg_5s + html_msg_6s

            send_anonymous_email(
                from_email="Downtime@abramad.com",
                to_email=finished_email_list,
                cc_email='',
                subject=f'اتمام بروزرسانی OS و نرم افزار های مشترکین VIP | {downtime_month_label} {downtime_year}',
                html_message=vip_email_body,
                direction="rtl"
            )

            # Bring up vip flag
            with open(vip_path, "w", encoding="utf-8") as file:
                file.write("1")

            print("All VIP customers Updated Successfully")

        elif to_be_updated_schedule_table == empty_schedule_table_vip and int(mediocre_flag) == 1 and int(vip_flag) == 1:
            print("All mediocre and VIP are updated and both flags are 1")

        else:

            # Send Email to King

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
                            font-family: Calibri;
                            text-align: right;
                        }
    
                        table {
                            font-family: DiodrumArabic-Regular;
                            border-collapse: collapse;
                            margin-left: 0;
                            direction: rtl;
                        }
    
                        table td {
                            border: 1px solid black;
                            padding: 8px;
                            width: 250px;
                            text-align: right;
                            direction: rtl; 
                        }
                        </style>
                      </head>
                      <body>
                    '''
            html_msg_2s = '''
                        <p  style="font-family: DiodrumArabic-Regular">با سلام و احترام</p>
                    '''
            html_msg_3s = f'''
                        <p  style="font-family: DiodrumArabic-Regular">در راستای بروزرسانی سیستم عامل مشترکین مدیریت شده ی ابرآمد به جهت نصب آخرین آپدیت های مایکروسافت در {downtime_month_label} ماه مشترکین زیر در تاریخ {downtime_day_label_fa} {downtime_day} {downtime_month_label} {downtime_year} از ساعت 01:00 الی 05:00 بامداد آپدیت میگردند.</p>
                    '''
            html_msg_4s = f'''
                        <p  style="font-family: DiodrumArabic-Regular"><b>{to_be_updated_schedule_table}</b></p>
                    '''
            html_msg_5s = f'''
                            <p  style="font-family: DiodrumArabic-Regular">@AbramadSystem لطفا کالکشنی برای مشترکین قرار گرفته شده در فایل Planned_For_Update_System قرار گرفته در پیوست برای بروزرسانی OS و اپلیکیشن ها در تاریخ مذکور ایجاد فرمایید.</p>
                        '''
            html_msg_6s = f'''
                                <p  style="font-family: DiodrumArabic-Regular">@AbramadSupport لطفا اطلاع رسانی به مشترکین به صورت تیکت، با استفاده از متن درون فایل EtelaResani-General–Ticket قرار گرفته به پیوست را انجام دهید.</p>
                            '''
            html_msg_7s = f'''
                                <p  style="font-family: DiodrumArabic-Regular">@Ehsan Hojjat لطفا در اطلاع رسانی به مشترکین به صورت SMS، با توجه به فایل های EtelaResani-General–SMS  و Planned_For_Update_SMS قرار گرفته به پیوست، تیم ساپورت را از یاری خود بهره مند سازید.</p>
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

            inform_email_body = html_msg_1s + html_msg_2s + html_msg_3s + html_line_break + html_msg_4s + html_line_break + html_msg_5s + html_msg_6s + html_msg_7s + html_msg_8s + html_line_break + html_msg_9s

            # Zipping files with password
            files = [ticket_path, sms_path, planned_for_update_sms_path, planned_for_update_system_path,
                             hid_csv_file]
            make_zip(files, zip_path, zip_pass)

            send_anonymous_email(
                from_email="Downtime@abramad.com",
                to_email=reciever_email,
                cc_email=cc_email,
                subject=f'اطلاعیه بروزرسانی مشترکین مدیریت شده ابرآمد | سری {int_version_no}  | {downtime_day} {downtime_month_label} {downtime_year}',
                html_message=inform_email_body,
                direction="rtl",
                attachments=[zip_path]
            )

            '''
            ##############################
            # Create and Attach Calendar #
            ##############################
    
    
            # Calculate Date for Calendar
            # Get today's Jalali date
            khareji_today = datetime.now().date()
    
            # Add two days to today's date
            khareji_downtime_date = khareji_today + timedelta(days=3)
    
            khareji_downtime_day = int(str(khareji_downtime_date)[8:10])
            khareji_downtime_month = int(str(khareji_downtime_date)[5:7])
            khareji_downtime_year = int(str(khareji_downtime_date)[:4])
    
    
            # Calendar Text
            text_cal = f"متن مربوط به ایمیل اطلاع رسانی سری {int_version_no}ام\nبرای {downtime_month_label} ماه {downtime_year}  را بررسی فرمایید\nبا سپاس"
    
            # Meeting details
            subject = f'اطلاعیه بروزرسانی مشترکین مدیریت شده ابرآمد | سری {int_version_no}  | {downtime_day} {downtime_month_label} {downtime_year}'
            start = datetime(khareji_downtime_year, khareji_downtime_month, khareji_downtime_day, 1,
                             0)  # Meeting start time
            end = start + timedelta(hours=4)  # Meeting end time
            location = 'سرور های مشترکین مربوطه'
            attendees = ['abramadops@systemgroup.net']
            organizer = 'sina.z@abramad.com'
    
            # Create iCalendar event
            event = Event()
            event.add('summary', subject)
            event.add('dtstart', start)
            event.add('dtend', end)
            event.add('location', location)
            event.add('organizer', organizer)
            event.add('description', text_cal)
            event.add('status', 'CONFIRMED')
    
            for attendee in attendees:
                event.add('attendee', attendee)
    
            # Create iCalendar calendar and add the event
            cal = Calendar()
            cal.add_component(event)
    
            # Generate the iCalendar content as a string
            ical_content = cal.to_ical()
    
            calendar_part = MIMEBase('text', 'calendar', method='REQUEST')
            calendar_part.set_payload(ical_content)
            encoders.encode_base64(calendar_part)
            calendar_part.add_header('Content-Disposition', 'attachment; filename="meeting.ics"')
    
            # Attach Calendar file
            msg.attach(calendar_part)
    
            # Attach Text to email
            msg.attach(MIMEText(inform_email_body, 'html'))
    
            # Connect to the SMTP server and send the email 465,*587*,25 (mail.systemgroup.net)
            # Send email info
            smtp_server = 'mail.systemgroup.net'
            smtp_port = 587
            smtp_username = username
            smtp_password = password
    
            # Send email function
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail('sina.z@abramad.com', reciever_email.split(",") + cc_email.split(','), msg.as_string())
            '''

            # Increment Version No by one
            int_version_no += 1
            # Overwrite the file with the new data
            with open(version_no_path, "w") as file:
                file.write(str(int_version_no))

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
