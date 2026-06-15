import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from icalendar import Calendar, Event
import time
import os


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


given_time = input("Enter Time in following 24 Hour format: HH:MM\n--> ")

# Get today's Jalali date
today = datetime.now().date()

# Add two days to today's date
import_date = today + timedelta(days=1)
import_year = str(import_date)[:4]
import_month = str(import_date)[5:7]
import_day = str(import_date)[8:]


# Body Text
text_mail = f'''
        <html dir="rtl">
          <body>
          <p style="font-family: DiodrumArabic-Regular">درود<br>با توجه به ایمیل ارسال شده از طرف واحد قفل در ساعت <b>{given_time}</b> لایسنس مربوطه ایمپورت گردد.<br>با سپاس</p>
          </body>
        </html>
        '''
text_cal = f'درود\nبا توجه به ایمیل ارسال شده از طرف واحد قفل در ساعت  {given_time}   لایسنس مربوطه ایمپورت گردد.\nبا سپاس'

# Meeting details
subject = f'ایمپورت لایسنس ارسالی با توجه به ایمیل ساعت {given_time} واحد قفل'
start = datetime(int(import_year), int(import_month), int(import_day), 6, 0)  # Meeting start time
end = start + timedelta(minutes=15)  # Meeting end time
location = 'سرور راه لاک مربوطه'
attendees = ['support@abramad.com']
organizer = 'sina.z@abramad.com'

# Create iCalendar event
event = Event()
event.add('summary', subject)
event.add('dtstart', start)
event.add('dtend', end)
event.add('location', location)
event.add('organizer', organizer)
event.add('description', text_cal)
event.add('status', 'CONFIRMED')

for attendee in attendees:
    event.add('attendee', attendee)

# Create iCalendar calendar and add the event
cal = Calendar()
cal.add_component(event)

# Generate the iCalendar content as a string
ical_content = cal.to_ical()

# Create email message
message = MIMEMultipart('alternative')
message['Subject'] = subject
message['From'] = organizer
message['To'] = ', '.join(attendees)


part1 = MIMEText(text_mail, 'html')
part2 = MIMEBase('text', 'calendar', method='REQUEST')
part2.set_payload(ical_content)
encoders.encode_base64(part2)
part2.add_header('Content-Disposition', 'attachment; filename="meeting.ics"')

message.attach(part1)
message.attach(part2)

# Connect to SMTP server and send the email
smtp_server = 'mail.systemgroup.net'
smtp_port = 587
smtp_username = username
smtp_password = password

with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.sendmail(organizer, attendees, message.as_string())

print(f'\nInvitation sent to {attendees} successfully')
time.sleep(3)
