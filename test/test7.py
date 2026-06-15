

from pyvim import connect
from pyVmomi import vim
import ssl
import warnings
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

username = decryptor("enc_sinaz_abramad","key_sinaz_abramad")
password = decryptor("enc_sinaz_pass","key_sinaz_pass")


# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)
# *** Connecting to ME-VC01.Abramad.Com to get the Report ***
# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

# Connecting to vCenter
ME_VC = connect.SmartConnect(host='mev-vc01.abramad.com', user=username, pwd=password, port=443, sslContext=context)
me_content = ME_VC.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if ( vm.name.startswith("MEV-") )]


sedaas_list = []
sepidar_daas_list = []
daas_list = []
not_configured_list = []

for vm in me_vms:

    # National ID
    vm_nat_id = ""
    vm_custom_attr = vm.summary.customValue
    for i in vm_custom_attr:
        if i.key == 303:
            vm_nat_id = i.value

    # Persian Name
    vm_persian_name = ""
    vm_custom_attr = vm.summary.customValue
    for i in vm_custom_attr:
        if i.key == 301:
            vm_persian_name = i.value


    # SeDaaS
    is_sedaas = 0
    vm_custom_attr = vm.summary.customValue
    for i in vm_custom_attr:
        if i.key == 308:
            is_sedaas = int(i.value)


    # Sepidar DaaS
    is_sepidar_daas = 0
    vm_custom_attr = vm.summary.customValue
    for i in vm_custom_attr:
        if i.key == 307:
            is_sepidar_daas = int(i.value)


    # DaaS
    is_daas = 0
    vm_custom_attr = vm.summary.customValue
    for i in vm_custom_attr:
        if i.key == 306:
            is_daas = int(i.value)


    if is_sedaas:
        sedaas_list.append([vm.name, vm_nat_id, vm_persian_name])

    if is_sepidar_daas:
        sepidar_daas_list.append([vm.name, vm_nat_id, vm_persian_name])

    if is_daas:
        daas_list.append([vm.name, vm_nat_id, vm_persian_name])

    if not is_daas and not is_sedaas and not is_sepidar_daas:
        not_configured_list.append([vm.name, vm_nat_id, vm_persian_name])


print(f"{20 * '#'}\nDaaS VMs:\n")
for i in daas_list:
    print(i)
print(f"{20 * '#'}\n")


print(f"{20 * '#'}\nSeDaaS VMs:\n")
for i in sedaas_list:
    print(i)
print(f"{20 * '#'}\n")


print(f"{20 * '#'}\nSepidar DaaS VMs:\n")
for i in sepidar_daas_list:
    print(i)
print(f"{20 * '#'}\n")


print(f"{20 * '#'}\nNot Configured VMs:\n")
for i in not_configured_list:
    print(i)
print(f"{20 * '#'}\n")