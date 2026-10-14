try:
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.application import MIMEApplication
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

    username = decryptor("enc_sinaz_abramad","key_sinaz_abramad")
    password = decryptor("enc_sinaz_pass","key_sinaz_pass")

    today_date_jalali_full = str(jdatetime.datetime.now())[:-7]
    #with open("/etc/haproxy/haproxy-config.log", "a") as log:
    #    log.write(today_date_jalali_full + "\n")
    hostname = socket.gethostname()

    # Try to start HAProxy service
    try:
        result = subprocess.run(['sudo', 'systemctl', 'start', 'haproxy'], check=True, capture_output=True, text=True)

        ############ Email Sending Part #############
        sender_email = username
        receiver_email = 'support@abramad.com,mehdi.a@abramad.com,alireza.ja@abramad.com'
        cc_email = 'mohammadhossein.kh@abramad.com,hossein.a@abramad.com'

        # Create a multipart message object
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['CC'] = cc_email
        msg['Subject'] = f'HAProxy Service Started after Failure | {hostname}'

        ##############################################
        ######### HTML Body Begin For Email ##########
        html_line_break = '''
                                <p><br></p>
                            '''
        html_msg_1 = '''
                            <html dir="ltr">
                              <body>
                            '''
        html_msg_2 = f'''
                                <p  style="font-family: DiodrumArabic-Regular"><b>## Moderate Warning ##</b></p>
                            '''
        html_msg_3 = f'''
                                <p  style="font-family: DiodrumArabic-Regular">haproxy service has stopped on <b>{hostname}</b> but got restarted automatically and is now up.</p>
                            '''
        html_msg_4 = f'''
                                <p  style="font-family: DiodrumArabic-Regular">Incident Date and Time: <b>{today_date_jalali_full}</b></p>
                            '''
        html_msg_5 = f'''
                                    <p  style="font-family: DiodrumArabic-Regular"><b>Sina Zare<br>Support Team Lead<br>Operation Team</b></p>
                                '''
        html_msg_6 = '''
                              </body>
                            </html>
                            '''
        ######### HTML Body End For Email ##########
        ############################################

        email_body = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_4 + html_msg_5 + html_line_break + html_line_break + html_msg_6
        msg.attach(MIMEText(email_body, 'html'))

        # Connect to the SMTP server and send the email 465,*587*,25 (mail.systemgroup.net)
        # Send email info
        smtp_server = 'mail.abramad.com'
        smtp_port = 587

        try:
            # Send email function
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())
        except Exception as email_error:
            print(f"Failed to send email: {email_error}")


    except Exception as service_error:

        ############ Email Sending Part #############
        sender_email = username
        receiver_email = 'support@abramad.com,mehdi.a@abramad.com,alireza.ja@abramad.com'
        cc_email = 'mohammadhossein.kh@abramad.com,hossein.a@abramad.com'

        # Create a multipart message object
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['CC'] = cc_email
        msg['Subject'] = f'HAProxy Service Failure | {hostname} | Bring Up Error'

        ##############################################
        ######### HTML Body Begin For Email ##########
        html_line_break = '''
                                <p><br></p>
                            '''
        html_msg_1 = '''
                            <html dir="ltr">
                              <body>
                            '''
        html_msg_2 = f'''
                                <p  style="font-family: DiodrumArabic-Regular"><b>## Critical Warning ##</b></p>
                            '''
        html_msg_3 = f'''
                                <p  style="font-family: DiodrumArabic-Regular">haproxy service has stopped on <b>{hostname}</b> and also failed to restart automatically.</p>
                            '''
        html_msg_4 = f'''
                                <p  style="font-family: DiodrumArabic-Regular">Incident Date and Time: <b>{today_date_jalali_full}</b><br><br>{str(service_error)}</p>
                            '''
        html_msg_5 = f'''
                                    <p  style="font-family: DiodrumArabic-Regular"><b>Sina Zare<br>Support Team Lead<br>Operation Team</b></p>
                                '''
        html_msg_6 = '''
                              </body>
                            </html>
                            '''
        ######### HTML Body End For Email ##########
        ############################################

        email_body = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_4 + html_msg_5 + html_line_break + html_line_break + html_msg_6
        msg.attach(MIMEText(email_body, 'html'))

        # Connect to the SMTP server and send the email 465,*587*,25 (mail.systemgroup.net)
        # Send email info
        smtp_server = 'mail.abramad.com'
        smtp_port = 587

        try:
            # Send email function
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())
        except Exception as email_error:
            print(f"Failed to send email: {email_error}")



except Exception as e:

    from cryptography.fernet import Fernet


    def decryptor(enc_env_var, key_env_var):

        # Load the key
        key = os.environ.get(key_env_var)
        encryption_key = Fernet(key)
        encrypted_password = (os.environ.get(enc_env_var)).encode()
        # Decrypt Data
        decrypted_password = encryption_key.decrypt(encrypted_password)

        return decrypted_password.decode()

    username = decryptor("enc_sinaz_abramad", "key_sinaz_abramad")
    password = decryptor("enc_sinaz_pass", "key_sinaz_pass")

    today_date_jalali_full = str(jdatetime.datetime.now())[:-7]
    # with open("/etc/haproxy/haproxy-config.log", "a") as log:
    #    log.write(today_date_jalali_full + "\n")
    hostname = socket.gethostname()

    ############ Email Sending Part #############
    sender_email = username
    receiver_email = 'support@abramad.com,mehdi.a@abramad.com,alireza.ja@abramad.com'
    cc_email = 'mohammadhossein.kh@abramad.com,hossein.a@abramad.com'

    # Create a multipart message object
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['CC'] = cc_email
    msg['Subject'] = f'HAProxy Service Failure | {hostname} | Bring Up Exception'

    ##############################################
    ######### HTML Body Begin For Email ##########
    html_line_break = '''
                        <p><br></p>
                    '''
    html_msg_1 = '''
                    <html dir="ltr">
                      <body>
                    '''
    html_msg_2 = f'''
                        <p  style="font-family: DiodrumArabic-Regular"><b>## Critical Warning ##</b></p>
                    '''
    html_msg_3 = f'''
                        <p  style="font-family: DiodrumArabic-Regular">haproxy service has stopped on <b>{hostname}</b> and the automatic bring up encountered an exception.</p>
                    '''
    html_msg_4 = f'''
                        <p  style="font-family: DiodrumArabic-Regular">Incident Date and Time: <b>{today_date_jalali_full}</b><br><br>{str(e)}</p>
                    '''
    html_msg_5 = f'''
                            <p  style="font-family: DiodrumArabic-Regular"><b>Sina Zare<br>Support Team Lead<br>Operation Team</b></p>
                        '''
    html_msg_6 = '''
                      </body>
                    </html>
                    '''
    ######### HTML Body End For Email ##########
    ############################################

    email_body = html_msg_1 + html_msg_2 + html_msg_3 + html_msg_4 + html_msg_5 + html_line_break + html_line_break + html_msg_6
    msg.attach(MIMEText(email_body, 'html'))

    # Connect to the SMTP server and send the email 465,*587*,25 (mail.systemgroup.net)
    # Send email info
    smtp_server = 'mail.abramad.com'
    smtp_port = 587

    try:
        # Send email function
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())
    except Exception as email_error:
        print(f"Failed to send email: {email_error}")

    print(str(e))
