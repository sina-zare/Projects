import openpyxl
from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import warnings
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



# Date Processes

from datetime import date
from persiantools.jdatetime import JalaliDate
import datetime

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

month_dict_persian = {
    "Dey": "دی",
    "Bah": "بهمن",
    "Esf": "اسفند",
    "Far": "فروردین",
    "Ord": "اردیبهشت",
    "Khor": "خرداد",
    "Tir": "تیر",
    "Mor": "مرداد",
    "Shah": "شهریور",
    "Mehr": "مهر",
    "Aban": "آبان",
    "Azar": "آذر"
}

# Get today's date
today = date.today()
# Convert to Persian date
persian_date = JalaliDate.to_jalali(today.year, today.month, today.day)
# Format the Persian date as "YYYY/MM/DD"
today_persian_date = persian_date.strftime("%Y/%m/%d")

current_month = f'{month_dict[str(today_persian_date[5:7])]}'
persian_current_month = month_dict_persian[current_month]
current_day = today_persian_date[8:11]
current_year = today_persian_date[0:4]
# Get the current date and time
current_date = datetime.datetime.now()
# Get the abbreviated name of the current day
day_name = current_date.strftime('%a')






# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)
# *** Connecting to ME-VC01.Abramad.Com to get the Report ***
# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

# Connecting to vCenter
ME_VC = connect.SmartConnect(host='me-vc01.abramad.com',user= username,pwd= password,port=443,sslContext=context)
me_content = ME_VC.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if (vm.name.startswith("MER-") or vm.name.startswith("MERD-") or vm.name.startswith("MEF-") or vm.name.startswith("MES-") or vm.name.startswith("MEA-") or vm.name.startswith("MEB-") or vm.name.startswith("MEM-") or vm.name.startswith("MEI-") or vm.name.startswith("MESA-"))]


rahkaran_servers = []
automation_servers = []

for vm in me_vms:
    if vm.runtime.powerState.lower() == "poweredon":

        # Info about Rahkaran Servers
        if vm.name.lower().startswith("mer"):

            # Get VM Persian Name
            vm_persian_name = ""
            custom_value_n = vm.summary.customValue
            for i in custom_value_n:
                if i.key == 103:
                    vm_persian_name = i.value

            # Get National ID Status
            vm_national_id = ""
            custom_value_n = vm.summary.customValue
            for i in custom_value_n:
                if i.key == 611:
                    vm_national_id = i.value

            # Get VM URL
            vm_url = ""
            vm_custom_attr = vm.summary.customValue
            for i in vm_custom_attr:
                if i.key == 604:
                    vm_url = i.value

            # retrieve vm IP address
            vm_ip = ""
            if vm.guest is not None:
                for nic in vm.guest.net:
                    if nic.ipConfig is not None:
                        for ip in nic.ipConfig.ipAddress:
                            if not ip.ipAddress.startswith('169.254') and not ip.ipAddress.startswith(
                                    'fe80'):
                                vm_ip = ip.ipAddress

            mer_vm_spec = [
                vm.name,
                vm_persian_name,
                vm_national_id,
                vm_ip,
                vm_url
            ]

            rahkaran_servers.append(mer_vm_spec)


        # Info about Automation Servers
        elif vm.name.lower().startswith("mea"):

            # Get VM Persian Name
            vm_persian_name = ""
            custom_value_n = vm.summary.customValue
            for i in custom_value_n:
                if i.key == 103:
                    vm_persian_name = i.value

            # Get National ID Status
            vm_national_id = ""
            custom_value_n = vm.summary.customValue
            for i in custom_value_n:
                if i.key == 611:
                    vm_national_id = i.value

            # Get VM URL
            vm_url = ""
            vm_custom_attr = vm.summary.customValue
            for i in vm_custom_attr:
                if i.key == 604:
                    vm_url = i.value

            # retrieve vm IP address
            vm_ip = ""
            if vm.guest is not None:
                for nic in vm.guest.net:
                    if nic.ipConfig is not None:
                        for ip in nic.ipConfig.ipAddress:
                            if not ip.ipAddress.startswith('169.254') and not ip.ipAddress.startswith(
                                    'fe80'):
                                vm_ip = ip.ipAddress

            mea_vm_spec = [
                vm.name,
                vm_persian_name,
                vm_national_id,
                vm_ip,
                vm_url
            ]

            automation_servers.append(mea_vm_spec)

Disconnect(ME_VC)

# Rahkaran Excel

