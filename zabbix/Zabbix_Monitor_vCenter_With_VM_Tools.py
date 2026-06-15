from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import warnings
from cryptography.fernet import Fernet
import os
from pyzabbix import ZabbixAPI


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
vcenter_addr = 'vab-vc01.abramad.com'
target_vm_name = 'VAE-UAG02'


# Ignore the warning/# Create an SSL context with no certificate verification
warnings.filterwarnings("ignore", category=DeprecationWarning)
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE


# Connecting to vCenter
print(f'connecting to {vcenter_addr}')
vc = connect.SmartConnect(host=vcenter_addr, user=username, pwd=password, port=443, sslContext=context)
content = vc.RetrieveContent()
vm_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
print('gathering vms')

vms = [vm for vm in vm_view.view if vm.name == target_vm_name]
vm_data = {}

if not vms:
    raise Exception(f"VM '{target_vm_name}' not found in {vcenter_addr}")

for vm in vms:

    vm_name = vm.name

    #vm_uuid = vm.config.uuid

    # retrieve vm ip address
    vm_private_ip = "0.0.0.0"
    if vm.guest is not None:
        candidate_ips = []
        for nic in vm.guest.net:
            if nic.ipConfig is not None:
                for ip in nic.ipConfig.ipAddress:
                    candidate_ips.append(ip.ipAddress)

        for ip in candidate_ips:
            if not ip.startswith(('169.254', 'fe80')):
                vm_private_ip = ip
                break

    vm_instance_uuid = vm.config.instanceUuid

    vm_data[vm_name] = {
        'name': vm_name,
        'ip': vm_private_ip,
        'uuid': vm_instance_uuid
    }
    print(f'\nName: {vm_name}\nPrivate IP: {vm_private_ip}\nInstance UUID: {vm_instance_uuid}')

Disconnect(vc)

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
        vmware_password_macro = 'BgTsM+7g24F{{SjD'
        for host in hosts_dict:
            try:

                # Host information
                host_name = hosts_dict[host]['name']  # {HOST.HOST}
                host_visible_name = host_name  # {HOST.NAME}
                host_ip = hosts_dict[host]['ip']

                # Macros
                macros = [
                    {"macro": "{$VMWARE.URL}", "value": f"https://{vcenter_addr}/sdk"},
                    {"macro": "{$VMWARE.USERNAME}", "value": "zabbix@abramad.com"},
                    {
                        "macro": "{$VMWARE.PASSWORD}",
                        "value": vmware_password_macro,
                        "type": 1
                    },
                    {"macro": "{$VMWARE.VM.UUID}", "value": f"{hosts_dict[host]['uuid']}"},
                ]

                new_host = zapi.host.create({
                    "host": host_name,
                    "name": host_visible_name,
                    "description": '',
                    "groups": hgroups_config["groups"],
                    "templates": templates_config["templates"],
                    "tags": tag_list,
                    "macros": macros,
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
zabbix_url = "https://vnk-zabbix.abramad.com"
zabbix_user = username.split('@')[0]
zabbix_password = password

zabbix_templates = ["VMware Guest"]

team = 'CRE_Team'

zabbix_tags = [
    {"tag": "Note", "value": ""},
    {"tag": "Owner", "value": f"{team}"},
    {"tag": "__zbx_jira", "value": "1"}
]

zabbix_host_groups = ["Appliances", f"{team}"]


zabbix_node_adder(zabbix_url, zabbix_user, zabbix_password, vm_data, zabbix_templates, zabbix_host_groups, zabbix_tags)
