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


sorted_vms_fnl = []

for vm in sorted_vms:
    if not vm.name.lower().endswith('-t') and not vm.name.lower().endswith('-db'):
        sorted_vms_fnl.append(vm)


mea_list = []
mer_list = []

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
            if days_between_persian_dates(vm_creation_date) > 30:
                # Get VM URL
                vm_url = ""
                vm_custom_attr = vm.summary.customValue
                for i in vm_custom_attr:
                    if i.key == 604:
                        vm_url = i.value


                if vm_url != "":
                    if 'http://' in vm_url.lower().strip() or 'https://' in vm_url.lower().strip():

                        # Get National ID Status
                        vm_national_id = ""
                        custom_value_n = vm.summary.customValue
                        for i in custom_value_n:
                            if i.key == 611:
                                vm_national_id = i.value

                        # Get VM Persian Name
                        vm_persian_name = ""
                        custom_value_n = vm.summary.customValue
                        for i in custom_value_n:
                            if i.key == 103:
                                vm_persian_name = i.value



                        # MEA Config
                        if vm.name.lower().startswith('mea-'):
                            mea_list.append([vm.name, vm_url, f'{vm_persian_name} - {vm_national_id}'])

                        # MER Config
                        if vm.name.lower().startswith('mer-'):
                            mer_list.append([vm.name, vm_url, f'{vm_persian_name} - {vm_national_id}'])



### Kuma ###

from uptime_kuma_api import UptimeKumaApi, MonitorType

api = UptimeKumaApi('http://172.17.255.90:3015/')
api.login('admin', 'I4=t8K<xn')

# Doing MER
for mer in mer_list:
    if mer[0] == 'MER-Ramak-LB':
        print(mer[0])
        mer_monitor_config = {
            "type": MonitorType.KEYWORD,
            "name": f"{mer[0]}-Test2",
            "url": f"{mer[1]}",
            "keyword": "ورود کاربران",
            "interval": 90,
            "maxretries": 3,
            "retryInterval": 30,
            "timeout": 72,
            "resendInterval": 480,
            "maxredirects": 10,
            "accepted_statuscodes": ['200-299'],
            "description": f"{mer[2]}",
            "notificationIDList": [1],  # Enable Telegram Notification
            "ignoreTls": True

        }

        result = api.add_monitor(**mer_monitor_config)
        print(result)

# Doing MEA
for mea in mea_list:
    mea_monitor_config = {
        "type": MonitorType.HTTP,
        "name": f"{mea[0]}",
        "url": f"{mea[1]}",
        "interval": 90,
        "maxretries": 3,
        "retryInterval": 30,
        "timeout": 72,
        "resendInterval": 480,
        "maxredirects": 10,
        "accepted_statuscodes": ['200-299'],
        "description": f"{mea[2]}",
        "notificationIDList": [1],  # Enable Telegram Notification
        "ignoreTls": True

    }

    result = api.add_monitor(**mea_monitor_config)
    print(result)


api.disconnect()

