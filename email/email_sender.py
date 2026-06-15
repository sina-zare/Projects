import os
import imaplib
import email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from stdiomask import getpass
import openpyxl
import time

username = input("Email Username: ")
password = getpass("Password: ")

try:
    # Taking Needed Data From xlsx
    customer_agents_excell_file = 'C:/Users/sina.z/Desktop/Python-Projects/Customer_Agents.xlsx'
    # Load the workbook
    workbook = openpyxl.load_workbook(customer_agents_excell_file)
    # Select the active sheet
    sheet = workbook.active
    # Create an empty list to store the rows
    crm_agent_rows = []
    # Iterate through the rows and append each row to the list
    for row in sheet.iter_rows(values_only=True):
        crm_agent_rows.append(row)


    valuable_crm_data = []
    # Taking Customer Name, Agent Email
    for data in crm_agent_rows:
        valuable_crm_data.append([data[1], data[9]])

    final_customer_data_list = []
    for data in valuable_crm_data:
        if (data[0] != None) and (data[1] != None):
            final_customer_data_list.append(data)

    #for data in final_customer_data_list:
    #    print(f"Customer Name: {data[0]}")
    #    print(f"Customer Email: {data[1]}")
    #    print("###########################\n")
except Exception as e:
    print(e)
    time.sleep(10)

# Sending Email
for data in final_customer_data_list:

    sender_email = username
    receiver_email = data[1]
    cc_email = 'mehrad.s@abramad.com,sales@abramad.com'

    attachment = 'C:/Users/sina.z/Desktop/Python-Projects/Bakhsh-Name-Maliati.png'

    # Create a multipart message object
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['CC'] = cc_email
    msg['Subject'] = f'پرداخت ما به تفاوت ارزش افزوده سال 1403 شرکت محترم {data[0]}'

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
                <p  style="font-family: DiodrumArabic-Regular">با سلام و احترام ؛</p>
            '''
    html_msg_3 = f'''
                <p  style="font-family: DiodrumArabic-Regular">شرکت محترم "<b>{data[0]}</b>"</p>
            '''
    html_msg_4 = f'''
                <p  style="font-family: DiodrumArabic-Regular">پیرو تغییر نرخ مالیات بر ارزش افزوده از ماخذ 9% به 10% در سال 1403 طبق بخشنامه 379/230/د اداره کل امور مالیاتی (به پیوست)، خواهشمند است درصورتی که آن شرکت محترم پیش پرداخت مربوط به دوره سال 1403 را با نرخ 9% انجام داده است نسبت به پرداخت مابه تفاوت نرخ مالیاتی اقدام فرماید.</p>
            '''
    html_msg_5 = f'''
                    <p  style="font-family: DiodrumArabic-Regular">پیشاپیش کمال تشکر و قدردانی را از همکاری شما عزیزان داریم.🌹</p>
                '''
    html_msg_7 = f'''
                <p style="font-family: DiodrumArabic-Regular"><em><b>مهراد سراج<br>کارشناس امور مالی<br>ابرآمد<br>02183382900(5993)</b></em></p>
            '''
    html_msg_8 = '''
              </body>
            </html>
            '''
    ######### HTML Body End For Email ##########
    ############################################

    email_body = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_4 + html_msg_5 + html_line_break + html_msg_7
    msg.attach(MIMEText(email_body, 'html'))

    with open(attachment, 'rb') as f:
        part = MIMEApplication(f.read(), Name=os.path.basename(attachment))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment)}"'
        msg.attach(part)

    # Connect to the SMTP server and send the email 465,*587*,25 (mail.systemgroup.net)
    # Send email info
    smtp_server = 'mail.systemgroup.net'
    smtp_port = 587

    try:
        # Send email function
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())

        print(f"Email sent for '{data[0]}'\n")
    except Exception as e:
        print(e)
        time.sleep(10)
