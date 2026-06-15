def resource_peak_checker(folder_path, db_file_path, receiver_email, cc_email):
    import imaplib
    import email
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from datetime import date
    from persiantools.jdatetime import JalaliDate
    import datetime
    import csv
    import os
    import time
    import random
    import re

    def decrypt(cipher_text, key):
        plain_text = ""
        for i in range(len(cipher_text)):
            char = cipher_text[i]
            plain_int = ord(char) - key
            plain_text += chr(plain_int)
        return plain_text

    def is_csv_empty(file_path):
        return os.path.getsize(file_path) == 0

    def append_to_csv(file_path, data):
        with open(file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(data)

    def append_to_csv_primary_db(data):
        with open("C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/Primary-Database/Resource-Issue-Database.csv",
                  'a', newline='') as file:
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

    def server_name_taker(text):
        words = text.lower().split()
        on_index = words.index("on")
        if "vip" in text.lower():
            return (words[on_index + 3]).replace('', '')
        else:
            return words[on_index + 1].replace('', '')

    def server_issue_taker(text):
        words = text.lower().split()
        critical_index = words.index("critical")

        return words[critical_index + 1]

    # Credentials
    from cryptography.fernet import Fernet
    def decryptor(enc_env_var, key_env_var):

        # Load the key
        key = os.environ.get(key_env_var)
        encryption_key = Fernet(key)
        encrypted_password = (os.environ.get(enc_env_var)).encode()
        # Decrypt Data
        decrypted_password = encryption_key.decrypt(encrypted_password.decode())

        # print(f"Decryped Text: {decrypted_password}")
        return decrypted_password.decode()

    username = decryptor("enc_sinaz_abramad", "key_sinaz_abramad")
    password = decryptor("enc_sinaz_pass", "key_sinaz_pass")

    today = datetime.date.today()

    seperated_folder_path = folder_path.split("/")
    customer_name = seperated_folder_path[-1]

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

    # Read the existing last ticket No created from the file
    ticket_no_path = "C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/TicketNo.txt"
    with open(ticket_no_path, "r") as file:
        ticket_no = file.read()

    # Connect to IMAP server
    mail = imaplib.IMAP4_SSL("mail.systemgroup.net")
    mail.login(username, password)

    # Select the subfolder
    mail.select(folder_path)

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
    list_of_vms = []

    # We used tupples instead of lists because they are hashable and immutable so we can use them in set() to remove duplicates
    for email in emails:
        list_of_vms.append((server_name_taker(email), server_issue_taker(email)))

    # Delete Duplicates in list_of_vms
    unique_list_of_vms = list(set(list_of_vms))

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

    duplicate_check_db_path = f"C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/ME-Resource-VIP/{db_file_path}"
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

                    # Memory Handling
                    if unique_vm[1] == "memory":
                        # Send new email to customer support
                        print(f"CSV Empty, Generating New Email for RAM of server: {unique_vm[0]}")
                        print("==================================================================")
                        # Increment Ticket No by one
                        int_ticket_no += 1
                        # Overwrite the file with the new data
                        with open(ticket_no_path, "w") as file:
                            file.write(str(int_ticket_no))

                        # Send message to Support via email
                        sender_email = 'sina.z@abramad.com'

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'مصرف بحرانی RAM | سرور {unique_vm[0]}'

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
                                        <p  style="font-family: DiodrumArabic-Regular">سرور <b>{unique_vm[0]}</b> بیش از 30 دقیقه هست که دچار مصرف بی رویه RAM <b>(بالای 90%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و در صورتی که نیاز به افزایش RAM سرور میباشد، این مورد را به اطلاع ما برسانید.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع بزودی به Down شدن سرویس، منجر خواهد شد.</p>
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
                        smtp_server = "mail.systemgroup.net"
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
                        ram_data_to_write_to_db = [unique_vm[0], "RAM", int_ticket_no,
                                                   (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, ram_data_to_write_to_db)
                        print(f"DB is appended and email sent to {receiver_email} for {unique_vm}\n")
                        data_to_write_to_primary_db = [unique_vm[0], "RAM", int_ticket_no,
                                                       (current_day + " " + current_month), receiver_email]
                        append_to_csv_primary_db(data_to_write_to_primary_db)
                        print(f"Primary DB Appended for {unique_vm}\n")

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(60, 70))

                    # CPU Handling
                    if unique_vm[1] == "cpu":
                        # Send new email to customer support
                        print(f"CSV Empty, Generating New Email for CPU of server: {unique_vm[0]}")
                        print("==================================================================")
                        # Increment Ticket No by one
                        int_ticket_no += 1
                        # Overwrite the file with the new data
                        with open(ticket_no_path, "w") as file:
                            file.write(str(int_ticket_no))

                        # Send message to Support via email
                        sender_email = 'sina.z@abramad.com'

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'مصرف بحرانی CPU | سرور {unique_vm[0]}'

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
                                        <p  style="font-family: DiodrumArabic-Regular">سرور <b>{unique_vm[0]}</b> بیش از 30 دقیقه هست که دچار مصرف بی رویه CPU <b>(بالای 90%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و در صورتی که نیاز به افزایش CPU سرور میباشد، این مورد را به اطلاع ما برسانید.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع بزودی به Down شدن سرویس، منجر خواهد شد.</p>
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
                        smtp_server = "mail.systemgroup.net"
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
                        cpu_data_to_write_to_db = [unique_vm[0], "CPU", int_ticket_no,
                                                   (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, cpu_data_to_write_to_db)
                        print(f"DB is appended and email sent to {receiver_email} for {unique_vm}\n")
                        data_to_write_to_primary_db = [unique_vm[0], "CPU", int_ticket_no,
                                                       (current_day + " " + current_month), receiver_email]
                        append_to_csv_primary_db(data_to_write_to_primary_db)
                        print(f"Primary DB Appended for {unique_vm}\n")

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(60, 70))


                # Check if csv is not empty
                else:
                    # Checking RAM
                    print("CSV Not Empty, Checking RAM DB file names to Email the Duplicates\n")
                    # Check if Duplicate exists
                    ram_vm_found = False

                    for ram_db_vm in data_read_from_db:
                        if unique_vm[0] == ram_db_vm[0] and ram_db_vm[1].lower() == "ram":
                            ram_vm_found = True
                            break

                    if ram_vm_found:
                        print(f"Duplicate RAM thing found: {unique_vm}, sending reminder to {receiver_email}\n")
                        print("=========================================================")

                        # distinguish month and day the request was sent
                        ram_persian_month_from_db = ""
                        ram_persian_month_from_db = month_dict_persian[re.sub(r"\d|\s", "", (ram_db_vm[3]))]

                        ram_persian_day_from_db = ""
                        ram_persian_day_from_db = re.sub(r"[a-zA-Z\s]", "", ram_db_vm[3])

                        # Send message to support via email
                        sender_email = 'sina.z@abramad.com'

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'پیگیری مصرف بحرانی {ram_db_vm[0]} | RAM'

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
                                <p  style="font-family: DiodrumArabic-Regular">طی سه روز گذشته درخواستی مبنی بر بررسی مصرف بی رویه Memory سرور <b>{ram_db_vm[0]}</b> با شماره درخواست <b>{ram_db_vm[2]}</b> <b>در تاریخ {ram_persian_day_from_db} {ram_persian_month_from_db} </b>ثبت شده است.<br>لطفا اگر موضوع را بررسی کرده اید، در نظر داشته باشید که این مشکل مجددا پیش آمده و نیازمند بررسی شما میباشد.</p>
                            '''
                        html_msg_4 = f'''
                                <p  style="font-family: DiodrumArabic-Regular">همانطور که میدانید، با توجه به وضعیت فعلی سرور، این موضوع بزودی به Down شدن سرویس منجر خواهد شد.</p>
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
                            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','),
                                            msg.as_string())

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(60, 70))

                    # If RAM VM was not found in DB
                    elif unique_vm[1].lower() != "cpu":
                        # No Duplicate Found
                        print(f"No RAM Duplicate Found, Generating New Email for {unique_vm}")
                        print("=========================================================")

                        # Increment Ticket No by one
                        int_ticket_no += 1
                        # Overwrite the file with the new data
                        with open(ticket_no_path, "w") as file:
                            file.write(str(int_ticket_no))

                        # Send message to support via email
                        sender_email = 'sina.z@abramad.com'

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'مصرف بحرانی RAM | سرور {unique_vm[0]}'

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
                                        <p  style="font-family: DiodrumArabic-Regular">سرور <b>{unique_vm[0]}</b> بیش از 30 دقیقه هست که دچار مصرف بی رویه RAM <b>(بالای 90%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و در صورتی که نیاز به افزایش RAM سرور میباشد، این مورد را به اطلاع ما برسانید.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع بزودی به Down شدن سرویس، منجر خواهد شد.</p>
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
                        smtp_server = "mail.systemgroup.net"
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
                        ram_data_to_write_to_db = [unique_vm[0], "RAM", int_ticket_no,
                                                   (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, ram_data_to_write_to_db)
                        print(f"DB is appended and email sent to {receiver_email} for {unique_vm}\n")
                        data_to_write_to_primary_db = [unique_vm[0], "RAM", int_ticket_no,
                                                       (current_day + " " + current_month), receiver_email]
                        append_to_csv_primary_db(data_to_write_to_primary_db)
                        print(f"Primary DB Appended for {unique_vm}\n")

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(60, 70))

                    ##############
                    ##############

                    # Checking CPU
                    print("\nCSV Not Empty, Checking CPU DB file names to Email the Duplicates\n")
                    # Check if Duplicate exists
                    cpu_vm_found = False

                    for cpu_db_vm in data_read_from_db:
                        if unique_vm[0] == cpu_db_vm[0] and cpu_db_vm[1].lower() == "cpu":
                            cpu_vm_found = True
                            break

                    if cpu_vm_found:
                        print(f"Duplicate CPU thing found: {unique_vm}, sending reminder to {receiver_email}\n")
                        print("=========================================================")

                        # distinguish month and day the request was sent
                        cpu_persian_month_from_db = ""
                        cpu_persian_month_from_db = month_dict_persian[re.sub(r"\d|\s", "", (cpu_db_vm[3]))]

                        cpu_persian_day_from_db = ""
                        cpu_persian_day_from_db = re.sub(r"[a-zA-Z\s]", "", cpu_db_vm[3])

                        # Send message to support via email
                        sender_email = 'sina.z@abramad.com'

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'پیگیری مصرف بحرانی {cpu_db_vm[0]} | CPU'

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
                                        <p  style="font-family: DiodrumArabic-Regular">طی سه روز گذشته درخواستی مبنی بر بررسی مصرف بی رویه CPU سرور <b>{cpu_db_vm[0]}</b> با شماره درخواست <b>{cpu_db_vm[2]}</b> <b>در تاریخ {cpu_persian_day_from_db} {cpu_persian_month_from_db} </b>ثبت شده است.<br>لطفا اگر موضوع را بررسی کرده اید، در نظر داشته باشید که این مشکل مجددا پیش آمده و نیازمند بررسی شما میباشد.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">همانطور که میدانید، با توجه به وضعیت فعلی سرور، این موضوع بزودی به Down شدن سرویس منجر خواهد شد.</p>
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
                            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','),
                                            msg.as_string())

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(60, 70))

                    # If CPU VM was not found in DB
                    elif unique_vm[1].lower() != "memory":
                        # No Duplicate Found
                        print(f"No CPU Duplicate Found, Generating New Email for {unique_vm}")
                        print("=========================================================")

                        # Increment Ticket No by one
                        int_ticket_no += 1
                        # Overwrite the file with the new data
                        with open(ticket_no_path, "w") as file:
                            file.write(str(int_ticket_no))

                        # Send message to support via email
                        sender_email = 'sina.z@abramad.com'

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'مصرف بحرانی CPU | سرور {unique_vm[0]}'

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
                                        <p  style="font-family: DiodrumArabic-Regular">سرور <b>{unique_vm[0]}</b> بیش از 30 دقیقه هست که دچار مصرف بی رویه CPU <b>(بالای 90%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و در صورتی که نیاز به افزایش CPU سرور میباشد، این مورد را به اطلاع ما برسانید.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع بزودی به Down شدن سرویس، منجر خواهد شد.</p>
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
                        smtp_server = "mail.systemgroup.net"
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
                        cpu_data_to_write_to_db = [unique_vm[0], "CPU", int_ticket_no,
                                                   (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, cpu_data_to_write_to_db)
                        print(f"DB is appended and email sent to {receiver_email} for {unique_vm}\n")
                        data_to_write_to_primary_db = [unique_vm[0], "CPU", int_ticket_no,
                                                       (current_day + " " + current_month), receiver_email]
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
                    f"<p><b>RAM DB File does not exist in <b>{duplicate_check_db_path}</b> | <em>{current_day}-{current_month}</em><br>Sending mail for below vms failed:<br></b><br>RAM Problems: {unique_list_of_vms}<br><br>Unread them again.</p>",
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
        msg['Subject'] = f'مصرف بحرانی منابع {current_month}-{current_day} | میرعماد '

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
            <p  style="font-family: DiodrumArabic-Regular">درخواست بررسی مصرف بحرانی منابع به تیم ساپورت مشترک برای سرور های زیر انجام شد:</p>
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

        inform_email_body = html_msg_1s + html_msg_2s + html_msg_3s + html_msg_4s + html_line_break + html_msg_5s + html_line_break + html_msg_6s + html_msg_7s
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


def resource_peak_checker_mgmt(folder_path, db_file_path, receiver_email, cc_email):
    import imaplib
    import email
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from datetime import date
    from persiantools.jdatetime import JalaliDate
    import datetime
    import csv
    import os
    import time
    import random
    import re

    def decrypt(cipher_text, key):
        plain_text = ""
        for i in range(len(cipher_text)):
            char = cipher_text[i]
            plain_int = ord(char) - key
            plain_text += chr(plain_int)
        return plain_text

    def is_csv_empty(file_path):
        return os.path.getsize(file_path) == 0

    def append_to_csv(file_path, data):
        with open(file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(data)

    def append_to_csv_primary_db(data):
        with open("C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/Primary-Database/Resource-Issue-Database.csv",
                  'a', newline='') as file:
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

    def server_name_taker(text):
        words = text.lower().split()
        on_index = words.index("on")
        if "vip" in text.lower():
            return (words[on_index + 3]).replace('', '')
        else:
            return words[on_index + 1].replace('', '')

    def server_issue_taker(text):
        words = text.lower().split()
        critical_index = words.index("critical")

        return words[critical_index + 1]

    # Credentials
    from cryptography.fernet import Fernet
    def decryptor(enc_env_var, key_env_var):

        # Load the key
        key = os.environ.get(key_env_var)
        encryption_key = Fernet(key)
        encrypted_password = (os.environ.get(enc_env_var)).encode()
        # Decrypt Data
        decrypted_password = encryption_key.decrypt(encrypted_password.decode())

        # print(f"Decryped Text: {decrypted_password}")
        return decrypted_password.decode()

    username = decryptor("enc_sinaz_abramad", "key_sinaz_abramad")
    password = decryptor("enc_sinaz_pass", "key_sinaz_pass")

    today = datetime.date.today()

    seperated_folder_path = folder_path.split("/")
    customer_name = seperated_folder_path[-1]

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

    # Read the existing last ticket No created from the file
    ticket_no_path = "C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/TicketNo.txt"
    with open(ticket_no_path, "r") as file:
        ticket_no = file.read()

    # Connect to IMAP server
    mail = imaplib.IMAP4_SSL("mail.systemgroup.net")
    mail.login(username, password)

    # Select the subfolder
    mail.select(folder_path)

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
    list_of_vms = []

    # We used tupples instead of lists because they are hashable and immutable so we can use them in set() to remove duplicates
    for email in emails:
        list_of_vms.append((server_name_taker(email), server_issue_taker(email)))

    # Delete Duplicates in list_of_vms
    unique_list_of_vms = list(set(list_of_vms))

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

    duplicate_check_db_path = f"C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/ME-Resource-VIP/{db_file_path}"
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

                    # Memory Handling
                    if unique_vm[1] == "memory":
                        # Send new email to customer support
                        print(f"CSV Empty, Generating New Email for RAM of server: {unique_vm[0]}")
                        print("==================================================================")
                        # Increment Ticket No by one
                        int_ticket_no += 1
                        # Overwrite the file with the new data
                        with open(ticket_no_path, "w") as file:
                            file.write(str(int_ticket_no))

                        # Send message to Support via email
                        sender_email = 'sina.z@abramad.com'

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'مصرف بحرانی RAM |  {unique_vm[0]}'

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
                                        <p  style="font-family: DiodrumArabic-Regular">نود <b>{unique_vm[0]}</b> بیش از 30 دقیقه هست که دچار مصرف بی رویه RAM <b>(بالای 90%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و نتیجه بررسی خود را به اطلاع تیم ساپورت برسانید.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی، این موضوع میتواند به بروز اختلال در سرویس دهی منجر شود.</p>
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
                        smtp_server = "mail.systemgroup.net"
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
                        ram_data_to_write_to_db = [unique_vm[0], "RAM", int_ticket_no,
                                                   (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, ram_data_to_write_to_db)
                        print(f"DB is appended and email sent to {receiver_email} for {unique_vm}\n")
                        data_to_write_to_primary_db = [unique_vm[0], "RAM", int_ticket_no,
                                                       (current_day + " " + current_month), receiver_email]
                        append_to_csv_primary_db(data_to_write_to_primary_db)
                        print(f"Primary DB Appended for {unique_vm}\n")

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(60, 70))

                    # CPU Handling
                    if unique_vm[1] == "cpu":
                        # Send new email to customer support
                        print(f"CSV Empty, Generating New Email for CPU of server: {unique_vm[0]}")
                        print("==================================================================")
                        # Increment Ticket No by one
                        int_ticket_no += 1
                        # Overwrite the file with the new data
                        with open(ticket_no_path, "w") as file:
                            file.write(str(int_ticket_no))

                        # Send message to Support via email
                        sender_email = 'sina.z@abramad.com'

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'مصرف بحرانی CPU |  {unique_vm[0]}'

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
                                        <p  style="font-family: DiodrumArabic-Regular">نود <b>{unique_vm[0]}</b> بیش از 30 دقیقه هست که دچار مصرف بی رویه CPU <b>(بالای 90%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و نتیجه بررسی خود را به اطلاع تیم ساپورت برسانید.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی، این موضوع میتواند به بروز اختلال در سرویس دهی منجر شود.</p>
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
                        smtp_server = "mail.systemgroup.net"
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
                        cpu_data_to_write_to_db = [unique_vm[0], "CPU", int_ticket_no,
                                                   (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, cpu_data_to_write_to_db)
                        print(f"DB is appended and email sent to {receiver_email} for {unique_vm}\n")
                        data_to_write_to_primary_db = [unique_vm[0], "CPU", int_ticket_no,
                                                       (current_day + " " + current_month), receiver_email]
                        append_to_csv_primary_db(data_to_write_to_primary_db)
                        print(f"Primary DB Appended for {unique_vm}\n")

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(60, 70))


                # Check if csv is not empty
                else:
                    # Checking RAM
                    print("CSV Not Empty, Checking RAM DB file names to Email the Duplicates\n")
                    # Check if Duplicate exists
                    ram_vm_found = False

                    for ram_db_vm in data_read_from_db:
                        if unique_vm[0] == ram_db_vm[0] and ram_db_vm[1].lower() == "ram":
                            ram_vm_found = True
                            break

                    if ram_vm_found:
                        print(f"Duplicate RAM thing found: {unique_vm}, sending reminder to {receiver_email}\n")
                        print("=========================================================")

                        # distinguish month and day the request was sent
                        ram_persian_month_from_db = ""
                        ram_persian_month_from_db = month_dict_persian[re.sub(r"\d|\s", "", (ram_db_vm[3]))]

                        ram_persian_day_from_db = ""
                        ram_persian_day_from_db = re.sub(r"[a-zA-Z\s]", "", ram_db_vm[3])

                        # Send message to support via email
                        sender_email = 'sina.z@abramad.com'

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'پیگیری مصرف بحرانی {ram_db_vm[0]} | RAM'

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
                                <p  style="font-family: DiodrumArabic-Regular">طی سه روز گذشته درخواستی مبنی بر بررسی مصرف بی رویه Memory نود <b>{ram_db_vm[0]}</b> با شماره درخواست <b>{ram_db_vm[2]}</b> <b>در تاریخ {ram_persian_day_from_db} {ram_persian_month_from_db} </b>ثبت شده است.<br>لطفا اگر موضوع را بررسی کرده اید، در نظر داشته باشید که این مشکل مجددا پیش آمده و نیازمند بررسی شما میباشد.</p>
                            '''
                        html_msg_4 = f'''
                                <p  style="font-family: DiodrumArabic-Regular">همانطور که میدانید، با توجه به وضعیت فعلی، این موضوع احتمال بروز اختلال در عملکرد یا نقص در سرویس دهی را افزایش میدهد.</p>
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
                            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','),
                                            msg.as_string())

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(60, 70))

                    # If RAM VM was not found in DB
                    elif unique_vm[1].lower() != "cpu":
                        # No Duplicate Found
                        print(f"No RAM Duplicate Found, Generating New Email for {unique_vm}")
                        print("=========================================================")

                        # Increment Ticket No by one
                        int_ticket_no += 1
                        # Overwrite the file with the new data
                        with open(ticket_no_path, "w") as file:
                            file.write(str(int_ticket_no))

                        # Send message to support via email
                        sender_email = 'sina.z@abramad.com'

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'مصرف بحرانی RAM |  {unique_vm[0]}'

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
                                        <p  style="font-family: DiodrumArabic-Regular">نود <b>{unique_vm[0]}</b> بیش از 30 دقیقه هست که دچار مصرف بی رویه RAM <b>(بالای 90%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و نتیجه بررسی خود را به اطلاع تیم ساپورت برسانید.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی، این موضوع میتواند به بروز اختلال در سرویس دهی منجر شود.</p>
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
                        smtp_server = "mail.systemgroup.net"
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
                        ram_data_to_write_to_db = [unique_vm[0], "RAM", int_ticket_no,
                                                   (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, ram_data_to_write_to_db)
                        print(f"DB is appended and email sent to {receiver_email} for {unique_vm}\n")
                        data_to_write_to_primary_db = [unique_vm[0], "RAM", int_ticket_no,
                                                       (current_day + " " + current_month), receiver_email]
                        append_to_csv_primary_db(data_to_write_to_primary_db)
                        print(f"Primary DB Appended for {unique_vm}\n")

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(60, 70))

                    ##############
                    ##############

                    # Checking CPU
                    print("\nCSV Not Empty, Checking CPU DB file names to Email the Duplicates\n")
                    # Check if Duplicate exists
                    cpu_vm_found = False

                    for cpu_db_vm in data_read_from_db:
                        if unique_vm[0] == cpu_db_vm[0] and cpu_db_vm[1].lower() == "cpu":
                            cpu_vm_found = True
                            break

                    if cpu_vm_found:
                        print(f"Duplicate CPU thing found: {unique_vm}, sending reminder to {receiver_email}\n")
                        print("=========================================================")

                        # distinguish month and day the request was sent
                        cpu_persian_month_from_db = ""
                        cpu_persian_month_from_db = month_dict_persian[re.sub(r"\d|\s", "", (cpu_db_vm[3]))]

                        cpu_persian_day_from_db = ""
                        cpu_persian_day_from_db = re.sub(r"[a-zA-Z\s]", "", cpu_db_vm[3])

                        # Send message to support via email
                        sender_email = 'sina.z@abramad.com'

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'پیگیری مصرف بحرانی {cpu_db_vm[0]} | CPU'

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
                                        <p  style="font-family: DiodrumArabic-Regular">طی سه روز گذشته درخواستی مبنی بر بررسی مصرف بی رویه CPU  <b>{cpu_db_vm[0]}</b> با شماره درخواست <b>{cpu_db_vm[2]}</b> <b>در تاریخ {cpu_persian_day_from_db} {cpu_persian_month_from_db} </b>ثبت شده است.<br>لطفا اگر موضوع را بررسی کرده اید، در نظر داشته باشید که این مشکل مجددا پیش آمده و نیازمند بررسی شما میباشد.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">همانطور که میدانید، با توجه به وضعیت فعلی، این موضوع احتمال بروز اختلال در عملکرد یا نقص در سرویس دهی را افزایش میدهد.</p>
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
                            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','),
                                            msg.as_string())

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(60, 70))

                    # If CPU VM was not found in DB
                    elif unique_vm[1].lower() != "memory":
                        # No Duplicate Found
                        print(f"No CPU Duplicate Found, Generating New Email for {unique_vm}")
                        print("=========================================================")

                        # Increment Ticket No by one
                        int_ticket_no += 1
                        # Overwrite the file with the new data
                        with open(ticket_no_path, "w") as file:
                            file.write(str(int_ticket_no))

                        # Send message to support via email
                        sender_email = 'sina.z@abramad.com'

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'مصرف بحرانی CPU |  {unique_vm[0]}'

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
                                        <p  style="font-family: DiodrumArabic-Regular">نود <b>{unique_vm[0]}</b> بیش از 30 دقیقه هست که دچار مصرف بی رویه CPU <b>(بالای 90%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و نتیجه بررسی خود را به اطلاع تیم ساپورت برسانید.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی، این موضوع میتواند به بروز اختلال در سرویس دهی منجر شود.</p>
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
                        smtp_server = "mail.systemgroup.net"
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
                        cpu_data_to_write_to_db = [unique_vm[0], "CPU", int_ticket_no,
                                                   (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, cpu_data_to_write_to_db)
                        print(f"DB is appended and email sent to {receiver_email} for {unique_vm}\n")
                        data_to_write_to_primary_db = [unique_vm[0], "CPU", int_ticket_no,
                                                       (current_day + " " + current_month), receiver_email]
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
                    f"<p><b>RAM DB File does not exist in <b>{duplicate_check_db_path}</b> | <em>{current_day}-{current_month}</em><br>Sending mail for below vms failed:<br></b><br>RAM Problems: {unique_list_of_vms}<br><br>Unread them again.</p>",
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
        msg['Subject'] = f'مصرف بحرانی منابع {current_month}-{current_day} | میرعماد '

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
            <p  style="font-family: DiodrumArabic-Regular">درخواست بررسی مصرف بحرانی منابع به تیم عملیات برای نود های زیر انجام شد:</p>
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

        inform_email_body = html_msg_1s + html_msg_2s + html_msg_3s + html_msg_4s + html_line_break + html_msg_5s + html_line_break + html_msg_6s + html_msg_7s
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


def resource_peak_checker_refah(folder_path, db_file_path, receiver_email, cc_email):
    import imaplib
    import email
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from datetime import date
    from persiantools.jdatetime import JalaliDate
    import datetime
    import csv
    import os
    import time
    import random
    import re

    def decrypt(cipher_text, key):
        plain_text = ""
        for i in range(len(cipher_text)):
            char = cipher_text[i]
            plain_int = ord(char) - key
            plain_text += chr(plain_int)
        return plain_text

    def is_csv_empty(file_path):
        return os.path.getsize(file_path) == 0

    def append_to_csv(file_path, data):
        with open(file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(data)

    def append_to_csv_primary_db(data):
        with open("C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/Primary-Database/Resource-Issue-Database.csv",
                  'a', newline='') as file:
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

    def server_name_taker(text):
        words = text.lower().split()
        on_index = words.index("on")
        if "vip" in text.lower():
            return (words[on_index + 3]).replace('', '')
        else:
            return words[on_index + 1].replace('', '')

    def server_issue_taker(text):
        words = text.lower().split()
        critical_index = words.index("critical")

        return words[critical_index + 1]

    # Credentials
    from cryptography.fernet import Fernet
    def decryptor(enc_env_var, key_env_var):

        # Load the key
        key = os.environ.get(key_env_var)
        encryption_key = Fernet(key)
        encrypted_password = (os.environ.get(enc_env_var)).encode()
        # Decrypt Data
        decrypted_password = encryption_key.decrypt(encrypted_password.decode())

        # print(f"Decryped Text: {decrypted_password}")
        return decrypted_password.decode()

    username = decryptor("enc_sinaz_abramad", "key_sinaz_abramad")
    password = decryptor("enc_sinaz_pass", "key_sinaz_pass")

    today = datetime.date.today()

    seperated_folder_path = folder_path.split("/")
    customer_name = seperated_folder_path[-1]

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

    # Read the existing last ticket No created from the file
    ticket_no_path = "C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/TicketNo.txt"
    with open(ticket_no_path, "r") as file:
        ticket_no = file.read()

    # Connect to IMAP server
    mail = imaplib.IMAP4_SSL("mail.systemgroup.net")
    mail.login(username, password)

    # Select the subfolder
    mail.select(folder_path)

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
    list_of_vms = []

    # We used tupples instead of lists because they are hashable and immutable so we can use them in set() to remove duplicates
    for email in emails:
        list_of_vms.append((server_name_taker(email), server_issue_taker(email)))

    # Delete Duplicates in list_of_vms
    unique_list_of_vms = list(set(list_of_vms))

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

    duplicate_check_db_path = f"C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/ME-Resource-VIP/{db_file_path}"
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

                    # Memory Handling
                    if unique_vm[1] == "memory":
                        # Send new email to customer support
                        print(f"CSV Empty, Generating New Email for RAM of server: {unique_vm[0]}")
                        print("==================================================================")
                        # Increment Ticket No by one
                        int_ticket_no += 1
                        # Overwrite the file with the new data
                        with open(ticket_no_path, "w") as file:
                            file.write(str(int_ticket_no))

                        # Send message to Support via email
                        sender_email = 'sina.z@abramad.com'

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'مصرف بحرانی 50% RAM | سرور {unique_vm[0]}'

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
                                        <p  style="font-family: DiodrumArabic-Regular">سرور <b>{unique_vm[0]}</b> دچار مصرف  RAM <b>(بالای 50%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و در صورتی که نیاز به افزایش RAM سرور میباشد، این مورد را به اطلاع ما برسانید.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">این مورد به درخواست شما ایجاد شده است و با پیش آمدن مجدد رخداد برای شما ارسال میگردد.</p>
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
                        smtp_server = "mail.systemgroup.net"
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
                        ram_data_to_write_to_db = [unique_vm[0], "RAM", int_ticket_no,
                                                   (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, ram_data_to_write_to_db)
                        print(f"DB is appended and email sent to {receiver_email} for {unique_vm}\n")
                        data_to_write_to_primary_db = [unique_vm[0], "RAM", int_ticket_no,
                                                       (current_day + " " + current_month), receiver_email]
                        append_to_csv_primary_db(data_to_write_to_primary_db)
                        print(f"Primary DB Appended for {unique_vm}\n")

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(60, 70))

                    # CPU Handling
                    if unique_vm[1] == "cpu":
                        # Send new email to customer support
                        print(f"CSV Empty, Generating New Email for CPU of server: {unique_vm[0]}")
                        print("==================================================================")
                        # Increment Ticket No by one
                        int_ticket_no += 1
                        # Overwrite the file with the new data
                        with open(ticket_no_path, "w") as file:
                            file.write(str(int_ticket_no))

                        # Send message to Support via email
                        sender_email = 'sina.z@abramad.com'

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'مصرف بحرانی 50% CPU | سرور {unique_vm[0]}'

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
                                        <p  style="font-family: DiodrumArabic-Regular">سرور <b>{unique_vm[0]}</b>  دچار مصرف CPU <b>(بالای 50%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و در صورتی که نیاز به افزایش CPU سرور میباشد، این مورد را به اطلاع ما برسانید.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">این مورد به درخواست شما ایجاد شده است و با پیش آمدن مجدد رخداد برای شما ارسال میگردد.</p>
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
                        smtp_server = "mail.systemgroup.net"
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
                        cpu_data_to_write_to_db = [unique_vm[0], "CPU", int_ticket_no,
                                                   (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, cpu_data_to_write_to_db)
                        print(f"DB is appended and email sent to {receiver_email} for {unique_vm}\n")
                        data_to_write_to_primary_db = [unique_vm[0], "CPU", int_ticket_no,
                                                       (current_day + " " + current_month), receiver_email]
                        append_to_csv_primary_db(data_to_write_to_primary_db)
                        print(f"Primary DB Appended for {unique_vm}\n")

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(60, 70))


                # Check if csv is not empty
                else:
                    # Checking RAM
                    print("CSV Not Empty, Checking RAM DB file names to Email the Duplicates\n")
                    # Check if Duplicate exists
                    ram_vm_found = False

                    for ram_db_vm in data_read_from_db:
                        if unique_vm[0] == ram_db_vm[0] and ram_db_vm[1].lower() == "ram":
                            ram_vm_found = True
                            break

                    if ram_vm_found:
                        print(f"Duplicate RAM thing found: {unique_vm}, sending reminder to {receiver_email}\n")
                        print("=========================================================")

                        # distinguish month and day the request was sent
                        ram_persian_month_from_db = ""
                        ram_persian_month_from_db = month_dict_persian[re.sub(r"\d|\s", "", (ram_db_vm[3]))]

                        ram_persian_day_from_db = ""
                        ram_persian_day_from_db = re.sub(r"[a-zA-Z\s]", "", ram_db_vm[3])

                        # Send message to support via email
                        sender_email = 'sina.z@abramad.com'

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'پیگیری مصرف بحرانی 50% {ram_db_vm[0]} | RAM'

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
                                <p  style="font-family: DiodrumArabic-Regular">طی سه روز گذشته درخواستی مبنی بر بررسی مصرف 50% Memory سرور <b>{ram_db_vm[0]}</b> با شماره درخواست <b>{ram_db_vm[2]}</b> <b>در تاریخ {ram_persian_day_from_db} {ram_persian_month_from_db} </b>ثبت شده است.<br>لطفا اگر موضوع را بررسی کرده اید، در نظر داشته باشید که این مشکل مجددا پیش آمده و نیازمند بررسی شما میباشد.</p>
                            '''
                        html_msg_4 = f'''
                                <p  style="font-family: DiodrumArabic-Regular">این مورد به درخواست شما ایجاد شده است و با پیش آمدن مجدد رخداد برای شما ارسال میگردد.</p>
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
                            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','),
                                            msg.as_string())

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(60, 70))

                    # If RAM VM was not found in DB
                    elif unique_vm[1].lower() != "cpu":
                        # No Duplicate Found
                        print(f"No RAM Duplicate Found, Generating New Email for {unique_vm}")
                        print("=========================================================")

                        # Increment Ticket No by one
                        int_ticket_no += 1
                        # Overwrite the file with the new data
                        with open(ticket_no_path, "w") as file:
                            file.write(str(int_ticket_no))

                        # Send message to support via email
                        sender_email = 'sina.z@abramad.com'

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'مصرف بحرانی 50% RAM | سرور {unique_vm[0]}'

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
                                        <p  style="font-family: DiodrumArabic-Regular">سرور <b>{unique_vm[0]}</b> دچار مصرف RAM <b>(بالای 50%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و در صورتی که نیاز به افزایش RAM سرور میباشد، این مورد را به اطلاع ما برسانید.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">این مورد به درخواست شما ایجاد شده است و با پیش آمدن مجدد رخداد برای شما ارسال میگردد.</p>
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
                        smtp_server = "mail.systemgroup.net"
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
                        ram_data_to_write_to_db = [unique_vm[0], "RAM", int_ticket_no,
                                                   (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, ram_data_to_write_to_db)
                        print(f"DB is appended and email sent to {receiver_email} for {unique_vm}\n")
                        data_to_write_to_primary_db = [unique_vm[0], "RAM", int_ticket_no,
                                                       (current_day + " " + current_month), receiver_email]
                        append_to_csv_primary_db(data_to_write_to_primary_db)
                        print(f"Primary DB Appended for {unique_vm}\n")

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(60, 70))

                    ##############
                    ##############

                    # Checking CPU
                    print("\nCSV Not Empty, Checking CPU DB file names to Email the Duplicates\n")
                    # Check if Duplicate exists
                    cpu_vm_found = False

                    for cpu_db_vm in data_read_from_db:
                        if unique_vm[0] == cpu_db_vm[0] and cpu_db_vm[1].lower() == "cpu":
                            cpu_vm_found = True
                            break

                    if cpu_vm_found:
                        print(f"Duplicate CPU thing found: {unique_vm}, sending reminder to {receiver_email}\n")
                        print("=========================================================")

                        # distinguish month and day the request was sent
                        cpu_persian_month_from_db = ""
                        cpu_persian_month_from_db = month_dict_persian[re.sub(r"\d|\s", "", (cpu_db_vm[3]))]

                        cpu_persian_day_from_db = ""
                        cpu_persian_day_from_db = re.sub(r"[a-zA-Z\s]", "", cpu_db_vm[3])

                        # Send message to support via email
                        sender_email = 'sina.z@abramad.com'

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'پیگیری مصرف بحرانی 50% {cpu_db_vm[0]} | CPU'

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
                                        <p  style="font-family: DiodrumArabic-Regular">طی سه روز گذشته درخواستی مبنی بر بررسی مصرف 50% CPU سرور <b>{cpu_db_vm[0]}</b> با شماره درخواست <b>{cpu_db_vm[2]}</b> <b>در تاریخ {cpu_persian_day_from_db} {cpu_persian_month_from_db} </b>ثبت شده است.<br>لطفا اگر موضوع را بررسی کرده اید، در نظر داشته باشید که این مشکل مجددا پیش آمده و نیازمند بررسی شما میباشد.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">این مورد به درخواست شما ایجاد شده است و با پیش آمدن مجدد رخداد برای شما ارسال میگردد.</p>
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
                            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','),
                                            msg.as_string())

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(60, 70))

                    # If CPU VM was not found in DB
                    elif unique_vm[1].lower() != "memory":
                        # No Duplicate Found
                        print(f"No CPU Duplicate Found, Generating New Email for {unique_vm}")
                        print("=========================================================")

                        # Increment Ticket No by one
                        int_ticket_no += 1
                        # Overwrite the file with the new data
                        with open(ticket_no_path, "w") as file:
                            file.write(str(int_ticket_no))

                        # Send message to support via email
                        sender_email = 'sina.z@abramad.com'

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'مصرف بحرانی 50% CPU | سرور {unique_vm[0]}'

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
                                        <p  style="font-family: DiodrumArabic-Regular">سرور <b>{unique_vm[0]}</b> دچار مصرف CPU <b>(بالای 50%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و در صورتی که نیاز به افزایش CPU سرور میباشد، این مورد را به اطلاع ما برسانید.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">این مورد به درخواست شما ایجاد شده است و با پیش آمدن مجدد رخداد برای شما ارسال میگردد.</p>
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
                        smtp_server = "mail.systemgroup.net"
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
                        cpu_data_to_write_to_db = [unique_vm[0], "CPU", int_ticket_no,
                                                   (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, cpu_data_to_write_to_db)
                        print(f"DB is appended and email sent to {receiver_email} for {unique_vm}\n")
                        data_to_write_to_primary_db = [unique_vm[0], "CPU", int_ticket_no,
                                                       (current_day + " " + current_month), receiver_email]
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
                    f"<p><b>RAM DB File does not exist in <b>{duplicate_check_db_path}</b> | <em>{current_day}-{current_month}</em><br>Sending mail for below vms failed:<br></b><br>RAM Problems: {unique_list_of_vms}<br><br>Unread them again.</p>",
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
        msg['Subject'] = f'مصرف بحرانی 50% منابع {current_month}-{current_day} | میرعماد '

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
            <p  style="font-family: DiodrumArabic-Regular">درخواست بررسی مصرف بحرانی 50% منابع به تیم ساپورت مشترک برای سرور های زیر انجام شد:</p>
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

        inform_email_body = html_msg_1s + html_msg_2s + html_msg_3s + html_msg_4s + html_line_break + html_msg_5s + html_line_break + html_msg_6s + html_msg_7s
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


################################# Function Calls #################################
##################################################################################


# ALaziz
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/ALaziz',
                      "ME-Resource-VIP-ALaziz-Duplicate-Check-DB.csv",
                      "mozhganfa@systemgroup.net,abbasas@systemgroup.net,saberj@systemgroup.net,hosseinmou@systemgroup.net,farahehp@systemgroup.net,iliyas@systemgroup.net,aflaki@amadehlaziz.com,s.shataei@amadehlaziz.com,mohammad.tehrani@alpagroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")

# Ramaka
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Ramak',
                      "ME-Resource-VIP-Ramak-Duplicate-Check-DB.csv",
                      "mozhganfa@systemgroup.net,abbasas@systemgroup.net,mohammadram@systemgroup.net,saberj@systemgroup.net,hosseinmou@systemgroup.net,farahehp@systemgroup.net,iliyas@systemgroup.net,yahyam@systemgroup.net,abbast@systemgroup.net,rezamo@systemgroup.net,amir.nezamabadi@ramakdairy.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# RamakBI
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/RamakBI',
                      "ME-Resource-VIP-RamakBI-Duplicate-Check-DB.csv",
                      "mozhganfa@systemgroup.net,abbasas@systemgroup.net,mohammadram@systemgroup.net,saberj@systemgroup.net,hosseinmou@systemgroup.net,farahehp@systemgroup.net,iliyas@systemgroup.net,yahyam@systemgroup.net,abbast@systemgroup.net,rezamo@systemgroup.net,amir.nezamabadi@ramakdairy.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# BehsazFarayand
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/BehsazFarayand',
                      "ME-Resource-VIP-BehsazFarayand-Duplicate-Check-DB.csv",
                      "marziehs@systemgroup.net,meysamhz@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")

