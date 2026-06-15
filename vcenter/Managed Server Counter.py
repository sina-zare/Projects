import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email import encoders
from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import csv
import os
import time
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

def pruner(customer_list):
    pruned_customer_list = []
    for omitable in customer_list:

        if "(راهکاران)" in omitable:
            omitable = omitable.replace("(راهکاران)", "")
        if "(Rahkaran)" in omitable:
            omitable = omitable.replace("(راهکاران)", "")
        if "اپلیکیشن" in omitable:
            omitable = omitable.replace("اپلیکیشن", "")
        if "دیتابیس" in omitable:
            omitable = omitable.replace("دیتابیس", "")
        if "توسعه" in omitable:
            omitable = omitable.replace("توسعه", "")
        if "اپ" in omitable:
            omitable = omitable.replace("اپ", "")
        if "دلفی" in omitable:
            omitable = omitable.replace("دلفی", "")
        if "سرور" in omitable:
            omitable = omitable.replace("سرور", "")
        if "لودبالانسر" in omitable:
            omitable = omitable.replace("لودبالانسر", "")
        if "تستی" in omitable:
            omitable = omitable.replace("تستی", "")
        if "1" in omitable:
            omitable = omitable.replace("1", "")
        if "اتوماسیون" in omitable:
            omitable = omitable.replace("اتوماسیون", "")
        if "سهام فصل" in omitable:
            omitable = omitable.replace("سهام فصل", "")
        if "BI" in omitable:
            omitable = omitable.replace("BI", "")
        if "bi" in omitable:
            omitable = omitable.replace("bi", "")
        if "سپیدار" in omitable:
            omitable = omitable.replace("سپیدار", "")
        if "مدیریت شده" in omitable:
            omitable = omitable.replace("مدیریت شده", "")
        if "build partner" in omitable:
            omitable = omitable.replace("-", " ")
        if "نسخه" in omitable:
            omitable = omitable.replace("-", " ")
        if ")" in omitable:
            omitable = omitable.replace(")", "")
        if "(" in omitable:
            omitable = omitable.replace("(", "")
        if "-" in omitable:
            omitable = omitable.replace("-", " ")
        if ":" in omitable:
            omitable = omitable.replace(":", " ")

        pruned_customer_list.append(omitable)

    return pruned_customer_list


today = datetime.date.today()

month_dict = {
    "1": "Dey",
    "2": "Bahman",
    "3": "Esfand",
    "4": "Farvardin",
    "5": "Ordibehesht",
    "6": "Khordad",
    "7": "Tir",
    "8": "Mordad",
    "9": "Shahrivar",
    "10": "Mehr",
    "11": "Aban",
    "12": "Azar"
}

month_dict_persian = {
    "1": "دی",
    "2": "بهمن",
    "3": "اسفند",
    "4": "فروردین",
    "5": "اردیبهشت",
    "6": "خرداد",
    "7": "تیر",
    "8": "مرداد",
    "9": "شهریور",
    "10": "مهر",
    "11": "آبان",
    "12": "آذر"
}

# Specify the current month
current_month = f'{month_dict[str(today.month)]}-1402'
current_month_persian = f'{month_dict_persian[str(today.month)]} 1402'

# Create the directory for the CSV files containing month
parent_directory = 'C:/Users/sina.z/Desktop/MIaaS_Server_Report/'
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
me_vms = [vm for vm in me_vm_view.view if (vm.name.startswith("MER-") or vm.name.startswith("MERD-") or vm.name.startswith("MEF-") or vm.name.startswith("MES-") or vm.name.startswith("MEA-") or vm.name.startswith("MEB-") or vm.name.startswith("MEM-") or vm.name.startswith("MEI-") )]


# Products
MER_count = 0
MER_customers = []

MEF_count = 0
MEF_customers = []

MES_count = 0
MES_customers = []

MEA_count = 0
MEA_customers = []

MEB_count = 0
MEB_customers = []

MEM_count = 0
MEM_customers = []

MEI_count = 0
MEI_customers = []


#Count number of servers per product and take their Persian name from custom attributes
for vm in me_vms:
    # Check count of Rahkaran servers
    if (vm.name.startswith("MER-") and (vm.runtime.powerState == "poweredOn")) or ((vm.name.startswith("MERD-") and (vm.runtime.powerState == "poweredOn"))) :

        MER_count += 1
        # Retrieve the value of the custom attribute with key 103 which is Role
        custom_value = vm.summary.customValue
        for i in custom_value:
            if i.key == 103:
                MER_customers.append(i.value)

