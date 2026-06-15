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
        with open("C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/Primary-Database/Resource-Issue-Database.csv",'a', newline='') as file:
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
            return (words[on_index + 3]).replace('"','')
        else:
            return words[on_index + 1].replace('"','')

    def server_issue_taker(text):
        words = text.lower().split()
        critical_index = words.index("critical")

        return words[critical_index + 1]


    # Credentials
    username = decrypt(os.environ.get('sin'), 9999)
    password = decrypt(os.environ.get('spass'), 9999)


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
                                        <p  style="font-family: DiodrumArabic-Regular">سرور <b>{unique_vm[0]}</b> بیش از دو ساعت هست که دچار مصرف بی رویه RAM <b>(بالای 90%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و در صورتی که نیاز به افزایش RAM سرور میباشد، این مورد را به اطلاع ما برسانید.</p>
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
                            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())


                        # Append data to db
                        ram_data_to_write_to_db = [unique_vm[0], "RAM", int_ticket_no, (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, ram_data_to_write_to_db)
                        print(f"DB is appended and email sent to {receiver_email} for {unique_vm}\n")
                        data_to_write_to_primary_db = [unique_vm[0], "RAM", int_ticket_no, (current_day + " " + current_month), receiver_email]
                        append_to_csv_primary_db(data_to_write_to_primary_db)
                        print(f"Primary DB Appended for {unique_vm}\n")

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(120, 300))

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
                                        <p  style="font-family: DiodrumArabic-Regular">سرور <b>{unique_vm[0]}</b> بیش از دو ساعت هست که دچار مصرف بی رویه CPU <b>(بالای 90%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و در صورتی که نیاز به افزایش CPU سرور میباشد، این مورد را به اطلاع ما برسانید.</p>
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
                            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())

                        # Append data to db
                        cpu_data_to_write_to_db = [unique_vm[0], "CPU", int_ticket_no, (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, cpu_data_to_write_to_db)
                        print(f"DB is appended and email sent to {receiver_email} for {unique_vm}\n")
                        data_to_write_to_primary_db = [unique_vm[0], "CPU", int_ticket_no, (current_day + " " + current_month), receiver_email]
                        append_to_csv_primary_db(data_to_write_to_primary_db)
                        print(f"Primary DB Appended for {unique_vm}\n")

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(120, 300))


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
                            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(120, 300))

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
                                        <p  style="font-family: DiodrumArabic-Regular">سرور <b>{unique_vm[0]}</b> بیش از دو ساعت هست که دچار مصرف بی رویه RAM <b>(بالای 90%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و در صورتی که نیاز به افزایش RAM سرور میباشد، این مورد را به اطلاع ما برسانید.</p>
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
                            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())


                        # Append data to db
                        ram_data_to_write_to_db = [unique_vm[0], "RAM", int_ticket_no, (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, ram_data_to_write_to_db)
                        print(f"DB is appended and email sent to {receiver_email} for {unique_vm}\n")
                        data_to_write_to_primary_db = [unique_vm[0], "RAM", int_ticket_no, (current_day + " " + current_month), receiver_email]
                        append_to_csv_primary_db(data_to_write_to_primary_db)
                        print(f"Primary DB Appended for {unique_vm}\n")

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(120, 300))

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
                            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(120, 300))

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
                                        <p  style="font-family: DiodrumArabic-Regular">سرور <b>{unique_vm[0]}</b> بیش از دو ساعت هست که دچار مصرف بی رویه CPU <b>(بالای 90%) </b> شده است، لطفا بررسی لازم را در خصوص process های در حال اجرا انجام دهید و در صورتی که نیاز به افزایش CPU سرور میباشد، این مورد را به اطلاع ما برسانید.</p>
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
                            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())

                        # Append data to db
                        cpu_data_to_write_to_db = [unique_vm[0], "CPU", int_ticket_no, (current_day + " " + current_month)]
                        append_to_csv(duplicate_check_db_path, cpu_data_to_write_to_db)
                        print(f"DB is appended and email sent to {receiver_email} for {unique_vm}\n")
                        data_to_write_to_primary_db = [unique_vm[0], "CPU", int_ticket_no, (current_day + " " + current_month), receiver_email]
                        append_to_csv_primary_db(data_to_write_to_primary_db)
                        print(f"Primary DB Appended for {unique_vm}\n")

                        # wait for 4 minute, so they think a human is doing it
                        time.sleep(random.randint(120, 300))




            except FileNotFoundError:

                # If file was not found
                # Send Email to King

                # Create a multipart message object
                msg = MIMEMultipart()
                msg['From'] = 'sina.z@abramad.com'
                msg['To'] = 'sina.z@abramad.com'
                msg['Subject'] = f'Error in Abri Resource RAM DB | {current_day}-{current_month}'
                msg.attach(MIMEText(f"<p><b>RAM DB File does not exist in <b>{duplicate_check_db_path}</b> | <em>{current_day}-{current_month}</em><br>Sending mail for below vms failed:<br></b><br>RAM Problems: {unique_list_of_vms}<br><br>Unread them again.</p>",'html'))

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