# Domino
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Domino',
                      "ME-Resource-VIP-Domino-Duplicate-Check-DB.csv",
                      "mortezat@systemgroup.net,abbasas@systemgroup.net,mozhganfa@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")

# Manimas
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Manimas',
                      "ME-Resource-VIP-Manimas-Duplicate-Check-DB.csv",
                      "elnazsha@systemgroup.net,mahnazsh@systemgroup.net,sedighehh@systemgroup.net,shahlagh@systemgroup.net,zahrabazr@systemgroup.net,zahrasha@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")

# Refah
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Refah',
                      "ME-Resource-VIP-Refah-Duplicate-Check-DB.csv",
                      "behdadb@systemgroup.net,homayoonb@systemgroup.net,saberj@systemgroup.net,farnooshgh@systemgroup.net,nedapo@systemgroup.net,arshad@refah.ir,alirezaj@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")

'''
# Refah 50
resource_peak_checker_refah('SolarwindsMonitoringVIP/ME_Resource/Refah_50',
                      "ME-Resource-VIP-Refah50-Duplicate-Check-DB.csv",
                    "behdadb@systemgroup.net,homayoonb@systemgroup.net,saberj@systemgroup.net,farnooshgh@systemgroup.net,nedapo@systemgroup.net,arshad@refah.ir,alirezaj@systemgroup.net",
                        "support@abramad.com,alireza.ja@abramad.com")
'''

