from pyVim.connect import Disconnect
from pyVim import connect
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
    decrypted_password = encryption_key.decrypt(encrypted_password)

    # print(f"Decryped Text: {decrypted_password}")
    return decrypted_password.decode()


username = "sina.z@abramad.com"
password = decryptor("enc_sinaz_pass", "key_sinaz_pass")

# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)
# *** Connecting to vCenter to get the Report ***
# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

# Connecting to vCenter
vra_vc = connect.SmartConnect(host='vra-vc01.abramad.com', user=username, pwd=password, port=443, sslContext=context)
vra_content = vra_vc.RetrieveContent()
vra_vm_view = vra_content.viewManager.CreateContainerView(vra_content.rootFolder, [vim.VirtualMachine], True)
vra_vms = [vm for vm in vra_vm_view.view if (vm.name.startswith("VRA-") and not vm.name.startswith("VRA-HAProxy") and not vm.name.startswith("VRA-Template"))]
vra_sorted_vms = sorted(vra_vms, key=lambda vm: vm.name.lower())

config_pt_begin = '''
{
  "version": "2.0",
  "columns": 10,
  "tiles": [

'''

config_pt_middle_ra = ''


for vm in vra_sorted_vms:

    # Skipping Exceptions
    #if vm.name.lower().startswith('ra-mistest') or vm.name.lower().startswith('ra-test') or vm.name.lower() == 'ra-pentest' or vm.name.lower() == 'ra-ebrahimk' or vm.name.lower() == 'ra-khaf' or vm.name.lower() == 'ra-gslco' or vm.name.lower() == 'ra-mojsevom' or vm.name.lower() == 'ra-gsanatpsh' or vm.name.lower() == 'ra-esacopasha' or vm.name.lower() == 'ra-rayan' or vm.name.lower() == 'ra-cloudbi' or vm.name.lower() == 'ra-eftekharmfg' or vm.name.lower() == 'ra-isakojo' or vm.name.lower() == 'ra-rokaceram' or vm.name.lower() == 'ra-nouragheshm' or vm.name.lower() == 'ra-farsademp' or vm.name.lower() == 'ra-nasajibor' or vm.name.lower() == 'ra-shahedstock' or vm.name.lower() == 'ra-poyaniro':
    #    continue

    vm_power_state = vm.runtime.powerState.lower()
    if vm_power_state == "poweredon":

        # Iterate through the hardware devices to find network adapters
        for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                        # Checking if vm is in 'VRA-1003-Customers' PortGroup
                        if device.backing.port.portgroupKey == 'dvportgroup-4018':

                                config_pt_middle_ra += f'''
    {{
      "type": "HTTP-RAW",
      "label": "{((vm.name).split('-'))[1]}",
      "params": {{
        "url": "https://{(vm.name.split('-'))[1]}.rahkaran.ir",
        "regex": "ورود کاربر",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }}
    }},

'''


config_pt_final_ra = '''



'''



temp_node_count = str(config_pt_begin + config_pt_middle_ra + config_pt_final_ra).split()
nodes = temp_node_count.count('"type":') + 1

config_pt_status = f'''
   {{
      "type": "PING",
      "label": "Internet",
      "params": {{
        "hostname": "1.1.1.1"
      }}
    }},

    {{
      "type": "PING",
      "label": "VRA: {nodes}",
      "params": {{
        "hostname": "1.1.1.1"
      }}
    }}

 ]
}}
'''

config = config_pt_begin + config_pt_middle_ra + config_pt_final_ra + config_pt_status

Disconnect(vra_vc)

# Saving config in file
with open('/docker-volumes/monitoror/config-vra.json', 'w') as file:
    file.write(config)