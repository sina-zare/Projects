from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import warnings
from datetime import datetime
from datetime import date
from persiantools.jdatetime import JalaliDate
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os


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


error_log = ""

# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)

context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

ME_VC = connect.SmartConnect(host='me-vc01.abramad.com',user=username,pwd= password,port=443,sslContext=context)
me_content = ME_VC.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if (vm.name.lower().startswith("mer-") or vm.name.lower().startswith("merd-") or vm.name.lower().startswith("mef-") or vm.name.lower().startswith("mes-") or vm.name.lower().startswith("mea-") or vm.name.lower().startswith("meb-") or vm.name.lower().startswith("mem-") or vm.name.lower().startswith("mei-") or vm.name.startswith("mesa-") )]


vms_with_shdate = []
powered_off_vms = []

for vm in me_vms:
    # find the poweredoff vms
    if vm.runtime.powerState == "poweredOff" and not vm.name.lower() == "mer-singletemp" and not vm.name.lower() == "mei-ava-centos7-template01" and not vm.name.lower() == "mei-ava-centos7-template02":

        powered_off_vms.append(vm.name)

        custom_attribute= vm.summary.customValue
        for i in custom_attribute:
            if i.key == 401:
                vm_shutdown_date = i.value
                if vm_shutdown_date.startswith("1402") or vm_shutdown_date.startswith("1403"):
                    vms_with_shdate.append(vm.name)


        try:
            print(f"{vm.name} meets the condition.")
        except ValueError:
            error_log += f"VM <em><b>{vm.name}</b></em> has bad shutdown date format or it does not exists."


vms_without_shdate = list(set(powered_off_vms) - set(vms_with_shdate))

# Send the text via email
sender_email = 'sina.z@abramad.com'
receiver_email = "sina.z@abramad.com"

# Create a multipart message object
msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = receiver_email
msg['Subject'] = f'{len(vms_without_shdate)} VMs that are Powered off but have no shutdown date'


message = "Below VMs are powered off but for some reason, have no shutdown date specified.<br>Please solve the issue as soon as possible.<br><br>These VMs Meet the condition:<br>"
if len(vms_without_shdate) == 0:
    tidy_message = "<p>Greetings King, you have a new message:<br><br><b>Congrats! your infrastructure is clean and tidy.</b></p>"
    tidy_message += f"<br><br>{error_log}<br><br><br> applet is brought to you by <b>S.Z</b><br>Made with <3<br><br><br><b>Sina Zare<br><em>Support Team Lead<br>Abramad’s Operation Team</b></em></p>"

    # Add HTML email text
    msg.attach(MIMEText(tidy_message, 'html'))

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
        server.sendmail(sender_email, "sina.z@abramad.com", msg.as_string())

else:
    for vm in vms_without_shdate:
        message += f"<br><em><b>{vm}</b></em>"

    message += f"<br><br>{error_log}<br><br><br> applet is brought to you by <b>S.Z</b><br>Made with <3<br><br><br><b>Sina Zare<br><em>Support Team Lead<br>Abramad’s Operation Team</b></em></p>"

    # Add HTML email text
    msg.attach(MIMEText(message, 'html'))

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
        server.sendmail(sender_email, "sina.z@abramad.com", msg.as_string())


Disconnect(ME_VC)