# Behnoush
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Behnoush',
                      "ME-Resource-VIP-Behnoush-Duplicate-Check-DB.csv",
                      "abbasas@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")

# Madiran
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Madiran',
                      "ME-Resource-VIP-Madiran-Duplicate-Check-DB.csv",
                      "samanehke@systemgroup.net, mohsenb@systemgroup.net, amirabbash@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")

# MGMT
resource_peak_checker_mgmt('SolarwindsMonitoringVIP/ME_Resource/MGMT',
                           "ME-Resource-VIP-MGMT-Duplicate-Check-DB.csv",
                           "abramadops@systemgroup.net,securityteam@abramad.com",
                           "support@abramad.com,alireza.ja@abramad.com,ehsan.h@abramad.com")

'''
# MEO MGMT
resource_peak_checker_mgmt('SolarwindsMonitoringVIP/ME_Resource/MEO_MGMT',
                      "ME-Resource-VIP-MEOMGMT-Duplicate-Check-DB.csv",
                    "zareh.k@abramad.com,saeed.k@abramad.com,openstack@systemgroup.net",
                        "abramadops@systemgroup.net,support@abramad.com,alireza.ja@abramad.com")
'''

# Behran
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Behran',
                      "ME-Resource-VIP-Behran-Duplicate-Check-DB.csv",
                      "mohsenab@systemgroup.net,arezup@systemgroup.net,mohammadjavadma@systemgroup.net,samanehke@systemgroup.net,mrezagh021@gmail.com",
                      # ,a.karimi.behran@gmail.com,mortezavi91@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# ArenaSMB
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/ArenaSMB',
                      "ME-Resource-VIP-ArenaSMB-Duplicate-Check-DB.csv",
                      "imanm@systemgroup.net,mohammadhasanp@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")

