from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import warnings
from stdiomask import getpass
import time

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

# Print with delay function
def print_with_delay(text):
    for char in text:
        print(f"Connecting, Please wait {char}", end='', flush=True)
        time.sleep(0.009)
        os.system('cls' if os.name == 'nt' else 'clear')

# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)

print("Here is the VM spec collector, made with love by S.Z")
# *** Connecting to ME-VC01.Abramad.Com to get the Report ***
# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE


username = input("Enter Username to connect to vCenter: ").strip()
# Take password in cipher text
password = getpass("Enter Password to connect to vCenter: ").strip()
receiver_email = input("Enter your Email address: ").lower()

# Clear CMD screen
os.system('cls' if os.name == 'nt' else 'clear')
# Print sequence of characters until connection is made
print_with_delay(["/","--","\\","|","/","--","\\","|","/","--","\\","|","/","--","\\","|","/","--","\\","|","/","--","\\","|"])


ME_VC = connect.SmartConnect(host='me-vc01.abramad.com',user=username,pwd=password,port=443,sslContext=context)
me_content = ME_VC.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if (vm.name.startswith("MER-") or vm.name.startswith("MEF-") or vm.name.startswith("MES-") or vm.name.startswith("MEA-") or vm.name.startswith("MEB-") or vm.name.startswith("MEM-") or vm.name.startswith("MEI-") )]



# Clear CMD screen
os.system('cls' if os.name == 'nt' else 'clear')

