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

username = 'sina.z@sgcloud.local'
password = decryptor("enc_sinaz_pass","key_sinaz_pass")


# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)
# *** Connecting to ME-VC01.Abramad.Com to get the Report ***
# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

# Connecting to vCenter
ME_VC = connect.SmartConnect(host='vc.sgcloud.local', user=username, pwd=password, port=443, sslContext=context)
me_content = ME_VC.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if (vm.name.startswith("VPS-"))]
sorted_vms = sorted(me_vms, key=lambda vm: vm.name.lower())


vps_list = []

for vm in sorted_vms:

    vm_power_state = vm.runtime.powerState.lower()
    if vm_power_state == "poweredon":

        vps_list.append(vm.name)


### Kuma ###
from uptime_kuma_api import UptimeKumaApi, MonitorType


def batch_vms(vps_list, batch_size=300):
    for i in range(0, len(vps_list), batch_size):
        yield vps_list[i:i + batch_size]


# Batching VMs in groups of 300
for batch in batch_vms(vps_list, 300):
    api = UptimeKumaApi('http://172.17.255.90:3016/')
    api.login('admin', 'I4=t8K<xn')

    for vm in batch:
        monitor_config = {
            "type": MonitorType.KEYWORD,
            "name": vm,
            "url": f"https://{vm.split('-')[1].lower()}.rahkaran.ir",
            "keyword": "ورود کاربران",
            "interval": 90,
            "maxretries": 3,
            "retryInterval": 30,
            "timeout": 72,
            "resendInterval": 480,
            "maxredirects": 10,
            "accepted_statuscodes": ['200-299'],
            # "notificationIDList": [1],  # Enable Telegram Notification if needed
            "ignoreTls": True
        }

        result = api.add_monitor(**monitor_config)
        print(result)

    api.disconnect()