# VarzeshG (Increased 8GB of RAM)
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/VarzeshG',
                      "ME-Resource-VIP-VarzeshG-Duplicate-Check-DB.csv",
                      "ehsanf@systemgroup.net,tara.noori62@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# Delino
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Delino',
                      "ME-Resource-VIP-Delino-Duplicate-Check-DB.csv",
                      "samangh@delino.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# PYara
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/PYara',
                      "ME-Resource-VIP-PYara-Duplicate-Check-DB.csv",
                      "mahdit@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")

# Goharbafan, DenizFoam, Amin, Rastanakh
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Goharbafan',
                      "ME-Resource-VIP-Goharbafan-Duplicate-Check-DB.csv",
                      "leilab@systemgroup.net,hosseinmo@systemgroup.net,zamaniyanmohsen@gmail.com,mohamadi85@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# FanavaranPT
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/FanavaranPT',
                      "ME-Resource-VIP-FanavaranPT-Duplicate-Check-DB.csv",
                      "behzadab@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")

# HGlass
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/HGlass',
                      "ME-Resource-VIP-HGlass-Duplicate-Check-DB.csv",
                      "samineht@systemgroup.net,samanehka@systemgroup.net,it2@hamadanglass.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# ParsAmpoul
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/ParsAmpoul',
                      "ME-Resource-VIP-ParsAmpoul-Duplicate-Check-DB.csv",
                      "mortezam@systemgroup.net,it@parsampoule.ir,info@parsampoule.ir,s.heidarali@parsampoule.ir,r.davoudi@parsampoule.ir",
                      "support@abramad.com,alireza.ja@abramad.com")