for vm in me_vms:
    # Check count of Rahkaran servers
    if (vm.name.startswith("MEF-") and (vm.runtime.powerState == "poweredOn")):

        MEF_count += 1
        # Retrieve the value of the custom attribute with key 103 which is Role
        custom_value = vm.summary.customValue
        for i in custom_value:
            if i.key == 103:
                MEF_customers.append(i.value)

for vm in me_vms:
    # Check count of Rahkaran servers
    if (vm.name.startswith("MES-") and (vm.runtime.powerState == "poweredOn")):

        MES_count += 1
        # Retrieve the value of the custom attribute with key 103 which is Role
        custom_value = vm.summary.customValue
        for i in custom_value:
            if i.key == 103:
                MES_customers.append(i.value)

for vm in me_vms:
    # Check count of Rahkaran servers
    if (vm.name.startswith("MEA-") and (vm.runtime.powerState == "poweredOn")):

        MEA_count += 1
        # Retrieve the value of the custom attribute with key 103 which is Role
        custom_value = vm.summary.customValue
        for i in custom_value:
            if i.key == 103:
                MEA_customers.append(i.value)

for vm in me_vms:
    # Check count of Rahkaran servers
    if (vm.name.startswith("MEB-") and (vm.runtime.powerState == "poweredOn")):

        MEB_count += 1
        # Retrieve the value of the custom attribute with key 103 which is Role
        custom_value = vm.summary.customValue
        for i in custom_value:
            if i.key == 103:
                MEB_customers.append(i.value)

for vm in me_vms:
    # Check count of Rahkaran servers
    if (vm.name.startswith("MEM-") and (vm.runtime.powerState == "poweredOn")):

        MEM_count += 1
        # Retrieve the value of the custom attribute with key 103 which is Role
        custom_value = vm.summary.customValue
        for i in custom_value:
            if i.key == 103:
                MEM_customers.append(i.value)

for vm in me_vms:
    # Check count of Rahkaran servers
    if (vm.name.startswith("MEI-") and (vm.runtime.powerState == "poweredOn")):

        MEI_count += 1
        # Retrieve the value of the custom attribute with key 103 which is Role
        custom_value = vm.summary.customValue
        for i in custom_value:
            if i.key == 103:
                MEI_customers.append(i.value)


#Pruning Customer names for tidier view
pruned_MER_customers = pruner(MER_customers)
pruned_MEF_customers = pruner(MEF_customers)
pruned_MES_customers = pruner(MES_customers)
pruned_MEA_customers = pruner(MEA_customers)
pruned_MEB_customers = pruner(MEB_customers)
pruned_MEM_customers = pruner(MEM_customers)
pruned_MEI_customers = pruner(MEI_customers)




