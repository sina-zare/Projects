import re
import csv
from email.mime.application import MIMEApplication
from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import warnings
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

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

context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

ME_VC = connect.SmartConnect(host='me-vc01.abramad.com',user= username,pwd= password,port=443,sslContext=context)
me_content = ME_VC.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if (vm.name.lower().startswith("mer-") or vm.name.lower().startswith("merd-") or vm.name.lower().startswith("mea-") )]
# Sort the me_vms list based on VM names
sorted_vms = sorted(me_vms, key=lambda vm: vm.name.lower())

# Create csv file and write first row
csv_report_path = 'C:/Users/sina.z/Desktop/Automation_Reports/URL_Dispenser/Customer_URL_Report.csv'
with open(csv_report_path, mode='w', newline='', encoding='utf-8') as file:

    # Create a CSV writer object
    writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # Write the header row to the CSV file
    writer.writerow(['VM Name', 'Private IP', 'Public IP', 'URL'])



    for vm in sorted_vms:

        # find the specified vm
        if vm.runtime.powerState == "poweredOn" and not vm.name.lower().endswith("-t"):
            if re.match(r"^mer-(?!.*-db).*", vm.name.lower()) or vm.name.lower().startswith("mea"):
            #if vm.name == "MER-ALaziz-APP1" and (vm.runtime.powerState == "poweredOn"):
                # retrieve vm IP address
                vm_ip = ""
                if vm.guest is not None:
                    for nic in vm.guest.net:
                        if nic.ipConfig is not None:
                            for ip in nic.ipConfig.ipAddress:
                                if not ip.ipAddress.startswith('169.254') and not ip.ipAddress.startswith('fe80'):
                                    vm_ip = ip.ipAddress


                # Check if public IP and URL Exists in VM Notes
                vm_public_ip = ""
                vm_url = ""

                # Get VM Public IP
                vm_custom_attr = vm.summary.customValue
                for i in vm_custom_attr:
                    if i.key == 603:
                        vm_public_ip = i.value

                # Get VM URL
                vm_custom_attr = vm.summary.customValue
                for i in vm_custom_attr:
                    if i.key == 604:
                        vm_url = i.value


                vm_info = [
                    vm.name,
                    vm_ip,
                    vm_public_ip,
                    vm_url
                ]


                try:
                    # write vm info to csv file
                    writer.writerow(vm_info)
                except IndexError:
                    print("Error Occured")


Disconnect(ME_VC)


# Send Email to King
# Create a multipart message object
receiver_email = "support@abramad.com"
cc_email = "mehdi.a@abramad.com,alireza.ja@abramad.com"

msg = MIMEMultipart()
msg['From'] = 'sina.z@abramad.com'
msg['To'] = receiver_email
msg['CC'] = cc_email
msg['Subject'] = f'گزارش URL مشترکین'

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
                <p  style="font-family: DiodrumArabic-Regular">گزارش URL مشترکین جهت بروزرسانی سرویس های مانیتورینگ به پیوست قرار گرفت.</p>
            '''
html_msg_4s = f'''
                <p  style="font-family: DiodrumArabic-Regular">سپاس از توجه و همراهی شما</p>
            '''
html_msg_5s = f'''
                <p style="font-family: DiodrumArabic-Regular"><em><b>سینا زارع<br>سرپرست تیم پشتیبانی ابرآمد<br>واحد عملیات</b></em></p>
            '''
html_msg_6s = '''
              </body>
            </html>
            '''

email_body = html_msg_1s + html_msg_2s + html_msg_3s + html_msg_4s + html_line_break + html_msg_5s + html_msg_6s

# Attachment
with open(csv_report_path, 'rb') as f:
    part = MIMEApplication(f.read(), Name=os.path.basename(csv_report_path))
    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(csv_report_path)}"'
    msg.attach(part)

msg.attach(MIMEText(email_body,'html'))

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
    server.sendmail('sina.z@abramad.com',receiver_email.split(",") + cc_email.split(","), msg.as_string())

