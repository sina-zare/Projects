from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import csv
import os
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

# Specify the current date
current_date = input("Enter the current date in this format, [1402-02-23]: ")

# Create the directory for the CSV files containing date
parent_directory = 'C:/Users/sina.z/Desktop/vCenterExports/'
final_path = os.path.join(parent_directory, current_date)
if not os.path.exists(final_path):
    os.makedirs(final_path)


# *** Connecting to ME-VC01.Abramad.Com to get the Report ***

# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

ME_VC = connect.SmartConnect(
    host='me-vc01.abramad.com',
    user= username,
    pwd= password,
    port=443,
    sslContext=context
)


print("Start connecting to 'me-vc01.abramad.com' vCenter...")
# MRA Process Time Calculation
me_start_time = time.time()

me_content = ME_VC.RetrieveContent()

print("Connected to 'me-vc01.abramad.com'")

me_vm_view = me_content.viewManager.CreateContainerView(
    me_content.rootFolder, [vim.VirtualMachine], True
)
me_vms = [vm for vm in me_vm_view.view if (vm.name.startswith("MER-") or vm.name.lower().startswith("MERD-") or vm.name.startswith("MEF-") or vm.name.startswith("MES-") or vm.name.startswith("MEA-") or vm.name.startswith("MEB-") or vm.name.startswith("MEM-") )]

# Specify the filename and full path to the CSV file
me_filename = f'ME-Managed-Servers-{current_date}.csv'
me_csv_path = os.path.join(final_path, me_filename)

# Open the CSV file in write mode
with open(me_csv_path, mode='w', newline='') as file:

    # Create a CSV writer object
    writer = csv.writer(file)

    # Write the header row to the CSV file
    writer.writerow(['VM Name', 'VM Power State', 'IP Address', 'Service', 'Published Port', 'Network Rules'])

    # Write the data to the CSV file
    for vm in me_vms:

        # Find out service
        me_service = {
            "MER": "Rahkaran",
            "MES": "Sepidar",
            "MEF": "Saham Fasl",
            "MEA": "Automation",
            "MEB": "Business Intelligence",
            "MEM": "OS Managed by Abramad"
        }

        # Find out published Port
        me_published_port = {
            "MER": "Either VIP or VServer Published on 80, 443",
            "MES": "Not Published",
            "MEF": "Published on 80, 443",
            "MEA": "If VIP: Published on 7001, If VServer: Published on 80, 443 ",
            "MEB": "Either VIP or VServer Published on 80, 443",
            "MEM": "Variable to customer's request"
        }

        # Find out network rules
        me_network_rule = {
            "MER": "Access from Src Int: any Src: all to Dst Int: CustMGMTService Dst: ME-RahLock-Group on TCP 22350, 22351",
            "MES": "Access from Src Int: SSL Tunnel Src: SepidarLockUsers to Dst Int: CustMGMTService Dst: ME-SepLock01 on TCP 9050, 9051",
            "MEF": "No service level rules required",
            "MEA": "Access from Src Int: any Src: Access-To-DongleSRV to Dst Int: CustMGMTService Dst: (ME-SEH01, ME-SEH02, ME-SEH03, ME-SEH04) on TCP/UDP (9200, 9443) and Ping",
            "MEB": "No service level rules required",
            "MEM": "Variable to customer's request"
        }

        # retrieve vm IP address
        me_vm_ip = ""
        if vm.guest is not None:
            for nic in vm.guest.net:
                if nic.ipConfig is not None:
                    for ip in nic.ipConfig.ipAddress:
                        if not ip.ipAddress.startswith('169.254') and not ip.ipAddress.startswith('fe80'):
                            me_vm_ip = ip.ipAddress


        # Create a list of data for the current VM
        row = [
            vm.name,
            vm.runtime.powerState,
            me_vm_ip,
            me_service[vm.name[:3]],
            me_published_port[vm.name[:3]],
            me_network_rule[vm.name[:3]],
        ]

        # Write the data to the CSV file
        writer.writerow(row)

# ME End process time calculation
me_end_time = time.time()

me_elapsed_time = me_end_time - me_start_time
print(f'ME VM Network rules data inserted successfully. The whole process took {me_elapsed_time:.2f} seconds\n\n')



Disconnect(ME_VC)