# Specify the filename and full path to the CSV file
MER_customer_csv_file_path = f'MER-Customers-{current_month}.csv'
MER_customer_full_file_path = os.path.join(final_path, MER_customer_csv_file_path)
# create a csv file to contain customer names
with open(MER_customer_full_file_path, mode='w', newline='', encoding='utf-8_sig') as file:

    # Create a CSV writer object
    writer = csv.writer(file, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # Write the header row to the CSV file
    writer.writerow(['نام مشتری'])
    for i in pruned_MER_customers:
        #converting string(customer name) to list, so that it does not iterate over string
        a = [i]
        writer.writerow(a)

# Specify the filename and full path to the CSV file
MEF_customer_csv_file_path = f'MEF-Customers-{current_month}.csv'
MEF_customer_full_file_path = os.path.join(final_path, MEF_customer_csv_file_path)
# create a csv file to contain customer names
with open(MEF_customer_full_file_path, mode='w', newline='', encoding='utf-8_sig') as file:

    # Create a CSV writer object
    writer = csv.writer(file, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # Write the header row to the CSV file
    writer.writerow(['نام مشتری'])
    for i in pruned_MEF_customers:
        #converting string(customer name) to list, so that it does not iterate over string
        a = [i]
        writer.writerow(a)

# Specify the filename and full path to the CSV file
MES_customer_csv_file_path = f'MES-Customers-{current_month}.csv'
MES_customer_full_file_path = os.path.join(final_path, MES_customer_csv_file_path)
# create a csv file to contain customer names
with open(MES_customer_full_file_path, mode='w', newline='', encoding='utf-8_sig') as file:

    # Create a CSV writer object
    writer = csv.writer(file, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # Write the header row to the CSV file
    writer.writerow(['نام مشتری'])
    for i in pruned_MES_customers:
        #converting string(customer name) to list, so that it does not iterate over string
        a = [i]
        writer.writerow(a)

# Specify the filename and full path to the CSV file
MEA_customer_csv_file_path = f'MEA-Customers-{current_month}.csv'
MEA_customer_full_file_path = os.path.join(final_path, MEA_customer_csv_file_path)
# create a csv file to contain customer names
with open(MEA_customer_full_file_path, mode='w', newline='', encoding='utf-8_sig') as file:

    # Create a CSV writer object
    writer = csv.writer(file, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # Write the header row to the CSV file
    writer.writerow(['نام مشتری'])
    for i in pruned_MEA_customers:
        #converting string(customer name) to list, so that it does not iterate over string
        a = [i]
        writer.writerow(a)

# Specify the filename and full path to the CSV file
MEB_customer_csv_file_path = f'MEB-Customers-{current_month}.csv'
MEB_customer_full_file_path = os.path.join(final_path, MEB_customer_csv_file_path)
# create a csv file to contain customer names
with open(MEB_customer_full_file_path, mode='w', newline='', encoding='utf-8_sig') as file:

    # Create a CSV writer object
    writer = csv.writer(file, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # Write the header row to the CSV file
    writer.writerow(['نام مشتری'])
    for i in pruned_MEB_customers:
        #converting string(customer name) to list, so that it does not iterate over string
        a = [i]
        writer.writerow(a)

# Specify the filename and full path to the CSV file
MEM_customer_csv_file_path = f'MEM-Customers-{current_month}.csv'
MEM_customer_full_file_path = os.path.join(final_path, MEM_customer_csv_file_path)
# create a csv file to contain customer names
with open(MEM_customer_full_file_path, mode='w', newline='', encoding='utf-8_sig') as file:

    # Create a CSV writer object
    writer = csv.writer(file, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # Write the header row to the CSV file
    writer.writerow(['نام مشتری'])
    for i in pruned_MEM_customers:
        #converting string(customer name) to list, so that it does not iterate over string
        a = [i]
        writer.writerow(a)

# Specify the filename and full path to the CSV file
MEI_customer_csv_file_path = f'MEI-Customers-{current_month}.csv'
MEI_customer_full_file_path = os.path.join(final_path, MEI_customer_csv_file_path)
# create a csv file to contain customer names
with open(MEI_customer_full_file_path, mode='w', newline='', encoding='utf-8_sig') as file:

    # Create a CSV writer object
    writer = csv.writer(file, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # Write the header row to the CSV file
    writer.writerow(['نام مشتری'])
    for i in pruned_MEI_customers:
        #converting string(customer name) to list, so that it does not iterate over string
        a = [i]
        writer.writerow(a)


sum_me_servers = MER_count + MEA_count + MEB_count + MEM_count + MEI_count + MEF_count + MES_count


# Send the CSV file via email
sender_email = 'sina.z@abramad.com'
receiver_email = 'marketing@abramad.com, sales@abramad.com, accounting@abramad.com, mehdi.a@abramad.com, alireza.ja@abramad.com, saeed.r@abramad.com, farnaz.sh@abramad.com, ehsan.h@abramad.com'

# Create a multipart message object
msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = receiver_email
msg['Subject'] = f'تعداد مشترکین ابرآمد بسته به نوع سرویس | {current_month_persian}'


# Attachments
MER_attachment = MER_customer_full_file_path
MEF_attachment = MEF_customer_full_file_path
MES_attachment = MES_customer_full_file_path
MEA_attachment = MEA_customer_full_file_path
MEB_attachment = MEB_customer_full_file_path
MEM_attachment = MEM_customer_full_file_path
MEI_attachment = MEI_customer_full_file_path



with open(MER_attachment, 'rb') as f:
    part = MIMEApplication(f.read(), Name=os.path.basename(MER_attachment))
    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(MER_attachment)}"'
    msg.attach(part)

with open(MEF_attachment, 'rb') as f:
    part = MIMEApplication(f.read(), Name=os.path.basename(MEF_attachment))
    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(MEF_attachment)}"'
    msg.attach(part)

with open(MES_attachment, 'rb') as f:
    part = MIMEApplication(f.read(), Name=os.path.basename(MES_attachment))
    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(MES_attachment)}"'
    msg.attach(part)

with open(MEA_attachment, 'rb') as f:
    part = MIMEApplication(f.read(), Name=os.path.basename(MEA_attachment))
    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(MEA_attachment)}"'
    msg.attach(part)

with open(MEB_attachment, 'rb') as f:
    part = MIMEApplication(f.read(), Name=os.path.basename(MEB_attachment))
    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(MEB_attachment)}"'
    msg.attach(part)

with open(MEM_attachment, 'rb') as f:
    part = MIMEApplication(f.read(), Name=os.path.basename(MEM_attachment))
    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(MEM_attachment)}"'
    msg.attach(part)

with open(MEI_attachment, 'rb') as f:
    part = MIMEApplication(f.read(), Name=os.path.basename(MEI_attachment))
    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(MEI_attachment)}"'
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
    <p  style="font-family: DiodrumArabic-Regular">فایل های قرار گرفته در پیوست نشان دهنده ی نام مشترکین ابرآمد بسته به نوع محصول، تا {current_month_persian} میباشد.</p>
