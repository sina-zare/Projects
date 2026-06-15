from pyvim.connect import Disconnect
from pyvim import connect
from pyVmomi import vim
import jdatetime
import warnings
import ssl
import os


def days_between_persian_dates(persian_date_str):
    # Parse the input Persian date string
    persian_year, persian_month, persian_day = map(int, persian_date_str.split('/'))

    # Create a jdatetime date object from the input date
    input_date = jdatetime.date(persian_year, persian_month, persian_day)

    # Get today's date in Persian calendar
    today_date = jdatetime.date.today()

    # Calculate the difference in days
    delta = (today_date - input_date).days
    return delta


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

username = 'sina.z@abramad.com'
password = decryptor("enc_sinaz_pass","key_sinaz_pass")


# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)
# *** Connecting to ME-VC01.Abramad.Com to get the Report ***
# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

# Connecting to vCenter
ME_VC = connect.SmartConnect(host='me-vc01.abramad.com', user=username, pwd=password, port=443, sslContext=context)
me_content = ME_VC.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if (vm.name.startswith("MER-")) or (vm.name.startswith("MERD-")) or (vm.name.startswith("MEA-"))]
sorted_vms = sorted(me_vms, key=lambda vm: vm.name.lower())

config_pt_begin = '''
{
  "version": "2.0",
  "columns": 12,
  "tiles": [

'''

config_pt_middle = ''

sorted_vms_fnl = []

for vm in sorted_vms:
    if not vm.name.lower().endswith('-t') and not vm.name.lower().endswith('-db'):
        sorted_vms_fnl.append(vm)


for vm in sorted_vms_fnl:

    vm_power_state = vm.runtime.powerState.lower()
    if vm_power_state == "poweredon":

        # Check if node needs to be monitored
        custom_value_m = vm.summary.customValue
        not_monitored = ''
        in_debt = ''
        for i in custom_value_m:
            if i.key == 902:
                not_monitored = i.value
            if i.key == 903:
                in_debt = i.value

        if not_monitored != '1' and in_debt != '1':

            # Get VM Creation Date
            vm_creation_date = ""
            custom_value_d = vm.summary.customValue
            for i in custom_value_d:
                if i.key == 104:
                    vm_creation_date = i.value

            # Check if app is deployed
            if days_between_persian_dates(vm_creation_date) > 20:
                # Get VM URL
                vm_url = ""
                vm_custom_attr = vm.summary.customValue
                for i in vm_custom_attr:
                    if i.key == 604:
                        vm_url = i.value


                if vm_url != "":
                    # Amend URL if needed
                    if not vm_url.lower().strip().startswith('http'):
                        vm_url = 'https://' + vm_url.lower().strip()

                    if 'http://' in vm_url.lower().strip() or 'https://' in vm_url.lower().strip():

                        # MEA Config
                        if vm.name.lower().startswith('mea-'):

                            config_pt_middle += f'''
    {{
      "type": "HTTP-STATUS",
      "label": "{vm.name}",
      "params": {{
        "url": "{vm_url.lower().strip()}",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }}
    }},
    
'''
                        elif vm.name.lower().startswith('mer-'):

                            config_pt_middle += f'''
    {{
      "type": "HTTP-RAW",
      "label": "{vm.name}",
      "params": {{
        "url": "{vm_url.lower().strip()}",
        "regex": "ورود کاربر",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }}
    }},

'''
                    else:
                        print(f"Deformed URL: {vm.name}")


