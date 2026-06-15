from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from email.header import decode_header
from icalendar import Calendar, Event
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from datetime import datetime
from email import encoders
import jdatetime
import imaplib
import smtplib
import quopri
import base64
import email
import time
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter
import traceback
import random
import time
import os

# --- Configuration ---
script_name = 'ehsan_jira_change_mgmt'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'https://me-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
datacenter = 'miremad'
target = 'jira_svc_acc_inbox'


# Create a registry for our custom metrics
registry = CollectorRegistry()

# Define metrics
duration_gauge = Gauge('script_exec_duration_seconds', 'Duration of my script', registry=registry)
status_gauge = Gauge('script_success', 'Whether script succeeded (1) or failed (0)', registry=registry)
total_execution_counter = Counter('script_total_execs', 'Total number of times the script has run', registry=registry)
total_failed_execution_counter = Counter('script_total_failed_execs', 'Total number of times the script has failed to finish gracefully', registry=registry)
last_error_message = Gauge('script_last_error_message','The last error message encountered during script execution',['error_summary', 'error_detail'], registry=registry)


# Simulate your script logic
start_time = time.time()
success = True
error_string_summary = ""
error_string_detail = ""


try:

    # --- Read script run counter from file ---
    def read_value_from_file(file_path):
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)  # Create the directory if it doesn't exist

        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write('0')
            return 0

        try:
            with open(file_path, 'r') as f:
                return int(f.read().strip())
        except ValueError:
            # In case of a corrupt or non-integer value
            return 0

    # --- Write updated count to file ---
    def write_value_to_file(file_path, value):
        with open(file_path, 'w') as f:
            f.write(str(value))




    def miladi_to_shamsi_date_converter(miladi_date):
        # Given date in "DD/Mon/YY" format
        # Parse the date string to a Python datetime object
        gregorian_date = datetime.strptime(miladi_date, "%d/%b/%y")

        # Convert the Gregorian date to Shamsi (Jalali) date
        shamsi_date = jdatetime.date.fromgregorian(date=gregorian_date)

        return shamsi_date


    def miladi_to_miladi_converter(miladi_date):
        # Given date string in "DD/Mon/YY" format
        # Parse the date string to a datetime object
        parsed_date = datetime.strptime(miladi_date, "%d/%b/%y")

        # Format the date to "YYYY-MM-DD" format
        formatted_date = parsed_date.strftime("%Y-%m-%d")

        # Remove leading zeros in month and day
        #formatted_date = formatted_date.replace('-0', '-')

        return formatted_date


    def _12_to_24_hour_converter(twelve_hour_format):
        # Given time string in 12-hour format "3:30 PM"
        # Parse the time string to a datetime object
        time_24hr = datetime.strptime(twelve_hour_format, "%I:%M %p")

        # Format the time to 24-hour format
        formatted_time = time_24hr.strftime("%H:%M")

        return formatted_time


    # Helper function to decode email headers
    def decode_mime_words(s):
        decoded_string = ''
        for word, encoding in decode_header(s):
            if isinstance(word, bytes):
                # Decode bytes to string
                if encoding:
                    decoded_string += word.decode(encoding)
                else:
                    decoded_string += word.decode('utf-8')
            else:
                decoded_string += word
        return decoded_string


    email_address_dict = {

        'SupportTeamMembers': 'soheila.s@abramad.com,parisa.j@abramad.com,soraya.h@abramad.com,mohammad.bar@abramad.com,amir.rz@abramad.com,sadegh.f@abramad.com,rayehe.a@abramad.com,ali.af@abramad.com',
        'NetworkTeamMembers': 'mehdi.a@abramad.com,ali.m@abramad.com,ali.j@abramad.com,behzad.az@abramad.com',
        'CSBTeam': 'alireza.ja@abramad.com,mohsen.sh@abramad.com,mohammad.m@abramad.com,sarah.s@abramad.com,maryam.d@abramad.com,ali.r@abramad.com,ardalan.t@abramad.com',
        'SystemTeamMembers': 'hossein.a@abramad.com,sulmaz.k@abramad.com',
        'SalesTeamMembers': 'mohammad.mr@abramad.com,marjan.z@abramad.com,sheida.r@abramad.com,sadaf.f@abramad.com,noushin.g@abramad.com,faezeh.g@abramad.com',
        'PaaSTeamMembers': 'reza.bey@abramad.com,aref.kh@abramad.com,sarah.ha@abramad.com,payam.b@abramad.com',
        'ITSMTeamMembers': 'ehsan.h@abramad.com,maryam.gh@abramad.com',
        'SecurityTeamMembers': 'roozbeh.r@abramad.com,sadra.a@abramad.com,alireza.sol@abramad.com,mohammadjavad.b@abramad.com,sara.mos@abramad.com,mohammadhossein.y@abramad.com,azita.z@abramad.com',
        'DevelopmentTeamMembers': 'aryan.e@abramad.com,mojtaba.sa@abramad.com,farshad.a@abramad.com,mateen.b@abramad.com,atena.h@abramad.com,mahta.sa@abramad.com,zahra.arj@abramad.com,mahdi.i@abramad.com,arsam.b@abramad.com',
        'MarketingTeamMembers': 'sharareh.b@abramad.com,elnaz.m@abramad.com,marjan.a@abramad.com,fatemeh.gh@abramad.com,yasmin.s@abramad.com',
        'DataCenterTeamMembers': 'zareh.k@abramad.com,farshid.gh@abramad.com,mohammad.ra@abramad.com',
        'IaaSTeamMembers': 'malihe.a@abramad.com,soheil.b@abramadcom,hamid.l@abramad.com,yashar.ans@abramad.com,mohsen.sep@abramad.com,amin.al@abramad.com,ramtin.f@abramad.com',
        'EPMTeamMembers': 'farnaz.sh@abramad.com,alireza.mah@abramad.com',
        'SRETeamMembers': 'roghayeh.s@abramad.com',
        'FinancialTeamMembers': 'sedighe.g@abramad.com,maryam.bo@abramad.com,yeganeh.f@abramad.com',
        'ProductTeamMembers': 'mohammadhossein.kh@abramad.com,amirhossein.gr@abramad.com,amir.re@abramad.com',
        'SysOps': 'soroush.M@abramad.com',
        'ITStandardTeamMember': 'saeedeh.z@abramad.com,fatemeh.sd@abramad.com'

    }

    email_group_dict = {

        'supportteammembers': 'support@abramad.com',
        'networkteammembers': 'networkteam@abramad.com',
        'csbteammembers': 'abramadcomputestorage@abramad.com',
        'systemteammembers': 'system@abramad.com',
        'managedserviceteammembers': 'system@abramad.com',
        'salesteammembers': 'sales@abramad.com',
        'paasteammembers': 'abramadpaas@abramad.com',
        'itsmteammembers': 'itsm@abramad.com',
        'securityteammembers': 'securityteamdep@abramad.com',
        'developmentteammembers': 'development@abramad.com',
        'productteammembers': 'product@abramad.com',
        'marketingteammembers': 'marketing@abramad.com',
        'datacenterteammembers': 'datacenter@abramad.com',
        'iaasteammembers': 'abramadiaas@abramad.com',
        'epmteammembers': 'epm@abramad.com',
        'financialteammembers': 'accounting@abramad.com',
        'sysopsteammembers': 'abramadsysops@abramad.com',
        'itstandardteammember': 'itstandard@abramad.com',
        'mlteammembers': 'mlplatform@abramad.com',
        'nocteammembers': 'noc@abramad.com',
    }

    username = 'abramadalert@abramad.com'
    password = '!@bramad20151360!'
    folder_path = 'ChangeManagement'


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

        # Parse the raw message
        email_message = email.message_from_bytes(raw_msg)

        # Decode the subject
        subject = decode_mime_words(email_message["Subject"])

        # Get the sender
        from_ = decode_mime_words(email_message.get("From"))

        # Initialize body variable
        body = ""

        # If the email message is multipart
        if email_message.is_multipart():
            # Iterate over each part
            for part in email_message.walk():
                # Get the content type
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                # Extract email body (text/plain or text/html)
                if "attachment" not in content_disposition:
                    if content_type == "text/plain":
                        body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')
                        break
                    elif content_type == "text/html":
                        # Optional: If you want the HTML content instead
                        body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')
        else:
            # Email is not multipart, just extract the body
            body = email_message.get_payload(decode=True).decode(email_message.get_content_charset() or 'utf-8')

        # Append the email details to the list
        emails.append({
            "subject": subject,
            "from": from_,
            "body": body
        })

    # Print out all the emails collected
    """for email in emails:
        print(f"Subject: {email['subject']}")
        print(f"From: {email['from']}")
        print(f"Body: {email['body']}\n\n")
        """

    email_body_dict = {}

    # Loop over the emails list using indices
    for i in range(len(emails)):
        # Access the body of each email
        body_content = emails[i]['body']

        # Store the body content in the dictionary, splitting it by pipe
        email_body_dict[f'{i + 1}'] = body_content.replace('\r\n', '').split('|')

    # Print the resulting dictionary
    #for k, v in email_body_dict.items():
    #    print(f"Key: {k}\nValue: {v}\n\n")

    # Value: ['SERVICDESK-18311', 'Add Cinder Policy (Production env)', 'Amin.Al', '24/Sep/24 3:30 PM', '24/Sep/24 4:30 PM', 'Ehsan.H', 'DevelopmentTeamMembers', ' IaaSTeamMembers']
    # 0 -> Ticket No
    # 1 -> Change Subject
    # 2 -> Change Assignee (doer)
    # 3 -> Change Start Date and Time
    # 4 -> Change End Date and Time
    # 5 -> Change Informed People
    # 6 -> Change Informed Groups


    for change in email_body_dict:

        ch_ticket_no = email_body_dict[change][0]
        ch_subject = email_body_dict[change][1]
        ch_assignee = email_body_dict[change][2]
        ch_start_dt = email_body_dict[change][3]
        ch_start_date = miladi_to_miladi_converter(ch_start_dt.split(' ')[0])
        ch_start_time = _12_to_24_hour_converter(' '.join(ch_start_dt.split(' ')[1:3]))
        ch_end_dt = email_body_dict[change][4]
        ch_end_date = miladi_to_miladi_converter(ch_end_dt.split(' ')[0])
        ch_end_time = _12_to_24_hour_converter(' '.join(ch_end_dt.split(' ')[1:3]))
        ch_informed_people = email_body_dict[change][5].split(',')
        ch_informed_groups = email_body_dict[change][6].split(',')



        print(20 * '#')
        print(ch_ticket_no)
        print(ch_subject)
        print(ch_assignee)
        print(ch_start_date)
        print(ch_start_time)
        print(ch_end_date)
        print(ch_end_time)
        print(ch_informed_people)
        print(ch_informed_groups)
        print(20 * '#' + '\n')


        # Meeting details
        subject = f'Change Management | {ch_subject}'
        start = datetime(int(ch_start_date[:4]), int(ch_start_date[5:7]), int(ch_start_date[8:]), int(ch_start_time.split(':')[0]), int(ch_start_time.split(':')[1]) )  # Meeting start time
        end = datetime(int(ch_end_date[:4]), int(ch_end_date[5:7]), int(ch_end_date[8:]), int(ch_end_time.split(':')[0]), int(ch_end_time.split(':')[1]) )  # Meeting end time

        # Body Text
        text_mail = f'''
    <!DOCTYPE html>
    <html dir="rtl">
      <head>
        <meta charset="UTF-8">
      </head>
      <body>
        <div>
          <p style="font-family:'B Koodak';">با سلام و احترام</p>
          <p style="font-family:'B Koodak';">لطفا کلندر قرار گرفته در پیوست با مشخصات زیر را تایید فرمایید:</p>
    
          <table border="1" style="width: 70%; text-align: right; font-family: 'B Koodak';">
            <tr>
              <th>اطلاعات تغییرات</th>
              <th>جزئیات</th>
            </tr>
            <tr>
              <td>شماره تغییرات</td>
              <td>{ch_ticket_no}</td>
            </tr>
            <tr>
              <td>موضوع تغییرات</td>
              <td>{ch_subject}</td>
            </tr>
            <tr>
              <td>مجری تغییرات</td>
              <td>{ch_assignee}</td>
            </tr>
            <tr>
              <td>زمان برنامه ریزی شده جهت اجرای تغییرات</td>
              <td>{start}</td>
            </tr>
            <tr>
              <td>زمان برنامه ریزی شده جهت پایان تغییرات</td>
              <td>{end}</td>
            </tr>
            <tr>
              <td>تیم‌های ذینفعان مطلع</td>
              <td>{', '.join(ch_informed_groups)}</td>
            </tr>
            <tr>
              <td>افراد ذینفع مطلع</td>
              <td>{', '.join(ch_informed_people)}</td>
            </tr>
          </table>
        </div>
        <p style="font-family:'B Koodak'; text-align:right; direction:rtl;">
          برای بازکردن صفحه درخواست به این
          <a class="jsm-issue-link" href="https://jira.abramad.com/projects/SERVICDESK/queues/custom/39/{ch_ticket_no}">
            لینک
          </a>
          مراجعه فرمایید.
        </p>
      </body>
    </html>
    
                '''
        link = f"https://jira.abramad.com/projects/SERVICDESK/queues/custom/39/{ch_ticket_no}"
        text_cal = f'To view the related change, please follow the link below:\n{link} '

        location = f'Jira Ticket No: {ch_ticket_no}'
        attendees = []
        organizer = username
        attendees.append(f'{ch_assignee.lower().strip()}@abramad.com')
        for p in ch_informed_people:
            attendees.append(f"{p.lower().strip()}@abramad.com")
        for g in ch_informed_groups:
            attendees.append(email_group_dict[g.lower().strip()])
        attendees.append('abramadalert@abramad.com')
        attendees.append('ehsan.h@abramad.com')


        #print(attendees)
        #time.sleep(100)
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

    #time.sleep(3)