'''
html_msg_4 = f'''
    <p  style="font-family: DiodrumArabic-Regular">تعداد سرور های راهکاران در زیرساخت ابرآمد <b>{MER_count}</b> عدد میباشد.</p>
'''
html_msg_5 = f'''
    <p  style="font-family: DiodrumArabic-Regular">تعداد سرور های سهام فصل در زیرساخت ابرآمد <b>{MEF_count}</b> عدد میباشد.</p>
'''
html_msg_6 = f'''
    <p  style="font-family: DiodrumArabic-Regular">تعداد سرور های سپیدار در زیرساخت ابرآمد <b>{MES_count}</b> عدد میباشد.</p>
'''
html_msg_7 = f'''
    <p  style="font-family: DiodrumArabic-Regular">تعداد سرور های اتوماسیون در زیرساخت ابرآمد <b>{MEA_count}</b> عدد میباشد.</p>
'''
html_msg_8 = f'''
    <p  style="font-family: DiodrumArabic-Regular">تعداد سرور های هوشمندی تجاری در زیرساخت ابرآمد <b>{MEB_count}</b> عدد میباشد.</p>
'''
html_msg_9 = f'''
    <p  style="font-family: DiodrumArabic-Regular">تعداد سرور های IaaS مدیریت شده در زیرساخت ابرآمد <b>{MEM_count}</b> عدد میباشد.</p>
'''
html_msg_10 = f'''
    <p  style="font-family: DiodrumArabic-Regular">تعداد سرور های IaaS مدیریت نشده در زیرساخت ابرآمد <b>{MEI_count}</b> عدد میباشد.</p>
'''
html_msg_11 = f'''
    <p  style="font-family: DiodrumArabic-Regular">مجموع تمامی سرور ها نیز <b>{sum_me_servers}</b> عدد میباشد.</p>
'''
html_msg_12 = f'''
    <p  style="font-family: DiodrumArabic-Regular">شایان ذکر است، در فایل های بالا عبارات استفاده شده معادل مفهوم زیر میباشند:<br>راهکاران، معادل MER<br>سهام فصل، معادل MEF<br>سپیدار، معادل MES<br>اتوماسیون، معادل MEA<br>هوشمندی تجاری، معادل MEB<br>سرور های IaaS مدیریت شده، معادل MEM<br>سرور های IaaS مدیریت نشده، معادل MEI</p>
'''
html_msg_13 = f'''
    <p style="font-family: DiodrumArabic-Regular"><em><b>سینا زارع<br>سرپرست تیم پشتیبانی ابرآمد<br>واحد عملیات</b></em></p>
'''
html_msg_14 = '''
  </body>
</html>
'''
######### HTML Body End For Email ##########
############################################
email_body = html_msg_1 + html_msg_2 + html_msg_3 + html_line_break + html_msg_4 + html_msg_5 + html_msg_6 + html_msg_7 + html_msg_8 + html_msg_9 + html_msg_10 + html_msg_11 + html_line_break + html_msg_12 + html_line_break + html_msg_13 + html_msg_14
# Add HTML email text
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
    server.sendmail(sender_email, "support@abramad.com", msg.as_string())

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
    server.sendmail(sender_email, "marketing@abramad.com", msg.as_string())

with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.sendmail(sender_email, "sales@abramad.com", msg.as_string())

with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.sendmail(sender_email, "accounting@abramad.com", msg.as_string())

with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.sendmail(sender_email, "farnaz.sh@abramad.com", msg.as_string())

with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.sendmail(sender_email, "ehsan.h@abramad.com", msg.as_string())

with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.sendmail(sender_email, "saeed.r@abramad.com", msg.as_string())

with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.sendmail(sender_email, "sina.z@abramad.com", msg.as_string())

Disconnect(ME_VC)
