from pyvim.connect import Disconnect
from pyvim import connect
from pyVmomi import vim
import warnings
import ssl
import os


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

sgusername = 'sina.z@sgcloud.local'
username = 'sina.z@abramad.com'
password = decryptor("enc_sinaz_pass","key_sinaz_pass")


# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)
# *** Connecting to ME-VC01.Abramad.Com to get the Report ***
# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

# Connecting to vCenter
VPS_VC = connect.SmartConnect(host='vc.sgcloud.local', user=sgusername, pwd=password, port=443, sslContext=context)
vps_content = VPS_VC.RetrieveContent()
vps_vm_view = vps_content.viewManager.CreateContainerView(vps_content.rootFolder, [vim.VirtualMachine], True)
vps_vms = [vm for vm in vps_vm_view.view if (vm.name.startswith("VPS-"))]
vps_sorted_vms = sorted(vps_vms, key=lambda vm: vm.name.lower())


vps_list = []

for vm in vps_sorted_vms:
    vps_list.append(vm.name)
    #vm_power_state = vm.runtime.powerState.lower()
    #if vm_power_state == "poweredon":





# Connecting to vCenter
MRA_VC = connect.SmartConnect(host='mra-vc01.abramad.com', user=username, pwd=password, port=443, sslContext=context)
mra_content = MRA_VC.RetrieveContent()
mra_vm_view = mra_content.viewManager.CreateContainerView(mra_content.rootFolder, [vim.VirtualMachine], True)
mra_vms = [vm for vm in mra_vm_view.view if (vm.name.startswith("RA-"))]
mra_sorted_vms = sorted(mra_vms, key=lambda vm: vm.name.lower())


ra_list = []

for vm in mra_sorted_vms:
    ra_list.append(vm.name)


for vps in vps_list:
    for ra in ra_list:

        if vps.split('-')[1].lower() == ra.split('-')[1].lower():
            print(vps)
            break