except Exception as err:
    print(f"Script failed: {err}")
    success = False
    error_string_summary = f"{type(err).__name__}: {err}"

    # Get the traceback and extract the last traceback frame
    tb = traceback.extract_tb(err.__traceback__)
    last_call = tb[-1]  # the last traceback frame, where the exception occurred
    error_string_detail = f"Error occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"



finally:
    # Finalizing Metrics
    # Script Duration
    duration = time.time() - start_time
    duration_gauge.set(duration)

    #Script Success Status
    status_gauge.set(1 if success else 0)

    # Script Total Executions
    total_exec_counts = read_value_from_file(total_exec_counter_file) + 1
    write_value_to_file(total_exec_counter_file, total_exec_counts)
    total_execution_counter.inc(total_exec_counts)

    if not success:
        # Script Total Failed Executions
        total_failed_exec_counts = read_value_from_file(total_failed_exec_counter_file) + 1
        write_value_to_file(total_failed_exec_counter_file, total_failed_exec_counts)
        total_failed_execution_counter.inc(total_failed_exec_counts)

        # Script Last Error Message
        last_error_message.labels(error_summary=error_string_summary, error_detail=error_string_detail).set(1)

    elif success:
        # Script Total Failed Executions
        total_failed_exec_counts = read_value_from_file(total_failed_exec_counter_file)
        total_failed_execution_counter.inc(total_failed_exec_counts)

        # Script Last Error Message
        last_error_message.labels(error_summary="None", error_detail="None").set(0)


    # Push metrics to Pushgateway
    push_to_gateway(
        gateway=pushgateway_url,
        job=job_name,
        grouping_key={'instance': instance, 'target': target, 'datacenter': datacenter},
        registry=registry
    )

    print('✅ Metrics Sent.')
