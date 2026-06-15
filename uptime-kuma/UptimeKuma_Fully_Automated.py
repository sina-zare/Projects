from uptime_kuma_api import UptimeKumaApi, MonitorType
from email.mime.multipart import MIMEMultipart
from cryptography.fernet import Fernet
from pyvim.connect import Disconnect
from email.mime.text import MIMEText
from pyvim import connect
from pyVmomi import vim
import jdatetime
import warnings
import smtplib
import time
import ssl
import os




def days_between_persian_dates(persian_date_str):
    # Parse the input Persian date string
    persian_year, persian_month, persian_day = map(int, persian_date_str.split('/'))

    # Create a jdatetime date object from the input date
    input_date = jdatetime.date(persian_year, persian_month, persian_day)

    # Get today's date in Persian calendar
    today_date = jdatetime.date.today()

    # Calculate the difference in days
    delta = (today_date - input_date).days
    return delta


def decryptor(enc_env_var, key_env_var):
    # Load the key
    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = (os.environ.get(enc_env_var)).encode()
    # Decrypt Data
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())

    # print(f"Decryped Text: {decrypted_password}")
    return decrypted_password.decode()


#################################################
################ Data Gathering #################

# Credentials
username = 'sina.z@abramad.com'
password = decryptor("enc_sinaz_pass", "key_sinaz_pass")

# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)
# *** Connecting to ME-VC01.Abramad.Com to get the Report ***
# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

# Connecting to vCenter
me_vc = connect.SmartConnect(host='me-vc01.abramad.com', user=username, pwd=password, port=443, sslContext=context)
me_content = me_vc.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if
          (vm.name.startswith("MER-")) or (vm.name.startswith("MERD-")) or (vm.name.startswith("MEA-"))]
sorted_vms = sorted(me_vms, key=lambda vm: vm.name.lower())

live_vms_all_dict = {}
live_vms_dict = {}
live_vms_set = set()
db_vms_set = set()
deletion_list = []
deletion_dict = {}
addition_list = []
addition_dict = {}

sorted_vms_fnl = []

# Pruning VM list
for vm in sorted_vms:
    if not vm.name.lower().endswith('-t') and not vm.name.lower().endswith('-db'):
        sorted_vms_fnl.append(vm)

for vm in sorted_vms_fnl:
    vm_power_state = vm.runtime.powerState.lower()
    if vm_power_state == "poweredon":

        # Check if node needs to be monitored
        custom_value_m = vm.summary.customValue
        not_monitored = ''
        in_debt = ''
        for i in custom_value_m:
            if i.key == 902:
                not_monitored = i.value
            if i.key == 903:
                in_debt = i.value

        if not_monitored != '1' and in_debt != '1':

            # Get VM Creation Date
            vm_creation_date = ""
            custom_value_d = vm.summary.customValue
            for i in custom_value_d:
                if i.key == 104:
                    vm_creation_date = i.value

            # Check if app is deployed
            if days_between_persian_dates(vm_creation_date) > 20:
                # Get VM URL
                vm_url = ""
                vm_custom_attr = vm.summary.customValue
                for i in vm_custom_attr:
                    if i.key == 604:
                        vm_url = i.value

                if vm_url != "":

                    # Amend URL if needed
                    if not vm_url.lower().strip().startswith('http'):
                        vm_url = 'https://' + vm_url.lower().strip()

                    # Get VM Persian Name
                    vm_persian_name = ""
                    custom_value_n = vm.summary.customValue
                    for i in custom_value_n:
                        if i.key == 103:
                            vm_persian_name = i.value

                    # Get VM Public IP
                    vm_public_ip = ""
                    vm_custom_attr = vm.summary.customValue
                    for i in vm_custom_attr:
                        if i.key == 603:
                            vm_public_ip = i.value

                    if 'http://' in vm_url.lower().strip() or 'https://' in vm_url.lower().strip():
                        live_vms_dict[f'{vm.name}'] = [vm.name, vm_url.lower(), f"{vm_persian_name}\n{vm_public_ip}"]
                        live_vms_set.add(vm.name)

Disconnect(me_vc)


#################################################
############ Comparison Calculation #############

with open("C:\\Users\\sina.z\\Desktop\\Python-Projects\\uptime-kuma-db.txt", 'r') as file:
    for row in file:
        db_vms_set.add(row.rstrip('\n'))

print(f"\nLeaving/Coming Servers:  --> Symmetric Difference <--  {live_vms_set.symmetric_difference(db_vms_set)}\n\n")

if len(db_vms_set) != len(live_vms_set):

    # Finding Old Nodes that should be deleted
    temp_db_vms_set = db_vms_set.copy()  # copying db_vms_set to temp_db_vms_set
    for db_item in temp_db_vms_set:
        if db_item not in live_vms_set:
            # Appending Deletion list
            deletion_list.append(db_item)
            # Discarding item from DB
            db_vms_set.discard(db_item)

    # Finding New Nodes that should be added
    temp_live_vms_set = live_vms_set.copy()  # copying live_vms_set to temp_live_vms_set
    for live_item in live_vms_set:
        if live_item not in db_vms_set:
            # Appending Addition list
            addition_list.append(live_item)
            # Adding item to DB
            db_vms_set.add(live_item)

    # Creating Addition_Dict
    for node_name in addition_list:
        for item in live_vms_dict:
            if node_name == live_vms_dict[f'{node_name}'][0]:
                addition_dict[f'{node_name}'] = live_vms_dict[f'{node_name}']

    """# Creating Deletion_Dict
    for node_name in deletion_list:
        for item in live_vms_dict:
            if node_name == live_vms_dict[f'{node_name}'][0]:
                deletion_dict[f'{node_name}'] = live_vms_dict[f'{node_name}']"""


