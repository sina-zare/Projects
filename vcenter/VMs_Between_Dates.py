import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import smtplib
from email.mime.multipart import MIMEMultipart
from persiantools.jdatetime import JalaliDate
from email.mime.text import MIMEText
import os
import warnings
import time
import csv

'''
from persiantools.jdatetime import JalaliDate

# Persian date to check
date_to_check = JalaliDate(1402, 1, 1)

# Boundary Persian dates
lower_boundary = JalaliDate(1402, 1, 1)
upper_boundary = JalaliDate(1402, 12, 29)

# Check if the Persian date falls between the boundary dates
if lower_boundary <= date_to_check <= upper_boundary:
    print("The Persian date falls between the boundary dates.")
else:
    print("The Persian date does not fall between the boundary dates.")
'''


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

    #print(f"Decryped Text: {decrypted_password}")
    return decrypted_password.decode()
username = decryptor("enc_sinaz_abramad","key_sinaz_abramad")
password = decryptor("enc_sinaz_pass","key_sinaz_pass")

selected_vms_path = 'C:/Users/sina.z/Desktop/Automation_Reports/VMs_Between_Dates/Selected-VMs.csv'

# Print with delay function
def print_with_delay_connecting(text):
    for char in text:
        print(f'Connecting Please Wait {char}      ', end='', flush=True)
        time.sleep(0.009)
        os.system('cls' if os.name == 'nt' else 'clear')


# Print with delay function
def print_with_delay_email(text):
    for char in text:
        print(f'{char} Email Sent {char}      ', end='', flush=True)
        time.sleep(0.01)
        os.system('cls' if os.name == 'nt' else 'clear')


# Print with delay function
def print_with_delay_email_verbose(text):
    for char in text:
        print(f'{char}Verbose Email Sent {char}      ', end='', flush=True)
        time.sleep(0.01)
        os.system('cls' if os.name == 'nt' else 'clear')


# Print with delay function
def print_with_delay(text):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(0.03)
    print("\n")


month_dict_persian = {
    "10": "دی",
    "11": "بهمن",
    "12": "اسفند",
    "01": "فروردین",
    "02": "اردیبهشت",
    "03": "خرداد",
    "04": "تیر",
    "05": "مرداد",
    "06": "شهریور",
    "07": "مهر",
    "08": "آبان",
    "09": "آذر"
}

# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)

print_with_delay("VMs Between Dates, made with love by S.Z")
time.sleep(1)
# *** Connecting to ME-VC01.Abramad.Com to get the Report ***
# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

receiver_email = input("Enter your Email address: ").lower()
receiver_email_complete = ""
if (not "@" in receiver_email):
    receiver_email_complete = receiver_email + "@abramad.com"
else:
    receiver_email_complete = receiver_email

# Clear CMD screen
os.system('cls' if os.name == 'nt' else 'clear')
# Print sequence of characters until connection is made
print_with_delay_connecting(["/", "--", "\\", "|", "/", "--", "\\", "|", "/", "--", "\\", "|"])

# Connecting to vCenter
ME_VC = connect.SmartConnect(host='me-vc01.abramad.com', user=username, pwd=password, port=443, sslContext=context)
me_content = ME_VC.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if (
            vm.name.startswith("MER-") or vm.name.startswith("MERD-") or vm.name.startswith(
        "MEF-") or vm.name.startswith("MES-") or vm.name.startswith("MEA-") or vm.name.startswith(
        "MEB-") or vm.name.startswith("MEM-") or vm.name.startswith("MEI-"))]

print_with_delay("Connected to vCenter\nVirtual Machines Loaded.")
time.sleep(1)

# Clear CMD screen
os.system('cls' if os.name == 'nt' else 'clear')

# Error Log
error_log = ""

true_flag = True