# Load the Excel file
workbook = openpyxl.Workbook()
# Select the worksheet where you want to add data
worksheet = workbook.active
# Write the dictionary data to the worksheet
header = ["Server Name","Persian Name", "National ID", "Private IP", "URL"]
worksheet.append(header)

for vm in rahkaran_servers:
    worksheet.append(vm)

# Save the changes to the Excel file
workbook.save(f'C:/Users/sina.z/Desktop/Automation_Reports/Report_to_Support/Rahkaran-Servers-Report-{current_day}-{current_month}-{current_year}.xlsx')



# Automation Excel

# Load the Excel file
workbook = openpyxl.Workbook()
# Select the worksheet where you want to add data
worksheet = workbook.active
# Write the dictionary data to the worksheet
header = ["Server Name","Persian Name", "National ID", "Private IP", "URL"]
worksheet.append(header)

for vm in automation_servers:
    worksheet.append(vm)

# Save the changes to the Excel file
workbook.save(f'C:/Users/sina.z/Desktop/Automation_Reports/Report_to_Support/Automation-Servers-Report-{current_day}-{current_month}-{current_year}.xlsx')



##########################
# Send Email to Rahkarania

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

sender_email = 'sina.z@abramad.com'
receiver_email = 'saraa@systemgroup.net, mortezam@systemgroup.net, meysama@systemgroup.net, javadk@systemgroup.net, mozhganfa@systemgroup.net, nedapo@systemgroup.net, ElaheB@systemgroup.net, foroughb@systemgroup.net'
cc_email = 'farahnazz@systemgroup.net, support@abramad.com, mehdi.a@abramad.com, alireza.ja@abramad.com'

rahkaran_attachment = f'C:/Users/sina.z/Desktop/Automation_Reports/Report_to_Support/Rahkaran-Servers-Report-{current_day}-{current_month}-{current_year}.xlsx'


# Create a multipart message object
msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = receiver_email
msg['CC'] = cc_email
msg['Subject'] = f'گزارش سرور های مشترکین سرویس راهکاران در بستر ابرآمد | {current_day} {persian_current_month} {current_year}'

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
html_msg_3 = f'''
            <p  style="font-family: DiodrumArabic-Regular">گزارش سرور های مشترکین سرویس راهکاران در بستر ابرآمد تا تاریخ {current_day} {persian_current_month} {current_year} پیوست قرار گرفت.</p>
        '''
html_msg_4 = f'''
            <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است که این گزارش به صورت ماهانه برای شما ارسال میگردد و از روی آن میتوانید به اطلاعات مشترکین راهکاران ابرآمد دست پیدا کنید. این گزارش به این منظور تهیه شده تا در صورت نیاز به اتصال به سرور مشترک مستقیما از طریق کاربری شخصی تان که توسط تیم پشتیبانی ابرآمد ایجاد میگردد، اقدام نمایید.</p>
        '''
html_msg_5 = f'''
                <p  style="font-family: DiodrumArabic-Regular">در صورتی که نیاز به ایجاد کاربری در زیرساخت ابرآمد دارید، اطلاعات زیر را در قالب جدول برای تیم ساپورت ابرآمد به آدرس: support@abramad.com ارسال نمایید.</p>
            '''
html_msg_6 = f'''
        <table>
                <tr>
                    <td><b>نام و نام خانوادگی</b></td>
                    <td><b>کد ملی</b></td>
                    <td><b>شماره همراه</b></td>
                    <td><b>آدرس ایمیل</b></td>
                </tr>
        </table>
            '''
html_msg_7 = f'''
            <p style="font-family: DiodrumArabic-Regular"><b>نکته مهم: ابرآمد سرویس راهکاران مشترکین را بصورت 24 ساعت در 7 روز هفته مانیتور میکند و در صورتی که سرویس Down شود، سلسله مراتبی از تسک ها توسط تیم پشتیبانی ابرآمد شکل میگیرد. لذا خواهشمند است در صورتی که نیاز به انجام اقداماتی دارید که منجر به Down شدن سرویس میگردد، حتما پیش از اقدام به تیم ساپورت ابرآمد، اطلاع رسانی فرمایید.  </b></p>
        '''
html_msg_8 = f'''
            <p style="font-family: DiodrumArabic-Regular"><em><b>سینا زارع<br>سرپرست تیم پشتیبانی ابرآمد<br>واحد عملیات</b></em></p>
        '''
html_msg_9 = '''
          </body>
        </html>
        '''
######### HTML Body End For Email ##########
############################################

