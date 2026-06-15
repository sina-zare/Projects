from datetime import datetime
from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import smtplib
from email.mime.multipart import MIMEMultipart
from persiantools.jdatetime import JalaliDate
from datetime import date
from email.mime.text import MIMEText
import warnings
import re
import time
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
script_name = 'empty_attributes'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'https://me-prometheus.abramad.com:9091'
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
            send_anonymous_email('ScriptErrors@abramad.com', 'support@abramad.com, abramadsysops@abramad.com', 'sina.z@abramad.com',
                                 f"email_sender Function Error in running All_VMs_Info.py",
                                 f"Error Occurred:<br><b>{err}<br></b> Agent: Empty_Attributes.py",
                                 'ltr')


    month_dict = {
        "1": "Dey",
        "2": "Bah",
        "3": "Esf",
        "4": "Far",
        "5": "Ord",
        "6": "Khor",
        "7": "Tir",
        "8": "Mor",
        "9": "Shah",
        "10": "Mehr",
        "11": "Aban",
        "12": "Azar"
    }

    # Get today's date
    today = date.today()
    # Convert to Persian date
    persian_date = JalaliDate.to_jalali(today.year, today.month, today.day)
    # Format the Persian date as "YYYY/MM/DD"
    today_persian_date = persian_date.strftime("%Y/%m/%d")

    current_month = f'{month_dict[str(today.month)]}'
    current_day = today_persian_date[8:11]


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
                vm.name.startswith("MER-") or vm.name.startswith("MEF-") or vm.name.startswith(
            "MES-") or vm.name.startswith("MEA-") or vm.name.startswith("MEB-") or vm.name.startswith(
            "MEM-") or vm.name.startswith("MERD-") or vm.name.startswith("MEI-") or vm.name.startswith("MESA-"))]

    count = 0
    all_poweredon_vm_defects = []
    all_poweredon_vm_defects_persian_name = []
    all_poweredon_vm_defects_create_date = []
    all_poweredon_vm_defects_shutdown_date = []
    all_poweredon_vm_defects_shutdown_ticket_no = []
    all_poweredon_vm_defects_national_id = []

    all_poweredoff_vm_defects = []
    all_poweredoff_vm_defects_persian_name = []
    all_poweredoff_vm_defects_create_date = []
    all_poweredoff_vm_defects_shutdown_date = []
    all_poweredoff_vm_defects_shutdown_ticket_no = []
    message_on = ""
    message_off = ""
    table_on = ""
    table_off = ""

    table_on_create_date = ""
    table_on_persian_name = ""
    table_on_national_id = ""

    table_off_create_date = ""
    table_off_shutdown_date = ""
    table_off_shutdown_ticket_no = ""
    table_off_persian_name = ""

    # Start Calculation of falling in dates VMs
    for vm in me_vms:
        vm_power_state = vm.runtime.powerState.lower()

        # Calculation for PoweredOn VMs
        if vm_power_state == "poweredon":

            if vm.name.lower() != "mea-abfan" and vm.name.lower() != "mea-damiranian" and vm.name.lower() != "mei-rezanaseri" and vm.name.lower() != "mer-aradhp" and vm.name.lower() != "mem-zubina" and vm.name.lower() != "mer-behranoil" and vm.name.lower() != "mem-sahamabri" and vm.name.lower() != "mem-farsanr-dem" and vm.name.lower() != "mer-hallaji" and vm.name.lower() != "mer-rastanakh" and vm.name.lower() != "mer-parvazs" and vm.name.lower() != "mei-misexam" and vm.name.lower() != "mesa-sahamabr03" and vm.name.lower() != "mer-amirreza" and vm.name.lower() != "mei-mkoulivand" and vm.name.lower() != "mei-padyab" and vm.name.lower() != "mei-paivandtech" and vm.name.lower() != "mer-ariyange" and vm.name.lower() != "mei-infokh8" and vm.name.lower() != "mei-gsalim" and vm.name.lower() != "mei-infokh9" and vm.name.lower() != "mer-dorna-t" and vm.name.lower() != "mer-sadaf-a1" and vm.name.lower() != "mer-sadaf-db" and vm.name.lower() != "mer-shimak-db" and vm.name.lower() != "mer-nikandarou":

                # Get VM Name
                pon_vm_name = vm.name

                # Get Real VM Creation Date
                pon_real_vm_creation_date = str(JalaliDate(vm.config.createDate)).replace("-", "/")
                # Get VM Creation Date
                pon_vm_creation_date = ""
                custom_value_d_on = vm.summary.customValue
                for i in custom_value_d_on:
                    if i.key == 104:
                        pon_vm_creation_date = i.value

                # Get VM Ticket No
                pon_ticket_no_defect = "Empty"
                vm_note = vm.config.annotation.split("\n")
                vm_ticket_no = (vm_note[0][10:]).replace(":", "").strip()
                if vm_ticket_no.isnumeric():
                    pon_ticket_no_defect = vm_ticket_no

                # Get Public IP
                pon_public_ip_defect = "Empty"
                # all vms starting with mer and not containing -db
                if re.match(r"^mer-(?!.*-db).*", vm.name.lower()):
                    # Get VM Public IP
                    vm_custom_attr = vm.summary.customValue
                    for i in vm_custom_attr:
                        if i.key == 603:
                            pon_public_ip_defect = i.value
                elif vm.name.startswith("MEF-") or vm.name.startswith("MES-") or vm.name.startswith(
                        "MEA-") or vm.name.startswith("MEB-") or vm.name.startswith("MEM-") or vm.name.startswith(
                        "MEI-") or vm.name.startswith("MERD-"):
                    # Get VM Public IP
                    vm_custom_attr = vm.summary.customValue
                    for i in vm_custom_attr:
                        if i.key == 603:
                            pon_public_ip_defect = i.value
                # all vms having -db*
                pattern = "-db.*"
                if re.search(pattern, vm.name, re.IGNORECASE):
                    pon_public_ip_defect = "No Need"

                # Get VM Persian Name
                pon_persian_name_defect = "Empty"
                custom_value_n = vm.summary.customValue
                for i in custom_value_n:
                    if i.key == 103:
                        pon_persian_name_defect = i.value

                # Get URL
                pon_url_defect = "Empty"
                # all vms starting with mer and not containing -db
                if re.match(r"^mer-(?!.*-db).*", vm.name.lower()):
                    # Get VM URL
                    vm_custom_attr = vm.summary.customValue
                    for i in vm_custom_attr:
                        if i.key == 604:
                            pon_url_defect = i.value
                elif vm.name.startswith("MEF-") or vm.name.startswith("MES-") or vm.name.startswith(
                        "MEA-") or vm.name.startswith("MEB-") or vm.name.startswith("MEM-") or vm.name.startswith(
                        "MEI-") or vm.name.startswith("MERD-"):
                    # Get VM URL
                    vm_custom_attr = vm.summary.customValue
                    for i in vm_custom_attr:
                        if i.key == 604:
                            pon_url_defect = i.value
                # all vms having -db*
                pattern = "-db.*"
                if re.search(pattern, vm.name, re.IGNORECASE):
                    pon_url_defect = "No Need"

                pon_vm_national_id_defect = "Empty"
                custom_value_n = vm.summary.customValue
                for i in custom_value_n:
                    if i.key == 611:
                        pon_vm_national_id_defect = i.value

                pon_vm_defects = [
                    pon_vm_name,
                    pon_vm_creation_date,
                    pon_ticket_no_defect,
                    pon_public_ip_defect,
                    pon_persian_name_defect,
                    pon_url_defect,
                    pon_vm_national_id_defect
                ]

                all_poweredon_vm_defects.append(pon_vm_defects)

                if pon_persian_name_defect == "Empty":
                    all_poweredon_vm_defects_persian_name.append([pon_vm_name, pon_persian_name_defect])
                if pon_vm_national_id_defect == "Empty":
                    all_poweredon_vm_defects_national_id.append([pon_vm_name, pon_vm_national_id_defect])
                if pon_vm_creation_date.strip() != pon_real_vm_creation_date.strip():
                    all_poweredon_vm_defects_create_date.append(
                        [pon_vm_name, pon_vm_creation_date, pon_real_vm_creation_date])

        # Calculation for PoweredOff VMs
        elif (vm_power_state == "poweredoff" and vm.name != "MER-SingleTEMP") or (
                vm_power_state == "poweredoff" and vm.name.lower() != "mei-sarv-template-ubuntu2204"):

            print(f"Powered Off: {vm.name}")

            # Get VM Name
            poff_vm_name = vm.name

            # Get Real VM Creation Date
            poff_real_vm_creation_date = str(JalaliDate(vm.config.createDate)).replace("-", "/")
            # Get VM Creation Date
            poff_vm_creation_date = ""
            custom_value_d_off = vm.summary.customValue
            for i in custom_value_d_off:
                if i.key == 104:
                    poff_vm_creation_date = i.value

            # Get VM Ticket No
            poff_ticket_no_defect = "Empty"
            vm_note = vm.config.annotation.split("\n")
            vm_ticket_no = (vm_note[0][10:]).replace(":", "").strip()
            if vm_ticket_no.isnumeric():
                poff_ticket_no_defect = vm_ticket_no

            # Get VM Shutdown Ticket No
            poff_shutdown_ticket_no_defect = ""
            if vm.name.lower() != "mei-ava-centos7-template01" and vm.name.lower() != "mei-ava-centos7-template02" and vm.name.lower() != "mer-singletemp" and vm.name.lower() != "mei-sarv-template-ubuntu2204" and vm.name.lower() != "mei-sarv-tmp":
                poff_shutdown_ticket_no_defect = "Empty"
                vm_note = vm.config.annotation.split("\n")
                vm_shutdown_ticket_no = vm_note
                # if vm_shutdown_ticket_no.isnumeric():
                poff_shutdown_ticket_no_defect = vm_shutdown_ticket_no

            # Get Public IP
            poff_public_ip_defect = "Empty"
            # all vms starting with mer and not containing -db
            if re.match(r"^mer-(?!.*-db).*", vm.name.lower()):
                # Get VM Public IP
                vm_custom_attr = vm.summary.customValue
                for i in vm_custom_attr:
                    if i.key == 603:
                        poff_public_ip_defect = i.value
            elif vm.name.startswith("MEF-") or vm.name.startswith("MES-") or vm.name.startswith(
                    "MEA-") or vm.name.startswith("MEB-") or vm.name.startswith("MEM-") or vm.name.startswith(
                "MEI-") or vm.name.startswith("MERD-"):
                # Get VM Public IP
                vm_custom_attr = vm.summary.customValue
                for i in vm_custom_attr:
                    if i.key == 603:
                        poff_public_ip_defect = i.value
            # all vms having -db*
            pattern = "-db.*"
            if re.search(pattern, vm.name, re.IGNORECASE):
                poff_public_ip_defect = "No Need"

            # Get VM Persian Name
            poff_persian_name_defect = ""
            if vm.name.lower() != "mei-ava-centos7-template01" and vm.name.lower() != "mei-ava-centos7-template02" and vm.name.lower() != "mer-singletemp" and vm.name.lower() != "mei-sarv-tmp":
                poff_persian_name_defect = "Empty"
                custom_value_n = vm.summary.customValue
                for i in custom_value_n:
                    if i.key == 103:
                        poff_persian_name_defect = i.value

            # Get URL
            poff_url_defect = "Empty"
            # all vms starting with mer and not containing -db
            if re.match(r"^mer-(?!.*-db).*", vm.name.lower()):
                # Get VM URL
                vm_custom_attr = vm.summary.customValue
                for i in vm_custom_attr:
                    if i.key == 604:
                        poff_url_defect = i.value
            elif vm.name.startswith("MEF-") or vm.name.startswith("MES-") or vm.name.startswith(
                    "MEA-") or vm.name.startswith("MEB-") or vm.name.startswith("MEM-") or vm.name.startswith(
                "MEI-") or vm.name.startswith("MERD-"):
                # Get VM URL
                vm_custom_attr = vm.summary.customValue
                for i in vm_custom_attr:
                    if i.key == 604:
                        poff_url_defect = i.value
            # all vms having -db*
            pattern = "-db.*"
            if re.search(pattern, vm.name, re.IGNORECASE):
                poff_url_defect = "No Need"

            # Get Shutdown Date
            poff_shutdown_date_defect = ""
            if vm.name.lower() != "mei-ava-centos7-template01" and vm.name.lower() != "mei-ava-centos7-template02" and vm.name.lower() != "mer-singletemp" and vm.name.lower() != "mei-sarv-tmp":
                poff_shutdown_date_defect = "Empty"
                custom_value_d = vm.summary.customValue
                for i in custom_value_d:
                    if i.key == 401:
                        poff_shutdown_date_defect = i.value

            if poff_vm_creation_date == "Empty" or poff_ticket_no_defect == "Empty" or poff_shutdown_ticket_no_defect == "Empty" or poff_public_ip_defect == "Empty" or poff_persian_name_defect == "Empty" or poff_url_defect == "Empty" or poff_shutdown_date_defect == "Empty":
                poff_vm_defects = [
                    poff_vm_name,
                    poff_vm_creation_date,
                    poff_ticket_no_defect,
                    poff_shutdown_ticket_no_defect,
                    poff_public_ip_defect,
                    poff_persian_name_defect,
                    poff_url_defect,
                    poff_shutdown_date_defect
                ]
                all_poweredoff_vm_defects.append(poff_vm_defects)

            # Persian Name Defect
            if poff_persian_name_defect == "Empty":
                all_poweredoff_vm_defects_persian_name.append([poff_vm_name, poff_persian_name_defect])
            # Create Date Defect
            if poff_vm_creation_date.strip() != poff_real_vm_creation_date.strip():
                all_poweredoff_vm_defects_create_date.append(
                    [poff_vm_name, poff_vm_creation_date, poff_real_vm_creation_date])
            # Shutdown Date Defect
            if poff_shutdown_date_defect == "Empty":
                all_poweredoff_vm_defects_shutdown_date.append([poff_vm_name, poff_shutdown_date_defect])
            # Shutdown Ticket No Defect
            if poff_shutdown_ticket_no_defect == "Empty":
                all_poweredoff_vm_defects_shutdown_ticket_no.append(([poff_vm_name, poff_shutdown_ticket_no_defect]))

    for vm_on in all_poweredon_vm_defects:
        table_on += f"""
                <table>
                    <tr>
    
                        <td>{vm_on[0]}</td>
                        <td><b>VM Name: </b></td>
                    </tr>
                    <tr>
    
                        <td>{vm_on[1]}</td>
                        <td><b>Creation Date: </b></td>
                    </tr>
                    <tr>
    
                        <td>{vm_on[2]}</td>
                        <td><b>Ticket No: </b></td>
                    </tr>
                    <tr>
    
                        <td>{vm_on[3]}</td>
                        <td><b>Public IP: </b></td>
                    </tr>
                    <tr>
    
                        <td>{vm_on[4]}</td>
                        <td><b>Persian Name: </b></td>
                    </tr>
                    <tr>
    
                        <td>{vm_on[5]}</td>
                        <td><b>URL: </b></td>
                    </tr>
                </table>
                <p><br><br></p>
        """
        message_on += f"<p>VM Name: {vm_on[0]}<br>Creation Date: {vm_on[1]}<br>Ticket No: {vm_on[2]}<br>Public IP: {vm_on[3]}<br>Persian Name: {vm_on[4]}<br>URL: {vm_on[5]}<br></p>"

    for i in all_poweredon_vm_defects_create_date:
        table_on_create_date += f"""
                <table>
                    <tr>
                        <td>{i[0]}</td>
                        <td><b>VM Name: </b></td>
                    </tr>
                    <tr>
                        <td>
                            <span style="color: #900C3F;">{i[1]}</span>
                        </td>
                        <td><b>Wrong Create Date: </b></td>
                    </tr>
                    <tr>
                        <td>
                            <span style="color: #46D070;">{i[2]}</span>
                        </td>
                        <td><b>Correct Create Date: </b></td>
                    </tr>
                </table>
                <p><br><br></p>
            """
    for i in all_poweredon_vm_defects_persian_name:
        table_on_persian_name += f"""
                        <table>
                            <tr>
                                <td>{i[0]}</td>
                                <td><b>VM Name: </b></td>
                            </tr>
                            <tr>
                                <td>{i[1]}</td>
                                <td>Persian Name: </td>
                            </tr>
                        </table>
                        <p><br><br></p>
    
                    """

    for i in all_poweredon_vm_defects_national_id:
        table_on_national_id += f"""
                        <table>
                            <tr>
                                <td>{i[0]}</td>
                                <td><b>VM Name: </b></td>
                            </tr>
                            <tr>
                                <td>{i[1]}</td>
                                <td>National ID: </td>
                            </tr>
                        </table>
                        <p><br><br></p>
    
                    """

    for vm_off in all_poweredoff_vm_defects:
        table_off += f"""
                    <table>
                        <tr>
                            <td>{vm_off[0]}</td>
                            <td><b>VM Name: </b></td>
                        </tr>
                        <tr>
    
                            <td>{vm_off[1]}</td>
                            <td><b>Creation Date: </b></td>
                        </tr>
                        <tr>
    
                            <td>{vm_off[2]}</td>
                            <td><b>Creation Ticket No: </b></td>
                        </tr>
                        <tr>
    
                            <td>{vm_off[3]}</td>
                            <td><b>Shutdown Ticket No: </b></td>
                        </tr>
                        <tr>
    
                            <td>{vm_off[4]}</td>
                            <td><b>Public IP: </b></td>
                        </tr>
                        <tr>
    
                            <td>{vm_off[5]}</td>
                            <td><b>Persian Name: </b></td>
                        </tr>
                        <tr>
    
                            <td>{vm_off[6]}</td>
                            <td><b>URL: </b></td>
                        </tr>
                    </table>
                    <p><br><br></p>
            """
        message_off += f"<p>VM Name: {vm_off[0]}<br>Creation Date: {vm_off[1]}<br>Creation Ticket No: {vm_off[2]}<br>Shutdown Ticket No: {vm_off[3]}<br>Public IP: {vm_off[4]}<br>Persian Name: {vm_off[5]}<br>URL: {vm_off[6]}<br></p>"

    for i in all_poweredoff_vm_defects_create_date:
        table_off_create_date += f"""
                <table>
                    <tr>
                        <td>{i[0]}</td>
                        <td><b>VM Name: </b></td>
                    </tr>
                    <tr>
                        <td>
                            <span style="color: #900C3F;">{i[1]}</span>
                        </td>
                        <td><b>Wrong Create Date: </b></td>
                    </tr>
                    <tr>
                        <td>
                            <span style="color: #46D070;">{i[2]}</span>
                        </td>
                        <td><b>Correct Create Date: </b></td>
                    </tr>
                </table>
                <p><br><br></p>
    
            """
    for i in all_poweredoff_vm_defects_shutdown_date:
        table_off_shutdown_date += f"""
                <table>
                    <tr>
                        <td>{i[0]}</td>
                        <td><b>VM Name: </b></td>
                    </tr>
                    <tr>
                        <td>{i[1]}</td>
                        <td>Shutdown Date: </td>
                    </tr>
                </table>
                <p><br><br></p>
            """
    for i in all_poweredoff_vm_defects_shutdown_ticket_no:
        table_off_shutdown_ticket_no += f"""
                    <table>
                        <tr>
                            <td>{i[0]}</td>
                            <td><b>VM Name: </b></td>
                        </tr>
                        <tr>
                            <td>{i[1]}</td>
                            <td>Shutdown Ticket No: </td>
                        </tr>
                    </table>
                    <p><br><br></p>
                """
    for i in all_poweredoff_vm_defects_persian_name:
        table_off_persian_name += f"""
                        <table>
                            <tr>
                                <td>{i[0]}</td>
                                <td><b>VM Name: </b></td>
                            </tr>
                            <tr>
                                <td>{i[1]}</td>
                                <td>Persian Name: </td>
                            </tr>
                        </table>
                        <p><br><br></p>
                    """

    ##############################################
    ######### HTML Body Begin For Email ##########
    html_line_break = '''
            <p><br></p>
        '''
    html_msg_1 = '''
        <html dir="rtl">
        <head>
            <style>
            table {
                font-family: DiodrumArabic-Regular;
                border-collapse: collapse;
                margin-left: 0;
            }
    
            table td {
                border: 1px solid black;
                padding: 8px;
                width: 250px;
                direction: ltr; 
            }
            </style>
          </head>
          <body>
        '''
    html_msg_2 = '''
            <p  style="font-family: DiodrumArabic-Regular">با سلام و احترام</p>
        '''
    html_msg_no_defect = '''
            <p  style="font-family: DiodrumArabic-Regular">تمامی attribute های مربوط به این ایمیل تکمیل میباشد و نقصی در این خصوص وجود ندارد.</p>
        '''
    html_msg_3 = f'''
            <p  style="font-family: DiodrumArabic-Regular">سرور های زیر دارای حداقل یک attribute خالی یا اشتباه میباشند، لطفا نسبت به تکمیل نمودن آنها اقدام نمایید.</p>
        '''
    html_msg_4 = f'''
                <p  style="font-family: DiodrumArabic-Regular"><b>لیست سرور های روشن:<br></b></p>
            '''
    html_msg_on_create_date_a = f'''
                <p  style="font-family: DiodrumArabic-Regular"><b>مشکلات مربوط به تاریخ ساخت سرور: <br></b></p>
            '''
    html_msg_on_create_date_b = table_on_create_date

    html_msg_on_persian_name_a = f'''
                <p  style="font-family: DiodrumArabic-Regular"><b>مشکلات مربوط به نام فارسی مشترک: <br></b></p>
            '''
    html_msg_on_persian_name_b = table_on_persian_name

    html_msg_on_national_id_a = f'''
                <p  style="font-family: DiodrumArabic-Regular"><b>مشکلات مربوط به شناسه ملی مشترک: <br></b></p>
            '''
    html_msg_on_national_id_b = table_on_national_id

    html_msg_7 = f'''
            <p style="font-family: DiodrumArabic-Regular"><b>لیست سرور های خاموش:<br></b></p>
        '''
    html_msg_off_create_date_a = f'''
                <p  style="font-family: DiodrumArabic-Regular"><b>مشکلات مربوط به تاریخ ساخت سرور: <br></b></p>
            '''
    html_msg_off_create_date_b = table_off_create_date

    html_msg_off_persian_name_a = f'''
                <p  style="font-family: DiodrumArabic-Regular"><b>مشکلات مربوط به نام فارسی مشترک: <br></b></p>
            '''
    html_msg_off_persian_name_b = table_off_persian_name

    html_msg_off_shutdown_date_a = f'''
                <p  style="font-family: DiodrumArabic-Regular"><b>مشکلات مربوط به تاریخ خاموشی سرور: <br></b></p>
            '''
    html_msg_off_shutdown_date_b = table_off_shutdown_date

    html_msg_off_shutdown_ticket_no_a = f'''
                <p  style="font-family: DiodrumArabic-Regular"><b>مشکلات مربوط به شماره تیکت خاموشی سرور: <br></b></p>
            '''
    html_msg_off_shutdown_ticket_no_b = table_off_shutdown_ticket_no

    html_msg_10 = f'''
            <p style="font-family: DiodrumArabic-Regular"></p>
        '''
    html_msg_11 = '''
          </body>
        </html>
        '''
    ######### HTML Body End For Email ##########
    ############################################

    email_body_create_date_defect = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_4 + html_msg_on_create_date_a + html_msg_on_create_date_b + html_msg_7 + html_msg_off_create_date_a + html_msg_off_create_date_b + html_msg_10 + html_msg_11
    email_body_persian_name_defect = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_4 + html_msg_on_persian_name_a + html_msg_on_persian_name_b + html_msg_7 + html_msg_off_persian_name_a + html_msg_off_persian_name_b + html_msg_10 + html_msg_11
    email_body_shutdown_date = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_7 + html_msg_off_shutdown_date_a + html_msg_off_shutdown_date_b + html_msg_10 + html_msg_11
    email_body_shutdown_ticket_no = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_7 + html_msg_off_shutdown_ticket_no_a + html_msg_off_shutdown_ticket_no_b + html_msg_10 + html_msg_11
    email_body_national_id_defect = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_4 + html_msg_on_national_id_a + html_msg_on_national_id_b + html_msg_10 + html_msg_11
    email_body_no_defect_exists = html_msg_1 + html_msg_2 + html_msg_no_defect + html_line_break + html_msg_10 + html_msg_11

    email_templates = [
        [email_body_create_date_defect, "Create Date Defects"],
        [email_body_persian_name_defect, "Persian Name Defect"],
        [email_body_shutdown_date, "Shutdown Date Defect"],
        [email_body_shutdown_ticket_no, "Shutdown Ticket No Defect"],
        [email_body_national_id_defect, "National ID Defect"]
    ]

    # Declare (Sender, To, CC)
    sender_email = 'sina.z@abramad.com'
    receiver_email = 'support@abramad.com'
    cc_email = 'mehdi.a@abramad.com, alireza.ja@abramad.com'

    # Check if Create Date Defect Exists
    if len(all_poweredon_vm_defects_create_date) == 0 and len(all_poweredoff_vm_defects_create_date) == 0:
        # Send Email to King

        '''send_anonymous_email(
            from_email="EmptyAttributes@abramad.com",
            to_email=receiver_email,
            cc_email=cc_email,
            subject=f'Server Empty Attributes | {current_month}-{current_day} | {email_templates[0][1]} ',
            html_message=email_body_no_defect_exists,
            direction="rtl"
            # attachments=[]
        )
    
        time.sleep(30)'''

    else:
        # Send Email to of defects

        send_anonymous_email(
            from_email="EmptyAttributes@abramad.com",
            to_email=receiver_email,
            cc_email=cc_email,
            subject=f'Server Empty Attributes | {current_month}-{current_day} | {email_templates[0][1]} ',
            html_message=email_templates[0][0],
            direction="rtl"
            # attachments=[]
        )

        #time.sleep(30)

    # Check if Persian Name Defect Exists
    if len(all_poweredon_vm_defects_persian_name) == 0 and len(all_poweredoff_vm_defects_persian_name) == 0:
        # Send Email to King

        '''send_anonymous_email(
            from_email="EmptyAttributes@abramad.com",
            to_email=receiver_email,
            cc_email=cc_email,
            subject=f'Server Empty Attributes | {current_month}-{current_day} | {email_templates[1][1]} ',
            html_message=email_body_no_defect_exists,
            direction="rtl"
            # attachments=[]
        )
    
        time.sleep(30)'''
    else:
        # Send Email to of defects

        send_anonymous_email(
            from_email="EmptyAttributes@abramad.com",
            to_email=receiver_email,
            cc_email=cc_email,
            subject=f'Server Empty Attributes | {current_month}-{current_day} | {email_templates[1][1]} ',
            html_message=email_templates[1][0],
            direction="rtl"
            # attachments=[]
        )

        #time.sleep(30)

    # Check if Shutdown Date Defect Exists
    if len(all_poweredoff_vm_defects_shutdown_date) == 0:
        # Send Email to King

        '''send_anonymous_email(
            from_email="EmptyAttributes@abramad.com",
            to_email=receiver_email,
            cc_email=cc_email,
            subject=f'Server Empty Attributes | {current_month}-{current_day} | {email_templates[2][1]} ',
            html_message=email_body_no_defect_exists,
            direction="rtl"
            # attachments=[]
        )
    
        time.sleep(30)'''
    else:
        # Send Email to of defects

        send_anonymous_email(
            from_email="EmptyAttributes@abramad.com",
            to_email=receiver_email,
            cc_email=cc_email,
            subject=f'Server Empty Attributes | {current_month}-{current_day} | {email_templates[2][1]} ',
            html_message=email_templates[2][0],
            direction="rtl"
            # attachments=[]
        )

        #time.sleep(30)

    # Check if Shutdown Ticket No Defect Exists
    if len(all_poweredoff_vm_defects_shutdown_ticket_no) == 0:
        # Send Email to King

        '''send_anonymous_email(
            from_email="EmptyAttributes@abramad.com",
            to_email=receiver_email,
            cc_email=cc_email,
            subject=f'Server Empty Attributes | {current_month}-{current_day} | {email_templates[3][1]} ',
            html_message=email_body_no_defect_exists,
            direction="rtl"
            # attachments=[]
        )
    
        time.sleep(30)'''
    else:
        # Send Email to of defects

        send_anonymous_email(
            from_email="EmptyAttributes@abramad.com",
            to_email=receiver_email,
            cc_email=cc_email,
            subject=f'Server Empty Attributes | {current_month}-{current_day} | {email_templates[3][1]} ',
            html_message=email_templates[3][0],
            direction="rtl"
            # attachments=[]
        )

        #time.sleep(30)

    # Check if Create Date Defect Exists
    if len(all_poweredon_vm_defects_national_id) == 0:
        # Send Email to King

        '''send_anonymous_email(
            from_email="EmptyAttributes@abramad.com",
            to_email=receiver_email,
            cc_email=cc_email,
            subject=f'Server Empty Attributes | {current_month}-{current_day} | {email_templates[4][1]} ',
            html_message=email_body_no_defect_exists,
            direction="rtl"
            # attachments=[]
        )
    
        time.sleep(30)'''
    else:
        # Send Email to of defects

        send_anonymous_email(
            from_email="EmptyAttributes@abramad.com",
            to_email=receiver_email,
            cc_email=cc_email,
            subject=f'Server Empty Attributes | {current_month}-{current_day} | {email_templates[4][1]} ',
            html_message=email_templates[4][0],
            direction="rtl"
            # attachments=[]
        )

        #time.sleep(30)

    # Disconnect from vCenter
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


