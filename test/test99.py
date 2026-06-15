def email_sender(username, password, email_receivers, email_cc, subject, direction, html_body,
                 mail_server='mail.systemgroup.net'):
    try:
        # Create a multipart message object
        msg = MIMEMultipart()
        msg['From'] = 'zabbix@abramad.com'
        msg['To'] = email_receivers
        msg['CC'] = email_cc
        msg['Subject'] = subject

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
                            <p  style="font-family: DiodrumArabic-Regular">{html_body}</p>
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
        msg.attach(MIMEText(email_body, 'html'))

        # Connect to the SMTP server and send the email on 587 TCP
        smtp_server = mail_server
        smtp_port = 587

        # Send email function
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(username, email_receivers.split(",") + email_cc.split(','), msg.as_string())

    except Exception as err:
        print(f"Mail Function Error: {err}")
        traceback.print_exc()
        email_sender(username, passphrase, default_receivers, default_cc,
                     f"Email Function Error in running Zabbix_OnPrem_Fully_Automated.py", "ltr",
                     f"Error Occurred:<br><b>{err}<br>{traceback.print_exc()}</b>")