elif len(db_vms_set) == len(live_vms_set) and db_vms_set != live_vms_dict:

    # Finding Old Nodes that should be deleted
    temp_db_vms_set = db_vms_set.copy()  # copying db_vms_set to temp_db_vms_set
    for db_item in temp_db_vms_set:
        if db_item not in live_vms_set:
            # Appending Deletion list
            deletion_list.append(db_item)
            # Discarding item from DB
            db_vms_set.discard(db_item)

    # Finding New Nodes that should be added
    temp_live_vms_set = live_vms_set.copy()  # copying live_vms_set to temp_live_vms_set
    for live_item in live_vms_set:
        if live_item not in db_vms_set:
            # Appending Addition list
            addition_list.append(live_item)
            # Adding item to DB
            db_vms_set.add(live_item)

    # Creating Addition_Dict
    for node_name in addition_list:
        for item in live_vms_dict:
            if node_name == live_vms_dict[f'{node_name}'][0]:
                addition_dict[f'{node_name}'] = live_vms_dict[f'{node_name}']

    """# Creating Deletion_Dict
    for node_name in deletion_list:
        for item in live_vms_dict:
            if node_name == live_vms_dict[f'{node_name}'][0]:
                deletion_dict[f'{node_name}'] = live_vms_dict[f'{node_name}']"""



##################################################
############ Saving Altered Database #############

with open("C:\\Users\\sina.z\\Desktop\\Python-Projects\\uptime-kuma-db.txt", 'w') as file:
    for item in db_vms_set:
        file.write(item + '\n')



##################################################
######### Adding/Deleting Nodes in Kuma ##########

api = UptimeKumaApi('http://192.168.175.48:3007/')
api.login('admin', 'I4=t8K<xn')
# Fetch all monitors
monitors = api.get_monitors()

# Node Deletion
for node in deletion_list:
    name = node

    monitor_id = None
    for monitor in monitors:
        if monitor['name'].lower() == name.lower():
            monitor_id = monitor['id']
            break

    # If the monitor exists, delete it
    if monitor_id:
        api.delete_monitor(monitor_id)
        print(f"Monitor '{name}' deleted successfully.")
    else:
        print(f"Monitor '{name}' not found.")


# Node Addition
mer_dict = {}
mea_dict = {}

# Distinguishing Services
for node in addition_dict:
    if addition_dict[f'{node}'][0].lower().startswith('mer-') or addition_dict[f'{node}'][0].lower().startswith('merd-'):
        mer_dict[f'{node}'] = addition_dict[f'{node}']
    elif addition_dict[f'{node}'][0].lower().startswith('mea-'):
        mea_dict[f'{node}'] = addition_dict[f'{node}']


# MER Addition
for node in mer_dict:
    name = mer_dict[f'{node}'][0]
    url = mer_dict[f'{node}'][1]
    desc = mer_dict[f'{node}'][2]

    mer_monitor_config = {
        "type": MonitorType.KEYWORD,
        "name": f"{name}",
        "url": f"{url}",
        "keyword": "ورود کاربران",
        "interval": 90,
        "maxretries": 3,
        "retryInterval": 30,
        "timeout": 72,
        "resendInterval": 480,
        "ignoreTls": True,
        "maxredirects": 10,
        "accepted_statuscodes": ['200-299'],
        "description": f"{desc}",
        "notificationIDList": [1, 2]  # Enable Telegram Notification
    }

    try:
        result = api.add_monitor(**mer_monitor_config)
        print(result, end=' : ')
        print(name)
        time.sleep(0.5)
    except Exception as err:
        print(err)




# MEA Addition
for node in mea_dict:
    name = mea_dict[f'{node}'][0]
    url = mea_dict[f'{node}'][1]
    desc = mea_dict[f'{node}'][2]

    mea_monitor_config = {
        "type": MonitorType.HTTP,
        "name": f"{name}",
        "url": f"{url}",
        "interval": 90,
        "maxretries": 3,
        "retryInterval": 30,
        "timeout": 72,
        "resendInterval": 480,
        "maxredirects": 10,
        "ignoreTls": True,
        "accepted_statuscodes": ['200-299'],
        "description": f"{desc}",
        "notificationIDList": [1, 2]  # Enable Telegram Notification
    }

    try:
        result = api.add_monitor(**mea_monitor_config)
        print(result, end=' : ')
        print(name)
        time.sleep(0.5)
    except Exception as err:
        print(err)

api.disconnect()



##################################
######### Sending Email ##########

recievers = "support@abramad.com"
cc = "mehdi.a@abramad.com, alireza.ja@abramad.com"

def email_sender(username, password, email_receivers, email_cc, subject, direction, html_body, mail_server='mail.abramad.com'):

    try:
        # Create a multipart message object
        msg = MIMEMultipart()
        msg['From'] = username
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
                                <p  style="font-family: DiodrumArabic-Regular"><b>Sina Zare<br>Support Team Lead<br>Operation Team</b></p>
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
        print(f"Function Error: {err}")
        email_sender(username,
                     password,
                     recievers,
                     cc,
                     f"Email Function Error in running UptimeKuma_Fully_Automated.py",
                     "ltr",
                     f"Error Occurred:<br><b>{err}</b>")

subject = "UptimeKuma Automatic Node Change"
html_body = f"""
<h4>Change Detected<br>Please regard the list below.</h4>
<p>Added Nodes: {addition_list}<br></p>
<p>Deleted Nodes: {deletion_list}<br></p>
"""

if len(addition_dict) > 0 or len(deletion_list) > 0:
    email_sender(username, password, recievers, cc, subject, 'ltr', html_body, "mail.systemgroup.net")
