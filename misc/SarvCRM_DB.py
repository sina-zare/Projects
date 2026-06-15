import openpyxl
import csv
from bs4 import BeautifulSoup
import jdatetime
import datetime
import pytz

# Function to parse Jalali datetime
def parse_jalali_datetime(jalali_str):
    return jdatetime.datetime.strptime(jalali_str, '%Y/%m/%d %H:%M:%S')

# Function to convert Miladi datetime to Shamsi
def convert_miladi_to_shamsi(miladi_datetime_str):
    miladi_format = "%Y-%m-%d %H:%M:%S"
    miladi_datetime = datetime.datetime.strptime(miladi_datetime_str, miladi_format)
    utc_timezone = pytz.utc
    localized_datetime = utc_timezone.localize(miladi_datetime)
    tehran_timezone = pytz.timezone('Asia/Tehran')
    converted_datetime = localized_datetime.astimezone(tehran_timezone)
    converted_date = converted_datetime.date()
    shamsi_date = jdatetime.date.fromgregorian(date=converted_date)
    shamsi_date_str = shamsi_date.strftime("%Y/%m/%d")
    time_str_330 = converted_datetime.strftime("%H:%M:%S")
    return f'{shamsi_date_str} {time_str_330}'

# Reading National_IDs
natid_path = "C:/Users/sina.z/Desktop/Python-Projects/SarvCRM-DB/NatIDs.xlsx"
workbook = openpyxl.load_workbook(natid_path)
sheet = workbook.active
natid_data = []
for row in sheet.iter_rows(values_only=True):
    if len(str(row[3])) < 10 and row[3] is not None:
        temp = [row[0], row[1], row[2], str(row[3]).zfill(10)]
        natid_data.append(temp)
    else:
        natid_data.append(row)

# Reading Tickets
cases_data = []
cases_path = "C:/Users/sina.z/Desktop/Python-Projects/SarvCRM-DB/cases.csv"
with open(cases_path, 'r', encoding='utf-8-sig') as read_file:
    reader = csv.reader(read_file)
    for row in reader:
        if row[2] == 'date_entered':
            continue
        soup = BeautifulSoup(row[6], 'lxml')
        raw_text = soup.get_text()
        converted_dt_case = convert_miladi_to_shamsi(row[2])
        cases_data.append([row[17], row[10], converted_dt_case, row[1], raw_text, row[0]])

# Remove informational tickets
info_keywords = ['اطلاعیه بروزرسانی', 'به اطلاع می‌رساند', 'اخطار قطع موقت', 'ارتقای زیرساخت شبکه', 'اطلاعیه', 'به استحضار می رساند', 'اطلاع\u200cرسانی', 'تمدی', 'تمدید', 'فاکتور',
                 'درخواست ساخت ماشین ابری', 'درخواست بروزرسانی ماشین ابری', 'نرم افزار فورتی', 'اطلاع رسانی', 'اعلام اختلال احتمالی', 'اعلام احتمال قطعی', 'معرفی نماینده', 'نرم افزار فوریت کلاینت برای سیستم عامل لینوکس',
                 'درخواست قطع موقت ماشین ابری', 'درخواست قطع دائم ماشین ابری', 'درخواست حذف ماشین ابری', 'اقدامات توسعه ای', 'جهت بهبود']
sorted_cases_data = sorted(cases_data, key=lambda x: parse_jalali_datetime(x[2]), reverse=True)
sorted_cases_data_non_informational = [ticket for ticket in sorted_cases_data if not any(keyword in ticket[3] for keyword in info_keywords)]

# Reading Comments
comments_data = []  # Ticket_ID  Comment_Date  Comment_value  User_ID

comments_path = "C:/Users/sina.z/Desktop/Python-Projects/SarvCRM-DB/comments.csv"
with open(comments_path, 'r', encoding='utf-8-sig') as read_file:
    reader = csv.reader(read_file)

    for row in reader:

        # Skipping 1st line
        if row[2] == 'date_entered':
            continue

        # Converting miladi to shamsi date and time
        converted_dt_comment = convert_miladi_to_shamsi(row[2])

        # Formatting HTML to raw text
        # Parse the HTML content
        soup_comment = BeautifulSoup(row[6], 'lxml')
        # Get the raw text
        raw_comment = soup_comment.get_text()

        comments_data.append([row[9], converted_dt_comment, row[2], raw_comment, row[4]])


# Sorting the list based on the parsed datetime objects in the second item, from newest to oldest
sorted_comments_data = sorted(comments_data, key=lambda x: parse_jalali_datetime(x[1]), reverse=False)

