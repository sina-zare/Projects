from pyVmomi import vim
from pyvim import connect
from pyvim.connect import Disconnect
import warnings
import ssl
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
# *** Connecting to ME-VC01.Abramad.Com to get the Report ***
# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE


# Connecting to vCenter
MRA_VC = connect.SmartConnect(host='mra-vc01.abramad.com',user= username,pwd= password,port=443,sslContext=context)
me_content = MRA_VC.RetrieveContent()
mra_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
mra_vms = [vm for vm in mra_vm_view.view if (vm.name.lower().startswith("ra-")) or (vm.name.lower().startswith("mra-"))]
# Sort the me_vms list based on VM names
sorted_vms = sorted(mra_vms, key=lambda vm: vm.name.lower())

ra_vms = []
ra_cloudlocks = []
receiver_email = 'support@abramad.com,mehdi.a@abramad.com,alireza.ja@abramad.com'
cc_email = 'gildaab@systemgroup.net'

for vm in sorted_vms:
    if vm.name.lower().startswith("ra-"):
        ra_vms.append(vm.name)
    if vm.name.lower().startswith("mra-cloudlock"):
        ra_cloudlocks.append(vm.name)

Disconnect(MRA_VC)


metric = 430
number_of_vms = len(ra_vms)
number_of_existing_cloudlocks = len(ra_cloudlocks)

remainder_of_division_by_450 = number_of_vms % metric
number_of_needed_cloudlocks = (number_of_vms // metric) + 1
amount_of_cloudlocks_to_be_added = number_of_needed_cloudlocks - number_of_existing_cloudlocks
space_to_be_full = metric - remainder_of_division_by_450


# if free space for vms is getting full and there is a need for increasing amount of cloudlocks
if amount_of_cloudlocks_to_be_added > 0:
    # Send Email to King
    # Create a multipart message object
    msg = MIMEMultipart()
    msg['From'] = 'sina.z@abramad.com'
    msg['To'] = 'sina.z@abramad.com'#receiver_email
    msg['CC'] = 'sina.z@abramad.com'#cc_email
    msg['Subject'] = f'هشدار جهت ایجاد سرور قفل ابری جدید | {space_to_be_full} سرور تا پر شدن'

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
                    <p  style="font-family: DiodrumArabic-Regular">با توجه به گسترش فروش و افزایش تعداد سرور های راهکاران ابری و نزدیک شدن به limit تعداد مشترکین ساپورت شده روی هر سرور قفل، نیازمند ایجاد {amount_of_cloudlocks_to_be_added} سرور MRA-CloudLock میباشیم.</p>
                '''
    html_msg_4s = f'''
                    <p  style="font-family: DiodrumArabic-Regular">تعداد سرور های ابری ساخته شده در زیرساخت RA در حال حاضر <b>{number_of_vms}</b> عدد میباشد.</p>
                '''
    html_msg_5s = f'''
                <p  style="font-family: DiodrumArabic-Regular">تعداد سرور های قفل ساخته شده در زیرساخت RA در حال حاضر <b>{number_of_existing_cloudlocks}</b> عدد میباشد.</p>
                '''
    html_msg_6s = f'''
                    <p  style="font-family: DiodrumArabic-Regular">{space_to_be_full} سرور تا ایجاد سرور قفل جدید، زمان باقی است.</p>
                    '''
    html_msg_8s = f'''
                    <p style="font-family: DiodrumArabic-Regular"><em><b>سینا زارع<br>سرپرست تیم پشتیبانی ابرآمد<br>واحد عملیات</b></em></p>
                '''
    html_msg_9s = '''
                      </body>
                    </html>
                    '''

    ######### HTML Body End For Email ##########
    ############################################

    inform_email_body = html_msg_1s + html_msg_2s + html_msg_3s + html_line_break + html_msg_4s + html_line_break + html_msg_5s + html_msg_6s + html_msg_8s + html_line_break + html_msg_9s

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
        server.sendmail('sina.z@abramad.com', 'sina.z@abramad.com', msg.as_string())
#reciever_email.split(",") + cc_email.split(',')