from pyVim import connect
from pyVim.connect import Disconnect
from pyVmomi import vim
import ssl
import warnings
from cryptography.fernet import Fernet
import os

def decryptor(enc_env_var, key_env_var):
    # Load the key
    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = (os.environ.get(enc_env_var)).encode()
    # Decrypt Data
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())
    # print(f"Decrypted Text: {decrypted_password}")
    return decrypted_password.decode()


username = 'sysops-svc@abramad.com'
password = decryptor('sysops-svc_enc', 'sysops-svc_key')

# Ignore the warning/# Create an SSL context with no certificate verification
warnings.filterwarnings("ignore", category=DeprecationWarning)
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE
vm_dict = {}
vcenter = 'vab-vc01.abramad.com'

# Connecting to vCenter
print(f'connecting to {vcenter}')
vc = connect.SmartConnect(host=vcenter, user=username, pwd=password, port=443, sslContext=context)
content = vc.RetrieveContent()
vm_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
print('gathering vms')

vms = [vm for vm in vm_view.view if vm.name.lower() == 'vae-uag01']

for vm in vms:

    vm_name = vm.name

    vm_uuid = vm.config.uuid

    # retrieve vm ip address
    vm_private_ip = "N/A"
    if vm.guest is not None:
        candidate_ips = []
        for nic in vm.guest.net:
            if nic.ipConfig is not None:
                for ip in nic.ipConfig.ipAddress:
                    candidate_ips.append(ip.ipAddress)

        for ip in candidate_ips:
            if not ip.startswith(('169.254', 'fe80')):
                vm_private_ip = ip
                break

    print(f'Name: {vm_name}\nUUID: {vm_uuid}\nPrivate IP: {vm_private_ip}')

Disconnect(vc)