"""for i in comments_data[:10]:
    print(i[1])
print('~~~~~~~~~~~~~~~~~~~')

for i in sorted_comments_data[:10]:
    print(i[1])"""

# Reading Usernames
username_dict = {
    'sma': 'ربات ابرآمد',
    'soheila.s': 'سهیلا سلطانی',
    'rayehe.a': 'رایحه علیدوستی',
    'mohammad.bar': 'محمد برغش',
    'sadegh.f': 'صادق فعله گری',
    'farshid.gh': 'فرشید قیاسوند',
    'sina.z': 'سینا زارع',
    'amir.rz': 'امیر رضایی',
    'soraya.h': 'ثریا حسینی',
    'parisa.j': 'پریسا جعفری',
    'sheida.r': 'شیدا رستمی',
    'faezeh.g': 'فائزه گندمی',
    'sadaf.f': 'صدف فیاض',
    'noushin.g': 'نوشین قرایی',
    'maryam.mat': 'مریم متمیر',
    'maryam.d': 'مریم دیندوست',
    'navid.r': 'نوید رضایی',
    'mehdi.a': 'مهدی امینی',
    'mohammad.z': 'محمد ذکایی',
    'mohammadreza.n': 'محمدرضا ناگهی',
    'ehsan.h': 'احسان حجت',
    'ali.m': 'علی ملکزاده',
    'alireza.j': 'علیرضا جواهرزاده',
    'bardia.r': 'بردیا رازانی',
    'farnaz.sh': 'فرناز شهرام',
    'mesbah.t': 'مصباح طاهراحمدی',
    'mohsen.sh': 'محسن شهریاری',
    'sharareh.b': 'شراره برادران',
    'abramadrobot': 'ربات ابرآمد',
    'mohammad.m': 'محمد مرادی',
    'marjan.z': 'مرجان زاهدی',
    'marjan.a': 'مرجان احمدی',
    'maryam.hk': 'مریم حاجی کریم',
    'roozbehr': 'روزبه رمضانی',
    'maryambo': 'مریم بوداغی',
    'maryam.b': 'مریم باقیزاده',
    'sedigheg': 'صدیقه گرمسیری',
    'behnam.s': 'بهنام صابری',
    'mina.m': 'مینا محمدی',
    'alireza.n': 'علیرضا ناصح',
    'saeed.k': 'سعید کاظمی',
    'ehsan.o': 'احسان عروه',
    'pouria.e': 'پوریا استکی'
}
username_data = []
username_path = "C:/Users/sina.z/Desktop/Python-Projects/SarvCRM-DB/Users.csv"
with open(username_path, 'r', encoding='utf-8-sig') as read_file:
    reader = csv.reader(read_file)
    for row in reader:
        if row[1].lower() in username_dict:
            username_data.append([row[0], username_dict[row[1].lower()]])





# Create lookup dictionaries

# National_IDs dictionary (excluding entries with 'None')
national_ids_dict = {item[3]: item for item in natid_data if item[3] != 'None'}

# Tickets dictionary indexed by Ticket_ID
tickets_dict = {item[5]: item for item in sorted_cases_data_non_informational}

# Comments dictionary indexed by Ticket_ID
comments_dict = {}
for comment in sorted_comments_data:
    ticket_id = comment[0]
    if ticket_id not in comments_dict:
        comments_dict[ticket_id] = []
    comments_dict[ticket_id].append(comment)

# Usernames dictionary indexed by User_ID
usernames_dict = {item[0]: item[1] for item in username_data}

# Combine data into a single structure

combined_data = {}

for national_id, account_data in national_ids_dict.items():
    entry = {
        'Account_ID': account_data[0],
        'Account_Type': account_data[1],
        'Account_Name': account_data[2],
        'National_ID': account_data[3],
        'Tickets': []
    }

    for ticket_id, ticket in tickets_dict.items():
        if ticket[0] == account_data[0]:
            ticket_entry = {
                'Ticket_Number': ticket[1],
                'Ticket_Date': ticket[2],
                'Ticket_Subject': ticket[3],
                'Ticket_Description': ticket[4],
                'Comments': []
            }

            for comment in comments_dict.get(ticket_id, []):
                comment_entry = {
                    'Comment_Date': comment[1],
                    'Comment_Value': comment[3],
                    'Username': usernames_dict.get(comment[4], 'مشترک')
                }
                ticket_entry['Comments'].append(comment_entry)

            entry['Tickets'].append(ticket_entry)

    combined_data[national_id] = entry


# Normalize the National_ID keys to integers
normalized_data = {}
for key, value in combined_data.items():
    try:
        normalized_key = str(key) if key else None
    except ValueError:
        normalized_key = None
    normalized_data[normalized_key] = value










