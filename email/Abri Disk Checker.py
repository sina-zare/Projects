import win32com.client
import html
from win32com.client import constants
from bs4 import BeautifulSoup

def get_outlook_inbox():
    outlook_app = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook_app.GetNamespace("MAPI")
    inbox = namespace.GetDefaultFolder(6)  # 6 represents the Inbox folder
    emails = inbox.Items
    return emails

def extract_emails():
    emails = get_outlook_inbox()
    extracted_emails = []
    for email in emails:
        # Take only UnRead emails
        if email.UnRead:
            extracted_emails.append({
                "Subject": email.Subject,
                "Sender": email.SenderName,
                "ReceivedTime": email.ReceivedTime,
                "Body": email.Body
            })
    return extracted_emails

# Usage example
extracted_emails = extract_emails()
print(len(extracted_emails))

'''
for email in extracted_emails:
    print("Subject:", email["Subject"])
    print("Sender:", email["Sender"])
    print("Received Time:", email["ReceivedTime"])
    print("Body:", email["Body"])
    print("---")
'''

outlook = win32com.client.Dispatch("Outlook.Application")

for email in extracted_emails:
    if email["Subject"].startswith("this is"):
        print(email["Subject"])
        print(email["Body"])
        # Create and send email from outlook
        mail = outlook.CreateItem(0)
        mail.Subject = "Test email subject from sina"
        html = "<body dir='rtl'>سلام کاکا برادر</body>"
        olFormatPlain = 1
        mail.BodyFormat = olFormatPlain
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.text

        mail.Body = text



        mail.To = "sina.z@abramad.com"
        mail.Cc = "sina.z@abramad.com;sinasilver91891.sz@gmail.com"
        mail.Send()