# Farahi
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Farahi',
                      "ME-Resource-VIP-Farahi-Duplicate-Check-DB.csv",
                      "nedapo@systemgroup.net,fathifar@farrahicarpet.com,mfathifar@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# AliDavari
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/AliDavari',
                      "ME-Resource-VIP-AliDavari-Duplicate-Check-DB.csv",
                      "keivansh@systemgroup.net,kouroshi@systemgroup.net,acc.zandiye1402@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# JTI
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/JTI',
                      "ME-Resource-VIP-JTI-Duplicate-Check-DB.csv",
                      "javadk@systemgroup.net,raziey@systemgroup.net,samanehka@systemgroup.net,yahyam@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")

# FarhangP
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/FarhangP',
                      "ME-Resource-VIP-FarhangP-Duplicate-Check-DB.csv",
                      "elahesal@systemgroup.net,mehdij@systemgroup.net,melikaab@systemgroup.net,fatemeh.heydari.j@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# Talkhoonche
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Talkhoonche',
                      "ME-Resource-VIP-Talkhoonche-Duplicate-Check-DB.csv",
                      "behnoushb@systemgroup.net,hasanm@systemgroup.net,mahdina@systemgroup.net,tannazf@systemgroup.net,aminaziziamin@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# MadStore
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/MadStore',
                      "ME-Resource-VIP-MadStore-Duplicate-Check-DB.csv",
                      "behnazy@systemgroup.net,elnazs@systemgroup.net,javadk@systemgroup.net,narimanna@systemgroup.net,hoseinkho@systemgroup.net,hamel-a@maadiran.com,zeinali@maadiran.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# Mahallat
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Mahallat',
                      "ME-Resource-VIP-Mahallat-Duplicate-Check-DB.csv",
                      "melikaab@systemgroup.net,rasoul.zamanipour@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# PouyanTeb
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/PouyanTeb',
                      "ME-Resource-VIP-PouyanTeb-Duplicate-Check-DB.csv",
                      "mohammadtav@systemgroup.net,raziey@systemgroup.net,zakiehf@systemgroup.net,bahareh_asna@yahoo.com,shiva@pouyanholding.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# GhLorestan
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/GhLorestan',
                      "ME-Resource-VIP-GhLorestan-Duplicate-Check-DB.csv",
                      "mahsatal@systemgroup.net,zahraka@systemgroup.net,alirezakeshavarz14022@gmail.com,sadjadrefaghat@gmail.com,yosef_ph2000@yahoo.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# NMohandesi
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/NMohandesi',
                      "ME-Resource-VIP-NMohandesi-Duplicate-Check-DB.csv",
                      "ayoob1892@gmail.com,f.fathi1988@yahoo.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# Aco
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Aco',
                      "ME-Resource-VIP-Aco-Duplicate-Check-DB.csv",
                      "shadim@systemgroup.net,mohammad.khodaei@aco-battery.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# PakAra
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/PakAra',
                      "ME-Resource-VIP-PakAra-Duplicate-Check-DB.csv",
                      "fatemehmaz@systemgroup.net,javadk@systemgroup.net,p.shakiba@pakara.ir",
                      "support@abramad.com,alireza.ja@abramad.com")

# NasajiB
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/NasajiB',
                      "ME-Resource-VIP-NasajiB-Duplicate-Check-DB.csv",
                      "farnooshgh@systemgroup.net,mohammadmo@systemgroup.net,mohammadnasr@systemgroup.net,itnbco@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# Peygir
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Peygir',
                      "ME-Resource-VIP-Peygir-Duplicate-Check-DB.csv",
                      "bahramb@systemgroup.net,mahtabl@systemgroup.net,melikaab@systemgroup.net,saeedsha@systemgroup.net,samanehka@systemgroup.net,samirah@systemgroup.net,hosseinrahimi2326@gmail.com,bazzi.hamid@gmail.com,k.movahedi@paygir.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# AlirezaR
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/AlirezaR',
                      "ME-Resource-VIP-AlirezaR-Duplicate-Check-DB.csv",
                      "amin.tabarzadi@gmail.com,melikarajabali@gmail.com,mo.movahedi@gmail.com,negar.hkh1992@gmail.com,pourya.webmaster@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# MJPasand
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/MJPasand',
                      "ME-Resource-VIP-MJPasand-Duplicate-Check-DB.csv",
                      "shahbaz2020@gmail.com,sepidar.abramad@gmail.com,sokan.abramad@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# Salim
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Salim',
                      "ME-Resource-VIP-Salim-Duplicate-Check-DB.csv",
                      "navido@systemgroup.net,zahrashah@systemgroup.net,armin_firouzi@hotmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# ZahraKalbasi
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/ZahraKalbasi',
                      "ME-Resource-VIP-ZahraKalbasi-Duplicate-Check-DB.csv",
                      "golsaso@systemgroup.net,mahdina@systemgroup.net,amin.ghazvini@gmail.com,a.m.ghazvini@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")

