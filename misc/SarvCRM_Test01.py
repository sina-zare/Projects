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
                 'درخواست ساخت ماشین ابری', 'درخواست بروزرسانی ماشین ابری', 'نرم افزار فورتی', 'اطلاع رسانی', 'اعلام اختلال احتمالی', 'اعلام احتمال قطعی', 'معرفی نماینده',
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
        if row[1] in username_dict:
            username_data.append([row[0], username_dict[row[1]]])





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
                    'Username': usernames_dict.get(comment[4], 'Unknown')
                }
                ticket_entry['Comments'].append(comment_entry)

            entry['Tickets'].append(ticket_entry)

    combined_data[national_id] = entry

# Display the combined data
"""import pprint

pprint.pprint(combined_data)
while 1:
    cmd = input(': ')
    try:
        for i in combined_data:
            print(eval(cmd))
    except Exception as e:
        print(f'Error: {e}')
"""


for i in combined_data:

    #if combined_data[i]['National_ID'] == '10320238410':
    #print(f'{combined_data[i]})')
    #print(f'Account Name: {combined_data[i]['Account_Name']}')
    #print(f'National ID: {combined_data[i]['National_ID']}')
    print(f'Tickets: {combined_data[i]['Tickets']}')
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n')

print(len(sorted_cases_data))
print(len(sorted_cases_data_non_informational))