while true_flag:

    # initializing variables
    server_info = ""
    server_info_verbose = ""
    all_vm_specs = []

    os.system('cls' if os.name == 'nt' else 'clear')
    no_vms_found = True

    # Check input date format and take lower boundary
    while True:
        try:
            lower_boundary = input("Enter Date in the following format --> YYYY/MM/DD\nFrom: ").split("/")
            lower_boundary_processed = JalaliDate(int(lower_boundary[0]), int(lower_boundary[1]),
                                                  int(lower_boundary[2]))
            break
        except (ValueError, IndexError):
            print_with_delay("Wrong Format! Try Again")
            os.system('cls' if os.name == 'nt' else 'clear')
    # Check input date format and take upper boundary
    while True:
        try:
            upper_boundary = input("\nPress Enter to get all VMs created till now:\nTo: ").split("/")
            # Check if upper_boundary is one syllabus(like empty or enter)
            if len(upper_boundary) == 1:
                # Set Today's Date
                upper_boundary_processed = JalaliDate.today()
                take_upper_boundary = str(upper_boundary_processed).split("-")
                persian_month_upper_boundary = month_dict_persian[take_upper_boundary[1]]
                os.system('cls' if os.name == 'nt' else 'clear')
                break
            else:
                upper_boundary_processed = JalaliDate(int(upper_boundary[0]), int(upper_boundary[1]),
                                                      int(upper_boundary[2]))
                take_upper_boundary = str(upper_boundary_processed).split("-")
                persian_month_upper_boundary = month_dict_persian[upper_boundary[1]]
                os.system('cls' if os.name == 'nt' else 'clear')
                break
        except (ValueError, IndexError):
            print_with_delay("Wrong Format! Try Again")
            os.system('cls' if os.name == 'nt' else 'clear')

    # Send Wait Message
    print_with_delay("Please Wait. Max 1 Min")

    persian_month_lower_boundary = month_dict_persian[lower_boundary[1]]

    ##############################################
    ######### HTML Body Begin For Email ##########
    html_line_break = '''
            <p><br></p>
        '''
    html_msg_1 = '''
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
    html_msg_2 = '''
            <p  style="font-family: DiodrumArabic-Regular">با سلام و احترام</p>
        '''
    html_msg_index_error = '''
            <p  style="font-family: DiodrumArabic-Regular">متاسفانه در برنامه VMs_Between_Dates خطای Index Error پیش آمده. لطفا هر چه سریعتر جهت حل نمودن آن اقدام نمایید.<br>متن ارور:<br></p>
        '''

    html_msg_general_error = '''
            <p  style="font-family: DiodrumArabic-Regular">متاسفانه در برنامه VMs_Between_Dates خطای General Error پیش آمده. لطفا هر چه سریعتر جهت حل نمودن آن اقدام نمایید.<br>متن ارور:<br></p>
        '''
    html_msg_3 = f'''
                <p  style="font-family: DiodrumArabic-Regular">اطلاعات سرور های ساخته شده از {lower_boundary[2]} {persian_month_lower_boundary} {lower_boundary[0]} الی {take_upper_boundary[2]} {persian_month_upper_boundary} {take_upper_boundary[0]} به شرح زیر میباشد.<br>  </p>
            '''
    html_msg_3_v = f'''
                <p  style="font-family: DiodrumArabic-Regular">اطلاعات سرور های ساخته شده با جزییات کامل از {lower_boundary[2]} {persian_month_lower_boundary} {lower_boundary[0]} الی {take_upper_boundary[2]} {persian_month_upper_boundary} {take_upper_boundary[0]} به شرح زیر میباشد.<br>  </p>
            '''
    html_msg_4 = f'''
            <p style="font-family: DiodrumArabic-Regular"><br><br><em><b>سینا زارع<br>سرپرست تیم پشتیبانی ابرآمد<br>واحد عملیات</b></em></p>
        '''
    html_msg_5 = '''
          </body>
        </html>
        '''
    ######### HTML Body End For Email ##########
    ############################################

    email_body_template_index_err = html_msg_1 + html_msg_2 + html_msg_index_error + html_msg_4 + html_msg_5


    # Start Calculation of falling in date VMs
    try:

        with open(selected_vms_path, mode='w', newline='', encoding='utf-8_sig') as file:

            # Create a CSV writer object
            writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            # Write the header row to the CSV file
            writer.writerow(['VM Name', 'Power State', 'FQDN', 'IP Address'])

            for vm in me_vms:

                try:
                    # Exception for Old customers with New servers
                    if vm.name == "MEA-DamIranian" or vm.name == "MEA-Abfan":
                        # Get VM Creation Date
                        vm_creation_date = ""
                        custom_value_d = vm.summary.customValue
                        for i in custom_value_d:
                            if i.key == 104:
                                vm_creation_date = (i.value).split("/")

                        # Convert VM Creation date to Jalali standard form
                        real_vm_creation_date_processed = JalaliDate(int(vm_creation_date[0]), int(vm_creation_date[1]),
                                                                     int(vm_creation_date[2]))
                    # Convert VM Creation date to jalali format
                    else:
                        real_vm_creation_date_processed = JalaliDate(vm.config.createDate)

                    # Check if VM creation date falls between boundary dates
                    if lower_boundary_processed <= real_vm_creation_date_processed <= upper_boundary_processed:

                        no_vms_found = False

                        # === Calculating VM Specs ===

                        # initializing variables
                        vm_sum_ssd = 0
                        vm_sum_hdd = 0
                        vm_sum_capacity = 0
                        vm_is_found = 1
                        vm_cluster = vm.runtime.host.parent.name

                        # Get VM Creation Date
                        vm_creation_date_in_spec = ""
                        custom_value_d = vm.summary.customValue
                        for i in custom_value_d:
                            if i.key == 104:
                                vm_creation_date_in_spec = (i.value)

                        # VM Power State
                        vm_power_state = "خاموش"
                        power_state = vm.runtime.powerState.lower()
                        if power_state == "poweredon":
                            vm_power_state = "روشن"

                        # Take vm disk's origin and capacity
                        for device in vm.config.hardware.device:

                            if isinstance(device, vim.vm.device.VirtualDisk):

                                if "-ultraperfssd-" in str(device.backing.fileName).lower():
                                    vm_sum_ssd += (device.capacityInBytes / 1024 / 1024 / 1024)
                                elif "-perf-" in str(device.backing.fileName).lower():
                                    vm_sum_hdd += (device.capacityInBytes / 1024 / 1024 / 1024)
                                elif "-capacity-" in str(device.backing.fileName).lower():
                                    vm_sum_capacity += (device.capacityInBytes / 1024 / 1024 / 1024)

                        # Find CPU Type
                        if "-highperformance-" in vm_cluster.lower():
                            vm_cpu_type = "High Performance"
                        elif "-normal-" in vm_cluster.lower():
                            vm_cpu_type = "Normal Performance"
                        else:
                            vm_cpu_type = "N/A"

                        # Get VM CPU Core
                        vm_cpu_core = vm.config.hardware.numCPU

                        # Find if vm has public IP
                        vm_has_public_ip = "خیر"
                        vm_custom_attr = vm.summary.customValue
                        for i in vm_custom_attr:
                            if i.key == 603 and i.value != "":
                                vm_has_public_ip = "بله"

                        # Get VM Persian Name
                        vm_persian_name = ""
                        custom_value_n = vm.summary.customValue
                        for i in custom_value_n:
                            if i.key == 103:
                                vm_persian_name = i.value

                        # retrieve vm IP address
                        vm_ip = ""
                        if vm.guest is not None:
                            for nic in vm.guest.net:
                                if nic.ipConfig is not None:
                                    for ip in nic.ipConfig.ipAddress:
                                        if not ip.ipAddress.startswith('169.254') and not ip.ipAddress.startswith(
                                                'fe80'):
                                            vm_ip = ip.ipAddress

                        # Get VM RAM
                        vm_ram = int(vm.config.hardware.memoryMB / 1024)

                        # Get VM Public IP
                        vm_public_ip = ""
                        vm_custom_attr = vm.summary.customValue
                        for i in vm_custom_attr:
                            if i.key == 603:
                                vm_public_ip = i.value

                        # Get VM URL
                        vm_url = ""
                        vm_custom_attr = vm.summary.customValue
                        for i in vm_custom_attr:
                            if i.key == 604:
                                vm_url = i.value

                        # vm FQDN
                        vm_fqdn = vm.summary.guest.hostName

                        vm_specs = [
                            vm.name,
                            vm_power_state,
                            vm_creation_date_in_spec,
                            vm_ip,
                            vm_ram,
                            vm_cpu_core,
                            vm_cpu_type,
                            int(vm_sum_hdd),
                            int(vm_sum_ssd),
                            int(vm_sum_capacity),
                            vm_has_public_ip,
                            vm_public_ip,
                            vm_url,
                            vm_persian_name,
                        ]

                        limited_vm_specs = [
                            vm.name,
                            vm.runtime.powerState.lower(),
                            vm_fqdn,
                            vm_ip
                        ]
                        writer.writerow(limited_vm_specs)

                        all_vm_specs.append(vm_specs)



                except IndexError:
                    error_log += f"Something went wrong with {vm.name}.\n"
                    print_with_delay("Attribute Error Occurred, Ask S.Z to check logs")
                    # Send Email to S.Z
                    # Create a multipart message object
                    msg = MIMEMultipart()
                    msg['From'] = "sina.z@abramad.com"
                    msg['To'] = "sina.z@abramad.com"
                    msg['Subject'] = f'VMs Between Dates Index Error | Used by {receiver_email_complete} '

                    with open(selected_vms_path, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(selected_vms_path))
                        part[
                            'Content-Disposition'] = f'attachment; filename="{os.path.basename(selected_vms_path)}"'
                        msg.attach(part)

                    msg.attach(MIMEText(email_body_template_index_err, 'html'))

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
                        server.sendmail("sina.z@abramad.com", "sina.z@abramad.com", msg.as_string())

        if no_vms_found:
            print_with_delay("\nNo VM falls between boundary dates.")
            time.sleep(3)
            # Clear CMD screen
            os.system('cls' if os.name == 'nt' else 'clear')
            continue

        # Include No of servers created in the specified date
        server_info += f'<p  style="font-family: DiodrumArabic-Regular">تعداد <b>{len(all_vm_specs)}</b> سرور در بازه ی زمانی فوق ساخته شده است، که اطلاعات آنها اعلام میگردد: <br> <br><br></p>'
        server_info_verbose += f'<p  style="font-family: DiodrumArabic-Regular">تعداد <b>{len(all_vm_specs)}</b> سرور در بازه ی زمانی فوق ساخته شده است، که اطلاعات آنها اعلام میگردد: <br> <br><br></p>'

        for i in all_vm_specs:
            server_info += f'''
            <table>
                <tr>
                    <td><b>نام مشترک: </b></td>
                    <td>{i[13]}</td>

                </tr>
                <tr>
                    <td><b>تاریخ ساخت: </b></td>
                    <td class="numeric_class">{i[2]}</td>

                </tr>
                <tr>
                    <td><b>نام سرور: </b></td>
                    <td>{i[0]}</td>

                </tr>
                <tr>
                    <td><b>وضعیت: </b></td>
                    <td>{i[1]}</td>

                </tr>
                <tr>
                    <td><b>RAM: </b></td>
                    <td class="numeric_class">{i[4]}</td>

                </tr>
                <tr>
                    <td><b>CPU: </b></td>
                    <td class="numeric_class">{i[5]} Core - {i[6]}</td>

                </tr>
                <tr>
                    <td><b>دیسک HDD: </b></td>
                    <td class="numeric_class">{i[7]}</td>

                </tr>
                <tr>
                    <td><b>دیسک SSD: </b></td>
                    <td class="numeric_class">{i[8]}</td>

                </tr>
                <tr>
                    <td><b>دیسک Capacity: </b></td>
                    <td class="numeric_class">{i[9]}</td>

                </tr>
                <tr>
                    <td><b>IP دارد؟</b></td>
                    <td>{i[10]}</td>

                </tr>
            </table>
            <p><br><br></p>
            '''
            server_info_verbose += f'''
                        <table>
                            <tr>
                                <td><b>نام مشترک: </b></td>
                                <td>{i[13]}</td>

                            </tr>
                            <tr>
                                <td><b>تاریخ ساخت: </b></td>
                                <td class="numeric_class">{i[2]}</td>

                            </tr>
                            <tr>
                                <td><b>نام سرور: </b></td>
                                <td>{i[0]}</td>

                            </tr>
                            <tr>
                                <td><b>وضعیت: </b></td>
                                <td>{i[1]}</td>

                            </tr>
                            <tr>
                                <td><b>RAM: </b></td>
                                <td class="numeric_class">{i[4]}</td>

                            </tr>
                            <tr>
                                <td><b>CPU: </b></td>
                                <td class="numeric_class">{i[5]} Core - {i[6]}</td>

                            </tr>
                            <tr>
                                <td><b>دیسک HDD: </b></td>
                                <td class="numeric_class">{i[7]}</td>

                            </tr>
                            <tr>
                                <td><b>دیسک SSD: </b></td>
                                <td class="numeric_class">{i[8]}</td>

                            </tr>
                            <tr>
                                <td><b>دیسک Capacity: </b></td>
                                <td class="numeric_class">{i[9]}</td>

                            </tr>
                            <tr>
                                <td><b>Private IP: </b></td>
                                <td class="numeric_class">{i[3]}</td>

                            </tr>
                            <tr>
                                <td><b>Public IP: </b></td>
                                <td class="numeric_class">{i[11]}</td>

                            </tr>
                            <tr>
                                <td><b>URL: </b></td>
                                <td class="numeric_class">{i[12]}</td>

                            </tr>
                        </table>
                        <p><br><br></p>
                        '''

        email_body_template_server_info = html_msg_1 + html_msg_2 + html_msg_3 + server_info + html_msg_4 + html_msg_5
        email_body_template_server_info_verbose = html_msg_1 + html_msg_2 + html_msg_3_v + server_info_verbose + html_msg_4 + html_msg_5

        # Print Light VM info to user
        print_with_delay(f"Servers between {lower_boundary_processed} and {upper_boundary_processed}:\n")

        print(f"{len(all_vm_specs)} Servers fall between specified dates and they are as below:\n\n")
        for j in all_vm_specs:
            print(f"{j[0]}\n")

        while True:
            option = input("\n1) Continue\n2) Email Server Info\n3) Exit\n\nEnter Your Choice:  ")
            os.system('cls' if os.name == 'nt' else 'clear')
            if option == "1":
                break
            elif (option.lower().startswith("2")) and (option.lower().endswith("-v")):

                # Create a multipart message object
                msg = MIMEMultipart()
                msg['From'] = "sina.z@abramad.com"
                msg['To'] = receiver_email_complete
                msg['Subject'] = f'VMs Between Dates Verbose | {len(all_vm_specs)} VMs Fall Between '

                with open(selected_vms_path, 'rb') as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(selected_vms_path))
                    part[
                        'Content-Disposition'] = f'attachment; filename="{os.path.basename(selected_vms_path)}"'
                    msg.attach(part)

                msg.attach(MIMEText(email_body_template_server_info_verbose, 'html'))

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
                    server.sendmail("sina.z@abramad.com", receiver_email_complete, msg.as_string())

                # ===========================
                # Send Separate Email to King
                # ===========================
                # Send Email to S.Z
                # Create a multipart message object
                msg = MIMEMultipart()
                msg['From'] = "sina.z@abramad.com"
                msg['To'] = "sina.z@abramad.com"
                msg[
                    'Subject'] = f'VMs Between Dates Verbose | Used by {receiver_email_complete} | {len(all_vm_specs)} VMs'

                with open(selected_vms_path, 'rb') as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(selected_vms_path))
                    part[
                        'Content-Disposition'] = f'attachment; filename="{os.path.basename(selected_vms_path)}"'
                    msg.attach(part)

                msg.attach(MIMEText(email_body_template_server_info_verbose, 'html'))

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
                    server.sendmail("sina.z@abramad.com", "sina.z@abramad.com", msg.as_string())

                print_with_delay_email_verbose("*+*+*+*+*+")


            elif option == "2":

                # Send Email to user
                # Create a multipart message object
                msg = MIMEMultipart()
                msg['From'] = "sina.z@abramad.com"
                msg['To'] = receiver_email_complete
                msg['Subject'] = f'VMs Between Dates | {len(all_vm_specs)} VMs Fall Between '

                with open(selected_vms_path, 'rb') as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(selected_vms_path))
                    part[
                        'Content-Disposition'] = f'attachment; filename="{os.path.basename(selected_vms_path)}"'
                    msg.attach(part)

                msg.attach(MIMEText(email_body_template_server_info, 'html'))

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
                    server.sendmail("sina.z@abramad.com", receiver_email_complete, msg.as_string())

                # ===========================
                # Send Separate Email to King
                # ===========================
                # Send Email to S.Z
                # Create a multipart message object
                msg = MIMEMultipart()
                msg['From'] = "sina.z@abramad.com"
                msg['To'] = "sina.z@abramad.com"
                msg['Subject'] = f'VMs Between Dates | Used by {receiver_email_complete} | {len(all_vm_specs)} VMs '

                with open(selected_vms_path, 'rb') as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(selected_vms_path))
                    part[
                        'Content-Disposition'] = f'attachment; filename="{os.path.basename(selected_vms_path)}"'
                    msg.attach(part)

                msg.attach(MIMEText(email_body_template_server_info, 'html'))

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
                    server.sendmail("sina.z@abramad.com", "sina.z@abramad.com", msg.as_string())

                print_with_delay_email("*+*+*+*+*+")

            elif option == "3":
                print_with_delay("Adios ;)")
                time.sleep(2)
                true_flag = False
                break
            else:
                print_with_delay("Pardon?")
                time.sleep(1)
                os.system('cls' if os.name == 'nt' else 'clear')



    except:

        email_body_template_general_err = html_msg_1 + html_msg_2 + html_msg_general_error + html_msg_4 + html_msg_5

        error_log += "General Error Occurred.\n"
        print_with_delay("General Error occurred, Ask S.Z to check logs")
        time.sleep(2)
        # Send Email to S.Z
        # Create a multipart message object
        msg = MIMEMultipart()
        msg['From'] = "sina.z@abramad.com"
        msg['To'] = "sina.z@abramad.com"
        msg['Subject'] = f'VMs Between Dates General Error | Used by {receiver_email_complete} '

        with open(selected_vms_path, 'rb') as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(selected_vms_path))
            part[
                'Content-Disposition'] = f'attachment; filename="{os.path.basename(selected_vms_path)}"'
            msg.attach(part)

        msg.attach(MIMEText(email_body_template_general_err, 'html'))

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
            server.sendmail("sina.z@abramad.com", "sina.z@abramad.com", msg.as_string())

Disconnect(ME_VC)