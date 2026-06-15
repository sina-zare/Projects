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

# Specify the current month
current_month = input("Enter the current month in this format, [Far-1402]: ")

# Create the directory for the CSV files containing month
parent_directory = 'C:/Users/sina.z/Desktop/RahkaranAbriReport/'
final_path = os.path.join(parent_directory, current_month)
if not os.path.exists(final_path):
    os.makedirs(final_path)


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

print("Connected to ''mra-vc01.abramad.com'")

mra_vm_view = mra_content.viewManager.CreateContainerView(
    mra_content.rootFolder, [vim.VirtualMachine], True
)
mra_vms = [vm for vm in mra_vm_view.view if (vm.name.startswith("RA-") and not vm.name.startswith("RA-Amini") and not vm.name.startswith("RA-MISTest2") and not vm.name.startswith("RA-Mistest") )]


# Specify the filename and full path to the CSV file
mra_filename = f'RA-Rep-{current_month}.csv'
mra_csv_path = os.path.join(final_path, mra_filename)

# Open the CSV file in write mode
with open(mra_csv_path, mode='w', newline='') as file:

    # Create a CSV writer object
    writer = csv.writer(file)

    # Write the header row to the CSV file
    writer.writerow(['VM Name', 'VM Power State', 'RAM (GB)', 'CPU', 'Disk (GB)', 'VM Tag'])

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
            ', '.join([tag.name for tag in vm.tag])
        ]

        # Write the data to the CSV file
        writer.writerow(row)

# MRA End process time calculation
mra_end_time = time.time()

mra_elapsed_time = mra_end_time - mra_start_time
print(f'MRA VM data inserted successfully. The whole process took {mra_elapsed_time:.2f} seconds\n\n')

Disconnect(MRA_VC)





# ***   ***   ***                    ***   ***   ***   ***

# *** Connecting to VC.SGCloud.Local to get the Report ***

# ***   ***   ***                    ***   ***   ***   ***


SGC_VC = connect.SmartConnect(
    host='vc.sgcloud.local',
    user='sina.z@sgcloud.local',
    pwd='S@Bw00fer20936741',
    port=443,
    sslContext=context
)

print("Start connecting to 'vc.sgcloud.local' vCenter...")
# SGC Process Time Calculation
sgc_start_time = time.time()

sgc_content = SGC_VC.RetrieveContent()

print("Connected to 'vc.sgcloud.local'")

sgc_vm_view = sgc_content.viewManager.CreateContainerView(
    sgc_content.rootFolder, [vim.VirtualMachine], True
)
sgc_vms = [vm for vm in sgc_vm_view.view if (vm.name.startswith("VPS-") and not vm.name.startswith("VPS-amini") and not vm.name.startswith("VPS-AutoUpTest1") and not vm.name.startswith("VPS-AutoUpTest2") and not vm.name.startswith("VPS-bkptest") and not vm.name.startswith("VPS-Inferatest") and not vm.name.startswith("VPS-NSXTest1") and not vm.name.startswith("VPS-NSXTest2") and not vm.name.startswith("VPS-SolarTest") and not vm.name.startswith("VPS-AutoUpTest2") and not vm.name.startswith("VPS-BKPTSTDB") and not vm.name.startswith("VPS-FanoosTst") and not vm.name.startswith("VPS-FanoosTst2") and not vm.name.startswith("VPS-Penet") and not vm.name.startswith("VPS-Penetration") )]


# Specify the filename and full path to the CSV file
sgc_filename = f'VPS-Rep-{current_month}.csv'
sgc_csv_path = os.path.join(final_path, sgc_filename)

# Open the CSV file in write mode
with open(sgc_csv_path, mode='w', newline='') as file:

    # Create a CSV writer object
    writer = csv.writer(file)

    # Write the header row to the CSV file
    writer.writerow(['VM Name', 'VM Power State', 'RAM (GB)', 'CPU', 'Disk (GB)', 'VM Tag'])

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
            #', '.join([tag.name for tag in vm.tag])
            vm.tag
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
mra_attachment = mra_csv_path
sgc_attachment = sgc_csv_path

with open(mra_attachment, 'rb') as f:
    part = MIMEApplication(f.read(), Name=os.path.basename(mra_attachment))
    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(mra_attachment)}"'
    msg.attach(part)

with open(sgc_attachment, 'rb') as f:
    part = MIMEApplication(f.read(), Name=os.path.basename(sgc_attachment))
    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(sgc_attachment)}"'
    msg.attach(part)

# Add HTML email text
msg.attach(MIMEText(f'<p>Dear Accounting Team, the attached files contain Rep files related to {current_month}<br>Made with Love :)<br>Cheers<br><br><br><b>Sina Zare<br><em>Support Team Lead<br>Abramad’s Operation Team</b></em></p>', 'html'))


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

print('\nEmail sent successfully.\n\nCode made with <3 by Sina.Z ')


