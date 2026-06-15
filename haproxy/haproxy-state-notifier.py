try:
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.application import MIMEApplication
    from email.header import Header
    import traceback
    import jdatetime
    import socket
    import time
    import os
    import subprocess

    # Credentials
    from cryptography.fernet import Fernet
    def decryptor(enc_env_var, key_env_var):

        # Load the key
        key = os.environ.get(key_env_var)
        encryption_key = Fernet(key)
        encrypted_password = (os.environ.get(enc_env_var)).encode()
        # Decrypt Data
        decrypted_password = encryption_key.decrypt(encrypted_password)

        return decrypted_password.decode()


    username = "sysops-svc@abramad.com"
    password = decryptor("sysops_svc_enc", "sysops_svc_key")

    default_receivers = "AbramadSysOps@abramad.com"
    default_cc = "sina.z@abramad.com"


    def send_anonymous_email(from_email, to_email, cc_email, subject, html_message, direction,
                             mail_server='mail.abramad.com'):
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

            # Create the MIME email object with HTML content
            msg = MIMEText(email_body, "html", "utf-8")
            msg["From"] = Header(from_email, "utf-8")
            msg["To"] = Header(", ".join(to_email_list), "utf-8")  # For display purposes
            msg["CC"] = Header(", ".join(cc_email_list), "utf-8")  # For display purposes
            msg["Subject"] = Header(subject, "utf-8")

            # Connect to the mail server and send the email
            with smtplib.SMTP(mail_server, 25) as server:
                server.sendmail(from_email, all_recipients, msg.as_string())
                print("Email sent successfully.")


        except Exception as err:
            print(f"email_sender Function Error: {err}")
            traceback.print_exc()
            send_anonymous_email('VRA-HAProxy@abramad.com', default_receivers, default_cc,
                                 f"email_sender Function Error in running haproxy-config-creator.py",
                                 f"Error Occurred:<br><b>{err}<br>{traceback.print_exc()}</b> Agent: haproxy-state-notifier.py",
                                 'ltr')


    today_date_jalali_full = str(jdatetime.datetime.now())[:-7]
    #with open("/etc/haproxy/haproxy-config.log", "a") as log:
    #    log.write(today_date_jalali_full + "\n")
    hostname = socket.gethostname()

    # Try to start HAProxy service
    try:
        result = subprocess.run(['sudo', 'systemctl', 'start', 'haproxy'], check=True, capture_output=True, text=True)

        ############ Email Sending Part #############

        try:
            # Send email function
            send_anonymous_email('VRA-HAProxy@abramad.com', default_receivers, default_cc,
                                 f'HAProxy Service Started after Failure | {hostname}',
                                 f"<b>## Moderate Warning ##</b><br>haproxy service has stopped on <b>{hostname}</b> but got restarted automatically and is now up.<br>Incident Date and Time: <b>{today_date_jalali_full}</b><br><br>Agent: haproxy-state-notifier.py",
                                 'ltr')

        except Exception as email_error:
            print(f"Failed to send email: {email_error}")


    except Exception as service_error:

        try:
            send_anonymous_email('VRA-HAProxy@abramad.com', default_receivers, default_cc,
                                 f'HAProxy Service Failure | {hostname} | Bring Up Error',
                                 f"<b>## Critical Warning ##</b><br>haproxy service has stopped on <b>{hostname}</b> and also failed to restart automatically.<br>Incident Date and Time: <b>{today_date_jalali_full}</b><br><br>Agent: haproxy-state-notifier.py",
                                 'ltr')

        except Exception as email_error:
            print(f"Failed to send email: {email_error}")



except Exception as e:

    from cryptography.fernet import Fernet


    today_date_jalali_full = str(jdatetime.datetime.now())[:-7]
    # with open("/etc/haproxy/haproxy-config.log", "a") as log:
    #    log.write(today_date_jalali_full + "\n")
    hostname = socket.gethostname()

    try:
        # Send email function
        send_anonymous_email('VRA-HAProxy@abramad.com', default_receivers, default_cc,
                             f'HAProxy Service Failure | {hostname} | Bring Up Exception',
                             f"<b>## Critical Warning ##</b><br>haproxy service has stopped on <b>{hostname}</b> and the automatic bring up encountered an exception.<br>Incident Date and Time: <b>{today_date_jalali_full}</b><br><br>Agent: haproxy-state-notifier.py",
                             'ltr')

    except Exception as email_error:
        print(f"Failed to send email: {email_error}")

    print(str(e))