# ShoyaSaz
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/ShoyaSaz',
                      "ME-Resource-VIP-ShoyaSaz-Duplicate-Check-DB.csv",
                      "bahramb@systemgroup.net,melikaab@systemgroup.net,miladfa@systemgroup.net,saeedsha@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")

# OmranKaloot
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/OmranKaloot',
                      "ME-Resource-VIP-OmranKaloot-Duplicate-Check-DB.csv",
                      "pmsirjan1@omrankaloot.ir,mohammadrezamir@systemgroup.net,mostafaa@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")

# ArianGe
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/ArianGe',
                      "ME-Resource-VIP-ArianGe-Duplicate-Check-DB.csv",
                      "fatemehaba@systemgroup.net,mohsenab@systemgroup.net,sorayaa@systemgroup.net,roya_shahabadi@yahoo.com",
                      "support@abramad.com,alireza.ja@abramad.com")




# TatPSA
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/TatPSA',
                      "ME-Resource-VIP-TatPSA-Duplicate-Check-DB.csv",
                      "abbasas@systemgroup.net,arashamiraskari@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Ava
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Ava',
                      "ME-Resource-VIP-Ava-Duplicate-Check-DB.csv",
                      "ebrahim.satari@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# KhatereStore
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/KhatereStore',
                      "ME-Resource-VIP-KhatereStore-Duplicate-Check-DB.csv",
                      "farnooshgh@systemgroup.net,nedapo@systemgroup.net,zeinabal@systemgroup.net,maryam.khorsandi05@gmail.com,taraneh.prt4719@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# ServatPaya
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/ServatPaya',
                      "ME-Resource-VIP-ServatPaya-Duplicate-Check-DB.csv",
                      "arezup@systemgroup.net,mitraar@systemgroup.net,neginma@systemgroup.net,mossaferin@payawm.ir",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# TizRo
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/TizRo',
                      "ME-Resource-VIP-TizRo-Duplicate-Check-DB.csv",
                      "nedapo@systemgroup.net,saharp@systemgroup.net,keihanikamran@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# NikManesh
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/NikManesh',
                      "ME-Resource-VIP-NikManesh-Duplicate-Check-DB.csv",
                      "tohids@systemgroup.net,vahidehal@systemgroup.net,mahdad.nickmanesh@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Mandegar
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Mandegar',
                      "ME-Resource-VIP-Mandegar-Duplicate-Check-DB.csv",
                      "javadk@systemgroup.net,info@shahrfarsh.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# CaspianPS
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/CaspianPS',
                      "ME-Resource-VIP-CaspianPS-Duplicate-Check-DB.csv",
                      "babadi@caspianpolymer.co,anoosheh@caspianpolymer.co,rostami@caspianpolymer.co,zeinalif365@gmail.com,amini@caspianpolymer.co,valipour@caspianpolymer.co,rostamnia@caspianpolymer.co,hasanzadeh@caspianpolymer.co,sanaz.h.mohajerani@gmail.com,elaheh.anoosheh@yahoo.com,etesami@caspianpolymer.co,khani@caspianpolymer.co",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# TalaChin
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/TalaChin',
                      "ME-Resource-VIP-TalaChin-Duplicate-Check-DB.csv",
                      "abbasas@systemgroup.net,jaberr@systemgroup.net,samineht@hamkaransystem.ir,piroozfar@yahoo.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# SazDar
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/SazDar',
                      "ME-Resource-VIP-SazDar-Duplicate-Check-DB.csv",
                      "kaveh_01@hotmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        

# HegmatanT
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/HegmatanT',
                      "ME-Resource-VIP-HegmatanT-Duplicate-Check-DB.csv",
                      "aminazi@systemgroup.net,mohammadrezayp@systemgroup.net,hegmatan.carpet@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")



# Mohsen_Store
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Mohsen_Store',
                      "ME-Resource-VIP-Mohsen_Store-Duplicate-Check-DB.csv",
                      "hasanm@systemgroup.net,saberj@systemgroup.net,farnooshgh@systemgroup.net,nedapo@systemgroup.net,sdshafiee2020@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Mandegar
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Mandegar',
                      "ME-Resource-VIP-Mandegar-Duplicate-Check-DB.csv",
                      "javadk@systemgroup.net,info@shahrfarsh.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# SGRamak
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/SGRamak',
                      "ME-Resource-VIP-SGRamak-Duplicate-Check-DB.csv",
                      "farahehp@systemgroup.net,golshan.golnari@gmail.com,hosseingm@systemgroup.net,hosseinni@systemgroup.net,payamam@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# SainaMehr
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/SainaMehr',
                      "ME-Resource-VIP-SainaMehr-Duplicate-Check-DB.csv",
                      "dariushma@systemgroup.net,elhamsb@systemgroup.net,nabi_alirezaei@bat.ir,ramona_beigi@bat.ir",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Avadis
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Avadis',
                      "ME-Resource-VIP-Avadis-Duplicate-Check-DB.csv",
                      "amirsam@systemgroup.net,mehdias@systemgroup.net,shahrzadh@systemgroup.net,avadis.khademian@gmail.com,mustafamolaeii@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# MadreseSaz
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/MadreseSaz',
                      "ME-Resource-VIP-MadreseSaz-Duplicate-Check-DB.csv",
                      "bahramb@systemgroup.net,mahtabl@systemgroup.net,melikaab@systemgroup.net,saeedsha@systemgroup.net,abassepehri563@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Hiland
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Hiland',
                      "ME-Resource-VIP-Hiland-Duplicate-Check-DB.csv",
                      "farnooshgh@systemgroup.net,nedapo@systemgroup.net,it@hilandbeauty.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# ShadiZh
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/ShadiZh',
                      "ME-Resource-VIP-ShadiZh-Duplicate-Check-DB.csv",
                      "abbasas@systemgroup.net,mohammadsho@systemgroup.net,monab@systemgroup.net,faezehsafarpour2019@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# PYara
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/PYara',
                      "ME-Resource-VIP-PYara-Duplicate-Check-DB.csv",
                      "mahdit@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# HabibZadeh
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/HabibZadeh',
                      "ME-Resource-VIP-HabibZadeh-Duplicate-Check-DB.csv",
                      "asmak@systemgroup.net,niloofarr@systemgroup.net,saharp@systemgroup.net,habibzadeh_shop@yahoo.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Sfandeqe
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Sfandeqe',
                      "ME-Resource-VIP-Sfandeqe-Duplicate-Check-DB.csv",
                      "minapo@systemgroup.net,s.zangane95@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# GolMikh
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/GolMikh',
                      "ME-Resource-VIP-GolMikh-Duplicate-Check-DB.csv",
                      "mahtabl@systemgroup.net,saeedsha@systemgroup.net,golmikh1980.co@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Farsan
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Farsan',
                      "ME-Resource-VIP-Farsan-Duplicate-Check-DB.csv",
                      "samirae@systemgroup.net,foroughp@systemgroup.net,rezameh@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Mjavardi
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Mjavardi',
                      "ME-Resource-VIP-Mjavardi-Duplicate-Check-DB.csv",
                      "mahtabl@systemgroup.net,mostafar@systemgroup.net,leilab@systemgroup.net,akramv@systemgroup.net,mortazavi@esfahanglass.com,pourzadeh@esfahanglass.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# CoolackSh
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/CoolackSh',
                      "ME-Resource-VIP-CoolackSh-Duplicate-Check-DB.csv",
                      "baharehkh@systemgroup.net,samanehmot@systemgroup.net,coolack.shargh1398@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# ArgK
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/ArgK',
                      "ME-Resource-VIP-ArgK-Duplicate-Check-DB.csv",
                      "vidata@systemgroup.net,sara.asgary29@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# GolnazOil
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/GolnazOil',
                      "ME-Resource-VIP-GolnazOil-Duplicate-Check-DB.csv",
                      "hadiss@systemgroup.net,mahtabl@systemgroup.net,sabaa@systemgroup.net,mh.golshan@gmail.com,mostafasoltani338@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# NabSteel
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/NabSteel',
                      "ME-Resource-VIP-NabSteel-Duplicate-Check-DB.csv",
                      "mojakhalaj@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# HZKahroba
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/HZKahroba',
                      "ME-Resource-VIP-HZKahroba-Duplicate-Check-DB.csv",
                      "amirmor@systemgroup.net,anitafa@systemgroup.net,arashp@systemgroup.net,farnooshgh@systemgroup.net,zaqaqi@gmail.com,ensieh.hajihosseini@hzkahroba.com,it@hzkahroba.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# ZPAlvand
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/ZPAlvand',
                      "ME-Resource-VIP-ZPAlvand-Duplicate-Check-DB.csv",
                      "moradimaryam2905@gmail.com,tina2118t@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Moniran
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Moniran',
                      "ME-Resource-VIP-Moniran-Duplicate-Check-DB.csv",
                      "homam@systemgroup.net,hoseinho@systemgroup.net,reyhanena@systemgroup.net,moniran@moniranco.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# KermanFalat
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/KermanFalat',
                      "ME-Resource-VIP-KermanFalat-Duplicate-Check-DB.csv",
                      "mahtabl@systemgroup.net,bahramb@systemgroup.net,saeedsha@systemgroup.net, kermanfalat@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# IPDMinoo
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/IPDMinoo',
                      "ME-Resource-VIP-IPDMinoo-Duplicate-Check-DB.csv",
                      "abbasas@systemgroup.net,akramz@systemgroup.net,parving@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# SGTest
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/SGTest',
                      "ME-Resource-VIP-SGTest-Duplicate-Check-DB.csv",
                      "abbaszar@systemgroup.net,jahanbakhshh@systemgroup.net,vahidrah@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# RpFath
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/RpFath',
                      "ME-Resource-VIP-RpFath-Duplicate-Check-DB.csv",
                      "zahraml@systemgroup.net,kharazm.reza@gmail.com,mohammadrezamir@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# ShahdNik
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/ShahdNik',
                      "ME-Resource-VIP-ShahdNik-Duplicate-Check-DB.csv",
                      "nedapo@systemgroup.net,alinob@systemgroup.net,arvint@systemgroup.net,elhamkasmaei@systemgroup.net,maryamvah@systemgroup.net,m.basiri@saediniaholding.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Arike
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Arike',
                      "ME-Resource-VIP-Arike-Duplicate-Check-DB.csv",
                      "zahrahanif@systemgroup.net,aminh@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Msepasi
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Msepasi',
                      "ME-Resource-VIP-Msepasi-Duplicate-Check-DB.csv",
                      "nedapo@systemgroup.net,farnooshgh@systemgroup.net,parving@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# SamStore
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/SamStore',
                      "ME-Resource-VIP-SamStore-Duplicate-Check-DB.csv",
                      "monab@systemgroup.net,farnooshgh@systemgroup.net,it@sam-home.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# KimiaGene
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/KimiaGene',
                      "ME-Resource-VIP-KimiaGene-Duplicate-Check-DB.csv",
                      "arashn@systemgroup.net,fatemehkam@systemgroup.net,barazandehamir@yahoo.com,en.ginagen@gmail.com,j.hadizadeh86@gmail.com,n.tavana@ginagen.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# ShikPoshAra
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/ShikPoshAra',
                      "ME-Resource-VIP-ShikPoshAra-Duplicate-Check-DB.csv",
                      "arashp@systemgroup.net,sarinakh@systemgroup.net,zahrahanif@systemgroup.net,nazaninsh@systemgroup.net,primocloth@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# YazdAir
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/YazdAir',
                      "ME-Resource-VIP-YazdAir-Duplicate-Check-DB.csv",
                      "amirmor@systemgroup.net,hasanm@systemgroup.net,javadk@systemgroup.net,mostafar@systemgroup.net,samineht@hamkaransystem.ir,a.ataie@yazdairways.com,jafari@yazdairways.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# GhHegmatan
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/GhHegmatan',
                      "ME-Resource-VIP-GhHegmatan-Duplicate-Check-DB.csv",
                      "bahramb@systemgroup.net,mahdiemo@systemgroup.net,melikaab@systemgroup.net,saeedsha@systemgroup.net,shamkhaniy@gmail.com,safari_public@yahoo.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Fkhorasan
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Fkhorasan',
                      "ME-Resource-VIP-Fkhorasan-Duplicate-Check-DB.csv",
                      "bahramb@systemgroup.net,hayedehr@systemgroup.net,mahtabl@systemgroup.net,saeedsha@systemgroup.net,j.shoaa@e-steel.ir",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Gsarmayeh
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Gsarmayeh',
                      "ME-Resource-VIP-Gsarmayeh-Duplicate-Check-DB.csv",
                      "navido@systemgroup.net,sh.navidi@platin.capital",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# SPKRahAhan
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/SPKRahAhan',
                      "ME-Resource-VIP-SPKRahAhan-Duplicate-Check-DB.csv",
                      "hamidfa@systemgroup.net,neginma@systemgroup.net,sanazz@hooshayand.ir,ravankhahalireza62@gmail.com,parinazb@hooshayand.ir",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# AkbariSadaf
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/AkbariSadaf',
                      "ME-Resource-VIP-AkbariSadaf-Duplicate-Check-DB.csv",
                      "elnazkh@systemgroup.net,nazaninsh@systemgroup.net,rahelehk@systemgroup.net,sadafshariatii@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# MsgLidoma
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/MsgLidoma',
                      "ME-Resource-VIP-MsgLidoma-Duplicate-Check-DB.csv",
                      "imanj@systemgroup.net,mohammadrezap@systemgroup.net,saeedya@systemgroup.net,rezaeiamehdi54@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# BATPars
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/BATPars',
                      "ME-Resource-VIP-BATPars-Duplicate-Check-DB.csv",
                      "nabi_alirezaei@bat.ir",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# TaminA
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/TaminA',
                      "ME-Resource-VIP-TaminA-Duplicate-Check-DB.csv",
                      "hamedd@systemgroup.net,mojtabasafi@systemgroup.net,majidabediidcard@gmail.com,info@taminatie.com,s.sh6861@yahoo.com,mohammad.hadi7580@yahoo.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# MTS
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/MTS',
                      "ME-Resource-VIP-MTS-Duplicate-Check-DB.csv",
                      "alira@systemgroup.net,behzadab@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# ArtaJS
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/ArtaJS',
                      "ME-Resource-VIP-ArtaJS-Duplicate-Check-DB.csv",
                      "shadim@systemgroup.net,m.khodayi2007@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# ParsianSaba
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/ParsianSaba',
                      "ME-Resource-VIP-ParsianSaba-Duplicate-Check-DB.csv",
                      "mohammadrezap@systemgroup.net,pegahb@systemgroup.net,shahlagh@systemgroup.net,amirhadadi12@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# YazdCable
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/YazdCable',
                      "ME-Resource-VIP-YazdCable-Duplicate-Check-DB.csv",
                      "behnazy@systemgroup.net,mahmoudna@systemgroup.net,raziey@systemgroup.net,sadafz@systemgroup.net,office@yazdcable.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        



