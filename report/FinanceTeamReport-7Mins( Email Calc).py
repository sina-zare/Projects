"""
This code does the stuff below:

1) Take all valid RA-* vms and their Tags from a file created at Farvardin 1402 (Line 213)
2) Take all valid RA-* vms and their RAM, CPU, Disk from its vCenter
3) Calculate VM cost and total price
4) Join all step 1&2 and outputs a file according to the given month

5) Take all valid VPS-* vms and their Tags from its vCenter(Using PowerShell script)
6) Take all valid VPS-* vms and their RAM, CPU, Disk from its vCenter
7) Calculate VM cost and total price
8) Join all step 4&5 and outputs a file according to the given month

9) Email created Files in step 4&8 to the Accountant Team
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email import encoders
from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import csv
import os
import time
import subprocess
import csv
from collections import defaultdict
import datetime

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

today = datetime.date.today()

month_dict = {
    "1": "Dey",
    "2": "Bahman",
    "3": "Esfand",
    "4": "Farvardin",
    "5": "Ordibehesht",
    "6": "Khordad",
    "7": "Tir",
    "8": "Mordad",
    "9": "Shahrivar",
    "10": "Mehr",
    "11": "Aban",
    "12": "Azar"
}

# RAM, CPU, Disk Financial Parameters
ram_price_per_gb = 600000
cpu_price_per_core = 1500000
disk_price_per_gb = 49500

# Calculation of total time spent
total_start_time = time.time()

# Specify the current month
current_month = f'{month_dict[str(today.month)]}-1403'

# Create the directory for the CSV files containing month
parent_directory = 'C:/Users/sina.z/Desktop/RahkaranAbriReport/'
final_path = os.path.join(parent_directory, current_month)
if not os.path.exists(final_path):
    os.makedirs(final_path)

# ***       Running Powershell Script to get MRA Tags              ***

# take RA Tagging start time
mra_ps_start_time = time.time()

# Path to the PowerShell script
mra_ps_script_path = "C:/Users/sina.z/Desktop/Python-Projects/RA-Tag.ps1"

from datetime import datetime

# Get the current time
now = datetime.now()
print(f"\nRunning Powershell script to fetch RA Tags --> {now.strftime('%H:%M:%S')}\n")
# Run the PowerShell script
result = subprocess.run(["powershell.exe", mra_ps_script_path], capture_output=True, text=True)

# Print the output of the PowerShell script
print(result.stdout)

# take MRA Tagging end time
mra_ps_end_time = time.time()
mra_ps_elapsed_time = mra_ps_end_time - mra_ps_start_time
print(f'\nMRA Tag data inserted successfully. The whole Tagging took {mra_ps_elapsed_time:.1f} seconds')

# *** Connecting to MRA-VC01.Abramad.Com to get the Report ***

# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

MRA_VC = connect.SmartConnect(
    host='mra-vc01.abramad.com',
    user= username,
    pwd= password,
    port=443,
    sslContext=context
)
now = datetime.now()
print(f"Start connecting to 'mra-vc01.abramad.com' vCenter --> {now.strftime('%H:%M:%S')}")
# MRA Process Time Calculation
mra_start_time = time.time()

mra_content = MRA_VC.RetrieveContent()


now = datetime.now()
print(f"Connected to 'mra-vc01.abramad.com' --> {now.strftime('%H:%M:%S')}")

mra_vm_view = mra_content.viewManager.CreateContainerView(
    mra_content.rootFolder, [vim.VirtualMachine], True
)
mra_vms = [vm for vm in mra_vm_view.view if (
        (vm.name.startswith("RA-") and not vm.name.startswith("RA-Amini")) or (vm.name.lower() == "mra-ansible") or (vm.name.lower() == "mra-ansible2") or (vm.name.lower() == "mra-updatevm") or (vm.name.lower() == "mra-backup") )]

# Specify the filename and full path to the MRA CSV REP file
mra_rep_filename = f'RA-Rep-{current_month}.csv'
mra_csv_rep_path = os.path.join(final_path, mra_rep_filename)

# path to MRA csv Tag file
mra_csv_tag_filename = f'RA-Tag-{current_month}.csv'
mra_csv_tag_path = os.path.join(final_path, mra_csv_tag_filename)

# Open the MRA Tag file and read its contents
mra_tag_dict = {}

with open(mra_csv_tag_path, newline='', encoding='utf-16-le') as csvfile:
    reader = csv.reader(csvfile)
    # Skip the header row if it exists
    next(reader, None)
    # Create a defaultdict to store the dictionary
    mra_tag_dict = defaultdict(list)
    # Loop through each row in the CSV file
    for row in reader:
        # Use the first column as the key
        key = row[0]
        # Use the rest of the columns as the value
        value = row[1:]
        # Add the value to the dictionary under the key
        mra_tag_dict[key].extend(value)

# Open the MRA CSV Rep file in write mode
with open(mra_csv_rep_path, mode='w', newline='', encoding='utf-8') as file:

    # Create a CSV writer object
    writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    # Write the header row to the CSV file
    writer.writerow(['VM Name', 'VM Power State', 'RAM (GB)', 'CPU', 'Disk (GB)', 'VM MoU & Farsi Name', 'VM Price'])

    # Financial Calculation variable declaration
    total_mra_ram_price = 0
    mra_vm_ram_price = 0
    total_mra_cpu_price = 0
    mra_vm_cpu_price = 0
    total_mra_disk_price = 0
    mra_vm_disk_price = 0
    total_mra_vm_sum_price = 0
    mra_vm_sum_price = 0


    # Write the data to the CSV file
    for vm in mra_vms:
        # Get the sum of virtual hard disk capacity of the virtual machine
        sum_of_disk_capacity = 0
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualDisk):
                sum_of_disk_capacity += device.capacityInBytes

        # Convert the sum of disk capacity to GB
        sum_of_disk_capacity_gb = sum_of_disk_capacity / (1024 * 1024 * 1024)

        # VM Compute Price calculation
        if (vm.runtime.powerState == "poweredOn"):
            mra_vm_ram_price = (int(vm.config.hardware.memoryMB / 1024)) * ram_price_per_gb
            total_mra_ram_price += mra_vm_ram_price
            mra_vm_cpu_price = (vm.config.hardware.numCPU) * cpu_price_per_core
            total_mra_cpu_price += mra_vm_cpu_price
            mra_vm_disk_price = (int(sum_of_disk_capacity_gb)) * disk_price_per_gb
            total_mra_disk_price += mra_vm_disk_price

            mra_vm_sum_price = mra_vm_ram_price + mra_vm_cpu_price + mra_vm_disk_price
            total_mra_vm_sum_price += mra_vm_sum_price

        elif (vm.runtime.powerState == "poweredOff"):
            mra_vm_disk_price = (int(sum_of_disk_capacity_gb)) * disk_price_per_gb
            mra_vm_sum_price = mra_vm_disk_price
            total_mra_vm_sum_price += mra_vm_sum_price

        else:
            print(f"The VM {vm.name} has a strange disk state!")

        # Create a list of data for the current VM
        row = [
            vm.name,
            vm.runtime.powerState,
            int(vm.config.hardware.memoryMB / 1024),
            vm.config.hardware.numCPU,
            int(sum_of_disk_capacity_gb),
            mra_tag_dict[vm.name],
            mra_vm_sum_price,

        ]

        # Write the data to the CSV file
        writer.writerow(row)

    # Append the SGC total cost data to the CSV file
    writer.writerow(['End of the report'])
    writer.writerow([f'Total Server Cost is equal to: {total_mra_vm_sum_price}'])

# MRA End process time calculation
mra_end_time = time.time()

mra_elapsed_time = mra_end_time - mra_start_time
print(f'MRA VM data inserted successfully. The whole process took {mra_elapsed_time:.2f} seconds\n\n')

Disconnect(MRA_VC)



# ***       Running Powershell Script to get VPS Tags             ***

# take VPS Tagging start time
#vps_ps_start_time = time.time()

#vps_ps_script_path = "C:/Users/sina.z/Desktop/Python-Projects/VPS-Tag.ps1"

#print("\nRunning Powershell script to fetch VPS Tags\n")
# Run the PowerShell script
#result = subprocess.run(["powershell.exe", vps_ps_script_path], capture_output=True, text=True)

# Print the output of the PowerShell script
#print(result.stdout)

# take VPS Tagging end time
#vps_ps_end_time = time.time()
#vps_ps_elapsed_time = vps_ps_end_time - vps_ps_start_time
#print(f'\nVPS Tag data inserted successfully. The whole Tagging took {vps_ps_elapsed_time:.1f} seconds')

# *** Connecting to VC.SGCloud.Local to get the Report ***

SGC_VC = connect.SmartConnect(
    host='vc.sgcloud.local',
    user='sina.z@sgcloud.local',
    pwd= password,
    port=443,
    sslContext=context
)

now = datetime.now()
print(f"VPS Tags fetched. --> {now.strftime('%H:%M:%S')}\n")
now = datetime.now()
print(f"Start connecting to 'vc.sgcloud.local' vCenter --> {now.strftime('%H:%M:%S')}")
# SGC Process Time Calculation
sgc_start_time = time.time()

sgc_content = SGC_VC.RetrieveContent()
now = datetime.now()
print(f"Connected to 'vc.sgcloud.local' --> {now.strftime('%H:%M:%S')}")

sgc_vm_view = sgc_content.viewManager.CreateContainerView(
    sgc_content.rootFolder, [vim.VirtualMachine], True
)
sgc_vms = [vm for vm in sgc_vm_view.view if
           ((vm.name.startswith("VPS-") and not vm.name.startswith(
        "VPS-AutoUpTest1") and not vm.name.startswith("VPS-AutoUpTest2") and not vm.name.startswith(
        "VPS-bkptest") and not vm.name.startswith("VPS-Inferatest") and not vm.name.startswith(
        "VPS-NSXTest1") and not vm.name.startswith("VPS-NSXTest2") and not vm.name.startswith(
        "VPS-SolarTest")  and not vm.name.startswith("VPS-BKPTSTDB") and not vm.name.startswith("VPS-FanoosTst") and not vm.name.startswith("VPS-Penet") and not vm.name.startswith("VPS-Penetration"))) or (vm.name.lower() == "ansible") or (vm.name.lower() == "bck") or (vm.name.lower() == "fanoos-1") or (vm.name.lower() == "cloud-demo") or (vm.name.lower() == "cloud-update-vm") or (vm.name.lower() == "drive") or (vm.name.lower() == "sgcloudreport") or (vm.name.lower() == "restorebackup")]

# Specify the filename and full path to the VPS CSV Rep file
sgc_filename = f'VPS-Rep-{current_month}.csv'
sgc_csv_rep_path = os.path.join(final_path, sgc_filename)

# path to VPS csv Tag file
sgc_csv_tag_path = 'C:/Users/sina.z/Desktop/Python-Projects/VPS-Tag-Far-1402.csv'

# Open the VPS Tag file and read its contents
sgc_tag_dict = {}

with open(sgc_csv_tag_path, newline='', encoding='utf-16-le') as csvfile:
    reader = csv.reader(csvfile)
    # Skip the header row if it exists
    next(reader, None)
    # Create a defaultdict to store the dictionary
    sgc_tag_dict = defaultdict(list)
    # Loop through each row in the CSV file
    for row in reader:
        # Use the first column as the key
        key = row[0]
        # Use the rest of the columns as the value
        value = row[1:]
        # Add the value to the dictionary under the key
        sgc_tag_dict[key].extend(value)

# Open the VPS CSV Rep file in write mode
with open(sgc_csv_rep_path, mode='w', newline='', encoding='utf-8') as file:

    # Create a CSV writer object
    writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    # Write the header row to the CSV file
    writer.writerow(['VM Name', 'VM Power State', 'RAM (GB)', 'CPU', 'Disk (GB)', 'VM MoU & Farsi Name', 'VM Price'])

    # Financial Calculation variable declaration
    total_sgc_ram_price = 0
    sgc_vm_ram_price = 0
    total_sgc_cpu_price = 0
    sgc_vm_cpu_price = 0
    total_sgc_disk_price = 0
    sgc_vm_disk_price = 0
    total_sgc_vm_sum_price = 0
    sgc_vm_sum_price = 0

    # Write the data to the CSV file
    for vm in sgc_vms:
        # Get the sum of virtual hard disk capacity of the virtual machine
        sum_of_disk_capacity = 0
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualDisk):
                sum_of_disk_capacity += device.capacityInBytes

        # Convert the sum of disk capacity to GB
        sum_of_disk_capacity_gb = sum_of_disk_capacity / (1024 * 1024 * 1024)

        # VM Compute Price calculation
        if (vm.runtime.powerState == "poweredOn"):
            sgc_vm_ram_price = (int(vm.config.hardware.memoryMB / 1024)) * ram_price_per_gb
            total_sgc_ram_price += sgc_vm_ram_price
            sgc_vm_cpu_price = (vm.config.hardware.numCPU) * cpu_price_per_core
            total_sgc_cpu_price += sgc_vm_cpu_price
            sgc_vm_disk_price = (int(sum_of_disk_capacity_gb)) * disk_price_per_gb
            total_sgc_disk_price += sgc_vm_disk_price

            sgc_vm_sum_price = sgc_vm_ram_price + sgc_vm_cpu_price + sgc_vm_disk_price
            total_sgc_vm_sum_price += sgc_vm_sum_price

        elif (vm.runtime.powerState == "poweredOff"):
            sgc_vm_disk_price = (int(sum_of_disk_capacity_gb)) * disk_price_per_gb
            sgc_vm_sum_price = sgc_vm_disk_price
            total_sgc_vm_sum_price += sgc_vm_sum_price

        else:
            print(f"The VM {vm.name} has a strange disk state!")

        # Create a list of data for the current VM
        row = [
            vm.name,
            vm.runtime.powerState,
            int(vm.config.hardware.memoryMB / 1024),
            vm.config.hardware.numCPU,
            int(sum_of_disk_capacity_gb),
            sgc_tag_dict[vm.name],
            sgc_vm_sum_price
        ]

        # Write the data to the CSV file
        writer.writerow(row)

    # Append the SGC total cost data to the CSV file
    writer.writerow(['End of the report'])
    writer.writerow([f'Total Server Cost is equal to: {total_sgc_vm_sum_price}'])


# SGC End process time calculation
sgc_end_time = time.time()

sgc_elapsed_time = sgc_end_time - sgc_start_time
print(f'SGC VM data inserted successfully. The whole process took {sgc_elapsed_time:.1f} seconds')

Disconnect(SGC_VC)



# Send the CSV file via email
sender_email = 'sina.z@abramad.com'
receiver_email = 'accounting@abramad.com, sina.z@abramad.com'
#cc_email = 'support@abramad.com'

# Create a multipart message object
msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = receiver_email
#msg['Cc'] = cc_email
msg['Subject'] = f'{current_month} Rep files'


# Attachments
mra_attachment = mra_csv_rep_path
sgc_attachment = sgc_csv_rep_path

with open(mra_attachment, 'rb') as f:
    part = MIMEApplication(f.read(), Name=os.path.basename(mra_attachment))
    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(mra_attachment)}"'
    msg.attach(part)

with open(sgc_attachment, 'rb') as f:
    part = MIMEApplication(f.read(), Name=os.path.basename(sgc_attachment))
    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(sgc_attachment)}"'
    msg.attach(part)

# Add HTML email text
msg.attach(MIMEText(
    f'<p>Dear Accounting Team, the attached files contain Rep files related to {current_month}<br>Total VM Cost is calculated in the very last line of both files.<br>Have a Nice day :)<br>Cheers<br><br><br><b>Sina Zare<br><em>Support Team Lead<br>Abramad’s Operation Team</b></em></p>',
    'html'))

# Connect to the SMTP server and send the email 465,*587*,25 (mail.systemgroup.net)

# Send email
smtp_server = 'mail.systemgroup.net'
smtp_port = 587
smtp_username = username
smtp_password = password
with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.sendmail(sender_email, receiver_email, msg.as_string())

with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.sendmail(sender_email, "sina.z@abramad.com", msg.as_string())

now = datetime.now()
print(f'\nEmail is now sent to the recipients successfully. --> {now.strftime("%H:%M:%S")}\n\nCode made with <3 by Sina.Z ')


# Calculation of total time spent
total_end_time = time.time()
total_elapsed_time = (total_end_time - total_start_time) / 60
print(f'Full process took {total_elapsed_time:.1f} minutes')


# breaking the while loop
time.sleep(60)

