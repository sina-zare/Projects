import os
def decrypt(cipher_text, key):
    plain_text = ""
    for i in range(len(cipher_text)):
        char = cipher_text[i]
        plain_int = ord(char) - key
        plain_text += chr(plain_int)
    return plain_text
def low_disk_checker(mail_server, username, password, folder_path, db_file_path, receiver_email, cc_email):

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
    import re

    def is_csv_empty(file_path):
        return os.path.getsize(file_path) == 0

    def append_to_csv(file_path, data):
        with open(file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(data)

    def append_to_csv_primary_db(data):
        with open("C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/Primary-Database/Disk-Issue-Database.csv",'a', newline='') as file:
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

    def find_next_character(string, substring):
        start_index = string.find(substring)
        if start_index != -1:
            next_character = string[start_index + len(substring)]
            return next_character
        else:
            return None


    def server_name_taker(text):
        words = text.lower().split()
        on_index = words.index("on")
        if "vip" in text.lower():
            return (words[on_index + 3]).replace('',"")
        else:
            return words[on_index + 1]


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
    mail = imaplib.IMAP4_SSL(mail_server)
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
        body = ""

        if email_message.is_multipart():
            # Iterate over email parts
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = email_message.get_payload(decode=True).decode()

        # Save email as dict in list
        emails.append({"subject": subject, "body": body})

        # Save email as dict in list
        # emails.append(subject)

    list_of_vms = []

    # Take VM Names and Drive Letters
    # We used tupples instead of lists because they are hashable and immutable so we can use them in set() to remove duplicates
    for email in emails:
        list_of_vms.append((server_name_taker(email["subject"]), find_next_character(email["body"], "Volume: ")))

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

    duplicate_check_db_path = f"C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/ME-Disk-VIP/{db_file_path}"
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

                    # Send new email to support
                    if unique_vm[1].lower() == "c":
                        print(f"Drive C of {unique_vm[0]} Full, sending email to Abramad Support")
                        print("================================================")

                        # Increment Ticket NO by one
                        int_ticket_no += 1
                        # Overwrite the file with the new data
                        with open(ticket_no_path, "w") as file:
                            file.write(str(int_ticket_no))

                        # Send message to Support via email
                        sender_email = 'sina.z@abramad.com'
                        receiver_email_abramad_support = "support@abramad.com" + "," + receiver_email
                        cc_email_abramad_support = " alireza.ja@abramad.com"

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = "support@abramad.com" + "," + receiver_email
                        msg['CC'] = " alireza.ja@abramad.com"
                        msg['Subject'] = f'پر شدن فضای درایو {unique_vm[1]} | سرور {unique_vm[0]}'

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
                                        <p  style="font-family: DiodrumArabic-Regular">درایو <b>{unique_vm[1]}</b> سرور <b>{unique_vm[0]}</b> پر شده است، لطفا نسبت به آزاد نمودن فضا و پاکسازی فایل های قابل حذف، اقدام نمایید.<p/>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع میتواند باعث down شدن سرویس مشترک گردد.</p>
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
                        smtp_server = mail_server
                        smtp_port = 587
                        smtp_username = username
                        smtp_password = password

                        # Send email function
                        with smtplib.SMTP(smtp_server, smtp_port) as server:
                            server.starttls()
                            server.login(smtp_username, smtp_password)
                            server.sendmail(sender_email, receiver_email_abramad_support.split(",") + cc_email_abramad_support.split(','), msg.as_string())

                        # Append data to db
                        data_to_write_to_db = [unique_vm[0], unique_vm[1], int_ticket_no,
                                               (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, data_to_write_to_db)
                        print(f"Email sent to Abramad Support for {unique_vm[0]}\n")
                        data_to_write_to_primary_db = [(f"{unique_vm[0]} on drive '{unique_vm[1]}'"), int_ticket_no,(current_day + " " + current_month), receiver_email]
                        append_to_csv_primary_db(data_to_write_to_primary_db)
                        print(f"Primary DB Appended for {unique_vm[0]}\n")

                    # Send new email to customer support
                    elif unique_vm[1].lower() != "c":

                        print(f"CSV Empty, Generating New Email for {unique_vm[0]}")
                        print("================================================")
                        # Increment Ticket NO by one
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
                        msg['Subject'] = f'پر شدن فضای درایو {unique_vm[1]} | سرور {unique_vm[0]}'

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
                                    <p  style="font-family: DiodrumArabic-Regular">درایو <b>{unique_vm[1]}</b> سرور <b>{unique_vm[0]}</b> پر شده است، لطفا نسبت به آزاد نمودن فضا و پاکسازی فایل های قابل حذف، اقدام نمایید.<p/>
                                '''
                        html_msg_4 = f'''
                                    <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع بزودی به عدم توانایی بکاپ گیری مشترک منجر خواهد شد یا در شرایط بدتر میتواند باعث down شدن سرویس ایشان گردد.</p>
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
                        smtp_server = mail_server
                        smtp_port = 587
                        smtp_username = username
                        smtp_password = password

                        # Send email function
                        with smtplib.SMTP(smtp_server, smtp_port) as server:
                            server.starttls()
                            server.login(smtp_username, smtp_password)
                            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())

                        # Append data to db
                        data_to_write_to_db = [unique_vm[0], unique_vm[1], int_ticket_no, (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, data_to_write_to_db)
                        print(f"DB is appended and email sent to {receiver_email} for {unique_vm[0]}\n")
                        data_to_write_to_primary_db = [(f"{unique_vm[0]} on drive '{unique_vm[1]}'"), int_ticket_no,
                                                       (current_day + " " + current_month), receiver_email]
                        append_to_csv_primary_db(data_to_write_to_primary_db)
                        print(f"Primary DB Appended for {unique_vm[0]}\n")


                # Check if csv is not empty
                else:
                    print("CSV Not Empty, Checking DB file names to Email the Duplicates\n")
                    # Check if Duplicate exists
                    vm_found = False

                    for db_vm in data_read_from_db:
                        if (unique_vm[0] == db_vm[0]):
                            vm_found = True
                            break

                    if vm_found  and (unique_vm[1].lower() != "c"):
                        print(f"Duplicate found: {unique_vm[0]}, sending reminder to {receiver_email}\n")
                        print("=========================================================")


                        # distinguish month and day the request was sent
                        persian_month_from_db = ""
                        persian_month_from_db = month_dict_persian[re.sub(r"\d|\s", "", (db_vm[3]))]

                        persian_day_from_db = ""
                        persian_day_from_db = re.sub(r"[a-zA-Z\s]", "", db_vm[3])

                        # Send message to customer support via email
                        sender_email = 'sina.z@abramad.com'


                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'پیگیری پر شدن فضای درایو {db_vm[1]} | سرور {db_vm[0]}'


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
                                        <p  style="font-family: DiodrumArabic-Regular">طی سه روز گذشته درخواستی مبنی بر بررسی پر شدن درایو <b>{db_vm[1]}</b> سرور <b>{db_vm[0]}</b> با شماره درخواست <b>{db_vm[2]}</b> <b>در تاریخ {persian_day_from_db} {persian_month_from_db} </b>ثبت شده است.<br>لطفا اگر موضوع را بررسی کرده اید، در نظر داشته باشید که این مشکل مجددا پیش آمده و نیازمند بررسی شما میباشد.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">همانطور که میدانید، با توجه به وضعیت فعلی سرور، این موضوع بزودی به عدم توانایی بکاپ گیری مشترک منجر خواهد شد یا در شرایط بدتر میتواند باعث down شدن سرویس ایشان گردد.</p>
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
                            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())


                    # Sending reminder to abramad support
                    elif vm_found and (unique_vm[1].lower() == "c"):
                        print(f"Duplicate found: {unique_vm[0]}, sending reminder to Abramad support\n")
                        print("=========================================================")

                        # distinguish month and day the request was sent
                        persian_month_from_db = ""
                        persian_month_from_db = month_dict_persian[re.sub(r"\d|\s", "", (db_vm[3]))]

                        persian_day_from_db = ""
                        persian_day_from_db = re.sub(r"[a-zA-Z\s]", "", db_vm[3])

                        # Send message to Hesam ina via email
                        sender_email = 'sina.z@abramad.com'
                        receiver_email_abramad_support = "support@abramad.com" + "," + receiver_email
                        cc_email_abramad_support = " alireza.ja@abramad.com"

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = "support@abramad.com" + "," + receiver_email
                        msg['CC'] = " alireza.ja@abramad.com"
                        msg['Subject'] = f'پیگیری پر شدن فضای درایو {db_vm[1]} | سرور {db_vm[0]}'

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
                                        <p  style="font-family: DiodrumArabic-Regular">طی سه روز گذشته درخواستی مبنی بر بررسی پر شدن درایو <b>{db_vm[1]}</b> سرور <b>{db_vm[0]}</b> با شماره درخواست <b>{db_vm[2]}</b> <b>در تاریخ {persian_day_from_db} {persian_month_from_db} </b>ثبت شده است.<br>لطفا اگر موضوع را بررسی کرده اید، در نظر داشته باشید که این مشکل مجددا پیش آمده و نیازمند بررسی شما میباشد.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">همانطور که میدانید، با توجه به وضعیت فعلی سرور، این موضوع میتواند باعث down شدن سرویس ایشان گردد.</p>
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
                            server.sendmail(sender_email, receiver_email_abramad_support.split(",") + cc_email_abramad_support.split(','), msg.as_string())

                    # No Duplicate found in db
                    else:

                        if unique_vm[1].lower() == "c":
                            # No Duplicate Found and drive is C Send new email to support
                            print(f"Drive C of {unique_vm[0]} Full, sending email to Abramad Support")
                            print("================================================")

                            # Increment Ticket NO by one
                            int_ticket_no += 1
                            # Overwrite the file with the new data
                            with open(ticket_no_path, "w") as file:
                                file.write(str(int_ticket_no))

                            # Send message to Support via email
                            sender_email = 'sina.z@abramad.com'
                            receiver_email_abramad_support = "support@abramad.com" + "," + receiver_email
                            cc_email_abramad_support = " alireza.ja@abramad.com"


                            # Create a multipart message object
                            msg = MIMEMultipart()
                            msg['From'] = sender_email
                            msg['To'] = "support@abramad.com" + "," + receiver_email
                            msg['CC'] = " alireza.ja@abramad.com"
                            msg['Subject'] = f'پر شدن فضای درایو {unique_vm[1]} | سرور {unique_vm[0]}'

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
                                            <p  style="font-family: DiodrumArabic-Regular">درایو <b>{unique_vm[1]}</b> سرور <b>{unique_vm[0]}</b> پر شده است، لطفا نسبت به آزاد نمودن فضا و پاکسازی فایل های قابل حذف، اقدام نمایید.<p/>
                                        '''
                            html_msg_4 = f'''
                                            <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع میتواند باعث down شدن سرویس مشترک گردد.</p>
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
                            smtp_server = mail_server
                            smtp_port = 587
                            smtp_username = username
                            smtp_password = password

                            # Send email function
                            with smtplib.SMTP(smtp_server, smtp_port) as server:
                                server.starttls()
                                server.login(smtp_username, smtp_password)
                                server.sendmail(sender_email, receiver_email_abramad_support.split(",") + cc_email_abramad_support.split(','), msg.as_string())

                            # Append data to db
                            data_to_write_to_db = [unique_vm[0], unique_vm[1], int_ticket_no,
                                                   (current_day + " " + current_month)]
                            append_to_csv(duplicate_check_db_path, data_to_write_to_db)
                            print(f"Email sent to Abramad Support for {unique_vm[0]}\n")
                            data_to_write_to_primary_db = [(f"{unique_vm[0]} on drive '{unique_vm[1]}'"), int_ticket_no,
                                                           (current_day + " " + current_month), receiver_email]
                            append_to_csv_primary_db(data_to_write_to_primary_db)
                            print(f"Primary DB Appended for {unique_vm[0]}\n")


                        else:
                            # No Duplicate Found and drive is not C Send email to support
                            print(f"No Duplicate Found, Generating New Email for {unique_vm[0]}")
                            print("=========================================================")

                            # Increment Ticket NO by one
                            int_ticket_no += 1
                            # Overwrite the file with the new data
                            with open(ticket_no_path, "w") as file:
                                file.write(str(int_ticket_no))

                            # Send message to Hesam ina via email
                            sender_email = 'sina.z@abramad.com'

                            # Create a multipart message object
                            msg = MIMEMultipart()
                            msg['From'] = sender_email
                            msg['To'] = receiver_email
                            msg['CC'] = cc_email
                            msg['Subject'] = f'پر شدن فضای درایو {unique_vm[1]} | سرور {unique_vm[0]}'

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
                                            <p  style="font-family: DiodrumArabic-Regular">درایو <b>{unique_vm[1]}</b> سرور <b>{unique_vm[0]}</b> پر شده است، لطفا نسبت به آزاد نمودن فضا و پاکسازی فایل های قابل حذف، اقدام نمایید.<p/>
                                        '''
                            html_msg_4 = f'''
                                            <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع بزودی به عدم توانایی بکاپ گیری مشترک منجر خواهد شد یا در شرایط بدتر میتواند باعث down شدن سرویس ایشان گردد.</p>
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
                            smtp_server = mail_server
                            smtp_port = 587
                            smtp_username = username
                            smtp_password = password

                            # Send email function
                            with smtplib.SMTP(smtp_server, smtp_port) as server:
                                server.starttls()
                                server.login(smtp_username, smtp_password)
                                server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())

                            # Append data to db
                            data_to_write_to_db = [unique_vm[0], unique_vm[1], int_ticket_no, (current_day + " " + current_month)]
                            append_to_csv(duplicate_check_db_path, data_to_write_to_db)
                            print(f"DB is appended and email sent to {receiver_email} for {unique_vm[0]}\n")
                            data_to_write_to_primary_db = [(f"{unique_vm[0]} on drive '{unique_vm[1]}'"), int_ticket_no,
                                                           (current_day + " " + current_month), receiver_email]
                            append_to_csv_primary_db(data_to_write_to_primary_db)
                            print(f"Primary DB Appended for {unique_vm[0]}\n")

            except FileNotFoundError:
                # If file was not found
                # Send Email to King
                # Create a multipart message object
                msg = MIMEMultipart()
                msg['From'] = 'sina.z@abramad.com'
                msg['To'] = 'sina.z@abramad.com'
                msg['Subject'] = f'Error in ME Disk VIP DB | {current_day}-{current_month} | {customer_name}'

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
        msg['Subject'] = f' پر شدن فضای درایو {current_month}-{current_day} '

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
            <p  style="font-family: DiodrumArabic-Regular">درخواست پاکسازی دیسک سرور های زیر در خصوص پر بودن فضای دیسک به تیم support مشترک ارسال شد.</p>
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
def low_disk_checker_mgmt(mail_server, username, password, folder_path, db_file_path, receiver_email, cc_email):

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
    import re

    def is_csv_empty(file_path):
        return os.path.getsize(file_path) == 0

    def append_to_csv(file_path, data):
        with open(file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(data)

    def append_to_csv_primary_db(data):
        with open("C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/Primary-Database/Disk-Issue-Database.csv",'a', newline='') as file:
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

    def find_next_character(string, substring):
        start_index = string.find(substring)
        if start_index != -1:
            next_character = string[start_index + len(substring)]
            return next_character
        else:
            return None

    def server_name_taker(text):
        words = text.lower().split()
        on_index = words.index("on")
        if "vip" in text.lower():
            return (words[on_index + 3]).replace('',"")
        else:
            return words[on_index + 1]


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
    mail = imaplib.IMAP4_SSL(mail_server)
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
        body = ""

        if email_message.is_multipart():
            # Iterate over email parts
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = email_message.get_payload(decode=True).decode()

        # Save email as dict in list
        emails.append({"subject": subject, "body": body})

        # Save email as dict in list
        # emails.append(subject)

    list_of_vms = []

    # Take VM Names and Drive Letters
    # We used tupples instead of lists because they are hashable and immutable so we can use them in set() to remove duplicates
    for email in emails:
        list_of_vms.append((server_name_taker(email["subject"]), find_next_character(email["body"], "Volume: ")))

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

    duplicate_check_db_path = f"C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/ME-Disk-VIP/{db_file_path}"
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

                    # Send new email to abramad operation team

                    print(f"CSV Empty, Generating New Email for {unique_vm[0]}")
                    print("================================================")
                    # Increment Ticket NO by one
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
                    msg['Subject'] = f'پر شدن فضای درایو {unique_vm[1]} | سرور {unique_vm[0]}'

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
                                <p  style="font-family: DiodrumArabic-Regular">درایو <b>{unique_vm[1]}</b> سرور <b>{unique_vm[0]}</b> پر شده است، لطفا نسبت به آزاد نمودن فضا و پاکسازی فایل های قابل حذف، اقدام نمایید.<p/>
                            '''
                    html_msg_4 = f'''
                                <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع میتواند باعث down شدن سرویس گردد.</p>
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
                    smtp_server = mail_server
                    smtp_port = 587
                    smtp_username = username
                    smtp_password = password

                    # Send email function
                    with smtplib.SMTP(smtp_server, smtp_port) as server:
                        server.starttls()
                        server.login(smtp_username, smtp_password)
                        server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())

                    # Append data to db
                    data_to_write_to_db = [unique_vm[0], unique_vm[1], int_ticket_no, (current_day + " " + current_month)]
                    append_to_csv(duplicate_check_db_path, data_to_write_to_db)
                    print(f"DB is appended and email sent to {receiver_email} for {unique_vm[0]}\n")
                    data_to_write_to_primary_db = [(f"{unique_vm[0]} on drive '{unique_vm[1]}'"), int_ticket_no,
                                                   (current_day + " " + current_month), receiver_email]
                    append_to_csv_primary_db(data_to_write_to_primary_db)
                    print(f"Primary DB Appended for {unique_vm[0]}\n")


                # Check if csv is not empty
                else:
                    print("CSV Not Empty, Checking DB file names to Email the Duplicates\n")
                    # Check if Duplicate exists
                    vm_found = False

                    for db_vm in data_read_from_db:
                        if (unique_vm[0] == db_vm[0]):
                            vm_found = True
                            break

                    if vm_found:
                        print(f"Duplicate found: {unique_vm[0]}, sending reminder to {receiver_email}\n")
                        print("=========================================================")


                        # distinguish month and day the request was sent
                        persian_month_from_db = ""
                        persian_month_from_db = month_dict_persian[re.sub(r"\d|\s", "", (db_vm[3]))]

                        persian_day_from_db = ""
                        persian_day_from_db = re.sub(r"[a-zA-Z\s]", "", db_vm[3])

                        # Send message to customer support via email
                        sender_email = 'sina.z@abramad.com'


                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'پیگیری پر شدن فضای درایو {db_vm[1]} | سرور {db_vm[0]}'


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
                                        <p  style="font-family: DiodrumArabic-Regular">طی سه روز گذشته درخواستی مبنی بر بررسی پر شدن درایو <b>{db_vm[1]}</b> سرور <b>{db_vm[0]}</b> با شماره درخواست <b>{db_vm[2]}</b> <b>در تاریخ {persian_day_from_db} {persian_month_from_db} </b>ثبت شده است.<br>لطفا اگر موضوع را بررسی کرده اید، در نظر داشته باشید که این مشکل مجددا پیش آمده و نیازمند بررسی شما میباشد.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">همانطور که میدانید، با توجه به وضعیت فعلی سرور، این موضوع بزودی میتواند باعث down شدن سرویس گردد.</p>
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
                            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())



                    else:
                        # No Duplicate Found
                        print(f"No Duplicate Found, Generating New Email for {unique_vm[0]}")
                        print("=========================================================")

                        # Increment Ticket NO by one
                        int_ticket_no += 1
                        # Overwrite the file with the new data
                        with open(ticket_no_path, "w") as file:
                            file.write(str(int_ticket_no))

                        # Send message to Hesam ina via email
                        sender_email = 'sina.z@abramad.com'

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'پر شدن فضای درایو {unique_vm[1]} | سرور {unique_vm[0]}'

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
                                        <p  style="font-family: DiodrumArabic-Regular">درایو <b>{unique_vm[1]}</b> سرور <b>{unique_vm[0]}</b> پر شده است، لطفا نسبت به آزاد نمودن فضا و پاکسازی فایل های قابل حذف، اقدام نمایید.<p/>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع میتواند باعث down شدن سرویس گردد.</p>
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
                        smtp_server = mail_server
                        smtp_port = 587
                        smtp_username = username
                        smtp_password = password

                        # Send email function
                        with smtplib.SMTP(smtp_server, smtp_port) as server:
                            server.starttls()
                            server.login(smtp_username, smtp_password)
                            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())

                        # Append data to db
                        data_to_write_to_db = [unique_vm[0], unique_vm[1], int_ticket_no, (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, data_to_write_to_db)
                        print(f"DB is appended and email sent to {receiver_email} for {unique_vm[0]}\n")
                        data_to_write_to_primary_db = [(f"{unique_vm[0]} on drive '{unique_vm[1]}'"), int_ticket_no,
                                                       (current_day + " " + current_month), receiver_email]
                        append_to_csv_primary_db(data_to_write_to_primary_db)
                        print(f"Primary DB Appended for {unique_vm[0]}\n")

            except FileNotFoundError:
                # If file was not found
                # Send Email to King
                # Create a multipart message object
                msg = MIMEMultipart()
                msg['From'] = 'sina.z@abramad.com'
                msg['To'] = 'sina.z@abramad.com'
                msg['Subject'] = f'Error in ME Disk VIP DB | {current_day}-{current_month} | {customer_name}'

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
        msg['Subject'] = f' پر شدن فضای درایو {current_month}-{current_day} '

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
            <p  style="font-family: DiodrumArabic-Regular">درخواست پاکسازی دیسک سرور های زیر در خصوص پر بودن فضای دیسک به تیم AbramadOps ارسال شد.</p>
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

def low_disk_checker_ramakdb(mail_server, username, password, folder_path, db_file_path, receiver_email, cc_email):

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
    import re

    def is_csv_empty(file_path):
        return os.path.getsize(file_path) == 0

    def append_to_csv(file_path, data):
        with open(file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(data)

    def append_to_csv_primary_db(data):
        with open("C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/Primary-Database/Disk-Issue-Database.csv",'a', newline='') as file:
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

    def find_next_character(string, substring):
        start_index = string.find(substring)
        if start_index != -1:
            next_character = string[start_index + len(substring)]
            return next_character
        else:
            return None


    def server_name_taker(text):
        words = text.lower().split()
        on_index = words.index("on")
        if "vip" in text.lower():
            return (words[on_index + 3]).replace('',"")
        else:
            return words[on_index + 1]


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
    mail = imaplib.IMAP4_SSL(mail_server)
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
        body = ""

        if email_message.is_multipart():
            # Iterate over email parts
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = email_message.get_payload(decode=True).decode()

        # Save email as dict in list
        emails.append({"subject": subject, "body": body})

        # Save email as dict in list
        # emails.append(subject)

    list_of_vms = []

    # Take VM Names and Drive Letters
    # We used tupples instead of lists because they are hashable and immutable so we can use them in set() to remove duplicates
    for email in emails:
        list_of_vms.append((server_name_taker(email["subject"]), find_next_character(email["body"], "Volume: ")))

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

    duplicate_check_db_path = f"C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/ME-Disk-VIP/{db_file_path}"
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

                    # Send new email to support
                    if unique_vm[1].lower() == "c":
                        print(f"Drive C of {unique_vm[0]} Full, sending email to Abramad Support")
                        print("================================================")

                        # Increment Ticket NO by one
                        int_ticket_no += 1
                        # Overwrite the file with the new data
                        with open(ticket_no_path, "w") as file:
                            file.write(str(int_ticket_no))

                        # Send message to Support via email
                        sender_email = 'sina.z@abramad.com'
                        receiver_email_abramad_support = "support@abramad.com" + "," + receiver_email
                        cc_email_abramad_support = " alireza.ja@abramad.com"

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = "support@abramad.com" + "," + receiver_email
                        msg['CC'] = " alireza.ja@abramad.com"
                        msg['Subject'] = f'پر شدن بیش از 85 درصد فضای درایو {unique_vm[1]} | سرور {unique_vm[0]}'

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
                                        <p  style="font-family: DiodrumArabic-Regular">درایو <b>{unique_vm[1]}</b> سرور <b>{unique_vm[0]}</b> کمتر از پانزده درصد فضای خالی دارد، لطفا نسبت به آزاد نمودن فضا و پاکسازی فایل های قابل حذف، اقدام نمایید.<p/>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع میتواند باعث down شدن سرویس مشترک گردد.</p>
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
                        smtp_server = mail_server
                        smtp_port = 587
                        smtp_username = username
                        smtp_password = password

                        # Send email function
                        with smtplib.SMTP(smtp_server, smtp_port) as server:
                            server.starttls()
                            server.login(smtp_username, smtp_password)
                            server.sendmail(sender_email, receiver_email_abramad_support.split(",") + cc_email_abramad_support.split(','), msg.as_string())

                        # Append data to db
                        data_to_write_to_db = [unique_vm[0], unique_vm[1], int_ticket_no,
                                               (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, data_to_write_to_db)
                        print(f"Email sent to Abramad Support for {unique_vm[0]}\n")
                        data_to_write_to_primary_db = [(f"{unique_vm[0]} on drive '{unique_vm[1]}'"), int_ticket_no,(current_day + " " + current_month), receiver_email]
                        append_to_csv_primary_db(data_to_write_to_primary_db)
                        print(f"Primary DB Appended for {unique_vm[0]}\n")

                    # Send new email to customer support
                    elif unique_vm[1].lower() != "c":

                        print(f"CSV Empty, Generating New Email for {unique_vm[0]}")
                        print("================================================")
                        # Increment Ticket NO by one
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
                        msg['Subject'] = f'پر شدن بیش از 85 درصد فضای درایو {unique_vm[1]} | سرور {unique_vm[0]}'

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
                                    <p  style="font-family: DiodrumArabic-Regular">درایو <b>{unique_vm[1]}</b> سرور <b>{unique_vm[0]}</b> کمتر از پانزده درصد فضای خالی دارد، لطفا نسبت به آزاد نمودن فضا و پاکسازی فایل های قابل حذف، اقدام نمایید.<p/>
                                '''
                        html_msg_4 = f'''
                                    <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع بزودی به عدم توانایی بکاپ گیری مشترک منجر خواهد شد یا در شرایط بدتر میتواند باعث down شدن سرویس ایشان گردد.</p>
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
                        smtp_server = mail_server
                        smtp_port = 587
                        smtp_username = username
                        smtp_password = password

                        # Send email function
                        with smtplib.SMTP(smtp_server, smtp_port) as server:
                            server.starttls()
                            server.login(smtp_username, smtp_password)
                            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())

                        # Append data to db
                        data_to_write_to_db = [unique_vm[0], unique_vm[1], int_ticket_no, (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, data_to_write_to_db)
                        print(f"DB is appended and email sent to {receiver_email} for {unique_vm[0]}\n")
                        data_to_write_to_primary_db = [(f"{unique_vm[0]} on drive '{unique_vm[1]}'"), int_ticket_no,
                                                       (current_day + " " + current_month), receiver_email]
                        append_to_csv_primary_db(data_to_write_to_primary_db)
                        print(f"Primary DB Appended for {unique_vm[0]}\n")


                # Check if csv is not empty
                else:
                    print("CSV Not Empty, Checking DB file names to Email the Duplicates\n")
                    # Check if Duplicate exists
                    vm_found = False

                    for db_vm in data_read_from_db:
                        if (unique_vm[0] == db_vm[0]):
                            vm_found = True
                            break

                    if vm_found  and (unique_vm[1].lower() != "c"):
                        print(f"Duplicate found: {unique_vm[0]}, sending reminder to {receiver_email}\n")
                        print("=========================================================")


                        # distinguish month and day the request was sent
                        persian_month_from_db = ""
                        persian_month_from_db = month_dict_persian[re.sub(r"\d|\s", "", (db_vm[3]))]

                        persian_day_from_db = ""
                        persian_day_from_db = re.sub(r"[a-zA-Z\s]", "", db_vm[3])

                        # Send message to customer support via email
                        sender_email = 'sina.z@abramad.com'


                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = receiver_email
                        msg['CC'] = cc_email
                        msg['Subject'] = f'پیگیری پر شدن بیش از 85 درصد فضای درایو {db_vm[1]} | سرور {db_vm[0]}'


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
                                        <p  style="font-family: DiodrumArabic-Regular">طی سه روز گذشته درخواستی مبنی بر بررسی پر شدن بیش از 85 درصد درایو <b>{db_vm[1]}</b> سرور <b>{db_vm[0]}</b> با شماره درخواست <b>{db_vm[2]}</b> <b>در تاریخ {persian_day_from_db} {persian_month_from_db} </b>ثبت شده است.<br>لطفا اگر موضوع را بررسی کرده اید، در نظر داشته باشید که این مشکل مجددا پیش آمده و نیازمند بررسی شما میباشد.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">همانطور که میدانید، با توجه به وضعیت فعلی سرور، این موضوع بزودی به عدم توانایی بکاپ گیری مشترک منجر خواهد شد یا در شرایط بدتر میتواند باعث down شدن سرویس ایشان گردد.</p>
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
                            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())


                    # Sending reminder to abramad support
                    elif vm_found and (unique_vm[1].lower() == "c"):
                        print(f"Duplicate found: {unique_vm[0]}, sending reminder to Abramad support\n")
                        print("=========================================================")

                        # distinguish month and day the request was sent
                        persian_month_from_db = ""
                        persian_month_from_db = month_dict_persian[re.sub(r"\d|\s", "", (db_vm[3]))]

                        persian_day_from_db = ""
                        persian_day_from_db = re.sub(r"[a-zA-Z\s]", "", db_vm[3])

                        # Send message to Hesam ina via email
                        sender_email = 'sina.z@abramad.com'
                        receiver_email_abramad_support = "support@abramad.com" + "," + receiver_email
                        cc_email_abramad_support = " alireza.ja@abramad.com"

                        # Create a multipart message object
                        msg = MIMEMultipart()
                        msg['From'] = sender_email
                        msg['To'] = "support@abramad.com" + "," + receiver_email
                        msg['CC'] = " alireza.ja@abramad.com"
                        msg['Subject'] = f'پیگیری پر شدن بیش از 85 درصد فضای درایو {db_vm[1]} | سرور {db_vm[0]}'

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
                                        <p  style="font-family: DiodrumArabic-Regular">طی سه روز گذشته درخواستی مبنی بر بررسی پر شدن بیش از 85 درصد درایو <b>{db_vm[1]}</b> سرور <b>{db_vm[0]}</b> با شماره درخواست <b>{db_vm[2]}</b> <b>در تاریخ {persian_day_from_db} {persian_month_from_db} </b>ثبت شده است.<br>لطفا اگر موضوع را بررسی کرده اید، در نظر داشته باشید که این مشکل مجددا پیش آمده و نیازمند بررسی شما میباشد.</p>
                                    '''
                        html_msg_4 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">همانطور که میدانید، با توجه به وضعیت فعلی سرور، این موضوع میتواند باعث down شدن سرویس ایشان گردد.</p>
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
                            server.sendmail(sender_email, receiver_email_abramad_support.split(",") + cc_email_abramad_support.split(','), msg.as_string())

                    # No Duplicate found in db
                    else:

                        if unique_vm[1].lower() == "c":
                            # No Duplicate Found and drive is C Send new email to support
                            print(f"Drive C of {unique_vm[0]} Full, sending email to Abramad Support")
                            print("================================================")

                            # Increment Ticket NO by one
                            int_ticket_no += 1
                            # Overwrite the file with the new data
                            with open(ticket_no_path, "w") as file:
                                file.write(str(int_ticket_no))

                            # Send message to Support via email
                            sender_email = 'sina.z@abramad.com'
                            receiver_email_abramad_support = "support@abramad.com" + "," + receiver_email
                            cc_email_abramad_support = " alireza.ja@abramad.com"


                            # Create a multipart message object
                            msg = MIMEMultipart()
                            msg['From'] = sender_email
                            msg['To'] = "support@abramad.com" + "," + receiver_email
                            msg['CC'] = " alireza.ja@abramad.com"
                            msg['Subject'] = f'پر شدن بیش از 85 درصد فضای درایو {unique_vm[1]} | سرور {unique_vm[0]}'

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
                                            <p  style="font-family: DiodrumArabic-Regular">درایو <b>{unique_vm[1]}</b> سرور <b>{unique_vm[0]}</b> کمتر از پانزده درصد فضای خالی دارد، لطفا نسبت به آزاد نمودن فضا و پاکسازی فایل های قابل حذف، اقدام نمایید.<p/>
                                        '''
                            html_msg_4 = f'''
                                            <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع میتواند باعث down شدن سرویس مشترک گردد.</p>
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
                            smtp_server = mail_server
                            smtp_port = 587
                            smtp_username = username
                            smtp_password = password

                            # Send email function
                            with smtplib.SMTP(smtp_server, smtp_port) as server:
                                server.starttls()
                                server.login(smtp_username, smtp_password)
                                server.sendmail(sender_email, receiver_email_abramad_support.split(",") + cc_email_abramad_support.split(','), msg.as_string())

                            # Append data to db
                            data_to_write_to_db = [unique_vm[0], unique_vm[1], int_ticket_no,
                                                   (current_day + " " + current_month)]
                            append_to_csv(duplicate_check_db_path, data_to_write_to_db)
                            print(f"Email sent to Abramad Support for {unique_vm[0]}\n")
                            data_to_write_to_primary_db = [(f"{unique_vm[0]} on drive '{unique_vm[1]}'"), int_ticket_no,
                                                           (current_day + " " + current_month), receiver_email]
                            append_to_csv_primary_db(data_to_write_to_primary_db)
                            print(f"Primary DB Appended for {unique_vm[0]}\n")


                        else:
                            # No Duplicate Found and drive is not C Send email to support
                            print(f"No Duplicate Found, Generating New Email for {unique_vm[0]}")
                            print("=========================================================")

                            # Increment Ticket NO by one
                            int_ticket_no += 1
                            # Overwrite the file with the new data
                            with open(ticket_no_path, "w") as file:
                                file.write(str(int_ticket_no))

                            # Send message to Hesam ina via email
                            sender_email = 'sina.z@abramad.com'

                            # Create a multipart message object
                            msg = MIMEMultipart()
                            msg['From'] = sender_email
                            msg['To'] = receiver_email
                            msg['CC'] = cc_email
                            msg['Subject'] = f'پر شدن بیش از 85 درصد فضای درایو {unique_vm[1]} | سرور {unique_vm[0]}'

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
                                            <p  style="font-family: DiodrumArabic-Regular">درایو <b>{unique_vm[1]}</b> سرور <b>{unique_vm[0]}</b> کمتر از پانزده درصد فضای خالی دارد، لطفا نسبت به آزاد نمودن فضا و پاکسازی فایل های قابل حذف، اقدام نمایید.<p/>
                                        '''
                            html_msg_4 = f'''
                                            <p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، با توجه به وضعیت فعلی سرور، این موضوع بزودی به عدم توانایی بکاپ گیری مشترک منجر خواهد شد یا در شرایط بدتر میتواند باعث down شدن سرویس ایشان گردد.</p>
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
                            smtp_server = mail_server
                            smtp_port = 587
                            smtp_username = username
                            smtp_password = password

                            # Send email function
                            with smtplib.SMTP(smtp_server, smtp_port) as server:
                                server.starttls()
                                server.login(smtp_username, smtp_password)
                                server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())

                            # Append data to db
                            data_to_write_to_db = [unique_vm[0], unique_vm[1], int_ticket_no, (current_day + " " + current_month)]
                            append_to_csv(duplicate_check_db_path, data_to_write_to_db)
                            print(f"DB is appended and email sent to {receiver_email} for {unique_vm[0]}\n")
                            data_to_write_to_primary_db = [(f"{unique_vm[0]} on drive '{unique_vm[1]}'"), int_ticket_no,
                                                           (current_day + " " + current_month), receiver_email]
                            append_to_csv_primary_db(data_to_write_to_primary_db)
                            print(f"Primary DB Appended for {unique_vm[0]}\n")

            except FileNotFoundError:
                # If file was not found
                # Send Email to King
                # Create a multipart message object
                msg = MIMEMultipart()
                msg['From'] = 'sina.z@abramad.com'
                msg['To'] = 'sina.z@abramad.com'
                msg['Subject'] = f'Error in ME Disk VIP DB | {current_day}-{current_month} | {customer_name}'

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
        msg['Subject'] = f' پر شدن بیش از 85 درصد فضای درایو {current_month}-{current_day} '

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
            <p  style="font-family: DiodrumArabic-Regular">درخواست پاکسازی دیسک سرور های زیر در خصوص پر بودن بیش از 85 درصد فضای دیسک به تیم support مشترک ارسال شد.</p>
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





############ Function Calls #############
#########################################


# MGMT
low_disk_checker_mgmt(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/MGMT',
    "ME-Disk-VIP-MGMT-Duplicate-Check-DB.csv",
    "abramadops@abramad.com,securityteam@abramad.com",
    "support@abramad.com,alireza.ja@abramad.com,ehsan.h@abramad.com"
)




# AmadehLaziz
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/ALaziz',
    "ME-Disk-VIP-ALaziz-Duplicate-Check-DB.csv",
    "mozhganfa@systemgroup.net,abbasas@systemgroup.net,aflaki@amadehlaziz.com,s.shataei@amadehlaziz.com,saberj@systemgroup.net,hosseinmou@systemgroup.net,farahehp@systemgroup.net,iliyas@systemgroup.net,mohammad.tehrani@alpagroup.net",
    "support@abramad.com,alireza.ja@abramad.com"
)




# Delino
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Delino',
    "ME-Disk-VIP-Delino-Duplicate-Check-DB.csv",
    "samangh@delino.com",
    "support@abramad.com,alireza.ja@abramad.com"
)




# Domino
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Domino',
    "ME-Disk-VIP-Domino-Duplicate-Check-DB.csv",
    "mortezat@systemgroup.net,abbasas@systemgroup.net,mozhganfa@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com"
)




# Madiran
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Madiran',
    "ME-Disk-VIP-Madiran-Duplicate-Check-DB.csv",
    "samanehke@systemgroup.net, mohsenb@systemgroup.net, amirabbash@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com"
)




# Mohsen Store
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Mohsen_Store',
    "ME-Disk-VIP-MohsenStore-Duplicate-Check-DB.csv",
    "hasanm@systemgroup.net,saberj@systemgroup.net,farnooshgh@systemgroup.net,nedapo@systemgroup.net,sdshafiee2020@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com"
)





# Ramak
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Ramak',
    "ME-Disk-VIP-Ramak-Duplicate-Check-DB.csv",
    "mozhganfa@systemgroup.net,abbasas@systemgroup.net,mohammadram@systemgroup.net,saberj@systemgroup.net,hosseinmou@systemgroup.net,farahehp@systemgroup.net,iliyas@systemgroup.net,yahyam@systemgroup.net,abbast@systemgroup.net,rezamo@systemgroup.net,amir.nezamabadi@ramakdairy.com",
    "support@abramad.com,alireza.ja@abramad.com"
)





# Ramak DB
low_disk_checker_ramakdb(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/RamakDB',
    "ME-Disk-VIP-RamakDB-Duplicate-Check-DB.csv",
    "mozhganfa@systemgroup.net,abbasas@systemgroup.net,mohammadram@systemgroup.net,saberj@systemgroup.net,hosseinmou@systemgroup.net,farahehp@systemgroup.net,iliyas@systemgroup.net,yahyam@systemgroup.net,abbast@systemgroup.net,rezamo@systemgroup.net,amir.nezamabadi@ramakdairy.com",
    "support@abramad.com,alireza.ja@abramad.com"
)





# Refah
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Refah',
    "ME-Disk-VIP-Refah-Duplicate-Check-DB.csv",
    "behdadb@systemgroup.net,homayoonb@systemgroup.net,saberj@systemgroup.net,farnooshgh@systemgroup.net,nedapo@systemgroup.net,arshad@refah.ir,alirezaj@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com"
)





# TatPSA
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/TatPSA',
    "ME-Disk-VIP-TatPSA-Duplicate-Check-DB.csv",
    "abbasas@systemgroup.net,akramz@systemgroup.net,mozhganfa@systemgroup.net,arashamiraskari@gmail.com,arashaskari@mail.com",
    "support@abramad.com,alireza.ja@abramad.com"
)





# ViraSystem
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/ViraSystem',
    "ME-Disk-VIP-ViraSystem-Duplicate-Check-DB.csv",
    "kamranf@systemgroup.net,jamalr@systemgroup.net,elhamsae@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com"
)





# RasamSystem
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/RasamSystem',
    "ME-Disk-VIP-RasamSystem-Duplicate-Check-DB.csv",
    "alirezan@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com"
)





# Manimas
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Manimas',
    "ME-Disk-VIP-Manimas-Duplicate-Check-DB.csv",
    "elnazsha@systemgroup.net,mahnazsh@systemgroup.net,sedighehh@systemgroup.net,shahlagh@systemgroup.net,zahrabazr@systemgroup.net,zahrasha@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com"
)




# Farsan
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Farsan',
    "ME-Disk-VIP-Farsan-Duplicate-Check-DB.csv",
    "samirae@systemgroup.net,foroughp@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com"
)


# Behnoush
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Behnoush',
    "ME-Disk-VIP-Behnoush-Duplicate-Check-DB.csv",
    "abbasas@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# Behran
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Behran',
    "ME-Disk-VIP-Behran-Duplicate-Check-DB.csv",
    "arezup@systemgroup.net,mohsenab@systemgroup.net,mohammadjavadma@systemgroup.net,samanehke@systemgroup.net,a.karimi.behran@gmail.com,mortezavi91@gmail.com,mrezagh021@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")





# ParsAmpoul
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/ParsAmpoul',
    "ME-Disk-VIP-ParsAmpoul-Duplicate-Check-DB.csv",
    "mortezam@systemgroup.net,it@parsampoule.ir,info@parsampoule.ir,s.heidarali@parsampoule.ir,r.davoudi@parsampoule.ir",
    "support@abramad.com,alireza.ja@abramad.com")



#           Rastanakh, Amin, DenizFoam, Goharbafan
# support:  hamed dehestani, mohsen abdolhamidi, mohammadjavad majidi, esfehan(deniz), leila_mehrajii@yahoo.com

# Goharbafan, DenizFoam, Amin, Rastanakh
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Goharbafan',
    "ME-Disk-VIP-Goharbafan-Duplicate-Check-DB.csv",
    "leilab@systemgroup.net,hosseinmo@systemgroup.net,zamaniyanmohsen@gmail.com,mohamadi85@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")





# IranParast
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/IranParast',
    "ME-Disk-VIP-IranParast-Duplicate-Check-DB.csv",
    "neginma@systemgroup.net,javadk@systemgroup.net,jobs@sepidmoj.com",
    "support@abramad.com,alireza.ja@abramad.com")





# MJavardi
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/MJavardi',
    "ME-Disk-VIP-MJavardi-Duplicate-Check-DB.csv",
    "mahtabl@systemgroup.net,mostafar@systemgroup.net,hosseinmo@systemgroup.net,hengamehm@systemgroup.net,golsaso@systemgroup.net,mortazavi@esfahanglass.com",
    "support@abramad.com,alireza.ja@abramad.com")





# RahkarSG
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/RahkarSG',
    "ME-Disk-VIP-RahkarSG-Duplicate-Check-DB.csv",
    "fakhredinm@systemgroup.net,faezehb@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")





# MorvaridSh
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/MorvaridSh',
    "ME-Disk-VIP-MorvaridSh-Duplicate-Check-DB.csv",
    "mohammadrezag@systemgroup.net,alitavalaei74@gmail.com,info@sepcogroup.co",
    "support@abramad.com,alireza.ja@abramad.com")





# NTKiavan
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/NTKiavan',
    "ME-Disk-VIP-NTKiavan-Duplicate-Check-DB.csv",
    "mahdina@systemgroup.net,meysamza@systemgroup.net,info@kamalibm.com",
    "support@abramad.com,alireza.ja@abramad.com")





# ArenaSMB
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/ArenaSMB',
    "ME-Disk-VIP-ArenaSMB-Duplicate-Check-DB.csv",
    "imanm@systemgroup.net,mohammadhasanp@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")





# MehrAvar
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/MehrAvar',
    "ME-Disk-VIP-MehrAvar-Duplicate-Check-DB.csv",
    "peyman.rahime@gmail.com,m.b.gharb@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")





# SatCompany
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/SatCompany',
    "ME-Disk-VIP-SatCompany-Duplicate-Check-DB.csv",
    "nastaranza@systemgroup.net,a.toam@satcompany.ir",
    "support@abramad.com,alireza.ja@abramad.com")





# ZKalbasi
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/ZKalbasi',
    "ME-Disk-VIP-ZKalbasi-Duplicate-Check-DB.csv",
    "golsaso@systemgroup.net,mahdina@systemgroup.net,amin.ghazvini@gmail.com,a.m.ghazvini@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")





# AkbariSadaf
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/AkbariSadaf',
    "ME-Disk-VIP-AkbariSadaf-Duplicate-Check-DB.csv",
    "elnazkh@systemgroup.net,nazaninsh@systemgroup.net,rahelehk@systemgroup.net,zahrahz@systemgroup.net,zahrahanif@systemgroup.net,zeinabal@systemgroup.net,sadafshariatii@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")





# Karshenasan
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Karshenasan',
    "ME-Disk-VIP-Karshenasan-Duplicate-Check-DB.csv",
    "mehdifo@systemgroup.net,amirch@systemgroup.net,kkdtbz@gmail.com,kkdtbz@yahoo.com",
    "support@abramad.com,alireza.ja@abramad.com")





# EchoStar
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/EchoStar',
    "ME-Disk-VIP-EchoStar-Duplicate-Check-DB.csv",
    "shival@systemgroup.net,javadk@systemgroup.net,fatemeozlati@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")





# BehsazFarayand
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/BehsazFarayand',
    "ME-Disk-VIP-BehsazFarayand-Duplicate-Check-DB.csv",
    "marziehs@systemgroup.net,meysamhz@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")





# AtlasTalaei
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/AtlasTalaei',
    "ME-Disk-VIP-AtlasTalaei-Duplicate-Check-DB.csv",
    "fatemehos@systemgroup.net,mohsenab@systemgroup.net,mohammad.taghdirifar@gmail.com,omid.baghaei640@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")





# AmitisShi
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/AmitisShi',
    "ME-Disk-VIP-AmitisShi-Duplicate-Check-DB.csv",
    "abbasas@systemgroup.net,samanehka@systemgroup.net,aria_kazemi@me.com,farnamkazemi@gmail.com,saeidmotamedi65@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")





# AriyanGe
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/ArianGe',
    "ME-Disk-VIP-AriyanGe-Duplicate-Check-DB.csv",
    "fatemehaba@systemgroup.net,mohsenab@systemgroup.net,sorayaa@systemgroup.net,roya_shahabadi@yahoo.com,raamin.a@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")





# SamanAir
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/SamanAir',
    "ME-Disk-VIP-SamanAir-Duplicate-Check-DB.csv",
    "hoseinkho@systemgroup.net,e.zeighamfard@saman.aero",
    "support@abramad.com,alireza.ja@abramad.com")





# BDehghan
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/BDehghan',
    "ME-Disk-VIP-BDehghan-Duplicate-Check-DB.csv",
    "shayanro@systemgroup.net,mehditm@systemgroup.net,mahdina@systemgroup.net,jahanbakhshh@systemgroup.net,hengamehm@systemgroup.net,golsaso@systemgroup.net,akramv@systemgroup.net,it@arshehkar.com",
    "support@abramad.com,alireza.ja@abramad.com")





# Rahpoo
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Rahpoo',
    "ME-Disk-VIP-Rahpoo-Duplicate-Check-DB.csv",
    "aminh@systemgroup.net,arezoono@systemgroup.net,farnooshgh@systemgroup.net,sorayaa@systemgroup.net,a.zeidabadi@hamnavardgroup.ir",
    "support@abramad.com,alireza.ja@abramad.com")






# HGlass
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/HGlass',
    "ME-Disk-VIP-HGlass-Duplicate-Check-DB.csv",
    "samineht@systemgroup.net,samanehka@systemgroup.net,it2@hamadanglass.com",
    "support@abramad.com,alireza.ja@abramad.com")






# GolnazOil
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/GolnazOil',
    "ME-Disk-VIP-GolnazOil-Duplicate-Check-DB.csv",
    "saharp@systemgroup.net,melikaas@systemgroup.net,hadiss@systemgroup.net,mahsav@systemgroup.net,mahtabl@systemgroup.net,mh.golshan@gmail.com,mostafasoltani338@ gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")




# HamGaman
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/HamGaman',
    "ME-Disk-VIP-HamGaman-Duplicate-Check-DB.csv",
    "shookaz@systemgroup.net,hosseinv@systemgroup.net,it@zabolcement.com",
    "support@abramad.com,alireza.ja@abramad.com")




# AhLorestan
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/AhLorestan',
    "ME-Disk-VIP-AhLorestan-Duplicate-Check-DB.csv",
    "raziey@systemgroup.net,samanehka@systemgroup.net,samineht@systemgroup.net,ali.malekshahian@gmail.com,smehrabnia@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")





# YazdAir
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/YazdAir',
    "ME-Disk-VIP-YazdAir-Duplicate-Check-DB.csv",
    "amirmor@systemgroup.net,hasanm@systemgroup.net,mostafar@systemgroup.net,a.ataie@yazdairways.com,jafari@yazdairways.com",
    "support@abramad.com,alireza.ja@abramad.com")





# IranDentists
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/IranDentists',
    "ME-Disk-VIP-IranDentists-Duplicate-Check-DB.csv",
    "farzadskf@yahoo.com",
    "support@abramad.com,alireza.ja@abramad.com")




# Zubin
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Zubin',
    "ME-Disk-VIP-Zubin-Duplicate-Check-DB.csv",
    "mehdifo@systemgroup.net,farhad_pakpour@yahoo.com",
    "support@abramad.com,alireza.ja@abramad.com")





'''
# Nan Sahar NOT DEPLOYED YET
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/JTI',
    "ME-Disk-VIP-JTI-Duplicate-Check-DB.csv",
    "javadk@systemgroup.net,raziey@systemgroup.net,samanehka@systemgroup.net,yahyam@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com"
)
'''




# Farahi
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Farahi',
    "ME-Disk-VIP-Farahi-Duplicate-Check-DB.csv",
    "nedapo@systemgroup.net,fathifar@farrahicarpet.com,mfathifar@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# AliDavari
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/AliDavari',
    "ME-Disk-VIP-AliDavari-Duplicate-Check-DB.csv",
    "keivansh@systemgroup.net,kouroshi@systemgroup.net,acc.zandiye1402@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# JTI
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/JTI',
    "ME-Disk-VIP-JTI-Duplicate-Check-DB.csv",
    "javadk@systemgroup.net,raziey@systemgroup.net,samanehka@systemgroup.net,yahyam@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# FarhangP
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/FarhangP',
    "ME-Disk-VIP-FarhangP-Duplicate-Check-DB.csv",
    "elahesal@systemgroup.net,mehdij@systemgroup.net,melikaab@systemgroup.net,fatemeh.heydari.j@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Talkhoonche
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Talkhoonche',
    "ME-Disk-VIP-Talkhoonche-Duplicate-Check-DB.csv",
    "behnoushb@systemgroup.net,hasanm@systemgroup.net,mahdina@systemgroup.net,tannazf@systemgroup.net,aminaziziamin@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# MadStore
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/MadStore',
    "ME-Disk-VIP-MadStore-Duplicate-Check-DB.csv",
    "behnazy@systemgroup.net,elnazs@systemgroup.net,javadk@systemgroup.net,narimanna@systemgroup.net,hoseinkho@systemgroup.net,hamel-a@maadiran.com,zeinali@maadiran.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Mahallat
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Mahallat',
    "ME-Disk-VIP-Mahallat-Duplicate-Check-DB.csv",
    "melikaab@systemgroup.net,rasoul.zamanipour@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# PouyanTeb
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/PouyanTeb',
    "ME-Disk-VIP-PouyanTeb-Duplicate-Check-DB.csv",
    "mohammadtav@systemgroup.net,raziey@systemgroup.net,zakiehf@systemgroup.net,bahareh_asna@yahoo.com,shiva@pouyanholding.com",
    "support@abramad.com,alireza.ja@abramad.com")



# GhLorestan
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/GhLorestan',
    "ME-Disk-VIP-GhLorestan-Duplicate-Check-DB.csv",
    "mahsatal@systemgroup.net,zahraka@systemgroup.net,alirezakeshavarz14022@gmail.com,sadjadrefaghat@gmail.com,yosef_ph2000@yahoo.com",
    "support@abramad.com,alireza.ja@abramad.com")



# NMohandesi
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/NMohandesi',
    "ME-Disk-VIP-NMohandesi-Duplicate-Check-DB.csv",
    "ayoob1892@gmail.com,f.fathi1988@yahoo.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Aco
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Aco',
    "ME-Disk-VIP-Aco-Duplicate-Check-DB.csv",
    "shadim@systemgroup.net,mohammad.khodaei@aco-battery.com",
    "support@abramad.com,alireza.ja@abramad.com")



# PakAra
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/PakAra',
    "ME-Disk-VIP-PakAra-Duplicate-Check-DB.csv",
    "fatemehmaz@systemgroup.net,javadk@systemgroup.net,p.shakiba@pakara.ir",
    "support@abramad.com,alireza.ja@abramad.com")



# NasajiB
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/NasajiB',
    "ME-Disk-VIP-NasajiB-Duplicate-Check-DB.csv",
    "farnooshgh@systemgroup.net,mohammadmo@systemgroup.net,itnbco@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Peygir
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Peygir',
    "ME-Disk-VIP-Peygir-Duplicate-Check-DB.csv",
    "bahramb@systemgroup.net,mahtabl@systemgroup.net,melikaab@systemgroup.net,saeedsha@systemgroup.net,samanehka@systemgroup.net,samirah@systemgroup.net,hosseinrahimi2326@gmail.com,bazzi.hamid@gmail.com,k.movahedi@paygir.com",
    "support@abramad.com,alireza.ja@abramad.com")



# AlirezaR
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/AlirezaR',
    "ME-Disk-VIP-AlirezaR-Duplicate-Check-DB.csv",
    "amin.tabarzadi@gmail.com,melikarajabali@gmail.com,mo.movahedi@gmail.com,negar.hkh1992@gmail.com,pourya.webmaster@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# MJPasand
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/MJPasand',
    "ME-Disk-VIP-MJPasand-Duplicate-Check-DB.csv",
    "shahbaz2020@gmail.com,sepidar.abramad@gmail.com,sokan.abramad@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Salim
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Salim',
    "ME-Disk-VIP-Salim-Duplicate-Check-DB.csv",
    "navido@systemgroup.net,zahrashah@systemgroup.net,armin_firouzi@hotmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# ZahraKalbasi
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/ZahraKalbasi',
    "ME-Disk-VIP-ZahraKalbasi-Duplicate-Check-DB.csv",
    "golsaso@systemgroup.net,mahdina@systemgroup.net,amin.ghazvini@gmail.com,a.m.ghazvini@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# ShoyaSaz
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/ShoyaSaz',
    "ME-Disk-VIP-ShoyaSaz-Duplicate-Check-DB.csv",
    "bahramb@systemgroup.net,melikaab@systemgroup.net,miladfa@systemgroup.net,saeedsha@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# OmranKaloot
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/OmranKaloot',
    "ME-Disk-VIP-OmranKaloot-Duplicate-Check-DB.csv",
    "pmsirjan1@omrankaloot.ir,mohammadrezamir@systemgroup.net,mostafaa@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# TatPSA
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/TatPSA',
    "ME-Disk-VIP-TatPSA-Duplicate-Check-DB.csv",
    "abbasas@systemgroup.net,arashamiraskari@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Ava
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Ava',
    "ME-Disk-VIP-Ava-Duplicate-Check-DB.csv",
    "ebrahim.satari@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# KhatereStore
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/KhatereStore',
    "ME-Disk-VIP-KhatereStore-Duplicate-Check-DB.csv",
    "farnooshgh@systemgroup.net,nedapo@systemgroup.net,zeinabal@systemgroup.net,maryam.khorsandi05@gmail.com,taraneh.prt4719@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# ServatPaya
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/ServatPaya',
    "ME-Disk-VIP-ServatPaya-Duplicate-Check-DB.csv",
    "arezup@systemgroup.net,mitraar@systemgroup.net,neginma@systemgroup.net,mossaferin@payawm.ir",
    "support@abramad.com,alireza.ja@abramad.com")



# TizRo
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/TizRo',
    "ME-Disk-VIP-TizRo-Duplicate-Check-DB.csv",
    "nedapo@systemgroup.net,saharp@systemgroup.net,keihanikamran@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# NikManesh
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/NikManesh',
    "ME-Disk-VIP-NikManesh-Duplicate-Check-DB.csv",
    "tohids@systemgroup.net,vahidehal@systemgroup.net,mahdad.nickmanesh@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Mandegar
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Mandegar',
    "ME-Disk-VIP-Mandegar-Duplicate-Check-DB.csv",
    "javadk@systemgroup.net,info@shahrfarsh.com",
    "support@abramad.com,alireza.ja@abramad.com")



# CaspianPS
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/CaspianPS',
    "ME-Disk-VIP-CaspianPS-Duplicate-Check-DB.csv",
    "babadi@caspianpolymer.co,anoosheh@caspianpolymer.co,rostami@caspianpolymer.co,zeinalif365@gmail.com,amini@caspianpolymer.co,valipour@caspianpolymer.co,rostamnia@caspianpolymer.co,hasanzadeh@caspianpolymer.co,sanaz.h.mohajerani@gmail.com,elaheh.anoosheh@yahoo.com,etesami@caspianpolymer.co,khani@caspianpolymer.co",
    "support@abramad.com,alireza.ja@abramad.com")



# TalaChin
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/TalaChin',
    "ME-Disk-VIP-TalaChin-Duplicate-Check-DB.csv",
    "abbasas@systemgroup.net,jaberr@systemgroup.net,samineht@hamkaransystem.ir,piroozfar@yahoo.com",
    "support@abramad.com,alireza.ja@abramad.com")



# SazDar
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/SazDar',
    "ME-Disk-VIP-SazDar-Duplicate-Check-DB.csv",
    "kaveh_01@hotmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# HegmatanT
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/HegmatanT',
    "ME-Disk-VIP-HegmatanT-Duplicate-Check-DB.csv",
    "aminazi@systemgroup.net,mohammadrezayp@systemgroup.net,hegmatan.carpet@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Mohsen_Store
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Mohsen_Store',
    "ME-Disk-VIP-Mohsen_Store-Duplicate-Check-DB.csv",
    "hasanm@systemgroup.net,saberj@systemgroup.net,farnooshgh@systemgroup.net,nedapo@systemgroup.net,sdshafiee2020@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Mandegar
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Mandegar',
    "ME-Disk-VIP-Mandegar-Duplicate-Check-DB.csv",
    "javadk@systemgroup.net,info@shahrfarsh.com",
    "support@abramad.com,alireza.ja@abramad.com")



# SGRamak
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/SGRamak',
    "ME-Disk-VIP-SGRamak-Duplicate-Check-DB.csv",
    "farahehp@systemgroup.net,golshan.golnari@gmail.com,hosseingm@systemgroup.net,hosseinni@systemgroup.net,payamam@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# SainaMehr
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/SainaMehr',
    "ME-Disk-VIP-SainaMehr-Duplicate-Check-DB.csv",
    "dariushma@systemgroup.net,elhamsb@systemgroup.net,nabi_alirezaei@bat.ir,ramona_beigi@bat.ir",
    "support@abramad.com,alireza.ja@abramad.com")



# Avadis
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Avadis',
    "ME-Disk-VIP-Avadis-Duplicate-Check-DB.csv",
    "amirsam@systemgroup.net,mehdias@systemgroup.net,shahrzadh@systemgroup.net,avadis.khademian@gmail.com,mustafamolaeii@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# MadreseSaz
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/MadreseSaz',
    "ME-Disk-VIP-MadreseSaz-Duplicate-Check-DB.csv",
    "bahramb@systemgroup.net,mahtabl@systemgroup.net,melikaab@systemgroup.net,saeedsha@systemgroup.net,abassepehri563@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Hiland
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Hiland',
    "ME-Disk-VIP-Hiland-Duplicate-Check-DB.csv",
    "farnooshgh@systemgroup.net,nedapo@systemgroup.net,it@hilandbeauty.com",
    "support@abramad.com,alireza.ja@abramad.com")



# ShadiZh
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/ShadiZh',
    "ME-Disk-VIP-ShadiZh-Duplicate-Check-DB.csv",
    "abbasas@systemgroup.net,mohammadsho@systemgroup.net,monab@systemgroup.net,faezehsafarpour2019@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# PYara
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/PYara',
    "ME-Disk-VIP-PYara-Duplicate-Check-DB.csv",
    "mahdit@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# HabibZadeh
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/HabibZadeh',
    "ME-Disk-VIP-HabibZadeh-Duplicate-Check-DB.csv",
    "asmak@systemgroup.net,niloofarr@systemgroup.net,saharp@systemgroup.net,habibzadeh_shop@yahoo.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Sfandeqe
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Sfandeqe',
    "ME-Disk-VIP-Sfandeqe-Duplicate-Check-DB.csv",
    "minapo@systemgroup.net,s.zangane95@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# GolMikh
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/GolMikh',
    "ME-Disk-VIP-GolMikh-Duplicate-Check-DB.csv",
    "mahtabl@systemgroup.net,saeedsha@systemgroup.net,golmikh1980.co@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Farsan
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Farsan',
    "ME-Disk-VIP-Farsan-Duplicate-Check-DB.csv",
    "samirae@systemgroup.net,foroughp@systemgroup.net,rezameh@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# Mjavardi
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Mjavardi',
    "ME-Disk-VIP-Mjavardi-Duplicate-Check-DB.csv",
    "mahtabl@systemgroup.net,mostafar@systemgroup.net,leilab@systemgroup.net,akramv@systemgroup.net,mortazavi@esfahanglass.com,pourzadeh@esfahanglass.com",
    "support@abramad.com,alireza.ja@abramad.com")



# CoolackSh
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/CoolackSh',
    "ME-Disk-VIP-CoolackSh-Duplicate-Check-DB.csv",
    "baharehkh@systemgroup.net,samanehmot@systemgroup.net,coolack.shargh1398@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# ArgK
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/ArgK',
    "ME-Disk-VIP-ArgK-Duplicate-Check-DB.csv",
    "vidata@systemgroup.net,sara.asgary29@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# GolnazOil
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/GolnazOil',
    "ME-Disk-VIP-GolnazOil-Duplicate-Check-DB.csv",
    "hadiss@systemgroup.net,mahtabl@systemgroup.net,sabaa@systemgroup.net,mh.golshan@gmail.com,mostafasoltani338@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# NabSteel
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/NabSteel',
    "ME-Disk-VIP-NabSteel-Duplicate-Check-DB.csv",
    "mojakhalaj@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# HZKahroba
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/HZKahroba',
    "ME-Disk-VIP-HZKahroba-Duplicate-Check-DB.csv",
    "amirmor@systemgroup.net,anitafa@systemgroup.net,arashp@systemgroup.net,farnooshgh@systemgroup.net,zaqaqi@gmail.com,ensieh.hajihosseini@hzkahroba.com,it@hzkahroba.com",
    "support@abramad.com,alireza.ja@abramad.com")



# ZPAlvand
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/ZPAlvand',
    "ME-Disk-VIP-ZPAlvand-Duplicate-Check-DB.csv",
    "moradimaryam2905@gmail.com,tina2118t@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Moniran
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Moniran',
    "ME-Disk-VIP-Moniran-Duplicate-Check-DB.csv",
    "homam@systemgroup.net,hoseinho@systemgroup.net,reyhanena@systemgroup.net,moniran@moniranco.com",
    "support@abramad.com,alireza.ja@abramad.com")



# KermanFalat
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/KermanFalat',
    "ME-Disk-VIP-KermanFalat-Duplicate-Check-DB.csv",
    "mahtabl@systemgroup.net,bahramb@systemgroup.net,saeedsha@systemgroup.net, kermanfalat@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# IPDMinoo
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/IPDMinoo',
    "ME-Disk-VIP-IPDMinoo-Duplicate-Check-DB.csv",
    "abbasas@systemgroup.net,akramz@systemgroup.net,parving@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# SGTest
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/SGTest',
    "ME-Disk-VIP-SGTest-Duplicate-Check-DB.csv",
    "abbaszar@systemgroup.net,jahanbakhshh@systemgroup.net,vahidrah@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# RpFath
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/RpFath',
    "ME-Disk-VIP-RpFath-Duplicate-Check-DB.csv",
    "zahraml@systemgroup.net,kharazm.reza@gmail.com,mohammadrezamir@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# ShahdNik
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/ShahdNik',
    "ME-Disk-VIP-ShahdNik-Duplicate-Check-DB.csv",
    "nedapo@systemgroup.net,alinob@systemgroup.net,arvint@systemgroup.net,elhamkasmaei@systemgroup.net,maryamvah@systemgroup.net,m.basiri@saediniaholding.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Arike
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Arike',
    "ME-Disk-VIP-Arike-Duplicate-Check-DB.csv",
    "zahrahanif@systemgroup.net,aminh@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# Msepasi
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Msepasi',
    "ME-Disk-VIP-Msepasi-Duplicate-Check-DB.csv",
    "nedapo@systemgroup.net,farnooshgh@systemgroup.net,parving@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# SamStore
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/SamStore',
    "ME-Disk-VIP-SamStore-Duplicate-Check-DB.csv",
    "monab@systemgroup.net,farnooshgh@systemgroup.net,it@sam-home.com",
    "support@abramad.com,alireza.ja@abramad.com")



# KimiaGene
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/KimiaGene',
    "ME-Disk-VIP-KimiaGene-Duplicate-Check-DB.csv",
    "arashn@systemgroup.net,fatemehkam@systemgroup.net,barazandehamir@yahoo.com,en.ginagen@gmail.com,j.hadizadeh86@gmail.com,n.tavana@ginagen.com",
    "support@abramad.com,alireza.ja@abramad.com")



# ShikPoshAra
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/ShikPoshAra',
    "ME-Disk-VIP-ShikPoshAra-Duplicate-Check-DB.csv",
    "arashp@systemgroup.net,sarinakh@systemgroup.net,zahrahanif@systemgroup.net,nazaninsh@systemgroup.net,primocloth@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# YazdAir
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/YazdAir',
    "ME-Disk-VIP-YazdAir-Duplicate-Check-DB.csv",
    "amirmor@systemgroup.net,hasanm@systemgroup.net,javadk@systemgroup.net,mostafar@systemgroup.net,samineht@hamkaransystem.ir,a.ataie@yazdairways.com,jafari@yazdairways.com",
    "support@abramad.com,alireza.ja@abramad.com")



# GhHegmatan
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/GhHegmatan',
    "ME-Disk-VIP-GhHegmatan-Duplicate-Check-DB.csv",
    "bahramb@systemgroup.net,mahdiemo@systemgroup.net,melikaab@systemgroup.net,saeedsha@systemgroup.net,shamkhaniy@gmail.com,safari_public@yahoo.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Fkhorasan
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Fkhorasan',
    "ME-Disk-VIP-Fkhorasan-Duplicate-Check-DB.csv",
    "bahramb@systemgroup.net,hayedehr@systemgroup.net,mahtabl@systemgroup.net,saeedsha@systemgroup.net,j.shoaa@e-steel.ir",
    "support@abramad.com,alireza.ja@abramad.com")



# Gsarmayeh
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Gsarmayeh',
    "ME-Disk-VIP-Gsarmayeh-Duplicate-Check-DB.csv",
    "navido@systemgroup.net,sh.navidi@platin.capital",
    "support@abramad.com,alireza.ja@abramad.com")



# SPKRahAhan
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/SPKRahAhan',
    "ME-Disk-VIP-SPKRahAhan-Duplicate-Check-DB.csv",
    "hamidfa@systemgroup.net,neginma@systemgroup.net,sanazz@hooshayand.ir,ravankhahalireza62@gmail.com,parinazb@hooshayand.ir",
    "support@abramad.com,alireza.ja@abramad.com")



# AkbariSadaf
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/AkbariSadaf',
    "ME-Disk-VIP-AkbariSadaf-Duplicate-Check-DB.csv",
    "elnazkh@systemgroup.net,nazaninsh@systemgroup.net,rahelehk@systemgroup.net,sadafshariatii@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# MsgLidoma
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/MsgLidoma',
    "ME-Disk-VIP-MsgLidoma-Duplicate-Check-DB.csv",
    "imanj@systemgroup.net,mohammadrezap@systemgroup.net,saeedya@systemgroup.net,rezaeiamehdi54@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# BATPars
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/BATPars',
    "ME-Disk-VIP-BATPars-Duplicate-Check-DB.csv",
    "nabi_alirezaei@bat.ir",
    "support@abramad.com,alireza.ja@abramad.com")



# TaminA
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/TaminA',
    "ME-Disk-VIP-TaminA-Duplicate-Check-DB.csv",
    "hamedd@systemgroup.net,mojtabasafi@systemgroup.net,majidabediidcard@gmail.com,info@taminatie.com,s.sh6861@yahoo.com,mohammad.hadi7580@yahoo.com",
    "support@abramad.com,alireza.ja@abramad.com")



# MTS
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/MTS',
    "ME-Disk-VIP-MTS-Duplicate-Check-DB.csv",
    "alira@systemgroup.net,behzadab@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# ArtaJS
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/ArtaJS',
    "ME-Disk-VIP-ArtaJS-Duplicate-Check-DB.csv",
    "shadim@systemgroup.net,m.khodayi2007@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# ParsianSaba
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/ParsianSaba',
    "ME-Disk-VIP-ParsianSaba-Duplicate-Check-DB.csv",
    "mohammadrezap@systemgroup.net,pegahb@systemgroup.net,shahlagh@systemgroup.net,amirhadadi12@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# YazdCable
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/YazdCable',
    "ME-Disk-VIP-YazdCable-Duplicate-Check-DB.csv",
    "behnazy@systemgroup.net,mahmoudna@systemgroup.net,raziey@systemgroup.net,sadafz@systemgroup.net,office@yazdcable.com",
    "support@abramad.com,alireza.ja@abramad.com")





# Msirjan
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Msirjan',
    "ME-Disk-VIP-Msirjan-Duplicate-Check-DB.csv",
    "mohammadrezamir@systemgroup.net,mostafaa@systemgroup.net,md.ghaseminejad@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# KooshaTrade
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/KooshaTrade',
    "ME-Disk-VIP-KooshaTrade-Duplicate-Check-DB.csv",
    "mohammadsho@systemgroup.net,samineht@hamkaransystem.ir,shival@systemgroup.net,hamidemand1@hotmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Bdehghan
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Bdehghan',
    "ME-Disk-VIP-Bdehghan-Duplicate-Check-DB.csv",
    "golsaso@systemgroup.net,hengamehm@systemgroup.net,mahdina@systemgroup.net,it@arshehkar.com,mohammad.bakhtiari@arshehkar.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Lidco
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Lidco',
    "ME-Disk-VIP-Lidco-Duplicate-Check-DB.csv",
    "saeedsha@systemgroup.net,melikaab@systemgroup.net,bahramb@systemgroup.net,info@lidco.ir",
    "support@abramad.com,alireza.ja@abramad.com")



# MaskanBHR
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/MaskanBHR',
    "ME-Disk-VIP-MaskanBHR-Duplicate-Check-DB.csv",
    "arashj@systemgroup.net,imanj@systemgroup.net,kami_198181@yahoo.com",
    "support@abramad.com,alireza.ja@abramad.com")



# SamanIR
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/SamanIR',
    "ME-Disk-VIP-SamanIR-Duplicate-Check-DB.csv",
    "sinad@systemgroup.net,javadk@systemgroup.net,farahani1318@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Mozayan
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Mozayan',
    "ME-Disk-VIP-Mozayan-Duplicate-Check-DB.csv",
    "masoumekh@systemgroup.net,sadafz@systemgroup.net,it@iranrover.ir",
    "support@abramad.com,alireza.ja@abramad.com")



# JahadNasr
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/JahadNasr',
    "ME-Disk-VIP-JahadNasr-Duplicate-Check-DB.csv",
    "behzadab@systemgroup.net,golsab@systemgroup.net,arttapart@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# ATHamkaran
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/ATHamkaran',
    "ME-Disk-VIP-ATHamkaran-Duplicate-Check-DB.csv",
    "nargesf@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# SepahanP
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/SepahanP',
    "ME-Disk-VIP-SepahanP-Duplicate-Check-DB.csv",
    "abbasas@systemgroup.net,mohammadsho@systemgroup.net,samineht@hamkaransystem.ir,letra.ir@yahoo.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Dorna
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Dorna',
    "ME-Disk-VIP-Dorna-Duplicate-Check-DB.csv",
    "mohammadsho@systemgroup.net,mortezat@systemgroup.net,admin@dorna-co.com",
    "support@abramad.com,alireza.ja@abramad.com")



# OfoghAlborz
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/OfoghAlborz',
    "ME-Disk-VIP-OfoghAlborz-Duplicate-Check-DB.csv",
    "zakiehf@systemgroup.net,javadk@systemgroup.net,samineht@hamkaransystem.ir,a.vahdat@ofoghealborz.com,m.zeyghami@ofoghealborz.com,m.naeini@ofoghealborz.com,m.hajikarim@ofoghealborz.com,o.daei@ofoghelaborz.com",
    "support@abramad.com,alireza.ja@abramad.com")



# FoladZanjan
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/FoladZanjan',
    "ME-Disk-VIP-FoladZanjan-Duplicate-Check-DB.csv",
    "fatemepo@systemgroup.net,saharp@systemgroup.net,saeedya@systemgroup.net,armanmoradii@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Mohsen
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Mohsen',
    "ME-Disk-VIP-Mohsen-Duplicate-Check-DB.csv",
    "nedapo@systemgroup.net,saberj@systemgroup.net,sarinakh@systemgroup.net,zahrahanif@systemgroup.net,mfathifar@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Mirzaei
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Mirzaei',
    "ME-Disk-VIP-Mirzaei-Duplicate-Check-DB.csv",
    "bahramb@systemgroup.net,azhansaftab@yahoo.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Sepand
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Sepand',
    "ME-Disk-VIP-Sepand-Duplicate-Check-DB.csv",
    "omid_hosseini@hotmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# BehanSar
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/BehanSar',
    "ME-Disk-VIP-BehanSar-Duplicate-Check-DB.csv",
    "saharp@systemgroup.net,packzad@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# DadeSaman
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/DadeSaman',
    "ME-Disk-VIP-DadeSaman-Duplicate-Check-DB.csv",
    "dssnovinit@gmail.com,em1362@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# BahmanBF
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/BahmanBF',
    "ME-Disk-VIP-BahmanBF-Duplicate-Check-DB.csv",
    "mostafar@systemgroup.net,zahrabag@systemgroup.net,delavaran@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# RayanIdea
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/RayanIdea',
    "ME-Disk-VIP-RayanIdea-Duplicate-Check-DB.csv",
    "orders@hi-kish.ir,k.hassanzadeh.k@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# NovinIdeh
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/NovinIdeh',
    "ME-Disk-VIP-NovinIdeh-Duplicate-Check-DB.csv",
    "m.faghihian@novinleather.com",
    "support@abramad.com,alireza.ja@abramad.com")



# NasajiArdakan
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/NasajiArdakan',
    "ME-Disk-VIP-NasajiArdakan-Duplicate-Check-DB.csv",
    "mahdik@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# HamrahT
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/HamrahT',
    "ME-Disk-VIP-HamrahT-Duplicate-Check-DB.csv",
    "fahimegh@systemgroup.net,farnooshgh@systemgroup.net,nedapo@systemgroup.net,m2hweb86@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# NTKiavan
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/NTKiavan',
    "ME-Disk-VIP-NTKiavan-Duplicate-Check-DB.csv",
    "leilab@systemgroup.net,mahdina@systemgroup.net,meysamza@systemgroup.net,ehsanrj@systemgroup.net,info@kamalibm.com",
    "support@abramad.com,alireza.ja@abramad.com")



# PayaCaspian
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/PayaCaspian',
    "ME-Disk-VIP-PayaCaspian-Duplicate-Check-DB.csv",
    "melikaab@systemgroup.net,saeedsha@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# SSourin
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/SSourin',
    "ME-Disk-VIP-SSourin-Duplicate-Check-DB.csv",
    "amirsam@systemgroup.net,fazilats@systemgroup.net,moghadam.sanaye@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# MJYazdi
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/MJYazdi',
    "ME-Disk-VIP-MJYazdi-Duplicate-Check-DB.csv",
    "mahsa.khmv94@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# SamanPardaz
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/SamanPardaz',
    "ME-Disk-VIP-SamanPardaz-Duplicate-Check-DB.csv",
    "behzadn@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# Asefi
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Asefi',
    "ME-Disk-VIP-Asefi-Duplicate-Check-DB.csv",
    "shahab.abdollahzadeh@sefimail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# DadeSaman
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/DadeSaman',
    "ME-Disk-VIP-DadeSaman-Duplicate-Check-DB.csv",
    "dssnovinit@gmail.com,em1362@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Shouder
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Shouder',
    "ME-Disk-VIP-Shouder-Duplicate-Check-DB.csv",
    "abbasas@systemgroup.net,minae@systemgroup.net,it@shouder.com",
    "support@abramad.com,alireza.ja@abramad.com")



# SamanPardaz
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/SamanPardaz',
    "ME-Disk-VIP-SamanPardaz-Duplicate-Check-DB.csv",
    "behzadn@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# ZubinT
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/ZubinT',
    "ME-Disk-VIP-ZubinT-Duplicate-Check-DB.csv",
    "mehdifo@systemgroup.net,hasanm@systemgroup.net,info@svg.ir",
    "support@abramad.com,alireza.ja@abramad.com")



# ShikPoshAra
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/ShikPoshAra',
    "ME-Disk-VIP-ShikPoshAra-Duplicate-Check-DB.csv",
    "arashp@systemgroup.net,mohammadnasr@systemgroup.net,sarinakh@systemgroup.net,zahrahanif@systemgroup.net,primocloth@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# SanatAghigh
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/SanatAghigh',
    "ME-Disk-VIP-SanatAghigh-Duplicate-Check-DB.csv",
    "niroosanat.aghigh2@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# DamavandPG
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/DamavandPG',
    "ME-Disk-VIP-DamavandPG-Duplicate-Check-DB.csv",
    "javadk@systemgroup.net,FereshtehH@systemgroup.net,MaryamHe@systemgroup.net,info@damavandpg.co.ir,amir.j1896@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com,sheida.r@abramad.com")



# CaspianPS
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/CaspianPS',
    "ME-Disk-VIP-CaspianPS-Duplicate-Check-DB.csv",
    "babadi@caspianpolymer.co,ehsanesee04444@gmail.com,anoosheh@caspianpolymer.co,rostami@caspianpolymer.co,zeinalif365@gmail.com,amini@caspianpolymer.co,moghadasi@caspianpolymer.co,valipour@caspianpolymer.co,rostamnia@caspianpolymer.co,hasanzadeh@caspianpolymer.co,elaheh.anoosheh@yahoo.com,etesami@caspianpolymer.co,khani@caspianpolymer.co",
    "support@abramad.com,alireza.ja@abramad.com")



# Alvan
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Alvan',
    "ME-Disk-VIP-Alvan-Duplicate-Check-DB.csv",
    "maryamab@systemgroup.net,mostafar@systemgroup.net,fallah@alvansabet.ir,rahimifard@alvansabet.ir",
    "support@abramad.com,alireza.ja@abramad.com")



# HaliStar
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/HaliStar',
    "ME-Disk-VIP-HaliStar-Duplicate-Check-DB.csv",
    "raziey@systemgroup.net,rezameh@systemgroup.net,shahramn@systemgroup.net,es.farid69@yahoo.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Suravajin
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Suravajin',
    "ME-Disk-VIP-Suravajin-Duplicate-Check-DB.csv",
    "aminh@systemgroup.net,maryamab@systemgroup.net,moozhanz@systemgroup.net,royae@systemgroup.net,parisaka@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# BalanSanat
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/BalanSanat',
    "ME-Disk-VIP-BalanSanat-Duplicate-Check-DB.csv",
    "saeedmog@systemgroup.net,sedighehh@systemgroup.net,shahlagh@systemgroup.net,balansanat@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# FonoonAsr
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/FonoonAsr',
    "ME-Disk-VIP-FonoonAsr-Duplicate-Check-DB.csv",
    "samineht@hamkaransystem.ir,m.hamedani@m-f-agroup.com",
    "support@abramad.com,alireza.ja@abramad.com")



# PayamSh
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/PayamSh',
    "ME-Disk-VIP-PayamSh-Duplicate-Check-DB.csv",
    "javadk@systemgroup.net,leylaf@systemgroup.net,samanehka@systemgroup.net,p.sh.shemirani@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Hoonam
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Hoonam',
    "ME-Disk-VIP-Hoonam-Duplicate-Check-DB.csv",
    "mohammadhasanp@systemgroup.net,mozhdeht@systemgroup.net,nedat@systemgroup.net,ali.abdeveis@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# TajCeram
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/TajCeram',
    "ME-Disk-VIP-TajCeram-Duplicate-Check-DB.csv",
    "keyvans@systemgroup.net,leilab@systemgroup.net,mahdiehka@systemgroup.net,reza.bozorgzad@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Network
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Network',
    "ME-Disk-VIP-Network-Duplicate-Check-DB.csv",
    "networkteam@abramad.com,mehdi.a@abramad.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Hallaji
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Hallaji',
    "ME-Disk-VIP-Hallaji-Duplicate-Check-DB.csv",
    "javadk@systemgroup.net,meysamza@systemgroup.net,mozhdehm@systemgroup.net,hallaji.akbar13@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# SilisBoloor
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/SilisBoloor',
    "ME-Disk-VIP-SilisBoloor-Duplicate-Check-DB.csv",
    "aidaz@systemgroup.net,amirmor@systemgroup.net,amirhoseink@systemgroup.net,leilab@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# Alvan
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Alvan',
    "ME-Disk-VIP-Alvan-Duplicate-Check-DB.csv",
    "fallah@alvansabet.ir,rahimifard@alvansabet.ir",
    "support@abramad.com,alireza.ja@abramad.com")



# SatCompany
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/SatCompany',
    "ME-Disk-VIP-SatCompany-Duplicate-Check-DB.csv",
    "aliabd@systemgroup.net,maryambe@systemgroup.net,reyhanehs@systemgroup.net,a.toam@satcompany.ir",
    "support@abramad.com,alireza.ja@abramad.com")



# Mboosak
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Mboosak',
    "ME-Disk-VIP-Mboosak-Duplicate-Check-DB.csv",
    "m.hormati@outlook.com,behnoushk@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")



# DamIranian
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/DamIranian',
    "ME-Disk-VIP-DamIranian-Duplicate-Check-DB.csv",
    "melikaab@systemgroup.net,bahramb@systemgroup.net,saeedsha@systemgroup.net,ashayershop@gmail.com,ashayershop@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# NamaNoor
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/NamaNoor',
    "ME-Disk-VIP-NamaNoor-Duplicate-Check-DB.csv",
    "abbaszar@systemgroup.net,elnazs@systemgroup.net,narimanna@systemgroup.net,v.aghabozorgi@gmail.com ",
    "support@abramad.com,alireza.ja@abramad.com")



# Zangan
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Zangan',
    "ME-Disk-VIP-Zangan-Duplicate-Check-DB.csv",
    "alirezapa@systemgroup.net,mad.machine.nazari@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Moghavasazi
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Moghavasazi',
    "ME-Disk-VIP-Moghavasazi-Duplicate-Check-DB.csv",
    "samineht@hamkaransystem.ir,moghavasazishargh@yahoo.com",
    "support@abramad.com,alireza.ja@abramad.com")



# AlborzNiroo
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/AlborzNiroo',
    "ME-Disk-VIP-AlborzNiroo-Duplicate-Check-DB.csv",
    "saharp@systemgroup.net,a.ahmadi@alborzniroo.ir",
    "support@abramad.com,alireza.ja@abramad.com")



# DaneshAmuzi
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/DaneshAmuzi',
    "ME-Disk-VIP-DaneshAmuzi-Duplicate-Check-DB.csv",
    "haniehs@systemgroup.net,somayehy@systemgroup.net,usia58@chmail.ir",
    "support@abramad.com,alireza.ja@abramad.com")



# Tizro
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Tizro',
    "ME-Disk-VIP-Tizro-Duplicate-Check-DB.csv",
    "faezehv@systemgroup.net,mahsav@systemgroup.net,nedapo@systemgroup.net,keihanikamran@gmail.com",
    "support@abramad.com,alireza.ja@abramad.com")



# Confluence
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/Confluence',
    "ME-Disk-VIP-Confluence-Duplicate-Check-DB.csv",
    "alireza.mah@abramad.com,mariak@systemgroup.net,ehsan.h@abramad.com,saeed.r@abramad.com,mehdi.a@abramad.com",
    "support@abramad.com,alireza.ja@abramad.com")



# RayanPars
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/RayanPars',
    "ME-Disk-VIP-RayanPars-Duplicate-Check-DB.csv",
    "saharp@systemgroup.net,raziey@systemgroup.net,minae@systemgroup.net  ,s.rajabimanesh@sanatrayanpars.ir",
    "support@abramad.com,alireza.ja@abramad.com")



# RasamSystem
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/RasamSystem',
    "ME-Disk-VIP-RasamSystem-Duplicate-Check-DB.csv",
    "alirezan@systemgroup.net,javadk@systemgroup.net",
    "support@abramad.com,alireza.ja@abramad.com")

