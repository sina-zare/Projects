import imaplib
import email
import random
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
from persiantools.jdatetime import JalaliDate
import datetime
import csv
import os
import re


def is_csv_empty(file_path):
    return os.path.getsize(file_path) == 0


def append_to_csv(file_path, data):
    with open(file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)

def append_to_csv_primary_db(data):
    with open("C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/Primary-Database/Disk-Issue-Database.csv", 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)

def vm_is_in_csv(file_path, vm_name):
    with open(file_path, 'r') as file:
        reader = csv.reader(file)

        for row in reader:
            print(f"vm in csv: {row[0]}\nvm in unique: {vm_name}\n\n")
            if row[0] == vm_name:
                return True
            else:
                return False

    return None  # VM name not found in CSV file


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

    #print(f"Decryped Text: {decrypted_password}")
    return decrypted_password.decode()

username = decryptor("enc_sinaz_abramad","key_sinaz_abramad")
password = decryptor("enc_sinaz_pass","key_sinaz_pass")

# Read the existing last ticket No created from the file
ticket_no_path = "C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/TicketNo.txt"
with open(ticket_no_path, "r") as file:
    ticket_no = file.read()

# Connect to IMAP server
mail = imaplib.IMAP4_SSL('mail.systemgroup.net')
mail.login(username, password)

# Select the parent folder (Solarwinds)
mail.select('"Solarwinds Monitoring"')

# Select the subfolder (Abri Disk)
mail.select('"Solarwinds Monitoring/Abri Disk"')

# Get all unread messages
type, data = mail.search(None, 'UNSEEN')
msg_ids = data[0].split()

# List to store emails as dicts
emails = []

for msg_id in msg_ids:
    # Fetch email message by ID
    res, msg = mail.fetch(msg_id, "(RFC822)")
    raw_msg = msg[0][1]
    email_message = email.message_from_bytes(raw_msg)

    # Extract email headers & body
    subject = email_message['subject']

    # Save email as dict in list
    emails.append(subject)

list_of_vms = []

# Take VM Names
for email in emails:
    list_of_vms.append(email[46:])

# Delete Duplicates in list_of_vms
unique_list_of_vms = set(list_of_vms)

print(unique_list_of_vms)
# Disconnect from inbox
mail.close()
mail.logout()

# Convert the file contents to an integer

if ticket_no.isnumeric():
    int_ticket_no = int(ticket_no)
    print("File contents type check good, Value:", int_ticket_no, "\n\n")
else:
    # Send Email to King
    # Create a multipart message object
    msg = MIMEMultipart()
    msg['From'] = 'sina.z@abramad.com'
    msg['To'] = 'sina.z@abramad.com'
    msg['Subject'] = f'Error in Ticket No | {current_day}-{current_month}'

    msg.attach(MIMEText(
        f"<p><b>Ticket No File does not contain valid integer data | <em>{current_day}-{current_month}</em><br>Sending mail for below vms failed:<br></b><br>{unique_list_of_vms}<br><br>Wrong Value: {ticket_no}</p>",
        'html'))

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

duplicate_check_db_path = "C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/Abri-Disk-Duplicate-Check-DB.csv"

data_read_from_db = []

