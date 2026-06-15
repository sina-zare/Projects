from pyvim import connect
from pyVmomi import vim
import ssl
import os
import warnings
from pyzabbix import ZabbixAPI
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
username = "sina.z@abramad.com"
password = decryptor("enc_sinaz_pass","key_sinaz_pass")

# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)

# *** Connecting to ME-VC01.Abramad.Com to get the Report ***
# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

# Connecting to vCenter
ME_VC = connect.SmartConnect(host='me-vc01.abramad.com',user= username,pwd= password,port=443,sslContext=context)
me_content = ME_VC.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
sorted_vms = sorted(me_vm_view.view, key=lambda vm: vm.name)
sorted_vms_narrow = []
for vm in sorted_vms:
    if (vm.runtime.powerState.lower() == 'poweredon') and ('template' not in vm.name.lower()) and ('khoshraftar' not in vm.name.lower()):

        # retrieve vm IP address
        vm_ip = ""
        if vm.guest is not None:
            for nic in vm.guest.net:
                if nic.ipConfig is not None:
                    for ip in nic.ipConfig.ipAddress:
                        if ip.ipAddress.startswith('172.17') or ip.ipAddress.startswith('172.21'):
                            sorted_vms_narrow.append(vm)




non_customer_vms = []
customer_vms = []

# Define management prefixes
customer_prefixes = ("MER-", "MEB-", "MEF-", "MES-", "MERD-", "MEM-", "MEI-", "MESA-", "MEA-")

# Separate customer and non-customer VMs
customer_vms = [vm for vm in sorted_vms if vm.name.startswith(customer_prefixes)]
non_customer_vms = [vm for vm in sorted_vms if not vm.name.startswith(customer_prefixes)]


# Output the results
print(f"Number of all VMs: {len(sorted_vms)}")
print(f"Number of customer VMs: {len(customer_vms)}")
print(f"Number of non-customer VMs: {len(non_customer_vms)}\n")

mer_dict = {}
mes_dict = {}
mef_dict = {}
mea_dict = {}
meb_dict = {}
mesa_dict = {}
mem_dict = {}
mei_dict = {}
men_dict = {}


# Gathering Data
for customer_vm in sorted_vms_narrow:

    # retrieve vm IP address
    vm_ip = ""
    if customer_vm.guest is not None:
        for nic in customer_vm.guest.net:
            if nic.ipConfig is not None:
                for ip in nic.ipConfig.ipAddress:
                    if ip.ipAddress.startswith('172.17') or ip.ipAddress.startswith('172.21'):
                        vm_ip = ip.ipAddress
    if vm_ip == "":
        vm_ip = '0.0.0.0'

    # VM Name
    vm_name = customer_vm.name

    # Get VM Persian Name
    vm_persian_name = ""
    custom_value_n = customer_vm.summary.customValue
    for i in custom_value_n:
        if i.key == 103:
            vm_persian_name = i.value


    if vm_name.startswith("MER-") or vm_name.startswith("MERD-"):
        mer_dict[customer_vm.name] = [vm_name, vm_ip, vm_persian_name]

    elif vm_name.startswith("MES-"):
        mes_dict[customer_vm.name] = [vm_name, vm_ip, vm_persian_name]

    elif vm_name.startswith("MEF-"):
        mef_dict[customer_vm.name] = [vm_name, vm_ip, vm_persian_name]

    elif vm_name.startswith("MEA-"):
        mea_dict[customer_vm.name] = [vm_name, vm_ip, vm_persian_name]

    elif vm_name.startswith("MEB-"):
        meb_dict[customer_vm.name] = [vm_name, vm_ip, vm_persian_name]

    elif vm_name.startswith("MESA-"):
        mesa_dict[customer_vm.name] = [vm_name, vm_ip, vm_persian_name]

    elif vm_name.startswith("MEM-"):
        mem_dict[customer_vm.name] = [vm_name, vm_ip, vm_persian_name]

    elif vm_name.startswith("MEI-"):
        mei_dict[customer_vm.name] = [vm_name, vm_ip, vm_persian_name]

    else:
        men_dict[customer_vm.name] = [vm_name, vm_ip, vm_persian_name]




print('vCenter Data gathered.\nStarting Zabbix Part\n')

