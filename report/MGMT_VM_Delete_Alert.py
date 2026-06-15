from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import warnings
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


# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)

context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

ME_VC = connect.SmartConnect(host='me-vc01.abramad.com',user=username,pwd= password,port=443,sslContext=context)
me_content = ME_VC.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if (vm.name.lower().startswith("me"))]



powered_off_vms = []

for vm in me_vms:
    # find the poweredoff vms
    if vm.runtime.powerState == "poweredOff" and vm.name.lower().startswith("me-") and not vm.name.lower().startswith("me-adcsroot") and not vm.name.lower() == "me-rahlocktemp" and not vm.name.lower() == "me-commserve-aryan" and not vm.name.lower() == "me-win2019-iscsi-test-vm" and not vm.name.lower() == "me-malekzadelab1" and not vm.name.lower() == "me-malekzadelab2":
        powered_off_vms.append(vm.name)

        print(f"{vm.name} meets the condition.")


# Send the text via email
sender_email = 'sina.z@abramad.com'
receiver_email = "abramadops@systemgroup.net"

# Create a multipart message object
msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = receiver_email
msg['Subject'] = f'{len(powered_off_vms)} سرور مدیریتی خاموش'

##############################################
######### HTML Body Begin For Email ##########
html_msg_1 = '''
<html dir="rtl">
  <body>
'''
html_msg_2 = '''
    <p  style="font-family: DiodrumArabic-Regular">با سلام و احترام</p>
'''
html_msg_3 = '''
    <p  style="font-family: DiodrumArabic-Regular">سرور های مدیریتی زیر در وضعیت خاموش میباشند اما هنوز در زیرساخت قرار دارند، لطفا در صورتی که همچنان به وجود آنها نیاز میباشد بررسی های لازمه را صورت دهید و در غیر این صورت نسبت به حذف آنها اقدام نمایید.</p>
'''
html_msg_4 = f'''
    <p style="font-family: DiodrumArabic-Regular"><em><b>سینا زارع<br>سرپرست تیم پشتیبانی ابرآمد<br>واحد عملیات</b></em></p>
'''
html_msg_5 = '''
  </body>
</html>
'''
######### HTML Body End For Email ##########
############################################

message = ""
# send email to sina.z if there is no powered off vms found.
if len(powered_off_vms) == 0:
    message = "<p><br><b>تبریک! زیرساخت فاقد هرگونه سرور خاموش میباشد.</b>بنابراین ایمیلی به اعضای عملیات ارسال نخواهد شد.<br></p>"

    # Add HTML email text
    email_body = html_msg_1 + message + html_msg_4 + html_msg_5

    # Connect to the SMTP server and send the email 465,*587*,25 (mail.systemgroup.net)
    # Send email info
    msg.attach(MIMEText(email_body, 'html'))
    smtp_server = 'mail.systemgroup.net'
    smtp_port = 587
    smtp_username = username
    smtp_password = password

    # Send email function
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, "sina.z@abramad.com", msg.as_string())
    print("Email Sent to Sina.Z")
# Send Email to Operation when there are powered off vms available
else:
    for vm in powered_off_vms:
        message += f"<br><em><b>{vm}</b></em>"

    # Add HTML email text
    email_body = html_msg_1 + html_msg_2 + html_msg_3 + message + html_msg_4 + html_msg_5

    # Connect to the SMTP server and send the email 465,*587*,25 (mail.systemgroup.net)
    # Send email info
    msg.attach(MIMEText(email_body, 'html'))
    smtp_server = 'mail.systemgroup.net'
    smtp_port = 587
    smtp_username = username
    smtp_password = password

    # Send email function
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, "abramadops@systemgroup.net", msg.as_string())

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, "sina.z@abramad.com", msg.as_string())

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, "saeed.r@abramad.com", msg.as_string())

    print("Email Sent to Operation Team")

Disconnect(ME_VC)