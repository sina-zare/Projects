import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import csv
import os
import warnings
from datetime import date
from persiantools.jdatetime import JalaliDate
import datetime

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

# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)

today = datetime.date.today()

month_dict = {
        "01": "Far",
        "02": "Ord",
        "03": "Khor",
        "04": "Tir",
        "05": "Mor",
        "06": "Shah",
        "07": "Mehr",
        "08": "Aban",
        "09": "Azar",
        "10": "Dey",
        "11": "Bah",
        "12": "Esf"
    }

# Get today's date
today = date.today()
# Convert to Persian date
persian_date = JalaliDate.to_jalali(today.year, today.month, today.day)
# Format the Persian date as "YYYY/MM/DD"
today_persian_date = persian_date.strftime("%Y/%m/%d")
current_persian_month = f'{month_dict[str(today_persian_date[5:7])]}'
# Specify the current month
current_month = f'MIaaS-Security-Report-{current_persian_month}-1403'

# Create the directory for the CSV files containing month
parent_directory = 'C:/Users/sina.z/Desktop/Managed_Servers_Sec_Report/'
final_path = os.path.join(parent_directory, current_month)
if not os.path.exists(final_path):
    os.makedirs(final_path)



# *** Connecting to ME-VC01.Abramad.Com to get the Report ***

# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

ME_VC = connect.SmartConnect(host='me-vc01.abramad.com',user=username,pwd= password,port=443,sslContext=context)
me_content = ME_VC.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if ( vm.name.startswith("MER-") or vm.name.lower().startswith("MERD-") or vm.name.startswith("MEF-") or vm.name.startswith("MES-") or vm.name.startswith("MEA-") or vm.name.startswith("MEB-") or vm.name.startswith("MEM-"))] #or vm.name.startswith("ME-") or vm.name.lower().startswith("infra-") or vm.name.lower().startswith("pvdint-") or vm.name.lower().startswith("mir-int") or vm.name.lower().startswith("med-") )]

# Sort the me_vms list based on VM names
sorted_vms = sorted(me_vms, key=lambda vm: vm.name.lower())


# Specify the filename and full path to the CSV file
MIaaS_csv_file_path = f'ME-Customers-Server-Report-{current_persian_month}-1403.csv'
MIaaS_sec_report_full_file_path = os.path.join(final_path, MIaaS_csv_file_path)

with open(MIaaS_sec_report_full_file_path, mode='w', newline='', encoding='utf-8') as file:

    # Create a CSV writer object
    writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # Write the header row to the CSV file
    writer.writerow(['VM Name', 'Power State', 'OS', 'FQDN', 'IP Address', 'Public IP'])

# Count number of servers per product and take their Persian name from custom attributes
    for vm in sorted_vms:
        # Check count of Rahkaran servers
        if (vm.name.lower().startswith("me") and not vm.name.lower().startswith("me-") and not vm.name.lower().startswith("mer-singletemp")):

            # Power State
            vm_power_state = vm.runtime.powerState

            # Guest OS
            vm_guest_os = vm.summary.config.guestFullName

            # retrieve vm IP address
            vm_ip = ""
            if vm.guest is not None:
                for nic in vm.guest.net:
                    if nic.ipConfig is not None:
                        for ip in nic.ipConfig.ipAddress:
                            if not ip.ipAddress.startswith('169.254') and not ip.ipAddress.startswith('fe80'):
                                vm_ip = ip.ipAddress

            # vm FQDN
            vm_fqdn = vm.summary.guest.hostName

            # Find if vm has public IP
            vm_public_ip = ""
            vm_custom_attr = vm.summary.customValue
            for i in vm_custom_attr:
                if i.key == 603 and i.value != "":
                    vm_public_ip = i.value

            # VM Information
            vm_info = [
                vm.name,
                vm_power_state,
                vm_guest_os,
                vm_fqdn,
                vm_ip,
                vm_public_ip
            ]

            try:
                # write vm info to csv file
                writer.writerow(vm_info)
            except IndexError:
                print("Error Occured")



# Specify the filename and full path to the CSV file
MGMT_csv_file_path = f'Management-Servers-Report-{current_persian_month}-1403.csv'
MGMT_server_report_full_file_path = os.path.join(final_path, MGMT_csv_file_path)

