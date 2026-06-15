"""
This code does the stuff below:

1) Take all valid RA-* vms and their Tags from a file created at Farvardin 1402 (Line 213)
2) Take all valid RA-* vms and their RAM, CPU, Disk from its vCenter
3) Join all step 1&2 and outputs a file according to the given month

4) Take all valid VPS-* vms and their Tags from its vCenter(Using PowerShell script)
5) Take all valid VPS-* vms and their RAM, CPU, Disk from its vCenter
6) Join all step 4&5 and outputs a file according to the given month

7) Email created Files in step 3&6 to the Accountant Team
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email import encoders
from pyVim import connect
from pyVim.connect import Disconnect
from pyVmomi import vim
import ssl
import csv
import os
import time
import subprocess
import csv
from collections import defaultdict

# Calculation of total time spent
total_start_time = time.time()

# Specify the current month
current_month = input("Enter the current month in this format, [Far-1402]: ")

# Create the directory for the CSV files containing month
parent_directory = 'C:/Users/sina.z/Desktop/RahkaranAbriReport/'
final_path = os.path.join(parent_directory, current_month)
if not os.path.exists(final_path):
    os.makedirs(final_path)

# ***       Running Powershell Script to get MRA Tags              ***

# take RA Tagging start time
mra_ps_start_time = time.time()

# Path to the PowerShell script
mra_ps_script_path = "C:/Users/sina.z/Desktop/Python/RA-Tag.ps1"

print("\nRunning Powershell script to fetch RA Tags\n")
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
    user='sina.z@abramad.com',
    pwd='S@Bw00fer20936741',
    port=443,
    sslContext=context
)

print("Start connecting to 'mra-vc01.abramad.com' vCenter...")
# MRA Process Time Calculation
mra_start_time = time.time()

mra_content = MRA_VC.RetrieveContent()

print("Connected to 'mra-vc01.abramad.com'")

mra_vm_view = mra_content.viewManager.CreateContainerView(
    mra_content.rootFolder, [vim.VirtualMachine], True
)
mra_vms = [vm for vm in mra_vm_view.view if (
            vm.name.startswith("RA-") and not vm.name.startswith("RA-Amini") and not vm.name.startswith(
        "RA-MISTest2") and not vm.name.startswith("RA-Mistest"))]

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
    writer.writerow(['VM Name', 'VM Power State', 'RAM (GB)', 'CPU', 'Disk (GB)', 'VM MoU & Farsi Name'])

    # Write the data to the CSV file
    for vm in mra_vms:
        # Get the sum of virtual hard disk capacity of the virtual machine
        sum_of_disk_capacity = 0
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualDisk):
                sum_of_disk_capacity += device.capacityInBytes

        # Convert the sum of disk capacity to GB
        sum_of_disk_capacity_gb = sum_of_disk_capacity / (1024 * 1024 * 1024)

        # Create a list of data for the current VM
        row = [
            vm.name,
            vm.runtime.powerState,
            int(vm.config.hardware.memoryMB / 1024),
            vm.config.hardware.numCPU,
            int(sum_of_disk_capacity_gb),
            mra_tag_dict[vm.name]
        ]

        # Write the data to the CSV file
        writer.writerow(row)

# MRA End process time calculation
mra_end_time = time.time()

mra_elapsed_time = mra_end_time - mra_start_time
print(f'MRA VM data inserted successfully. The whole process took {mra_elapsed_time:.2f} seconds\n\n')

Disconnect(MRA_VC)

# ***       Running Powershell Script to get VPS Tags             ***

# take VPS Tagging start time
#vps_ps_start_time = time.time()

#vps_ps_script_path = "C:/Users/sina.z/Desktop/Python/VPS-Tag.ps1"

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
    pwd='S@Bw00fer20936741',
    port=443,
    sslContext=context
)

print("VPS Tags fetched.\n")
print("Start connecting to 'vc.sgcloud.local' vCenter...")
# SGC Process Time Calculation
sgc_start_time = time.time()

sgc_content = SGC_VC.RetrieveContent()

print("Connected to 'vc.sgcloud.local'")

sgc_vm_view = sgc_content.viewManager.CreateContainerView(
    sgc_content.rootFolder, [vim.VirtualMachine], True
)
sgc_vms = [vm for vm in sgc_vm_view.view if (
            vm.name.startswith("VPS-") and not vm.name.startswith("VPS-amini") and not vm.name.startswith(
        "VPS-AutoUpTest1") and not vm.name.startswith("VPS-AutoUpTest2") and not vm.name.startswith(
        "VPS-bkptest") and not vm.name.startswith("VPS-Inferatest") and not vm.name.startswith(
        "VPS-NSXTest1") and not vm.name.startswith("VPS-NSXTest2") and not vm.name.startswith(
        "VPS-SolarTest") and not vm.name.startswith("VPS-AutoUpTest2") and not vm.name.startswith(
        "VPS-BKPTSTDB") and not vm.name.startswith("VPS-FanoosTst") and not vm.name.startswith(
        "VPS-FanoosTst2") and not vm.name.startswith("VPS-Penet") and not vm.name.startswith("VPS-Penetration"))]

# Specify the filename and full path to the VPS CSV Rep file
sgc_filename = f'VPS-Rep-{current_month}.csv'
sgc_csv_rep_path = os.path.join(final_path, sgc_filename)

# path to VPS csv Tag file
sgc_csv_tag_path = 'C:/Users/sina.z/Desktop/Python/VPS-Tag-Far-1402.csv'

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
    writer.writerow(['VM Name', 'VM Power State', 'RAM (GB)', 'CPU', 'Disk (GB)', 'VM MoU & Farsi Name'])

    # Write the data to the CSV file
    for vm in sgc_vms:
        # Get the sum of virtual hard disk capacity of the virtual machine
        sum_of_disk_capacity = 0
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualDisk):
                sum_of_disk_capacity += device.capacityInBytes

        # Convert the sum of disk capacity to GB
        sum_of_disk_capacity_gb = sum_of_disk_capacity / (1024 * 1024 * 1024)

        # Create a list of data for the current VM
        row = [
            vm.name,
            vm.runtime.powerState,
            int(vm.config.hardware.memoryMB / 1024),
            vm.config.hardware.numCPU,
            int(sum_of_disk_capacity_gb),
            sgc_tag_dict[vm.name]
        ]

        # Write the data to the CSV file
        writer.writerow(row)

# SGC End process time calculation
sgc_end_time = time.time()

sgc_elapsed_time = sgc_end_time - sgc_start_time
print(f'MRA VM data inserted successfully. The whole process took {sgc_elapsed_time:.1f} seconds')

Disconnect(SGC_VC)



# Send the CSV file via email
sender_email = 'sina.z@abramad.com'
receiver_email = 'sina.z@abramad.com'

# Create a multipart message object
msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = receiver_email
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
    f'<p>Dear Accounting Team, the attached files contain Rep files related to {current_month}<br>Have a Nice day :)<br>Cheers<br><br><br><b>Sina Zare<br><em>Support Team Lead<br>Abramad’s Operation Team</b></em></p>',
    'html'))

# Connect to the SMTP server and send the email 465,*587*,25 (mail.systemgroup.net)

# Send email
smtp_server = 'mail.systemgroup.net'
smtp_port = 587
smtp_username = 'sina.z@abramad.com'
smtp_password = 'S@Bw00fer20936741'
with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.sendmail(sender_email, receiver_email, msg.as_string())

print('\nEmail is now sent to the recipients successfully.\n\nCode made with <3 by Sina.Z')


# Calculation of total time spent
total_end_time = time.time()
total_elapsed_time = (total_end_time - total_start_time) / 60
print(f'Full process took {total_elapsed_time:.1f} minutes')


# breaking the while loop
time.sleep(60)