# Take DB Data for later calculations
with open(duplicate_check_db_path, 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        data_read_from_db.append(row)

if len(unique_list_of_vms) > 0:
    # Main Functionality
    for unique_vm in unique_list_of_vms:
        try:
            # Check if csv is empty
            if is_csv_empty(duplicate_check_db_path):
                print(f"CSV Empty, Generating New Email for {unique_vm}")
                print("================================================")
                # Increment Ticket NO by one
                int_ticket_no += 1
                # Overwrite the file with the new data
                with open(ticket_no_path, "w") as file:
                    file.write(str(int_ticket_no))

                # Send message to Hesam ina via email
                sender_email = 'sina.z@abramad.com'
                receiver_email = 'hesamr@systemgroup.net, nedar@systemgroup.net, javadk@systemgroup.net'
                cc_email = 'support@abramad.com,  alireza.ja@abramad.com'

                # Create a multipart message object
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = receiver_email
                msg['CC'] = cc_email
                msg['Subject'] = f'پر شدن فضای درایو D | سرور {unique_vm}'

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
                                                            <p  style="font-family: DiodrumArabic-Regular">درایو <b>D</b> سرور <b>{unique_vm}</b> پر شده است، لطفا نسبت به آزاد نمودن فضا و پاکسازی فایل های قابل حذف، اقدام نمایید.<p/>
                                                        '''
                html_msg_4 = f'''
                                                            <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع بزودی به عدم توانایی بکاپ گیری مشترک منجر خواهد شد.</p>
                                                        '''
                html_msg_5 = f'''
                                                                    <p  style="font-family: DiodrumArabic-Regular"><b>شماره درخواست: {int_ticket_no}</b></p>
                                                                '''
                html_msg_6 = f'''
                                                            <p  style="font-family: DiodrumArabic-Regular">با سپاس فراوان</p>
                                                        '''
                html_msg_7 = f'''
                                                            <p style="font-family: DiodrumArabic-Regular"><em><b>سینا زارع<br>سرپرست تیم پشتیبانی ابرآمد<br>واحد عملیات</b></em></p>
                                                        '''
                html_msg_8 = '''
                                                          </body>
                                                        </html>
                                                        '''
                ######### HTML Body End For Email ##########
                ############################################

                email_body = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_4 + html_line_break + html_msg_5 + html_line_break + html_msg_6 + html_line_break + html_msg_7 + html_msg_8
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
                    server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','),
                                    msg.as_string())

                # Append data to db
                data_to_write_to_db = [unique_vm, int_ticket_no, (current_day + " " + current_month)]
                append_to_csv(duplicate_check_db_path, data_to_write_to_db)
                print(f"DB is appended and email sent to hesam ina for {unique_vm}\n")
                data_to_write_to_primary_db = [unique_vm, int_ticket_no, (current_day + " " + current_month), "RahkaranAbriSupport@systemgroup.net"]
                append_to_csv_primary_db(data_to_write_to_primary_db)
                print(f"Primary DB Appended for {unique_vm}\n")

                # wait for 4 minute, so they think a human is doing it
                time.sleep(random.randint(60, 70))

            # Check if csv is not empty
            else:
                print("CSV Not Empty, Checking DB file names to Email the Duplicates\n")
                # Check if Duplicate exists
                vm_found = False

                for db_vm in data_read_from_db:
                    if unique_vm == db_vm[0]:
                        vm_found = True
                        break

                if vm_found:
                    print(f"Duplicate found: {unique_vm}, sending reminder to CFRS\n")
                    print("=========================================================")

                    # distinguish month and day the request was sent
                    persian_month_from_db = ""
                    persian_month_from_db = month_dict_persian[re.sub(r"\d|\s", "", (db_vm[2]))]

                    persian_day_from_db = ""
                    persian_day_from_db = re.sub(r"[a-zA-Z\s]", "", db_vm[2])

                    # Send message to Hesam ina via email
                    sender_email = 'sina.z@abramad.com'
                    receiver_email = 'hesamr@systemgroup.net, nedar@systemgroup.net, javadk@systemgroup.net'
                    cc_email = 'support@abramad.com,alireza.ja@abramad.com'

                    # Create a multipart message object
                    msg = MIMEMultipart()
                    msg['From'] = sender_email
                    msg['To'] = receiver_email
                    msg['CC'] = cc_email
                    msg['Subject'] = f'پیگیری پر شدن فضای درایو D | سرور {db_vm[0]}'

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
                            <p  style="font-family: DiodrumArabic-Regular">طی سه روز گذشته درخواستی مبنی بر بررسی پر شدن درایو <b>D</b> سرور <b>{db_vm[0]}</b> با شماره درخواست <b>{db_vm[1]}</b> <b>در تاریخ {persian_day_from_db} {persian_month_from_db} </b>ثبت شده است.<br>لطفا اگر موضوع را بررسی کرده اید، در نظر داشته باشید که این مشکل مجددا پیش آمده و نیازمند بررسی شما میباشد.</p>
                        '''
                    html_msg_4 = f'''
                            <p  style="font-family: DiodrumArabic-Regular">همانطور که میدانید، با توجه به وضعیت فعلی سرور، این موضوع بزودی به عدم توانایی بکاپ گیری مشترک منجر خواهد شد.</p>
                        '''
                    html_msg_5 = f'''
                            <p  style="font-family: DiodrumArabic-Regular">با سپاس فراوان از زحمات شما</p>
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

                    email_body = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_4 + html_line_break + html_msg_5 + html_line_break + html_msg_6 + html_line_break + html_msg_7
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
                        server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','),
                                        msg.as_string())

                    # wait for 4 minute, so they think a human is doing it
                    time.sleep(random.randint(60, 70))

                else:
                    # No Duplicate Found
                    print(f"No Duplicate Found, Generating New Email for {unique_vm}")
                    print("=========================================================")

                    # Increment Ticket NO by one
                    int_ticket_no += 1
                    # Overwrite the file with the new data
                    with open(ticket_no_path, "w") as file:
                        file.write(str(int_ticket_no))

                    # Send message to Hesam ina via email
                    sender_email = 'sina.z@abramad.com'
                    receiver_email = 'hesamr@systemgroup.net, nedar@systemgroup.net, javadk@systemgroup.net'
                    cc_email = 'support@abramad.com, alireza.ja@abramad.com'

                    # Create a multipart message object
                    msg = MIMEMultipart()
                    msg['From'] = sender_email
                    msg['To'] = receiver_email
                    msg['CC'] = cc_email
                    msg['Subject'] = f'پر شدن فضای درایو D | سرور {unique_vm}'

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
                                        <p  style="font-family: DiodrumArabic-Regular">درایو <b>D</b> سرور <b>{unique_vm}</b> پر شده است، لطفا نسبت به آزاد نمودن فضا و پاکسازی فایل های قابل حذف، اقدام نمایید.<p/>
                                    '''
                    html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع بزودی به عدم توانایی بکاپ گیری مشترک منجر خواهد شد.</p>
                                    '''
                    html_msg_5 = f'''
                                                <p  style="font-family: DiodrumArabic-Regular"><b>شماره درخواست: {int_ticket_no}</b></p>
                                            '''
                    html_msg_6 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">با سپاس فراوان</p>
                                    '''
                    html_msg_7 = f'''
                                        <p style="font-family: DiodrumArabic-Regular"><em><b>سینا زارع<br>سرپرست تیم پشتیبانی ابرآمد<br>واحد عملیات</b></em></p>
                                    '''
                    html_msg_8 = '''
                                      </body>
                                    </html>
                                    '''
                    ######### HTML Body End For Email ##########
                    ############################################

                    email_body = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_4 + html_line_break + html_msg_5 + html_line_break + html_msg_6 + html_line_break + html_msg_7 + html_msg_8
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
                        server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','),
                                        msg.as_string())

                    # Append data to db
                    data_to_write_to_db = [unique_vm, int_ticket_no, (current_day + " " + current_month)]
                    append_to_csv(duplicate_check_db_path, data_to_write_to_db)
                    print(f"DB is appended and email sent to hesam ina for {unique_vm}\n")
                    data_to_write_to_primary_db = [unique_vm, int_ticket_no, (current_day + " " + current_month),"RahkaranAbriSupport@systemgroup.net"]
                    append_to_csv_primary_db(data_to_write_to_primary_db)
                    print(f"Primary DB Appended for {unique_vm}\n")

                    # wait for 1 minute, so they think a human is doing it
                    time.sleep(random.randint(60, 70))

        except FileNotFoundError:
            # If file was not found
            # Send Email to King
            # Create a multipart message object
            msg = MIMEMultipart()
            msg['From'] = 'sina.z@abramad.com'
            msg['To'] = 'sina.z@abramad.com'
            msg['Subject'] = f'Error in Abri Disk DB | {current_day}-{current_month}'

            msg.attach(MIMEText(
                f"<p><b>DB File does not exist in <b>{duplicate_check_db_path}</b> | <em>{current_day}-{current_month}</em><br>Sending mail for below vms failed:<br></b><br>{unique_list_of_vms}<br><br>Unread them again.</p>",
                'html'))

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


    # Send Email to King
    # Create a multipart message object
    msg = MIMEMultipart()
    msg['From'] = 'sina.z@abramad.com'
    msg['To'] = 'sina.z@abramad.com'
    msg['Subject'] = f' پر شدن فضای درایو {current_month}-{current_day} |  D '

    ##############################################
    ######### HTML Body Begin For Email ##########
    html_line_break = '''
        <p><br></p>
    '''
    html_msg_1s = '''
    <html dir="rtl">
      <body>
    '''
    html_msg_2s = '''
        <p  style="font-family: DiodrumArabic-Regular">با سلام و احترام</p>
    '''
    html_msg_3s = f'''
        <p  style="font-family: DiodrumArabic-Regular">درخواست پاکسازی دیسک سرور های زیر در خصوص پر بودن فضای دیسک به تیم CFRS ارسال شد.</p>
    '''
    html_msg_4s = f'''
        <p  style="font-family: DiodrumArabic-Regular"><b>{unique_list_of_vms}</b></p>
    '''
    html_msg_5s = f'''
            <p  style="font-family: DiodrumArabic-Regular">مجموعا <b>{int_ticket_no}</b> درخواست، ثبت شده است.</p>
        '''
    html_msg_6s = f'''
        <p style="font-family: DiodrumArabic-Regular"><em><b>سینا زارع<br>سرپرست تیم پشتیبانی ابرآمد<br>واحد عملیات</b></em></p>
    '''
    html_msg_7s = '''
      </body>
    </html>
    '''
    ######### HTML Body End For Email ##########
    ############################################

    email_body = html_msg_1s + html_msg_2s + html_msg_3s + html_msg_4s + html_line_break + html_msg_5s + html_line_break + html_msg_6s + html_msg_7s
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
        server.sendmail('sina.z@abramad.com', 'sina.z@abramad.com', msg.as_string())
