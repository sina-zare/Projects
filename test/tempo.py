from pyVim import connect
from pyVim.connect import Disconnect
from pyVmomi import vim
import ssl
import warnings
import os


# Decryption function
def decrypt(cipher_text, key):
    plain_text = ""
    for i in range(len(cipher_text)):
        char = cipher_text[i]
        plain_int = ord(char) - key
        plain_text += chr(plain_int)
    return plain_text


# Credentials
username = decrypt(os.environ.get('sin'), 9999)
password = decrypt(os.environ.get('spass'), 9999)

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


'''
me_buildlock01_customers = []
me_rahlock01_customers = []
me_rahlock02_customers = []
me_rahlock03_customers = []
me_rahlock04_customers = []
me_rahklock05_customers = []
me_rahlock06_customers = []
me_rahlock07_customers = []
me_rahlock08_customers = []
'''

# ================================================================================
import requests
import re

for lock_server in rahlock_servers:
    # Define the URL of the web page you want to fetch
    url = f"http://{lock_server[1]}:22352/license_monitoring/sessions.html"

    # create a variable for that rahlock
    temp = lock_server[0].split(".")
    variable_name = temp[0][3:].lower()
    print(variable_name)

    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Extract the text content from the response
        page_content = response.text

        if variable_name == "rahlock07":
            print(page_content)

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

        # take the matched strings and append them to their corresponding list. runs all that comes between " "
        exec(f"me_{variable_name}_customers = (matched_strings)")
    else:
        print("Failed to fetch the web page.")

print(me_rahlock07_customers)
print(len(me_rahlock07_customers))