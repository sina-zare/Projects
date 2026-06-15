import imaplib
import email
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
import random


############# Function Definition ##############
################################################

def is_csv_empty(file_path):
    return os.path.getsize(file_path) == 0


def append_to_csv(file_path, data):
    with open(file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)

def append_to_csv_primary_db(data):
    with open("C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/Primary-Database/Resource-Issue-Database.csv", 'a', newline='') as file:
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
#from sinzi import decryptor
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


############# Email Connection ##############
#############################################


# Connect to IMAP server
mail = imaplib.IMAP4_SSL('mail.systemgroup.net')
mail.login(username, password)

# Select the parent folder (Solarwinds)
mail.select('"Solarwinds Monitoring"')

# Select the subfolder (Abri Disk)
mail.select('"Solarwinds Monitoring/Abri Resource"')



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

# Creating list for cpu and memory vms
list_of_cpu_vms = []
list_of_ram_vms = []

# Take VM Names
for email in emails:

    if email.lower().startswith("critical cpu utilization on"):
        list_of_cpu_vms.append((email[28:]).strip('"'))
    if email.lower().startswith("critical memory utilization on"):
        list_of_ram_vms.append((email[31:]).strip('"'))


# Delete Duplicates in list_of_vms
unique_list_of_cpu_vms = set(list_of_cpu_vms)
unique_list_of_ram_vms = set(list_of_ram_vms)

print(f"CPU Peak Usage VMs: {unique_list_of_cpu_vms}")
print(f"RAM Peak Usage VMs: {unique_list_of_ram_vms}")

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
        f"<p><b>Ticket No File does not contain valid integer data | <em>{current_day}-{current_month}</em><br>Sending mail for below vms failed:<br></b><br>RAM Peak: {unique_list_of_ram_vms}<br>CPU Peak: {unique_list_of_cpu_vms}<br><br>Wrong Value: {ticket_no}</p>",
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

# Declare DB paths
ram_duplicate_check_db_path = "C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/Abri-Resource-RAM-Duplicate-Check-DB.csv"
cpu_duplicate_check_db_path = "C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/Abri-Resource-CPU-Duplicate-Check-DB.csv"
ram_data_read_from_db = []
cpu_data_read_from_db = []