email_body = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_4 + html_line_break + html_msg_5 + html_msg_6 + html_line_break + html_msg_7 + html_line_break + html_msg_8 + html_msg_9
msg.attach(MIMEText(email_body, 'html'))

with open(rahkaran_attachment, 'rb') as f:
    part = MIMEApplication(f.read(), Name=os.path.basename(rahkaran_attachment))
    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(rahkaran_attachment)}"'
    msg.attach(part)

# Connect to the SMTP server and send the email 465,*587*,25 (mail.systemgroup.net)
# Send email info
smtp_server = 'mail.systemgroup.net'
smtp_port = 587


# Send email function
with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    server.login(username, password)
    server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())






##############################
# Send Email to Automation iia

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

sender_email = 'sina.z@abramad.com'
receiver_email = 'ehsanf@systemgroup.net, samiras@systemgroup.net, mahtabl@systemgroup.net, SaeedSha@systemgroup.net'
cc_email = 'support@abramad.com, mehdi.a@abramad.com, alireza.ja@abramad.com'

automation_attachment = f'C:/Users/sina.z/Desktop/Automation_Reports/Report_to_Support/Automation-Servers-Report-{current_day}-{current_month}-{current_year}.xlsx'

# Create a multipart message object
msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = receiver_email
msg['CC'] = cc_email
msg['Subject'] = f'گزارش سرور های مشترکین سرویس اتوماسیون در بستر ابرآمد | {current_day} {persian_current_month} {current_year}'

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
html_msg_3 = f'''
            <p  style="font-family: DiodrumArabic-Regular">گزارش سرور های مشترکین سرویس اتوماسیون در بستر ابرآمد تا تاریخ {current_day} {persian_current_month} {current_year} پیوست قرار گرفت.</p>
        '''
html_msg_4 = f'''
            <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است که این گزارش به صورت ماهانه برای شما ارسال میگردد و از روی آن میتوانید به اطلاعات مشترکین اتوماسیون ابرآمد دست پیدا کنید. این گزارش به این منظور تهیه شده تا در صورت نیاز به اتصال به سرور مشترک مستقیما از طریق کاربری شخصی تان که توسط تیم پشتیبانی ابرآمد ایجاد میگردد، اقدام نمایید.</p>
        '''
html_msg_5 = f'''
                <p  style="font-family: DiodrumArabic-Regular">در صورتی که نیاز به ایجاد کاربری در زیرساخت ابرآمد دارید، اطلاعات زیر را در قالب جدول برای تیم ساپورت ابرآمد به آدرس: support@abramad.com ارسال نمایید.</p>
            '''
html_msg_6 = f'''
        <table>
                <tr>
                    <td><b>نام و نام خانوادگی</b></td>
                    <td><b>کد ملی</b></td>
                    <td><b>شماره همراه</b></td>
                    <td><b>آدرس ایمیل</b></td>
                </tr>
        </table>
            '''
html_msg_7 = f'''
            <p style="font-family: DiodrumArabic-Regular"><b>نکته مهم: ابرآمد سرویس اتوماسیون مشترکین را بصورت 24 ساعت در 7 روز هفته مانیتور میکند و در صورتی که سرویس Down شود، سلسله مراتبی از تسک ها توسط تیم پشتیبانی ابرآمد شکل میگیرد. لذا خواهشمند است در صورتی که نیاز به انجام اقداماتی دارید که منجر به Down شدن سرویس میگردد، حتما پیش از اقدام به تیم ساپورت ابرآمد، اطلاع رسانی فرمایید.  </b></p>
        '''
html_msg_8 = f'''
            <p style="font-family: DiodrumArabic-Regular"><em><b>سینا زارع<br>سرپرست تیم پشتیبانی ابرآمد<br>واحد عملیات</b></em></p>
        '''
html_msg_9 = '''
          </body>
        </html>
        '''
######### HTML Body End For Email ##########
############################################

email_body = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_4 + html_line_break + html_msg_5 + html_msg_6 + html_line_break + html_msg_7 + html_line_break + html_msg_8 + html_msg_9
msg.attach(MIMEText(email_body, 'html'))

with open(automation_attachment, 'rb') as f:
    part = MIMEApplication(f.read(), Name=os.path.basename(automation_attachment))
    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(automation_attachment)}"'
    msg.attach(part)

# Connect to the SMTP server and send the email 465,*587*,25 (mail.systemgroup.net)
# Send email info
smtp_server = 'mail.systemgroup.net'
smtp_port = 587

# Send email function
with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    server.login(username, password)
    server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())