# Msirjan
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Msirjan',
                      "ME-Resource-VIP-Msirjan-Duplicate-Check-DB.csv",
                      "mohammadrezamir@systemgroup.net,mostafaa@systemgroup.net,md.ghaseminejad@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# KooshaTrade
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/KooshaTrade',
                      "ME-Resource-VIP-KooshaTrade-Duplicate-Check-DB.csv",
                      "mohammadsho@systemgroup.net,samineht@hamkaransystem.ir,shival@systemgroup.net,hamidemand1@hotmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Bdehghan
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Bdehghan',
                      "ME-Resource-VIP-Bdehghan-Duplicate-Check-DB.csv",
                      "golsaso@systemgroup.net,hengamehm@systemgroup.net,mahdina@systemgroup.net,it@arshehkar.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Lidco
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Lidco',
                      "ME-Resource-VIP-Lidco-Duplicate-Check-DB.csv",
                      "saeedsha@systemgroup.net,melikaab@systemgroup.net,bahramb@systemgroup.net,info@lidco.ir",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# MaskanBHR
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/MaskanBHR',
                      "ME-Resource-VIP-MaskanBHR-Duplicate-Check-DB.csv",
                      "arashj@systemgroup.net,imanj@systemgroup.net,kami_198181@yahoo.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# SamanIR
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/SamanIR',
                      "ME-Resource-VIP-SamanIR-Duplicate-Check-DB.csv",
                      "sinad@systemgroup.net,javadk@systemgroup.net,farahani1318@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Mozayan
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Mozayan',
                      "ME-Resource-VIP-Mozayan-Duplicate-Check-DB.csv",
                      "masoumekh@systemgroup.net,sadafz@systemgroup.net,it@iranrover.ir",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# JahadNasr
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/JahadNasr',
                      "ME-Resource-VIP-JahadNasr-Duplicate-Check-DB.csv",
                      "behzadab@systemgroup.net,golsab@systemgroup.net,arttapart@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# ATHamkaran
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/ATHamkaran',
                      "ME-Resource-VIP-ATHamkaran-Duplicate-Check-DB.csv",
                      "nargesf@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# SepahanP
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/SepahanP',
                      "ME-Resource-VIP-SepahanP-Duplicate-Check-DB.csv",
                      "abbasas@systemgroup.net,mohammadsho@systemgroup.net,samineht@hamkaransystem.ir,letra.ir@yahoo.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Dorna
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Dorna',
                      "ME-Resource-VIP-Dorna-Duplicate-Check-DB.csv",
                      "mohammadsho@systemgroup.net,mortezat@systemgroup.net,admin@dorna-co.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# OfoghAlborz
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/OfoghAlborz',
                      "ME-Resource-VIP-OfoghAlborz-Duplicate-Check-DB.csv",
                      "zakiehf@systemgroup.net,javadk@systemgroup.net,samineht@hamkaransystem.ir,a.vahdat@ofoghealborz.com,m.zeyghami@ofoghealborz.com,m.naeini@ofoghealborz.com,m.hajikarim@ofoghealborz.com,o.daei@ofoghelaborz.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# FoladZanjan
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/FoladZanjan',
                      "ME-Resource-VIP-FoladZanjan-Duplicate-Check-DB.csv",
                      "fatemepo@systemgroup.net,saharp@systemgroup.net,saeedya@systemgroup.net,armanmoradii@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Mohsen
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Mohsen',
                      "ME-Resource-VIP-Mohsen-Duplicate-Check-DB.csv",
                      "nedapo@systemgroup.net,saberj@systemgroup.net,sarinakh@systemgroup.net,zahrahanif@systemgroup.net,mfathifar@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Mirzaei
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Mirzaei',
                      "ME-Resource-VIP-Mirzaei-Duplicate-Check-DB.csv",
                      "bahramb@systemgroup.net,azhansaftab@yahoo.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Sepand
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Sepand',
                      "ME-Resource-VIP-Sepand-Duplicate-Check-DB.csv",
                      "omid_hosseini@hotmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# BehanSar
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/BehanSar',
                      "ME-Resource-VIP-BehanSar-Duplicate-Check-DB.csv",
                      "saharp@systemgroup.net,packzad@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# DadeSaman
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/DadeSaman',
                      "ME-Resource-VIP-DadeSaman-Duplicate-Check-DB.csv",
                      "dssnovinit@gmail.com,em1362@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# BahmanBF
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/BahmanBF',
                      "ME-Resource-VIP-BahmanBF-Duplicate-Check-DB.csv",
                      "mostafar@systemgroup.net,zahrabag@systemgroup.net,delavaran@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# RayanIdea
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/RayanIdea',
                      "ME-Resource-VIP-RayanIdea-Duplicate-Check-DB.csv",
                      "orders@hi-kish.ir,k.hassanzadeh.k@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# NovinIdeh
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/NovinIdeh',
                      "ME-Resource-VIP-NovinIdeh-Duplicate-Check-DB.csv",
                      "m.faghihian@novinleather.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# NasajiArdakan
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/NasajiArdakan',
                      "ME-Resource-VIP-NasajiArdakan-Duplicate-Check-DB.csv",
                      "mahdik@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# HamrahT
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/HamrahT',
                      "ME-Resource-VIP-HamrahT-Duplicate-Check-DB.csv",
                      "fahimegh@systemgroup.net,farnooshgh@systemgroup.net,nedapo@systemgroup.net,m2hweb86@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# NTKiavan
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/NTKiavan',
                      "ME-Resource-VIP-NTKiavan-Duplicate-Check-DB.csv",
                      "leilab@systemgroup.net,mahdina@systemgroup.net,meysamza@systemgroup.net,ehsanrj@systemgroup.net,info@kamalibm.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# PayaCaspian
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/PayaCaspian',
                      "ME-Resource-VIP-PayaCaspian-Duplicate-Check-DB.csv",
                      "melikaab@systemgroup.net,saeedsha@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# SSourin
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/SSourin',
                      "ME-Resource-VIP-SSourin-Duplicate-Check-DB.csv",
                      "amirsam@systemgroup.net,fazilats@systemgroup.net,moghadam.sanaye@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# MJYazdi
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/MJYazdi',
                      "ME-Resource-VIP-MJYazdi-Duplicate-Check-DB.csv",
                      "mahsa.khmv94@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# SamanPardaz
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/SamanPardaz',
                      "ME-Resource-VIP-SamanPardaz-Duplicate-Check-DB.csv",
                      "behzadn@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Asefi
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Asefi',
                      "ME-Resource-VIP-Asefi-Duplicate-Check-DB.csv",
                      "shahab.abdollahzadeh@sefimail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# DadeSaman
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/DadeSaman',
                      "ME-Resource-VIP-DadeSaman-Duplicate-Check-DB.csv",
                      "dssnovinit@gmail.com,em1362@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Shouder
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Shouder',
                      "ME-Resource-VIP-Shouder-Duplicate-Check-DB.csv",
                      "abbasas@systemgroup.net,minae@systemgroup.net,it@shouder.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# SamanPardaz
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/SamanPardaz',
                      "ME-Resource-VIP-SamanPardaz-Duplicate-Check-DB.csv",
                      "behzadn@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# ZubinT
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/ZubinT',
                      "ME-Resource-VIP-ZubinT-Duplicate-Check-DB.csv",
                      "mehdifo@systemgroup.net,hasanm@systemgroup.net,info@svg.ir",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# ShikPoshAra
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/ShikPoshAra',
                      "ME-Resource-VIP-ShikPoshAra-Duplicate-Check-DB.csv",
                      "arashp@systemgroup.net,mohammadnasr@systemgroup.net,sarinakh@systemgroup.net,zahrahanif@systemgroup.net,primocloth@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# SanatAghigh
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/SanatAghigh',
                      "ME-Resource-VIP-SanatAghigh-Duplicate-Check-DB.csv",
                      "niroosanat.aghigh2@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# DamavandPG
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/DamavandPG',
                      "ME-Resource-VIP-DamavandPG-Duplicate-Check-DB.csv",
                      "javadk@systemgroup.net,FereshtehH@systemgroup.net,MaryamHe@systemgroup.net,info@damavandpg.co.ir,amir.j1896@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com,sheida.r@abramad.com")
                        


