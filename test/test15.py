from pyVim import connect
from pyVim.connect import Disconnect
from pyVmomi import vim
from email.header import Header
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

prefixes = ("vr1-", "vr2-", "vr3-", "vrd-", "vat-", "vbi-", "vmi-", "vsp-", "vsf-", "via-")

# Ignore the warning/# Create an SSL context with no certificate verification
warnings.filterwarnings("ignore", category=DeprecationWarning)
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

# Connecting to vCenter
print('connecting to vc')
vc = connect.SmartConnect(host='me-vc01.abramad.com', user=username, pwd=password, port=443, sslContext=context)
content = vc.RetrieveContent()
vm_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
print('gathering vms')
vms = [vm for vm in vm_view.view if vm.name.lower().startswith('mer-rahkarsg')]

# Sort the me_vms list based on VM names
#print('sorting vms')
#sorted_vms = sorted(vms, key=lambda vm: vm.name.lower())

for vm in vms:

    # get vm custom attributes
    print(vm.name)
    vm_attrs = {}
    for attr in vm.summary.customValue:
        # Attribute key value check
        print(f'{attr.key}: {attr.value}')
