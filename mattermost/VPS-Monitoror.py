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

    # print(f"Decryped Text: {decrypted_password}")
    return decrypted_password.decode()


username = decryptor("enc_sinaz_abramad", "key_sinaz_abramad")
password = decryptor("enc_sinaz_pass", "key_sinaz_pass")

# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)
# *** Connecting to vCenter to get the Report ***
# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE


################ VPS #################
# Connecting to vCenter
vps_vc = connect.SmartConnect(host='vc.sgcloud.local', user='sina.z@sgcloud.local', pwd=password, port=443, sslContext=context)
vps_content = vps_vc.RetrieveContent()
vps_vm_view = vps_content.viewManager.CreateContainerView(vps_content.rootFolder, [vim.VirtualMachine], True)
vps_vms = [vm for vm in vps_vm_view.view if (vm.name.startswith("VPS-"))]
vps_sorted_vms = sorted(vps_vms, key=lambda vm: vm.name.lower())

config_pt_begin = '''
{
  "version": "2.0",
  "columns": 30,
  "tiles": [

'''
config_pt_middle_vps = ''
config_pt_final_vps = ''

for vm in vps_sorted_vms:

    # Skipping Exceptions
    if vm.name == 'VPS-Z' :
        continue

    vm_power_state = vm.runtime.powerState.lower()
    if vm_power_state == "poweredon":

        config_pt_middle_vps += f'''
    {{
      "type": "HTTP-RAW",
      "label": "{vm.name}",
      "params": {{
        "url": "https://{(vm.name.split('-'))[1]}.rahkaran.ir",
        "regex": "ورود کاربر",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }}
    }},

'''


config_pt_final_vps = '''
    {
      "type": "HTTP-STATUS",
      "label": "P8) VPS",
      "params": {
        "url": "https://www.google.com",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    }


 ]
}
'''


Disconnect(vps_vc)
config = config_pt_begin + config_pt_middle_vps + config_pt_final_vps
print(config)