# Take RAM DB Data for later calculations
with open(ram_duplicate_check_db_path, 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        ram_data_read_from_db.append(row)

# Take CPU DB Data for later calculations
with open(cpu_duplicate_check_db_path, 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        cpu_data_read_from_db.append(row)


##################### Start of Part 1 #######################
########################## RAM ##############################

# Go for calculation of RAM
if len(unique_list_of_ram_vms) > 0:
    # Main Functionality
    print("Doing RAM:")
    for unique_vm in unique_list_of_ram_vms:
        try:
            # Check if csv is empty
            if is_csv_empty(ram_duplicate_check_db_path):
                print(f"CSV Empty, Generating New Email for {unique_vm}")
                print("================================================")
                # Increment Ticket No by one
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
                msg['Subject'] = f'مصرف بی رویه {unique_vm} | RAM'

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
                            <p  style="font-family: DiodrumArabic-Regular">سرور <b>{unique_vm}</b> بیش از دو ساعت هست که دچار مصرف بی رویه RAM <b>(بالای 90%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و در صورتی که نیاز به افزایش RAM سرور میباشد، این مورد را به اطلاع ما برسانید.</p>
                        '''
                html_msg_4 = f'''
                            <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع بزودی به Down شدن سرویس راهکاران مشترک منجر خواهد شد.</p>
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

                ram_email_body = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_4 + html_line_break + html_msg_5 + html_line_break + html_msg_6 + html_line_break + html_msg_7 + html_msg_8
                msg.attach(MIMEText(ram_email_body, 'html'))

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
                    server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','),msg.as_string())

                # Append data to db
                ram_data_to_write_to_db = [unique_vm, int_ticket_no, (current_day + " " + current_month)]
                append_to_csv(ram_duplicate_check_db_path, ram_data_to_write_to_db)
                print(f"DB is appended and email sent to hesam ina for {unique_vm}\n")
                data_to_write_to_primary_db = [unique_vm, "RAM", int_ticket_no, (current_day + " " + current_month),
                                               "RahkaranAbriSupport@systemgroup.net"]
                append_to_csv_primary_db(data_to_write_to_primary_db)
                print(f"Primary DB Appended for {unique_vm}\n")

                # wait for 4 minute, so they think a human is doing it
                time.sleep(random.randint(60, 70))

            # Check if csv is not empty
            else:
                print("CSV Not Empty, Checking RAM DB file names to Email the Duplicates\n")
                # Check if Duplicate exists
                ram_vm_found = False

                for ram_db_vm in ram_data_read_from_db:
                    if unique_vm == ram_db_vm[0]:
                        ram_vm_found = True
                        break

                if ram_vm_found:
                    print(f"Duplicate RAM thing found: {unique_vm}, sending reminder to CFRS\n")
                    print("=========================================================")

                    # distinguish month and day the request was sent
                    ram_persian_month_from_db = ""
                    ram_persian_month_from_db = month_dict_persian[re.sub(r"\d|\s", "", (ram_db_vm[2]))]

                    ram_persian_day_from_db = ""
                    ram_persian_day_from_db = re.sub(r"[a-zA-Z\s]", "", ram_db_vm[2])

                    # Send message to Hesam ina via email
                    sender_email = 'sina.z@abramad.com'
                    receiver_email = 'hesamr@systemgroup.net, nedar@systemgroup.net, javadk@systemgroup.net'
                    cc_email = 'support@abramad.com, alireza.ja@abramad.com'

                    # Create a multipart message object
                    msg = MIMEMultipart()
                    msg['From'] = sender_email
                    msg['To'] = receiver_email
                    msg['CC'] = cc_email
                    msg['Subject'] = f'پیگیری مصرف بی رویه {ram_db_vm[0]} | RAM'

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
                            <p  style="font-family: DiodrumArabic-Regular">طی سه روز گذشته درخواستی مبنی بر بررسی مصرف بی رویه Memory سرور <b>{ram_db_vm[0]}</b> با شماره درخواست <b>{ram_db_vm[1]}</b> <b>در تاریخ {ram_persian_day_from_db} {ram_persian_month_from_db} </b>ثبت شده است.<br>لطفا اگر موضوع را بررسی کرده اید، در نظر داشته باشید که این مشکل مجددا پیش آمده و نیازمند بررسی شما میباشد.</p>
                        '''
                    html_msg_4 = f'''
                            <p  style="font-family: DiodrumArabic-Regular">همانطور که میدانید، با توجه به وضعیت فعلی سرور، این موضوع بزودی به Down شدن سرویس راهکاران مشترک منجر خواهد شد.</p>
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

                    ram_email_body = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_4 + html_line_break + html_msg_5 + html_line_break + html_msg_6 + html_line_break + html_msg_7
                    msg.attach(MIMEText(ram_email_body, 'html'))

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
                        server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','),msg.as_string())

                    # wait for 4 minute, so they think a human is doing it
                    time.sleep(random.randint(60, 70))

                else:
                    # No Duplicate Found
                    print(f"No RAM Duplicate Found, Generating New Email for {unique_vm}")
                    print("=========================================================")

                    # Increment Ticket No by one
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
                    msg['Subject'] = f'مصرف بی رویه {unique_vm} | RAM'

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
                                <p  style="font-family: DiodrumArabic-Regular">سرور <b>{unique_vm}</b> بیش از دو ساعت هست که دچار مصرف بی رویه RAM <b>(بالای 90%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و در صورتی که نیاز به افزایش RAM سرور میباشد، این مورد را به اطلاع ما برسانید.</p>
                            '''
                    html_msg_4 = f'''
                                <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع بزودی به Down شدن سرویس راهکاران مشترک منجر خواهد شد.</p>
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

                    ram_email_body = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_4 + html_line_break + html_msg_5 + html_line_break + html_msg_6 + html_line_break + html_msg_7 + html_msg_8
                    msg.attach(MIMEText(ram_email_body, 'html'))

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
                        server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())

                    # Append data to db
                    ram_data_to_write_to_db = [unique_vm, int_ticket_no, (current_day + " " + current_month)]
                    append_to_csv(ram_duplicate_check_db_path, ram_data_to_write_to_db)
                    print(f"RAM DB is appended and email sent to hesam ina for {unique_vm}\n")
                    data_to_write_to_primary_db = [unique_vm, "RAM", int_ticket_no, (current_day + " " + current_month),
                                                   "RahkaranAbriSupport@systemgroup.net"]
                    append_to_csv_primary_db(data_to_write_to_primary_db)
                    print(f"Primary DB Appended for {unique_vm}\n")

                    # wait for 4 minute, so they think a human is doing it
                    time.sleep(random.randint(60, 70))

        except FileNotFoundError:
            # If file was not found
            # Send Email to King
            # Create a multipart message object
            msg = MIMEMultipart()
            msg['From'] = 'sina.z@abramad.com'
            msg['To'] = 'sina.z@abramad.com'
            msg['Subject'] = f'Error in Abri Resource RAM DB | {current_day}-{current_month}'

            msg.attach(MIMEText(
                f"<p><b>RAM DB File does not exist in <b>{ram_duplicate_check_db_path}</b> | <em>{current_day}-{current_month}</em><br>Sending mail for below vms failed:<br></b><br>RAM Problems: {unique_list_of_ram_vms}<br><br>Unread them again.</p>",
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

    # End of CPU Calculations

    # Send Email to King
    # Create a multipart message object
    msg = MIMEMultipart()
    msg['From'] = 'sina.z@abramad.com'
    msg['To'] = 'sina.z@abramad.com'
    msg['Subject'] = f'مصرف بی رویه منابع {current_month}-{current_day} | RAM'

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
        <p  style="font-family: DiodrumArabic-Regular">درخواست مصرف بی رویه RAM سرور های زیر به تیم CFRS ارسال شد.</p>
    '''
    html_msg_4s = f'''
        <p  style="font-family: DiodrumArabic-Regular"><b>For RAM: {unique_list_of_ram_vms}</b></p>
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

    ram_inform_email_body = html_msg_1s + html_msg_2s + html_msg_3s + html_msg_4s + html_line_break + html_msg_5s + html_line_break + html_msg_6s + html_msg_7s
    msg.attach(MIMEText(ram_inform_email_body, 'html'))

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

    print("Finished Calculation on RAM incidents")


##################### Start of Part 2 #######################
########################## CPU ##############################

# Go for calculation of CPU
if len(unique_list_of_cpu_vms) > 0:
    # Main Functionality
    print("Doing CPU:")
    for unique_vm in unique_list_of_cpu_vms:
        try:
            # Check if csv is empty
            if is_csv_empty(cpu_duplicate_check_db_path):
                print(f"CSV Empty, Generating New Email for {unique_vm}")
                print("================================================")
                # Increment Ticket No by one
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
                msg['Subject'] = f'مصرف بی رویه {unique_vm} | CPU'

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
                            <p  style="font-family: DiodrumArabic-Regular">سرور <b>{unique_vm}</b> بیش از دو ساعت هست که دچار مصرف بی رویه CPU <b>(بالای 90%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و در صورتی که نیاز به افزایش CPU سرور میباشد، این مورد را به اطلاع ما برسانید.</p>
                        '''
                html_msg_4 = f'''
                            <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع بزودی به Down شدن سرویس راهکاران مشترک منجر خواهد شد.</p>
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

                cpu_email_body = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_4 + html_line_break + html_msg_5 + html_line_break + html_msg_6 + html_line_break + html_msg_7 + html_msg_8
                msg.attach(MIMEText(cpu_email_body, 'html'))

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
                    server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())

                # Append data to db
                cpu_data_to_write_to_db = [unique_vm, int_ticket_no, (current_day + " " + current_month)]
                append_to_csv(cpu_duplicate_check_db_path, cpu_data_to_write_to_db)
                print(f"DB is appended and email sent to hesam ina for {unique_vm}\n")
                data_to_write_to_primary_db = [unique_vm, "CPU", int_ticket_no, (current_day + " " + current_month),
                                               "RahkaranAbriSupport@systemgroup.net"]
                append_to_csv_primary_db(data_to_write_to_primary_db)
                print(f"Primary DB Appended for {unique_vm}\n")

                # wait for 4 minute, so they think a human is doing it
                time.sleep(random.randint(60, 70))

            # Check if csv is not empty
            else:
                print("CSV Not Empty, Checking CPU DB file names to Email the Duplicates\n")
                # Check if Duplicate exists
                cpu_vm_found = False

                for cpu_db_vm in cpu_data_read_from_db:
                    if unique_vm == cpu_db_vm[0]:
                        cpu_vm_found = True
                        break

                if cpu_vm_found:
                    print(f"Duplicate CPU thing found: {unique_vm}, sending reminder to CFRS\n")
                    print("=========================================================")

                    # distinguish month and day the request was sent
                    cpu_persian_month_from_db = ""
                    cpu_persian_month_from_db = month_dict_persian[re.sub(r"\d|\s", "", (cpu_db_vm[2]))]

                    cpu_persian_day_from_db = ""
                    cpu_persian_day_from_db = re.sub(r"[a-zA-Z\s]", "", cpu_db_vm[2])

                    # Send message to Hesam ina via email
                    sender_email = 'sina.z@abramad.com'
                    receiver_email = 'hesamr@systemgroup.net, nedar@systemgroup.net, javadk@systemgroup.net'
                    cc_email = 'support@abramad.com, alireza.ja@abramad.com'

                    # Create a multipart message object
                    msg = MIMEMultipart()
                    msg['From'] = sender_email
                    msg['To'] = receiver_email
                    msg['CC'] = cc_email
                    msg['Subject'] = f'پیگیری مصرف بی رویه {cpu_db_vm[0]} | RAM'

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
                            <p  style="font-family: DiodrumArabic-Regular">طی سه روز گذشته درخواستی مبنی بر بررسی مصرف بی رویه CPU سرور <b>{cpu_db_vm[0]}</b> با شماره درخواست <b>{cpu_db_vm[1]}</b> <b>در تاریخ {cpu_persian_day_from_db} {cpu_persian_month_from_db} </b>ثبت شده است.<br>لطفا اگر موضوع را بررسی کرده اید، در نظر داشته باشید که این مشکل مجددا پیش آمده و نیازمند بررسی شما میباشد.</p>
                        '''
                    html_msg_4 = f'''
                            <p  style="font-family: DiodrumArabic-Regular">همانطور که میدانید، با توجه به وضعیت فعلی سرور، این موضوع بزودی به Down شدن سرویس راهکاران مشترک منجر خواهد شد.</p>
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

                    cpu_email_body = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_4 + html_line_break + html_msg_5 + html_line_break + html_msg_6 + html_line_break + html_msg_7
                    msg.attach(MIMEText(cpu_email_body, 'html'))

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
                        server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','),msg.as_string())

                    # wait for 4 minute, so they think a human is doing it
                    time.sleep(random.randint(60, 70))

                else:
                    # No Duplicate Found
                    print(f"No CPU Duplicate Found, Generating New Email for {unique_vm}")
                    print("=========================================================")

                    # Increment Ticket No by one
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
                    msg['Subject'] = f'مصرف بی رویه {unique_vm} | CPU'

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
                                <p  style="font-family: DiodrumArabic-Regular">سرور <b>{unique_vm}</b> بیش از دو ساعت هست که دچار مصرف بی رویه CPU <b>(بالای 90%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و در صورتی که نیاز به افزایش CPU سرور میباشد، این مورد را به اطلاع ما برسانید.</p>
                            '''
                    html_msg_4 = f'''
                                <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع بزودی به Down شدن سرویس راهکاران مشترک منجر خواهد شد.</p>
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

                    cpu_email_body = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_4 + html_line_break + html_msg_5 + html_line_break + html_msg_6 + html_line_break + html_msg_7 + html_msg_8
                    msg.attach(MIMEText(cpu_email_body, 'html'))

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
                        server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())

                    # Append data to db
                    cpu_data_to_write_to_db = [unique_vm, int_ticket_no, (current_day + " " + current_month)]
                    append_to_csv(cpu_duplicate_check_db_path, cpu_data_to_write_to_db)
                    print(f"CPU DB is appended and email sent to hesam ina for {unique_vm}\n")
                    data_to_write_to_primary_db = [unique_vm, "CPU", int_ticket_no, (current_day + " " + current_month),
                                                   "RahkaranAbriSupport@systemgroup.net"]
                    append_to_csv_primary_db(data_to_write_to_primary_db)
                    print(f"Primary DB Appended for {unique_vm}\n")

                    # wait for 4 minute, so they think a human is doing it
                    time.sleep(random.randint(60, 70))

        except FileNotFoundError:
            # If file was not found
            # Send Email to King
            # Create a multipart message object
            msg = MIMEMultipart()
            msg['From'] = 'sina.z@abramad.com'
            msg['To'] = 'sina.z@abramad.com'
            msg['Subject'] = f'Error in Abri Resource CPU DB | {current_day}-{current_month}'

            msg.attach(MIMEText(
                f"<p><b>CPU DB File does not exist in <b>{cpu_duplicate_check_db_path}</b> | <em>{current_day}-{current_month}</em><br>Sending mail for below vms failed:<br></b><br>RAM Problems: {unique_list_of_cpu_vms}<br><br>Unread them again.</p>",
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


    # End of CPU Calculations

    # Send Email to King
    # Create a multipart message object
    msg = MIMEMultipart()
    msg['From'] = 'sina.z@abramad.com'
    msg['To'] = 'sina.z@abramad.com'
    msg['Subject'] = f'مصرف بی رویه منابع {current_month}-{current_day} | CPU'

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
        <p  style="font-family: DiodrumArabic-Regular">درخواست مصرف بی رویه CPU سرور های زیر به تیم CFRS ارسال شد.</p>
    '''
    html_msg_4s = f'''
        <p  style="font-family: DiodrumArabic-Regular"><b>For CPU: {unique_list_of_cpu_vms}</b></p>
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

    cpu_inform_email_body = html_msg_1s + html_msg_2s + html_msg_3s + html_msg_4s + html_line_break + html_msg_5s + html_line_break + html_msg_6s + html_msg_7s
    msg.attach(MIMEText(cpu_inform_email_body, 'html'))

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

    print("Finished Calculation on CPU incidents")