class Ticket:
    def __init__(self, ticket_id, subject, description, date, comments):
        self.ticket_id = ticket_id
        self.subject = subject
        self.description = description
        self.date = date
        self.comments = comments

    def __str__(self):
        return f"Ticket ID: {self.ticket_id}\nSubject: {self.subject}\nDescription: {self.description}\nDate: {self.date}\nComments: {self.comments}"


class Customer:
    def __init__(self, national_id, name, customer_type):
        self.national_id = national_id
        self.name = name
        self.customer_type = customer_type
        self.tickets = {}

    def add_ticket(self, ticket):
        self.tickets[ticket.ticket_id] = ticket

    def get_ticket(self, ticket_id):
        t_id = self.tickets[ticket_id].ticket_id
        t_date = self.tickets[ticket_id].date
        t_subject = self.tickets[ticket_id].subject
        t_desc = self.tickets[ticket_id].description
        t_comments = self.tickets[ticket_id].comments
        ht_comments = ''

        for t_comment in t_comments:#range(0, len(t_comments)):
            comment_date = t_comment['Comment_Date']
            comment_value = t_comment['Comment_Value']
            comment_username = t_comment['Username']

            ht_comments += f'''
{50 * '~'}
{comment_value}

{comment_username} - {comment_date}

'''

        t_body = f'''
شماره تیکت: {t_id}  -  تاریخ: {t_date}
موضوع: {t_subject}

توضیحات:
{t_desc}


کامنت ها:
{ht_comments}
'''
        return t_body

    def show_tickets(self):
        ticket_ids = list(self.tickets.keys())
        sorted_ticket_ids = sorted(ticket_ids)
        print(f"Ticket Count: {len(sorted_ticket_ids)}\nTicket IDs: {sorted_ticket_ids}\n")

    # Returning an error if someone looks for an attribute of a non-existing ticket
    def __getattr__(self, item):
        if item in self.tickets:
            return self.tickets[item]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

    def __str__(self):
        return f"Customer National ID: {self.national_id}\nName: {self.name}\nType: {self.customer_type}\nTickets: {list(self.tickets.keys())}"


# Dictionary to hold all customer objects
customers = {}

# Iterate through normalized_data and create Customer and Ticket objects
for national_id, data in normalized_data.items():
    if national_id is not None:
        customer = Customer(
            national_id=national_id,
            name=data['Account_Name'],
            customer_type=data['Account_Type']
        )

        for ticket_data in data['Tickets']:
            ticket = Ticket(
                ticket_id=ticket_data['Ticket_Number'],
                subject=ticket_data['Ticket_Subject'],
                description=ticket_data['Ticket_Description'],
                date=ticket_data['Ticket_Date'],
                comments=ticket_data['Comments']
            )
            customer.add_ticket(ticket)

        customers[national_id] = customer

# Filter customers to include only those with tickets
valid_customers = {nat_id: cust for nat_id, cust in customers.items() if len(cust.tickets) != 0}






#################################################################################
#################################################################################


import os
from jira import JIRA

# JIRA instance URL
jira_url = 'https://jira.abramad.com'  # Replace with your Jira server URL

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

# JIRA credentials
jira_username = decryptor("enc_sinaz_abramad","key_sinaz_abramad")
jira_password = decryptor("enc_sinaz_pass","key_sinaz_pass")

# Connect to JIRA with SSL verification disabled
options = {
    'server': jira_url,
    'verify': False  # Disable SSL verification
}

# Create a JIRA client
jira = JIRA(options=options, basic_auth=(jira_username.split('@')[0], jira_password))


"""for nat_id in valid_customers:
    ticket_list_c = valid_customers[nat_id].tickets

    for t in ticket_list_c:
        all_subjects = valid_customers[nat_id].tickets[t].subject"""


# Issue details
issue_dict = {
    'project': {'key': 'SERVICDESK'},
    'issuetype': {'name': 'Customer Incident'},
    'summary': f'SarvCRM{customers['14008905066'].tickets['13850'].ticket_id}-{customers['14008905066'].national_id}-{customers['14008905066'].customer_type}',
    'description': f'{customers['14008905066'].get_ticket('13850')}',
    'customfield_11223': '0058231341',
    'assignee': {'name': 'jira.portal'}
}

# Create the issue
new_issue = jira.create_issue(fields=issue_dict)

# Now update the reporter field separately
#jira.issue(new_issue.key).update(fields={'reporter': {'name': 'jira.portal'}})

print(f"Issue created: {new_issue.key}")