################################# Function Calls #################################
##################################################################################


# ALaziz
resource_peak_checker('"Solarwinds Monitoring VIP/ME Resource/ALaziz"',
                      "ME-Resource-VIP-ALaziz-Duplicate-Check-DB.csv",
                    "abbasas@systemgroup.net",
                        "support@abramad.com,mehdi.a@abramad.com,alireza.ja@abramad.com")



# Ramak
resource_peak_checker('"Solarwinds Monitoring VIP/ME Resource/Ramak"',
                      "ME-Resource-VIP-Ramak-Duplicate-Check-DB.csv",
                    "rezaab@systemgroup.net,hosseinmou@systemgroup.net,kouroshi@systemgroup.net,masoudsh@systemgroup.net",
                        "support@abramad.com,mehdi.a@abramad.com,alireza.ja@abramad.com")




# BehsazFarayand
resource_peak_checker('"Solarwinds Monitoring VIP/ME Resource/BehsazFarayand"',
                      "ME-Resource-VIP-BehsazFarayand-Duplicate-Check-DB.csv",
                    "marziehs@systemgroup.net,meysamhz@systemgroup.net",
                        "support@abramad.com,mehdi.a@abramad.com,alireza.ja@abramad.com")




# Domino
resource_peak_checker('"Solarwinds Monitoring VIP/ME Resource/Domino"',
                      "ME-Resource-VIP-Domino-Duplicate-Check-DB.csv",
                    "mortezat@systemgroup.net,abbasas@systemgroup.net,mozhganfa@systemgroup.net",
                        "support@abramad.com,mehdi.a@abramad.com,alireza.ja@abramad.com")




# Manimas
resource_peak_checker('"Solarwinds Monitoring VIP/ME Resource/Manimas"',
                      "ME-Resource-VIP-Manimas-Duplicate-Check-DB.csv",
                    "elnazsha@systemgroup.net,mahnazsh@systemgroup.net,sedighehh@systemgroup.net,shahlagh@systemgroup.net,zahrabazr@systemgroup.net,zahrasha@systemgroup.net",
                        "support@abramad.com,mehdi.a@abramad.com,alireza.ja@abramad.com")




# Refah
resource_peak_checker('"Solarwinds Monitoring VIP/ME Resource/Refah"',
                      "ME-Resource-VIP-Refah-Duplicate-Check-DB.csv",
                    "behdadb@systemgroup.net,homayoonb@systemgroup.net,saberj@systemgroup.net,farnooshgh@systemgroup.net,meysama@systemgroup.net,nedapo@systemgroup.net",
                        "support@abramad.com,mehdi.a@abramad.com,alireza.ja@abramad.com")




# SW
resource_peak_checker('"Solarwinds Monitoring VIP/ME Resource/SW"',
                      "ME-Resource-VIP-SW-Duplicate-Check-DB.csv",
                    "sara.b@abramad.com,maryam.mat@abramad.com",
                        "support@abramad.com,mehdi.a@abramad.com,alireza.ja@abramad.com")




