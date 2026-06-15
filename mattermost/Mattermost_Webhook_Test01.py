ch_ticket_no = "1234"
ch_subject = "موضوع تست"
ch_assignee = "علی رضایی"
start = "2025-08-10 10:00"
end = "2025-08-10 12:00"
ch_informed_groups = ["تیم ۱", "تیم ۲"]
ch_informed_people = ["فرد ۱", "فرد ۲"]

markdown_message = f"""
:rotating_light: **پیام مهم** :rotating_light:

| جزئیات                               | اطلاعات تغییرات                 |
|------------------------------------|-------------------------------|
| {ch_ticket_no}                      | شماره تغییرات                  |
| {ch_subject}                       | موضوع تغییرات                 |
| {ch_assignee}                      | مجری تغییرات                  |
| {start}                          | زمان برنامه ریزی شده جهت اجرای تغییرات |
| {end}                            | زمان برنامه ریزی شده جهت پایان تغییرات |
| {', '.join(ch_informed_groups)}   | تیم‌های ذینفعان مطلع           |
| {', '.join(ch_informed_people)}   | افراد ذینفع مطلع               |

برای بازکردن صفحه درخواست به این [لینک](https://pm.abramad.com/projects/SERVICDESK/queues/custom/39/{ch_ticket_no}) مراجعه فرمایید.
"""


import requests

webhook_url = "https://mattermost.abramad.com/hooks/abciaz9ca3bpdxukx5hofbgpny"
payload = {
    "text": markdown_message
}

{
  "text": ":rotating_light: **Change** :rotating_light:\n\n| جزئیات | اطلاعات تغییرات |\n|---|---|\n| {{issue.key}} | شماره تغییرات |\n| {{issue.summary}} | موضوع تغییرات |\n| {{issue.assignee.displayName}} | مجری تغییرات |\n| {{issue.Start Date}} | زمان برنامه ریزی شده جهت اجرای تغییرات |\n| {{issue.End Date}} | زمان برنامه ریزی شده جهت پایان تغییرات |\n| {{issue.customfield_groups}} | تیم‌های ذینفعان مطلع |\n| {{issue.customfield_people}} | افراد ذینفع مطلع |\n\nبرای بازکردن صفحه درخواست به این [لینک](https://pm.abramad.com/browse/{{issue.key}}) مراجعه فرمایید."
}


response = requests.post(webhook_url, json=payload)

if response.status_code == 200:
    print("Success")
else:
    print(f"Failure: {response.status_code} - {response.text}")