# Zabbix Part
def zabbix_node_adder(url, username, password, hosts_dict, template_list, host_group_list, tag_list):

    try:
        #  host_dict involves key values, that the values are a list consisting of 3 indexes ['Host Name', 'IP Address', 'Description']
        template_ids = {}
        host_group_ids = {}

        # Connect to Zabbix API
        zapi = ZabbixAPI(url)
        zapi.login(username, password)

        # Step 1: Get the Template ID
        for template_name in template_list:
            template = zapi.template.get(filter={"host": template_name})
            if not template:
                raise Exception(f"Template '{template_name}' not found.")
            template_ids[template_name] = template[0]["templateid"]
        # Create the "groups" list dynamically
        templates = [{"templateid": tpl_id} for tpl_id in template_ids.values()]
        # Create the final config
        templates_config = {"templates": templates}


        # Step 2: Get the Host Group ID
        for host_group_name in host_group_list:
            host_group = zapi.hostgroup.get(filter={"name": host_group_name})
            if not host_group:
                raise Exception(f"Host group '{host_group_name}' not found.")
            host_group_ids[host_group_name] = host_group[0]["groupid"]
        # Create the "groups" list dynamically
        hgroups = [{"groupid": group_id} for group_id in host_group_ids.values()]
        # Create the final config
        hgroups_config = {"groups": hgroups}


        # Step 3: Create the new host with description and visible name
        for host in hosts_dict:
            try:

                # Host information
                host_name = hosts_dict[host][0].split('.')[0]  # {HOST.HOST}
                host_fqdn = hosts_dict[host][0].strip()
                host_visible_name = hosts_dict[host][0].split('.')[0]  # {HOST.NAME}
                host_ip = hosts_dict[host][1].strip()
                host_desc = f"{hosts_dict[host][2]}"  # Host Description

                new_host = zapi.host.create({
                    "host": host_name,
                    "name": host_visible_name,
                    "description": host_desc,
                    "groups": hgroups_config["groups"],
                    "templates": templates_config["templates"],
                    "tags": tag_list,
                    "interfaces": [{
                        "type": 1,  # Type 2 = SNMP
                        "main": 1,  # Mark this as the main interface
                        "useip": 1,  # Use IP address for connection
                        "ip": host_ip,
                        "dns": "",
                        "port": "10050"
                    }]
                })


                print(f"Host '{host_name}' created with ID {new_host['hostids'][0]}")
                print('#############\n')

            except Exception as loop_err:
                print(f"Error adding host '{host_name}': {loop_err}")

    except Exception as err:
        print(f"Error: {err}")


# Zabbix server credentials
zabbix_url = "http://172.17.234.13/zabbix"
zabbix_user = "sina.z"
zabbix_password = password
zabbix_templates = ["ICMP Ping IP"]

zabbix_tags = [
    {"tag": "Note", "value": ""},
    {"tag": "Owner", "value": "Support_Team"}
]
men_zabbix_tags = [
    {"tag": "Note", "value": ""},
    {"tag": "Owner", "value": "Management"}
]

mer_zabbix_host_groups = ["MER", "ME_OnPrem_ICMP"]
mes_zabbix_host_groups = ["MES", "ME_OnPrem_ICMP"]
mef_zabbix_host_groups = ["MEF", "ME_OnPrem_ICMP"]
mea_zabbix_host_groups = ["MEA", "ME_OnPrem_ICMP"]
meb_zabbix_host_groups = ["MEB", "ME_OnPrem_ICMP"]
mesa_zabbix_host_groups = ["MESA", "ME_OnPrem_ICMP"]
mem_zabbix_host_groups = ["MEM", "ME_OnPrem_ICMP"]
mei_zabbix_host_groups = ["MEI", "ME_OnPrem_ICMP"]
men_zabbix_host_groups = ["Management_ICMP"]


zabbix_node_adder(zabbix_url, zabbix_user, zabbix_password, mer_dict, zabbix_templates, mer_zabbix_host_groups, zabbix_tags)
zabbix_node_adder(zabbix_url, zabbix_user, zabbix_password, mes_dict, zabbix_templates, mes_zabbix_host_groups, zabbix_tags)
zabbix_node_adder(zabbix_url, zabbix_user, zabbix_password, mef_dict, zabbix_templates, mef_zabbix_host_groups, zabbix_tags)
zabbix_node_adder(zabbix_url, zabbix_user, zabbix_password, mea_dict, zabbix_templates, mea_zabbix_host_groups, zabbix_tags)
zabbix_node_adder(zabbix_url, zabbix_user, zabbix_password, meb_dict, zabbix_templates, meb_zabbix_host_groups, zabbix_tags)
zabbix_node_adder(zabbix_url, zabbix_user, zabbix_password, mesa_dict, zabbix_templates, mesa_zabbix_host_groups, zabbix_tags)
zabbix_node_adder(zabbix_url, zabbix_user, zabbix_password, mem_dict, zabbix_templates, mem_zabbix_host_groups, zabbix_tags)
zabbix_node_adder(zabbix_url, zabbix_user, zabbix_password, mei_dict, zabbix_templates, mei_zabbix_host_groups, zabbix_tags)
zabbix_node_adder(zabbix_url, zabbix_user, zabbix_password, men_dict, zabbix_templates, men_zabbix_host_groups, men_zabbix_tags)

# 1403/10/16
