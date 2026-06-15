import os
from jira import JIRA


comment = '''
سهیلا سلطانی - 18:12 - 1403/04/19


درود و احترام   
مشترک گرامی    
جهت استفاده از VPN  لطفا از نرم افزار Forticlient، استفاده نمایید، لینک راهنمای اتصال به سرور قرار داده شده است .    




اطلاعات لاگین شما به شرح زیر است:

VPN Username :0384113516
Remote  username: cloud\0384113516
Private IP: 172.17.36.4
Public IP: 92.61.181.53



از طریق سامانه ی selfservice.abramad.com در بخش Forgot Your Password پسورد جدیدی برای اکانت خود ایجاد نمایید.
لازم بــه ذکــر اســت کــه رمــز عبــور کاربــری شــما هــر 180 روز یکبــار، منقضــی شــده و لازم اســت تــا رمــز عبــور جدیــدی تنظیـم گـردد. 


 

لینک دانلود راهنمای فورتی کلاینت:
 
https://abmd.ir/VPN-abramad
 
لینک دانلود فورتی کلاینت:
 
https://abramad.thr-storage.abramad.com:9021/support/forticlient/forticlient.msi


 
با سپاس  
 
تیم فنی ابرآمد
'''



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
jira_username = 'support'
jira_password = decryptor('enc_jira_automation_user','key_jira_automation_user')


# Connect to JIRA with SSL verification disabled
options = {
    'server': jira_url,
    'verify': False  # Disable SSL verification
}

# Create a JIRA client
jira = JIRA(options=options, basic_auth=(jira_username.split('@')[0], jira_password))

issue_dict = {
            'project': {'key': 'SERVICDESK'},
            'issuetype': {'name': 'Archive-Customer-Ticket'},
            'summary': f'امیر دادخواه-0384113516-آقای امیر دادخواه - درخواست سرور توسعه-ArchiveTicket37046',
            'customfield_11717': f'آقای امیر دادخواه - درخواست سرور توسعه',  # Ticket Subject
            'customfield_11328': f'امیر دادخواه',  # Customer Name
            'description': f'تاریخ ثبت تیکت: 1403/04/19 15:04\n\nلطفا مطابق جیرا ثبت شده ، سرور توسعه به استقرار دهنده -  اقای مرتضی طاهرخانی تحویل گردد.',
            'customfield_11223': f'0384113516',  # National ID
            'reporter': {'name': 'jira.portal'},
            'assignee': {'name': 'jira.portal'},
            'customfield_11343': {'name': 'SupportTeamMembers'}

        }

# Create the issue
new_issue = jira.create_issue(fields=issue_dict)

jira.add_comment(new_issue, comment)

# Perform the transition to change the issue state to Resolved
jira.transition_issue(new_issue, '11')

print(f"Issue created: {new_issue.key} ")
