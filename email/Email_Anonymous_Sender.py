import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header

def send_anonymous_email(from_email, to_email, cc_email, subject, html_message, direction,
                         mail_server='mail.abramad.com', attachments=None):
    try:
        ##############################################
        ######### HTML Body Begin For Email ##########
        html_line_break = '''
                                <p><br></p>
                            '''
        html_msg_1 = f'''
                            <html dir={direction}>
                              <body>
                            '''
        html_msg_2 = f'''
                                <p  style="font-family: DiodrumArabic-Regular">{html_message}</p>
                            '''
        html_msg_3 = f'''
                                '''
        html_msg_4 = '''
                              </body>
                            </html>
                            '''
        ######### HTML Body End For Email ##########
        ############################################

        email_body = html_msg_1 + html_msg_2 + html_line_break + html_line_break + html_msg_3 + html_msg_4

        # Split email addresses into lists
        to_email_list = to_email.split(",") if to_email else []
        cc_email_list = cc_email.split(",") if cc_email else []
        all_recipients = to_email_list + cc_email_list

        # Create the email message
        msg = MIMEMultipart()
        msg["From"] = Header(from_email, "utf-8")
        msg["To"] = Header(", ".join(to_email_list), "utf-8")  # For display purposes
        msg["CC"] = Header(", ".join(cc_email_list), "utf-8")  # For display purposes
        msg["Subject"] = Header(subject, "utf-8")

        # Attach HTML body
        msg.attach(MIMEText(email_body, "html", "utf-8"))

        # Attach files if any
        if attachments:
            for attachment in attachments:
                if os.path.exists(attachment):
                    with open(attachment, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(attachment))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment)}"'
                        msg.attach(part)
                else:
                    print(f"Warning: Attachment {attachment} not found.")

        # Connect to the mail server and send the email
        with smtplib.SMTP(mail_server, 25) as server:
            server.sendmail(from_email, all_recipients, msg.as_string())
            print("Email sent successfully.")

    except Exception as err:
        print(f"email_sender Function Error: {err}")
        send_anonymous_email(from_email, 'abramadsysops@abramad.com', 'sina.z@abramad.com',
                             f"email_sender Function Error in running All_VMs_Info.py",
                             f"Error Occurred:<br><b>{err}<br></b> Agent: All_VMs_Info.py",
                             'ltr')




send_anonymous_email(
    from_email="your_email@abramad.com",
    to_email="sina.z@abramad.com",
    cc_email="sinasilver91891.sz@gmail.com",
    subject="Test Email with Attachment",
    html_message="This is a test email with an attachment.",
    direction="ltr",
    attachments=["C:\\Downloads\\Chrome\\1.yaml", "C:\\Downloads\\Chrome\\2.yaml"]
)