with open(MGMT_server_report_full_file_path, mode='w', newline='', encoding='utf-8') as file:

    # Create a CSV writer object
    writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # Write the header row to the CSV file
    writer.writerow(['VM Name', 'Power State', 'OS', 'FQDN', 'IP Address', 'Public IP'])

# Count number of servers per product and take their Persian name from custom attributes
    for vm in sorted_vms:
        # Check count of Rahkaran servers
        if ( ((vm.name.lower().startswith("me-") and not vm.name.lower().startswith("me-rahlocktemp"))) or vm.name.lower().startswith("infra-") or vm.name.lower().startswith("pvdint-") or vm.name.lower().startswith("mir-int") or vm.name.lower().startswith("med-")):

            # Power State
            vm_power_state = vm.runtime.powerState

            # Guest OS
            vm_guest_os = vm.summary.config.guestFullName

            # retrieve vm IP address
            vm_ip = ""
            if vm.guest is not None:
                for nic in vm.guest.net:
                    if nic.ipConfig is not None:
                        for ip in nic.ipConfig.ipAddress:
                            if not ip.ipAddress.startswith('169.254') and not ip.ipAddress.startswith('fe80'):
                                vm_ip = ip.ipAddress

            # vm FQDN
            vm_fqdn = vm.summary.guest.hostName

            # VM Information
            vm_info = [
                vm.name,
                vm_power_state,
                vm_guest_os,
                vm_fqdn,
                vm_ip
            ]

            try:
                # write vm info to csv file
                writer.writerow(vm_info)
            except IndexError:
                print("Error Occured")


"""
# Send the CSV file via email
sender_email = 'sina.z@abramad.com'
receiver_email = 'securityteam@abramad.com, mehdi.a@abramad.com, alireza.ja@abramad.com'

# Create a multipart message object
msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = receiver_email
msg['Subject'] = f'Abramad MIaaS & MGMT Servers | {current_month}'


# Attachments
customer_servers_attachment = MIaaS_sec_report_full_file_path
mgmt_servers_attachment = MGMT_server_report_full_file_path

with open(customer_servers_attachment, 'rb') as f:
    part = MIMEApplication(f.read(), Name=os.path.basename(customer_servers_attachment))
    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(customer_servers_attachment)}"'
    msg.attach(part)

with open(mgmt_servers_attachment, 'rb') as f:
    part = MIMEApplication(f.read(), Name=os.path.basename(mgmt_servers_attachment))
    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(mgmt_servers_attachment)}"'
    msg.attach(part)

##############################################
######### HTML Body Begin For Email ##########

html_line_break = '''
                    <p><br></p>
                '''
html_msg_1 = '''
            <html dir="rtl">
              <body>
            '''
html_msg_2 = '''
                <p  style="font-family: DiodrumArabic-Regular">با سلام و احترام</p>
            '''
html_msg_3 = f'''
                <p  style="font-family: DiodrumArabic-Regular">لیست سرور های مدیریت شده و سرور های مشترکین ابرآمد که تا امروز ساخته شده، به پیوست تقدیم حضور میگردد.<p/>
                        '''

html_msg_4 = f'''
                <p  style="font-family: DiodrumArabic-Regular">این گزارش هر دو هفته یک بار برای شما ارسال میشود.</p>
            '''

html_msg_5 = f'''
                <p  style="font-family: DiodrumArabic-Regular">با سپاس فراوان</p>
            '''
html_msg_6 = f'''
                <p style="font-family: DiodrumArabic-Regular"><em><b>سینا زارع<br>سرپرست تیم پشتیبانی ابرآمد<br>واحد عملیات</b></em></p>
            '''
html_msg_7 = '''
              </body>
            </html>
            '''
######### HTML Body End For Email ##########
############################################

email_body = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_4 + html_line_break + html_msg_5 + html_line_break + html_msg_6 + html_msg_7

# Add HTML email text
msg.attach(MIMEText(email_body, 'html'))

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
    server.sendmail(sender_email, "securityteam@abramad.com", msg.as_string())

with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.sendmail(sender_email, "mehdi.a@abramad.com", msg.as_string())

with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.sendmail(sender_email, "alireza.ja@abramad.com", msg.as_string())

with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.sendmail(sender_email, "sina.z@abramad.com", msg.as_string())

"""
Disconnect(ME_VC)