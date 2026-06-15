from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import warnings
import os
import pandas as pd
import csv


class customer_server:
    def __init__(self,  name, ip, hostname, national_id, persian_name, agent_name, agent_email, agent_mobile, hid):
        self.name = name
        self.ip = ip
        self.hostname = hostname
        self.national_id = national_id
        self.persian_name = persian_name
        self.agent_name = agent_name
        self.agent_email = agent_email
        self.agent_mobile = agent_mobile
        self.hid = hid


# Decryption function
def decrypt(cipher_text, key):
    plain_text = ""
    for i in range(len(cipher_text)):
        char = cipher_text[i]
        plain_int = ord(char) - key
        plain_text += chr(plain_int)
    return plain_text


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

# *** Connecting to ME-VC01.Abramad.Com to get the Report ***
warnings.filterwarnings("ignore", category=DeprecationWarning)
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

# Connecting to vCenter
ME_VC = connect.SmartConnect(host='me-vc01.abramad.com', user=username, pwd=password, port=443, sslContext=context)
me_content = ME_VC.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if (vm.name.startswith("ME-") or vm.name.startswith("MER-") or vm.name.startswith("MERD-"))]
sorted_vms = sorted(me_vms, key=lambda vm: vm.name.lower())

rahlock_servers = []

for vm in sorted_vms:
    if (vm.name.lower().startswith("me-rahlock") and not vm.name.lower().startswith("me-rahlocktemp")) or (vm.name.lower().startswith("me-buildlock") and not vm.name.lower().startswith("me-rahlocktemp")):

        # retrieve vm IP address
        vm_ip = ""
        if vm.guest is not None:
            for nic in vm.guest.net:
                if nic.ipConfig is not None:
                    for ip in nic.ipConfig.ipAddress:
                        if not ip.ipAddress.startswith('169.254') and not ip.ipAddress.startswith('fe80'):
                            vm_ip = ip.ipAddress

        # retrieve vm Hostname
        vm_hostname = vm.summary.guest.hostName

        rahlock_servers.append([vm_hostname,vm_ip])


# ================================================================================
import requests
import re
rahlock_customers = {}

for lock_server in rahlock_servers:
    # Define the URL of the web page you want to fetch
    url = f"http://{lock_server[1]}:22352/license_monitoring/sessions.html"

    # create a variable for that rahlock
    temp = lock_server[0].split(".")
    rahlock_variable_name = temp[0][3:].lower()
    #print(variable_name)

    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Extract the text content from the response
        page_content = response.text

        # Use regular expressions to find all strings starting with "172.17"
        ip_pattern = r"172\.\d{1,3}\.\d{1,3}\.\d{1,3}"  # Regex pattern to match IP addresses
        cloud_pattern = r">(.*?cloud\.local)<"  # Regex pattern to match strings starting after > and before < and ending with "cloud.local"

        ip_matches = re.findall(ip_pattern, page_content)
        ip_matches.remove(lock_server[1])
        cloud_matches = re.findall(cloud_pattern, page_content)

        # Combine the matched IP addresses and cloud.local strings
        matched_strings = ip_matches + cloud_matches

        # Remove duplicates using set and convert to a list
        matched_strings = list(set(matched_strings))

        # making exec variable global so eval() can retrieve it
        #exec(f"global me_{rahlock_variable_name}_customers")
        # creating list for each rahlock
        #exec(f"me_{rahlock_variable_name}_customers = []")
        # take the matched strings and append them to their corresponding list. runs all that comes between " "
        #exec(f"me_{rahlock_variable_name}_customers.append(matched_strings)")
        # append list using eval() to retrieve it
        #rahlock_customers.append(eval(f"me_{rahlock_variable_name}_customers"))

        rahlock_customers[f"me_{rahlock_variable_name}_customers"] = matched_strings

    else:
        print("Failed to fetch the web page.")

'''
for key, value in rahlock_customers.items():
    print(f"Key: {key}")
    for i in value:

        print(f"Value: {i}")
    print("****************")
'''


#'''
# ======================================================= Creating Object for Each VM ===================================================================
agent_data_path = f"C:/Users/sina.z/Desktop/Automation_Reports/Downtime/raw.xlsx"
hid_data_path = f"C:/Users/sina.z/Desktop/Automation_Reports/Downtime/rawt.csv"
vcenter_vms = {}

