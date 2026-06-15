import csv
from pyzabbix import ZabbixAPI
from cryptography.fernet import Fernet
import os


def decryptor(enc_env_var, key_env_var):
    # Load the key
    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = (os.environ.get(enc_env_var)).encode()
    # Decrypt Data
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())

    # print(f"Decryped Text: {decrypted_password}")
    return decrypted_password.decode()


# Open the CSV file
with open("C:\\Temp\\VNK-iLO-HTTP-URL.csv", mode='r') as file:
    csv_data = csv.reader(file)
    fcsw_data = {}

    # Skip the first line
    for _ in range(1):
        next(csv_data)

    # Read the rows
    for row in csv_data:
        fcsw_data[row[0]] = row
        #print(fcsw_data[row[0]])


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
                host_visible_name = hosts_dict[host][0].split('.')[0]  # {HOST.NAME}
                host_ip = hosts_dict[host][1].strip()  # Host IP
                host_macro = hosts_dict[host][2]  # Host Macro
                host_desc = f""  # Host Description {hosts_dict[host][3]}

                zabbix_macros = [
                    {"macro": "{$ILO.URL}", "value": f"{host_macro}"}
                ]

                new_host = zapi.host.create({
                    "host": host_name,
                    "name": host_visible_name,
                    "description": host_desc,
                    "groups": hgroups_config["groups"],
                    "templates": templates_config["templates"],
                    "tags": tag_list,
                    "macros": zabbix_macros,
                    "interfaces": [{
                    "type": 1,  # Type 1 = Agent
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
zabbix_url = "http://172.29.6.7/"
zabbix_user = "sysops-svc"
zabbix_password = decryptor('sysops-svc_enc', 'sysops-svc_key')

zabbix_templates = ["HPE iLO by HTTP"]
zabbix_host_groups = ["CSB_Team", "ILO"]
zabbix_tags = [
        {"tag": "Note", "value": ""},
        {"tag": "Owner", "value": "CSB_Team"}
    ]


zabbix_node_adder(zabbix_url, zabbix_user, zabbix_password, fcsw_data, zabbix_templates, zabbix_host_groups, zabbix_tags)


'''
iLO:
    zabbix_templates = ["HP iLO by SNMP"]
    zabbix_host_groups = ["CSB_Team", "ILO"]
    zabbix_tags = [
        {"tag": "Note", "value": ""},
        {"tag": "Owner", "value": "CSB_Team"}
    ]
'''

'''
Network Switches:
                                    Leaf                             AMGT, DMGT, CMGT   
    zabbix_templates = ["Cisco Nexus 9000 Series by SNMP"] or ["Cisco IOS by SNMP-SwitchOOB"]
    zabbix_host_groups = ["Switches", "Network_Team", "OOB-Switches", "Nexus-Switches", "Leaf_Switch"]
    zabbix_tags = [
        {"tag": "Note", "value": ""},
        {"tag": "Owner", "value": "Network_Team"}
    ]
'''