# CaspianPS
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/CaspianPS',
                      "ME-Resource-VIP-CaspianPS-Duplicate-Check-DB.csv",
                      "babadi@caspianpolymer.co,ehsanesee04444@gmail.com,anoosheh@caspianpolymer.co,rostami@caspianpolymer.co,zeinalif365@gmail.com,amini@caspianpolymer.co,moghadasi@caspianpolymer.co,valipour@caspianpolymer.co,rostamnia@caspianpolymer.co,hasanzadeh@caspianpolymer.co,elaheh.anoosheh@yahoo.com,etesami@caspianpolymer.co,khani@caspianpolymer.co",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Alvan
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Alvan',
                      "ME-Resource-VIP-Alvan-Duplicate-Check-DB.csv",
                      "maryamab@systemgroup.net,mostafar@systemgroup.net,fallah@alvansabet.ir,rahimifard@alvansabet.ir",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# HaliStar
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/HaliStar',
                      "ME-Resource-VIP-HaliStar-Duplicate-Check-DB.csv",
                      "raziey@systemgroup.net,rezameh@systemgroup.net,shahramn@systemgroup.net,es.farid69@yahoo.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Suravajin
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Suravajin',
                      "ME-Resource-VIP-Suravajin-Duplicate-Check-DB.csv",
                      "aminh@systemgroup.net,maryamab@systemgroup.net,moozhanz@systemgroup.net,royae@systemgroup.net,parisaka@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# BalanSanat
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/BalanSanat',
                      "ME-Resource-VIP-BalanSanat-Duplicate-Check-DB.csv",
                      "saeedmog@systemgroup.net,sedighehh@systemgroup.net,shahlagh@systemgroup.net,balansanat@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# FonoonAsr
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/FonoonAsr',
                      "ME-Resource-VIP-FonoonAsr-Duplicate-Check-DB.csv",
                      "samineht@hamkaransystem.ir,m.hamedani@m-f-agroup.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# PayamSh
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/PayamSh',
                      "ME-Resource-VIP-PayamSh-Duplicate-Check-DB.csv",
                      "javadk@systemgroup.net,leylaf@systemgroup.net,samanehka@systemgroup.net,p.sh.shemirani@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Hoonam
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Hoonam',
                      "ME-Resource-VIP-Hoonam-Duplicate-Check-DB.csv",
                      "mohammadhasanp@systemgroup.net,mozhdeht@systemgroup.net,nedat@systemgroup.net,ali.abdeveis@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# TajCeram
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/TajCeram',
                      "ME-Resource-VIP-TajCeram-Duplicate-Check-DB.csv",
                      "keyvans@systemgroup.net,leilab@systemgroup.net,mahdiehka@systemgroup.net,reza.bozorgzad@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Network
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Network',
                      "ME-Resource-VIP-Network-Duplicate-Check-DB.csv",
                      "networkteam@abramad.com,mehdi.a@abramad.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Hallaji
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Hallaji',
                      "ME-Resource-VIP-Hallaji-Duplicate-Check-DB.csv",
                      "javadk@systemgroup.net,meysamza@systemgroup.net,mozhdehm@systemgroup.net,hallaji.akbar13@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# SilisBoloor
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/SilisBoloor',
                      "ME-Resource-VIP-SilisBoloor-Duplicate-Check-DB.csv",
                      "aidaz@systemgroup.net,amirmor@systemgroup.net,amirhoseink@systemgroup.net,leilab@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Alvan
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Alvan',
                      "ME-Resource-VIP-Alvan-Duplicate-Check-DB.csv",
                      "fallah@alvansabet.ir,rahimifard@alvansabet.ir",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# SatCompany
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/SatCompany',
                      "ME-Resource-VIP-SatCompany-Duplicate-Check-DB.csv",
                      "aliabd@systemgroup.net,maryambe@systemgroup.net,reyhanehs@systemgroup.net,a.toam@satcompany.ir",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Mboosak
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Mboosak',
                      "ME-Resource-VIP-Mboosak-Duplicate-Check-DB.csv",
                      "m.hormati@outlook.com,behnoushk@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# DamIranian
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/DamIranian',
                      "ME-Resource-VIP-DamIranian-Duplicate-Check-DB.csv",
                      "melikaab@systemgroup.net,bahramb@systemgroup.net,saeedsha@systemgroup.net,ashayershop@gmail.com,ashayershop@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# NamaNoor
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/NamaNoor',
                      "ME-Resource-VIP-NamaNoor-Duplicate-Check-DB.csv",
                      "abbaszar@systemgroup.net,elnazs@systemgroup.net,narimanna@systemgroup.net,v.aghabozorgi@gmail.com ",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Zangan
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Zangan',
                      "ME-Resource-VIP-Zangan-Duplicate-Check-DB.csv",
                      "alirezapa@systemgroup.net,mad.machine.nazari@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Moghavasazi
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Moghavasazi',
                      "ME-Resource-VIP-Moghavasazi-Duplicate-Check-DB.csv",
                      "samineht@hamkaransystem.ir,moghavasazishargh@yahoo.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# AlborzNiroo
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/AlborzNiroo',
                      "ME-Resource-VIP-AlborzNiroo-Duplicate-Check-DB.csv",
                      "saharp@systemgroup.net,a.ahmadi@alborzniroo.ir",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# DaneshAmuzi
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/DaneshAmuzi',
                      "ME-Resource-VIP-DaneshAmuzi-Duplicate-Check-DB.csv",
                      "haniehs@systemgroup.net,somayehy@systemgroup.net,usia58@chmail.ir",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Tizro
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Tizro',
                      "ME-Resource-VIP-Tizro-Duplicate-Check-DB.csv",
                      "faezehv@systemgroup.net,mahsav@systemgroup.net,nedapo@systemgroup.net,keihanikamran@gmail.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# Confluence
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/Confluence',
                      "ME-Resource-VIP-Confluence-Duplicate-Check-DB.csv",
                      "alireza.mah@abramad.com,mariak@systemgroup.net,ehsan.h@abramad.com,saeed.r@abramad.com,mehdi.a@abramad.com",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# RayanPars
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/RayanPars',
                      "ME-Resource-VIP-RayanPars-Duplicate-Check-DB.csv",
                      "saharp@systemgroup.net,raziey@systemgroup.net,minae@systemgroup.net  ,s.rajabimanesh@sanatrayanpars.ir",
                      "support@abramad.com,alireza.ja@abramad.com")
                        


# RasamSystem
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/RasamSystem',
                      "ME-Resource-VIP-RasamSystem-Duplicate-Check-DB.csv",
                      "alirezan@systemgroup.net,javadk@systemgroup.net",
                      "support@abramad.com,alireza.ja@abramad.com")
                        
