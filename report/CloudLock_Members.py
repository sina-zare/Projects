from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import warnings
import os
import csv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib



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

# *** Connecting to ME-VC01.Abramad.Com to get the Report ***
warnings.filterwarnings("ignore", category=DeprecationWarning)
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

# Connecting to vCenter
MRA_VC = connect.SmartConnect(host='mra-vc01.abramad.com', user=username, pwd=password, port=443, sslContext=context)
mra_content = MRA_VC.RetrieveContent()
mra_vm_view = mra_content.viewManager.CreateContainerView(mra_content.rootFolder, [vim.VirtualMachine], True)
mra_vms = [vm for vm in mra_vm_view.view if (vm.name.startswith("MRA-") or vm.name.startswith("RA-"))]
sorted_vms = sorted(mra_vms, key=lambda vm: vm.name.lower())

cloudlock_servers = []

for vm in sorted_vms:
    if (vm.name.lower().startswith("mra-cloudlock")):

        # retrieve vm IP address
        vm_ip = ""
        if vm.guest is not None:
            for nic in vm.guest.net:
                if nic.ipConfig is not None:
                    for ip in nic.ipConfig.ipAddress:
                        if not ip.ipAddress.startswith('169.254') and not ip.ipAddress.startswith('fe80'):
                            vm_ip = ip.ipAddress

        # retrieve vm Hostname
        vm_hostname = vm.summary.guest.hostName

        cloudlock_servers.append([vm_hostname,vm_ip])

#for i in cloudlock_servers:
#    print(f"{i[0]} : {i[1]}")

# ================================================================================
import requests
import re
cloudlock_customers = {}
#test = [cloudlock_servers[1], cloudlock_servers[2]]
for lock_server in cloudlock_servers:
    # Define the URL of the web page you want to fetch
    url = f"http://{lock_server[1]}:22352/license_monitoring/sessions.html"

    # create a variable for that cloudlock
    temp = lock_server[0].split(".")
    cloudlock_variable_name = temp[0][4:].lower()
    #print(cloudlock_variable_name)

    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Extract the text content from the response
        page_content = response.text

        # Use regular expressions to find all strings starting with "172.17"
        ip_pattern = r"192\.\d{1,3}\.\d{1,3}\.\d{1,3}"  # Regex pattern to match IP addresses
        cloud_pattern = r">(.*?cloud\.local)<"  # Regex pattern to match strings starting after > and before < and ending with "cloud.local"

        #ip_matches = re.findall(ip_pattern, page_content)
        #ip_matches.remove(lock_server[1])
        cloud_matches = re.findall(cloud_pattern, page_content)


        # Combine the matched IP addresses and cloud.local strings
        #matched_strings = ip_matches + cloud_matches

        # Remove duplicates using set and convert to a list
        matched_strings = list(set(cloud_matches))

        # making exec variable global so eval() can retrieve it
        #exec(f"global me_{rahlock_variable_name}_customers")
        # creating list for each rahlock
        #exec(f"me_{rahlock_variable_name}_customers = []")
        # take the matched strings and append them to their corresponding list. runs all that comes between " "
        #exec(f"me_{rahlock_variable_name}_customers.append(matched_strings)")
        # append list using eval() to retrieve it
        #rahlock_customers.append(eval(f"me_{rahlock_variable_name}_customers"))

        cloudlock_customers[f"mra_{cloudlock_variable_name}_customers"] = matched_strings

    else:
        print("Failed to fetch the web page.")

'''
for key, value in cloudlock_customers.items():
    print(f"Key: {key}")
    for i in value:

        print(f"Value: {i}")
    print("****************")
'''




for key, value in cloudlock_customers.items():

    # Open CSV file
    with open(f'C:/Users/sina.z/Desktop/Automation_Reports/CloudLock_Members/{key}.csv', 'w',encoding='utf-8_sig', newline='') as f:

        # Write header
        writer = csv.writer(f)
        writer.writerow(["VM Names"])

        # Write rows from value list
        for data in value:
            writer.writerow([data])

# Taking out last cloudlock server members
last_cloudlock_server_name = list(cloudlock_customers.keys())[-1]
last_cloudlock_server_member_count = len(cloudlock_customers[last_cloudlock_server_name])
left_capacity_to_be_full = 470 - last_cloudlock_server_member_count
#print(last_cloudlock_server_member_count)


if left_capacity_to_be_full < 0:

    # Sending Email

    # Declare (Sender, To, CC)
    sender_email = 'sina.z@abramad.com'
    receiver_email = 'support@abramad.com'
    cc_email = 'mehdi.a@abramad.com, alireza.ja@abramad.com'

    # Create a multipart message object
    msg = MIMEMultipart()
    msg['From'] = 'sina.z@abramad.com'
    msg['To'] = receiver_email
    msg['CC'] = cc_email
    msg['Subject'] = f'هشدار ایجاد سرور قفل ابری جدید | {left_capacity_to_be_full} سرور تا تکمیل ظرفیت سرور {last_cloudlock_server_name[:15]}'

    ##############################################
    ######### HTML Body Begin For Email ##########
    html_line_break = '''
                            <p><br></p>
                        '''
    html_msg_1s = '''
                        <html dir="rtl">
                        <head>
                            <style>
                            .numeric_class {
                                direction: ltr;
    
                            </style>
                          </head>
                          <body>
                        '''
    html_msg_2s = '''
                        <p  style="font-family: DiodrumArabic-Regular">با سلام و احترام</p>
                    '''
    html_msg_3s = f'''
                        <p  style="font-family: DiodrumArabic-Regular">با توجه به گسترش فروش و افزایش تعداد سرور های راهکاران ابری و نزدیک شدن به limit تعداد مشترکین ساپورت شده روی هر سرور قفل، نیازمند ایجاد سرور جدیدی در زیرساخت MRA میباشیم.</p>
                    '''
    html_msg_4s = f'''
                        <p  style="font-family: DiodrumArabic-Regular">تعداد سرور هایی که از <b>{last_cloudlock_server_name[:15]}</b> سرویس میگیرند، <b>{last_cloudlock_server_member_count}</b> سرور میباشد.</p>
                    '''

    html_msg_6s = f'''
                        <p  style="font-family: DiodrumArabic-Regular"> سرور فعلی میتواند به <b>{left_capacity_to_be_full}</b> سرور دیگر تا تکمیل شدن ظرفیتش سرویس دهد.</p>
                        '''
    html_msg_8s = f'''
                        <p style="font-family: DiodrumArabic-Regular"><em><b>سینا زارع<br>سرپرست تیم پشتیبانی ابرآمد<br>واحد عملیات</b></em></p>
                    '''
    html_msg_9s = '''
                          </body>
                        </html>
                        '''

    ######### HTML Body End For Email ##########
    ############################################

    inform_email_body = html_msg_1s + html_msg_2s + html_msg_3s + html_msg_4s + html_msg_6s + html_line_break + html_msg_8s + html_line_break + html_msg_9s

    # Attach Text to email
    msg.attach(MIMEText(inform_email_body, 'html'))

    # Connect to the SMTP server and send the email 465,*587*,25 (mail.systemgroup.net)
    # Send email info
    smtp_server = 'mail.systemgroup.net'
    smtp_port = 587
    smtp_username = username
    smtp_password = password

    # Send email function
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, receiver_email.split(",") + cc_email.split(','), msg.as_string())



Disconnect(MRA_VC)