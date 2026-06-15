import winrm
import os
import re
from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import warnings
from jdatetime import date, datetime

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
username_abramad = decryptor("enc_sinaz_abramad","key_sinaz_abramad")
username_cloud = decryptor("enc_sinaz_cloud","key_sinaz_cloud")
password = decryptor("enc_sinaz_pass","key_sinaz_pass")

# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)
# *** Connecting to ME-VC01.Abramad.Com to get the Report ***
# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

# Connecting to vCenter
ME_VC = connect.SmartConnect(host='me-vc01.abramad.com', user=username_abramad, pwd=password, port=443, sslContext=context)
me_content = ME_VC.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if (vm.name.startswith("MER-") or vm.name.startswith("MERD-") or vm.name.startswith("MEF-") or vm.name.startswith("MES-") or vm.name.startswith("MEA-") or vm.name.startswith("MEB-") or vm.name.startswith("MEM-") or vm.name.startswith("MEI-"))]

# Sort the me_vms list based on VM names
sorted_vms = sorted(me_vms, key=lambda vm: vm.name.lower())
me_servers = {}
me_server_keys = []
me_server_values = []

for vm in sorted_vms:

    if vm.name.lower().startswith("mer-refah"):
        vm_power_state = vm.runtime.powerState
        if vm_power_state.lower() == "poweredon":

            # VM Name
            vm_name = vm.name

            # retrieve vm IP address
            vm_ip = ""
            if vm.guest is not None:
                for nic in vm.guest.net:
                    if nic.ipConfig is not None:
                        for ip in nic.ipConfig.ipAddress:
                            if not ip.ipAddress.startswith('169.254') and not ip.ipAddress.startswith('fe80'):
                                vm_ip = ip.ipAddress

            # vm FQDN
            vm_fqdn = vm.summary.guest.hostName

            me_server_keys.append(vm_name)
            me_server_values.append([vm_fqdn, vm_ip])

# Populate the dictionary within a for loop
for key, value in zip(me_server_keys, me_server_values):
    me_servers[key] = value

print("VMs Taken")

# Log Path
today_date_jalali = date.today().strftime("%Y-%m-%d")
current_time = (str(datetime.now())[11:19]).replace(":", "-")
log_path = f"C:\\Users\\sina.z\\Desktop\\Automation_Reports\\Purge_User_Profiles\\{today_date_jalali}"
full_log_path = f"{log_path}\\{current_time}-Profile-Purge.txt"

# Ensure log directory exists, create if it doesn't
if not os.path.exists(log_path):
    os.makedirs(log_path)

# Deleting Profiles Section

with open(f"{log_path}\\{current_time}-Profile-Purge.txt", "a") as text_file:

    for vm in me_servers:

        # Create a WinRM session with credssp authentication
        session = winrm.Session(me_servers[vm][1], auth=(username_cloud, password), transport='ntlm')

        # Define the command to get directories in C:\\Users
        command = "Get-ChildItem -Path 'C:\\Users' -Directory"
        # Run the command and get the result
        result = session.run_ps(command)
        # Decode the result and split it into lines
        directories = result.std_out.decode().split('\n')
        # taking out Folder Names
        folder_names = [directory_name[48:].strip() for directory_name in directories]


        # Delete directories starting with a number from 0 to 9
        for folder in folder_names:

            if re.match(r'^[0-9]', folder):
                command = f"Remove-Item -Path '{os.path.join("D:\\Test", folder)}' -Recurse -Force"
                session.run_ps(command)
                text_file.write(f"\n{'#' * 90}\n---------------- {vm} ----------------\n'{folder}' User Profile Deleted for {me_servers[vm][0]}.\n{'#' * 90}\n")
                print(f"{folder} Deleted for {vm}")