for vm in sorted_vms:
    if (vm.name.lower().startswith("mer-")) or (vm.name.lower().startswith("merd-")):

        # Spec Calculations

        # retrieve vm name
        vm_name = vm.name

        # retrieve vm IP address
        vm_ip = ""
        if vm.guest is not None:
            for nic in vm.guest.net:
                if nic.ipConfig is not None:
                    for ip in nic.ipConfig.ipAddress:
                        if not ip.ipAddress.startswith('169.254') and not ip.ipAddress.startswith('fe80'):
                            vm_ip = ip.ipAddress

        # retrieve vm Hostname
        vm_hostname = vm.summary.guest.hostName

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


        # Initializing CustomerServer Objects
        exec(f"{vm_name.replace('-', '_')} = customer_server(vm_name, vm_ip, vm_hostname, vm_national_id, vm_persian_name, '', '', '', '')")


        # Generating Agent Data
        raw_sms_data = pd.read_excel(agent_data_path, dtype=str)
        # Specify the column indices you want to extract (0-based index)
        columns_indices = [1, 3, 5, 6, 8]
        # Extract the specified columns from each row and store them in a list
        extracted_data = [list(row.iloc[columns_indices]) for index, row in raw_sms_data.iterrows()]

        for raw_info in extracted_data:
            vm_agent_name = ""
            vm_agent_email = ""
            vm_agent_mobile = ""
            vm_persian_name_more_specific = ""

            if vm_national_id.strip() == str(raw_info[0]).strip():
                vm_persian_name_more_specific = str(raw_info[1]).strip()
                vm_agent_name = str(raw_info[2]).strip()
                vm_agent_email = str(raw_info[3]).strip()
                vm_agent_mobile = str(raw_info[4]).strip()

                exec(f"{vm_name.replace('-', '_')}.persian_name = vm_persian_name_more_specific")
                exec(f"{vm_name.replace('-', '_')}.agent_name = vm_agent_name")
                exec(f"{vm_name.replace('-', '_')}.agent_email = vm_agent_email")
                exec(f"{vm_name.replace('-', '_')}.agent_mobile = vm_agent_mobile")


        # Generating HID
        sarv_data = []
        with open(hid_data_path, 'r', encoding='utf-8-sig') as read_file:
            reader = csv.reader(read_file)
            # Skip the first 8 lines
            for _ in range(8):
                next(reader)

            for row in reader:
                sarv_data.append([row[0], row[4]])


        # Filling HID
        # eval() returns the object you call inside it
        vm_instance = eval(vm_name.replace('-', '_'))
        for sarv_datum in sarv_data:
            if getattr(vm_instance, 'agent_email').strip() == sarv_datum[0].strip():
                setattr(vm_instance, 'hid', sarv_datum[1])

        # saving all created vm objects in a dict
        vcenter_vms[f"{vm_name.replace("-","_")}"] = eval(vm_name.replace("-","_"))

###########################################################################################################################



# creating a variable for object oriented rahlock customers
oo_rahlock_customers = {
    "oo_me_buildlock01_customers": [],
    "oo_me_rahlock01_customers": [],
    "oo_me_rahlock02_customers": [],
    "oo_me_rahlock03_customers": [],
    "oo_me_rahlock04_customers": [],
    "oo_me_rahlock05_customers": [],
    "oo_me_rahlock06_customers": [],
    "oo_me_rahlock07_customers": [],
    "oo_me_rahlock08_customers": [],
    "oo_me_rahlock09_customers": [],
    "oo_me_rahlock10_customers": [],
    "oo_me_rahlock11_customers": [],
    "oo_me_rahlock12_customers": [],
    "oo_me_rahlock13_customers": [],
    "oo_me_rahlock14_customers": [],
    "oo_me_rahlock15_customers": [],
    "oo_me_rahlock16_customers": [],
    "oo_me_rahlock17_customers": [],
    "oo_me_rahlock18_customers": [],
    "oo_me_rahlock19_customers": [],
    "oo_me_rahlock20_customers": []
}

for vm_key, vm_value in vcenter_vms.items():
    for rahlock_key, rahlock_value in rahlock_customers.items():
        for each_entry in rahlock_value:
            if each_entry == vm_value.ip or each_entry == vm_value.hostname:
                sms_format = f"{vm_value.agent_email}({vm_value.agent_name})"

                oo_rahlock_customers[f"oo_{rahlock_key}"].extend([[vm_value.name, vm_value.persian_name, vm_value.hid, vm_value.agent_mobile, sms_format]])



for key, value in oo_rahlock_customers.items():

    # Get the key name without "oo_"
    csv_name = key[3:]

    # Open CSV file
    with open(f'C:/Users/sina.z/Desktop/Automation_Reports/RahLock_Members/{csv_name}.csv', 'w',encoding='utf-8_sig', newline='') as f:

        # Write header
        writer = csv.writer(f)
        writer.writerow(["name", "persian_name", "hid", "agent_mobile", "sms_format"])

        # Write rows from value list
        for row in value:
            writer.writerow(row)


Disconnect(ME_VC)
#print()
#for key, value in oo_rahlock_customers.items():
#    print(f"Key: {key}")
#    print(f"Value: {value}")
#    print(f"******************************************************\n")



#'''