config_pt_final = '''
    {
      "type": "HTTP-STATUS",
      "label": "MEM-DadeSaman",
      "params": {
        "url": "https://sardchal.com",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },
  
   {
      "type": "HTTP-STATUS",
      "label": "MEM-Delino",
      "params": {
        "url": "https://delino.com",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },
  
   {
      "type": "HTTP-STATUS",
      "label": "MEM-Dorna",
      "params": {
        "url": "http://185.141.213.151",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },

   {
      "type": "HTTP-STATUS",
      "label": "AvaRasa Website",
      "params": {
        "url": "https://easymed.ir",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },

   {
      "type": "HTTP-STATUS",
      "label": "SarvCRM Website",
      "params": {
        "url": "https://app.sarvcrm.com",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },

   {
      "type": "HTTP-STATUS",
      "label": "Customer VPN Portal",
      "params": {
        "url": "https://remote.abramad.com:1044",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },

   {
      "type": "HTTP-STATUS",
      "label": "Staff VPN Portal",
      "params": {
        "url": "https://remote2.abramad.com:1044",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },

   {
      "type": "HTTP-STATUS",
      "label": "Abramad Website",
      "params": {
        "url": "https://www.abramad.com",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },

   {
      "type": "HTTP-STATUS",
      "label": "Abramad Platform",
      "params": {
        "url": "https://cloud.abramad.com",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },

   {
      "type": "HTTP-STATUS",
      "label": "Abramad SelfService",
      "params": {
        "url": "https://selfservice.abramad.com",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },
    
    {
      "type": "HTTP-STATUS",
      "label": "Abramad Jira",
      "params": {
        "url": "https://jira.abramad.com",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },

    {
      "type": "HTTP-STATUS",
      "label": "Abramad Confluence",
      "params": {
        "url": "https://confluence.abramad.com",
        "statusCodeMin": 200,
        "statusCodeMax": 299
      }
    },
    
   {
      "type": "PORT",
      "label": "Abramad SpeedTest",
      "params": {
        "hostname": "speedtest.abramad.com",
        "port": 8080
      }
    },

   {
      "type": "PORT",
      "label": "Abramad ECS",
      "params": {
        "hostname": "thr-storage.abramad.com",
        "port": 9021
      }
    },

   {
      "type": "PORT",
      "label": "ME-SepLock01",
      "params": {
        "hostname": "me-seplock01.abramad.com",
        "port": 9050
      }
    },

    {
      "type": "PORT",
      "label": "ME-BuildLock01",
      "params": {
        "hostname": "me-buildlock01.abramad.com",
        "port": 22350
      }
    }, 

   {
      "type": "PORT",
      "label": "ME-RahLock01",
      "params": {
        "hostname": "me-rahlock01.abramad.com",
        "port": 22350
      }
    },

   {
      "type": "PORT",
      "label": "ME-RahLock02",
      "params": {
        "hostname": "me-rahlock02.abramad.com",
        "port": 22350
      }
    },

   {
      "type": "PORT",
      "label": "ME-RahLock03",
      "params": {
        "hostname": "me-rahlock03.abramad.com",
        "port": 22350
      }
    },

   {
      "type": "PORT",
      "label": "ME-RahLock04",
      "params": {
        "hostname": "me-rahlock04.abramad.com",
        "port": 22350
      }
    },

   {
      "type": "PORT",
      "label": "ME-RahLock05",
      "params": {
        "hostname": "me-rahlock05.abramad.com",
        "port": 22350
      }
    },

   {
      "type": "PORT",
      "label": "ME-RahLock06",
      "params": {
        "hostname": "me-rahlock06.abramad.com",
        "port": 22350
      }
    },

   {
      "type": "PORT",
      "label": "ME-RahLock07",
      "params": {
        "hostname": "me-rahlock07.abramad.com",
        "port": 22350
      }
    },

   {
      "type": "PORT",
      "label": "ME-RahLock08",
      "params": {
        "hostname": "me-rahlock08.abramad.com",
        "port": 22350
      }
    },

   {
      "type": "PORT",
      "label": "ME-RahLock09",
      "params": {
        "hostname": "me-rahlock09.abramad.com",
        "port": 22350
      }
    },

   {
      "type": "PORT",
      "label": "ME-RahLock10",
      "params": {
        "hostname": "me-rahlock10.abramad.com",
        "port": 22350
      }
    },

   {
      "type": "PORT",
      "label": "ME-RahLock11",
      "params": {
        "hostname": "me-rahlock11.abramad.com",
        "port": 22350
      }
    },

   {
      "type": "PORT",
      "label": "ME-RahLock12",
      "params": {
        "hostname": "172.17.242.86",
        "port": 22350
      }
    },
    
   {
      "type": "PORT",
      "label": "ME-RahLock13",
      "params": {
        "hostname": "me-rahlock13.abramad.com",
        "port": 22350
      }
    },

    {
      "type": "PORT",
      "label": "ME-SEH01",
      "params": {
        "hostname": "me-seh01.abramad.com",
        "port": 9200
      }
    },

   {
      "type": "PORT",
      "label": "ME-SEH02",
      "params": {
        "hostname": "me-seh02.abramad.com",
        "port": 9200
      }
    },

    {
      "type": "PORT",
      "label": "ME-SEH03",
      "params": {
        "hostname": "me-seh03.abramad.com",
        "port": 9200
      }
    },

   {
      "type": "PORT",
      "label": "ME-SEH04",
      "params": {
        "hostname": "me-seh04.abramad.com",
        "port": 9200
      }
    },

   {
      "type": "PORT",
      "label": "ME-SEH05",
      "params": {
        "hostname": "me-seh05.abramad.com",
        "port": 9200
      }
    },

'''

temp_node_count = str(config_pt_begin + config_pt_middle + config_pt_final).split()
nodes = temp_node_count.count('"type":') + 2


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
      "label": "DC73 Internet",
      "params": {{
        "hostname": "193.106.190.1"
      }}
    }},
    
    {{
      "type": "PING",
      "label": "Nodes: {nodes}",
      "params": {{
        "hostname": "1.1.1.1"
      }}
    }}

 ]
}}
'''

config = config_pt_begin + config_pt_middle + config_pt_final + config_pt_status

Disconnect(ME_VC)

print(config)
# Saving config in file
#with open('/docker-volumes/monitoror/.env', 'w') as file:
#    file.write(config)