while True:
    # take vm name from input
    vm_name = input("Enter target VM name: ").lower().strip()


    # calculate for 'vm not found state' check
    vm_is_found = 0
    for vm in me_vms:

        # find the specified vm
        if (vm.name.lower() == vm_name.lower()):

            # initializing variables
            sum_ssd = 0
            sum_hdd = 0
            sum_capacity = 0
            vm_is_found = 1
            vm_cluster = vm.runtime.host.parent.name

            # VM Power State
            vm_power_state = vm.runtime.powerState.capitalize()

            # Take vm disk's origin and capacity
            for device in vm.config.hardware.device:

                if isinstance(device, vim.vm.device.VirtualDisk):

                    if "-ultraperfssd-" in str(device.backing.fileName).lower():
                        sum_ssd += (device.capacityInBytes / 1024 / 1024 / 1024)
                    elif "-perf-" in str(device.backing.fileName).lower():
                        sum_hdd += (device.capacityInBytes / 1024 / 1024 / 1024)
                    elif "-capacity-" in str(device.backing.fileName).lower():
                        sum_capacity += (device.capacityInBytes / 1024 / 1024 / 1024)

            # Find CPU Type
            if "-highperformance-" in vm_cluster.lower():
                cpu_type = "High Performance"
            elif "-normal-" in vm_cluster.lower():
                cpu_type = "Normal Performance"
            else:
                cpu_type = "N/A"

            # retrieve vm IP address
            vm_ip = ""
            if vm.guest is not None:
                for nic in vm.guest.net:
                    if nic.ipConfig is not None:
                        for ip in nic.ipConfig.ipAddress:
                            if not ip.ipAddress.startswith('169.254') and not ip.ipAddress.startswith('fe80'):
                                vm_ip = ip.ipAddress

            # Get VM Note
            vm_note = vm.config.annotation

            # Check if public IP and URL Exists in VM Notes
            vm_public_ip = ""
            vm_url = ""

            # Get VM Public IP
            vm_custom_attr = vm.summary.customValue
            for i in vm_custom_attr:
                if i.key == 603:
                    vm_public_ip = i.value

            # Get VM URL
            vm_custom_attr = vm.summary.customValue
            for i in vm_custom_attr:
                if i.key == 604:
                    vm_url = i.value

            # Get VM Persian Name
            vm_persian_name = ""
            custom_value_n = vm.summary.customValue
            for i in custom_value_n:
                if i.key == 103:
                    vm_persian_name = i.value

            # Get VM Creation Date
            vm_creation_date = ""
            custom_value_d = vm.summary.customValue
            for i in custom_value_d:
                if i.key == 104:
                    vm_creation_date = i.value


            vm_specs = [
                vm.name,
                vm_ip,
                vm_power_state,
                int(vm.config.hardware.memoryMB / 1024),
                vm.config.hardware.numCPU,
                cpu_type,
                sum_hdd,
                sum_ssd,
                sum_capacity,
                vm_public_ip,
                vm_url,
                vm_note,
                vm_persian_name,
                vm_creation_date
            ]

            try:
                print(f"\n\n~~~~ {vm_specs[0]}  <-->  {vm_specs[2]} ~~~~\n\n^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nRAM: {vm_specs[3]}GB\nCPU: {vm_specs[4]} core - {vm_specs[5]}\nHDD Disk: {vm_specs[6]:.0f}GB\nSSD Disk: {vm_specs[7]:.0f}GB\nCapacity Disk: {vm_specs[8]:.0f}GB\nPrivate IP: {vm_specs[1]}\nPublic IP: {vm_specs[9]}\nURL: {vm_specs[10]}\n^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n\nAdditional Description:\n{vm_specs[11]}\nCreation Date: {vm_specs[13]}\nPersian Name: {vm_specs[12]}\n\n\n")
            except IndexError:
                vm_note.append("")
                vm_note.append("")
                print(f"\n\n~~~~ {vm_specs[0]}  <-->  {vm_specs[2]} ~~~~\n\n^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nRAM: {vm_specs[3]}GB\nCPU: {vm_specs[4]} core - {vm_specs[5]}\nHDD Disk: {vm_specs[6]:.0f}GB\nSSD Disk: {vm_specs[7]:.0f}GB\nCapacity Disk: {vm_specs[8]:.0f}GB\nPrivate IP: {vm_specs[1]}\nPublic IP: {vm_specs[9]}\nURL: {vm_specs[10]}\n^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n\nAdditional Description:\n{vm_specs[11]}\nCreation Date: {vm_specs[13]}\nPersian Name: {vm_specs[12]}\n\n\n")

    if vm_is_found == 0:
        print("\nVM does not exist!, try again")
        continue


    # give options
    button = int(input("Choose from options below:\n1) Continue\n2) Email the specs\n3) Exit\ninput your choice: "))
    os.system('cls' if os.name == 'nt' else 'clear')
    if button == 1:
        continue

    elif button == 2:
        # Send the text via email
        sender_email = 'sina.z@abramad.com'

        # Create a multipart message object
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f'{vm_specs[0]} Specifications | {vm_specs[10]}'

        # Add HTML email text
        msg.attach(MIMEText(
            f'<p>The information below is sent to you by <b>Spec Collector</b><br><br><br>~~~~ {vm_specs[0]}  <-->  {vm_specs[2]} ~~~~<br><br>^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^<br>RAM: {vm_specs[3]}GB<br>CPU: {vm_specs[4]} core - {vm_specs[5]}<br>HDD Disk: {vm_specs[6]:.0f}GB<br>SSD Disk: {vm_specs[7]:.0f}GB<br>Capacity Disk: {vm_specs[8]:.0f}GB<br>Private IP: {vm_specs[1]}<br>Public IP: {vm_specs[9]}<br>URL: {vm_specs[10]}<br>^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^<br><br>Additional Description:<br>{vm_specs[11]}<br>Creation Date: {vm_specs[13]}<br>Persian Name: {vm_specs[12]}<br><br><br><br><br><br>The applet is brought to you by <b>S.Z</b><br>Made with <3<br><br><br><b>Sina Zare<br><em>Support Team Lead<br>Abramad’s Operation Team</b></em></p>',
            'html'))

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
            server.sendmail(sender_email, receiver_email, msg.as_string())

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, "sina.z@abramad.com", msg.as_string())

        button_after_email_sent = int(input("Email sent!\nWanna continue or exit?\n1) Continue\n2) Exit\n"))
        os.system('cls' if os.name == 'nt' else 'clear')
        if button_after_email_sent == 1:
            continue
        elif button_after_email_sent == 2:
            break
        else:
            print("Pardon? Getting you back to start point")

    elif button == 3:
        break
        Disconnect(ME_VC)
