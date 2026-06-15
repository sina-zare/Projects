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

# Connecting to vCenter
mra_vc = connect.SmartConnect(host='mra-vc01.abramad.com', user=username, pwd=password, port=443, sslContext=context)
mra_content = mra_vc.RetrieveContent()
mra_vm_view = mra_content.viewManager.CreateContainerView(mra_content.rootFolder, [vim.VirtualMachine], True)
mra_vms = [vm for vm in mra_vm_view.view if (vm.name.startswith("RA-"))]
mra_sorted_vms = sorted(mra_vms, key=lambda vm: vm.name.lower())

config_pt_begin = '''
{
  "version": "2.0",
  "columns": 30,
  "tiles": [

'''

config_pt_middle_ra = ''


for vm in mra_sorted_vms:

    # Skipping Exceptions
    if vm.name.lower().startswith('ra-mistest') or vm.name.lower().startswith('ra-test') or vm.name.lower() == 'ra-pentest' or vm.name.lower() == 'ra-ebrahimk' or vm.name.lower() == 'ra-khaf' or vm.name.lower() == 'ra-gslco' or vm.name.lower() == 'ra-mojsevom' or vm.name.lower() == 'ra-gsanatpsh' or vm.name.lower() == 'ra-esacopasha' or vm.name.lower() == 'ra-rayan' or vm.name.lower() == 'ra-cloudbi' or vm.name.lower() == 'ra-eftekharmfg' or vm.name.lower() == 'ra-isakojo' or vm.name.lower() == 'ra-rokaceram' or vm.name.lower() == 'ra-nouragheshm' or vm.name.lower() == 'ra-farsademp' or vm.name.lower() == 'ra-nasajibor' or vm.name.lower() == 'ra-shahedstock' or vm.name.lower() == 'ra-poyaniro':
        continue

    vm_power_state = vm.runtime.powerState.lower()
    if vm_power_state == "poweredon":

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
    
    {
      "type": "HTTP-RAW",
      "label": "Ebrahimk",
      "params": {
        "url": "https://Ebrahimk.rahkaran.ir",
        "regex": "Login",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },
    
    {
      "type": "HTTP-RAW",
      "label": "EftekharMFG",
      "params": {
        "url": "https://unco.rahkaran.ir",
        "regex": "ﻭﺭﻭﺩ ﮎﺍﺮﺑﺭ",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },
    
    {
      "type": "HTTP-RAW",
      "label": "esacopasha",
      "params": {
        "url": "https://pashazadeh.rahkaran.ir",
        "regex": "ﻭﺭﻭﺩ ﮎﺍﺮﺑﺭ",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },
    
    {
      "type": "HTTP-RAW",
      "label": "IsakoJo",
      "params": {
        "url": "https://easyyadak.rahkaran.ir",
        "regex": "ﻭﺭﻭﺩ ﮎﺍﺮﺑﺭ",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },
    
    {
      "type": "HTTP-RAW",
      "label": "Konsersiom",
      "params": {
        "url": "https://ilmc.rahkaran.ir",
        "regex": "ﻭﺭﻭﺩ ﮎﺍﺮﺑﺭ",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },
    
    {
      "type": "HTTP-RAW",
      "label": "Khaf",
      "params": {
        "url": "https://khafcement.rahkaran.ir",
        "regex": "ورود کاربر",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },
    
    {
      "type": "HTTP-RAW",
      "label": "Farsademp",
      "params": {
        "url": "https://farsadsanat.rahkaran.ir",
        "regex": "ﻭﺭﻭﺩ ﮎﺍﺮﺑﺭ",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },
    
    {
      "type": "HTTP-RAW",
      "label": "Gsanatpsh",
      "params": {
        "url": "https://golchin.rahkaran.ir",
        "regex": "ﻭﺭﻭﺩ ﮎﺍﺮﺑﺭ",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },
    
    {
      "type": "HTTP-RAW",
      "label": "GSLCo",
      "params": {
        "url": "https://GSLCo.rahkaran.ir",
        "regex": "Login",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },

     {
      "type": "HTTP-RAW",
      "label": "MojSevom",
      "params": {
        "url": "https://Mandegar.rahkaran.ir",
        "regex": "ﻭﺭﻭﺩ ﮎﺍﺮﺑﺭ",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },
    
    {
      "type": "HTTP-RAW",
      "label": "Nouragheshm",
      "params": {
        "url": "https://domil.rahkaran.ir",
        "regex": "ﻭﺭﻭﺩ ﮎﺍﺮﺑﺭ",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },
    
     {
      "type": "HTTP-RAW",
      "label": "Rayan",
      "params": {
        "url": "https://ParsAnahid.rahkaran.ir",
        "regex": "ﻭﺭﻭﺩ ﮎﺍﺮﺑﺭ",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },
    
    {
      "type": "HTTP-RAW",
      "label": "RokaCeram",
      "params": {
        "url": "https://ronikaceram.rahkaran.ir",
        "regex": "ﻭﺭﻭﺩ ﮎﺍﺮﺑﺭ",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },


'''



temp_node_count = str(config_pt_begin + config_pt_middle_ra + config_pt_final_ra).split()
nodes = temp_node_count.count('"type":') + 1

config_pt_status = f'''
   {{
      "type": "PING",
      "label": "Internet Connection",
      "params": {{
        "hostname": "1.1.1.1"
      }}
    }},

    {{
      "type": "PING",
      "label": "ME-RA Nodes: {nodes}",
      "params": {{
        "hostname": "1.1.1.1"
      }}
    }}

 ]
}}
'''

config = config_pt_begin + config_pt_middle_ra + config_pt_final_ra + config_pt_status

Disconnect(mra_vc)

# Saving config in file
with open('/docker-volumes/monitoror/config-abri.json', 'w') as file:
    file.write(config)

