# ---Module Call---
from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import os
import warnings
from datetime import datetime
from datetime import date
from persiantools.jdatetime import JalaliDate
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

# ---Function Creation---
def calculate_days_between_dates(start_date, end_date):
    date_format = "%Y/%m/%d"  # Specify the format of the dates
    start_date_obj = datetime.strptime(start_date, date_format)
    end_date_obj = datetime.strptime(end_date, date_format)
    delta = end_date_obj - start_date_obj
    return delta.days

# ---Main Code---
# Get today's date
today = date.today()
# Convert to Persian date
persian_date = JalaliDate.to_jalali(today.year, today.month, today.day)
# Format the Persian date as "YYYY/MM/DD"
today_persian_date = persian_date.strftime("%Y/%m/%d")

# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)
# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

ME_VC = connect.SmartConnect(host='me-vc01.abramad.com',user= username,pwd= password,port=443,sslContext=context)
me_content = ME_VC.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if ( (vm.name.lower().startswith("mer-refah")) and ( not vm.name.lower().startswith("mer-refahts-db1") and ( not vm.name.lower().startswith("mer-refahhq-db1"))) )]

# Message and Error Log that should be Emailed
noisy_vms = []
error_log = ""

for vm in me_vms:
    vm_total_ssd = 0

    # Take vm disk's origin and capacity
    for device in vm.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualDisk):
            if "-ultraperfssd-" in str(device.backing.fileName).lower():
                vm_total_ssd += (int(device.capacityInBytes / 1024 / 1024 / 1024))

    # Get VM Creation Date
    vm_creation_date = ""
    custom_value_d = vm.summary.customValue
    for i in custom_value_d:
        if i.key == 104:
            vm_creation_date = i.value

    # Brings number of days that the VM is Active and powered on
    vm_powered_on_days = calculate_days_between_dates(vm_creation_date, today_persian_date)
    try:
        if ( (vm_powered_on_days > 3) and (vm_total_ssd > 599) ):
            noisy_vms.append([vm.name, vm_total_ssd, vm_powered_on_days])
    except:
        error_log += f"{vm.name} throws error\n"


# Send Email only if there is a Noisy server available
if len(noisy_vms) >= 1:
    if error_log == "":
        # Send the text via email
        sender_email = 'sina.z@abramad.com'
        receiver_email = 'mehdi.a@abramad.com, alireza.ja@abramad.com, saeed.r@abramad.com, sina.z@abramad.com, support@abramad.com, sales@abramad.com'

        # Create a multipart message object
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f'سرور های رفاه دارای دیسک امانی | {len(noisy_vms)} سرور'



        html_msg_1 = '''
        <html dir="rtl">
          <body>
        '''
        html_msg_2 = '''
            <p  style="font-family: DiodrumArabic-Regular"> به اطلاع میرساند لیست سرور های زیر نمایانگر سرور های شرکت رفاه میباشند که پس از گذشت 3 روز از درخواست، همچنان دیسک امانی SSD به آنها مانت میباشد: </p>
        '''
        html_msg_3 = f'''
            <p style="font-family: DiodrumArabic-Regular"><em><b>سینا زارع<br>سرپرست تیم پشتیبانی ابرآمد<br>واحد عملیات</b></em></p>
        '''
        html_msg_4 = '''
          </body>
        </html>
        '''
        message = "<br>"
        for vm_info in noisy_vms:
            mail_vm_name = vm_info[0]
            mail_vm_total_ssd = vm_info[1]
            mail_vm_poweron_days = vm_info[2]
            message += f"<p style='font-family: DiodrumArabic-Regular'>سرور با نام {mail_vm_name}، {mail_vm_poweron_days} روز است که ساخته شده و دارای {mail_vm_total_ssd}GB دیسک SSD میباشد.</p>"
        #message += f"<br><br>{error_log}<br><br><br> applet is brought to you by <b>S.Z</b><br><br><br><b>Sina Zare<br><em>Support Team Lead<br>Abramad’s Operation Team</b></em></p>"

        # Add HTML email text
        email_body = html_msg_1 + html_msg_2 + message + html_msg_3 + html_msg_4
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
            server.sendmail(sender_email, "alireza.ja@abramad.com", msg.as_string())
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, "mehdi.a@abramad.com", msg.as_string())

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, "saeed.r@abramad.com", msg.as_string())

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, "sina.z@abramad.com", msg.as_string())

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, "support@abramad.com", msg.as_string())

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, "sales@abramad.com", msg.as_string())


    elif error_log != "":
        # Send the error via email to sina
        sender_email = 'sina.z@abramad.com'
        receiver_email = 'sina.z@abramad.com'

        # Create a multipart message object
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = 'Refah SSD Report Error'

        msg.attach(MIMEText(error_log, 'html'))

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