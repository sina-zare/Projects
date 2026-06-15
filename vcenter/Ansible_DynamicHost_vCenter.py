# Module Imports
from cryptography.fernet import Fernet
from pyvim import connect
from pyVmomi import vim
import warnings
import ssl
import os


def decryptor(enc_env_var, key_env_var):

    # Load the key
    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = (os.environ.get(enc_env_var)).encode()
    # Decrypt Data
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())

    #print(f"Decryped Text: {decrypted_password}")
    return decrypted_password.decode()


# Function to check if a VM is under the 'SYSOPS' folder
def is_in_sysops_folder(vm):
    parent = vm.parent
    while parent:
        if isinstance(parent, vim.Folder) and parent.name == "SysOpsTeam":
            return True
        parent = parent.parent
    return False

# ================================================================================ #

username = 'sysops-svc@abramad.com'
password = decryptor('sysops-svc_enc', 'sysops-svc_key')

# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)

# *** Connecting to ME-VC01.Abramad.Com to get the Report ***
# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

# Connecting to vCenter
vc = connect.SmartConnect(host='vab-vc01.abramad.com',user= username,pwd= password,port=443,sslContext=context)
vc_content = vc.RetrieveContent()
vc_vm_view = vc_content.viewManager.CreateContainerView(vc_content.rootFolder, [vim.VirtualMachine], True)

# Filtering VMs in the 'SYSOPS' folder
sysops_vms = [vm for vm in vc_vm_view.view if is_in_sysops_folder(vm)]
sorted_vms = sorted(sysops_vms, key=lambda vm: vm.name)
count = 0

for vm in sorted_vms:

    # VM Name
    vm_name = vm.name

    # retrieve vm IP address
    vm_ip = "0.0.0.0"
    if vm.guest is not None:
        for nic in vm.guest.net:
            if nic.ipConfig is not None:
                for ip in nic.ipConfig.ipAddress:
                    if ip.ipAddress.startswith('172.'): #or ip.ipAddress.startswith('172.21'):
                        vm_ip = ip.ipAddress
    #if 'powerdns' in vm_name.lower():
    print(f"{vm_name} ansible_host={vm_ip}")
    count += 1

    #print(f"{vm_name} ansible_host={vm_ip}")
print(count)
