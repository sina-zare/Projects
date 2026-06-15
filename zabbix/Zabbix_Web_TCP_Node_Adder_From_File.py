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
with open("D:\\OneDrive\\Abramad\\Excels\\Abramad-Services-URL.csv", mode='r') as file:
    csv_data = csv.reader(file)
    me_zabbix_data = {}
    vnk_zabbix_data = {}
    me_zabbix_codemeter = {}
    vnk_zabbix_codemeter = {}

    # Skip the first line
    for _ in range(1):
        next(csv_data)

    # Read the rows
    for row in csv_data:
        if row[1].startswith('http'):

            if row[3] == 'me-zabbix':
                me_zabbix_data[row[0]] = [row[0], row[1], row[4]]
            if row[3] == 'vnk-zabbix':
                vnk_zabbix_data[row[0]] = [row[0], row[1], row[4]]

        if row[1].startswith('tcp'):
            
            if row[2] == '22350' and row[3] == 'me-zabbix':
                me_zabbix_codemeter[row[0]] = [row[0], row[4], row[5]]
            if row[2] == '22350' and row[3] == 'vnk-zabbix':
                vnk_zabbix_codemeter[row[0]] = [row[0], row[4], row[5]]


username = 'sina.z'
passphrase = decryptor("enc_sinaz_pass", "key_sinaz_pass")
me_zab_url1 = 'http://zab.abramad.com/zabbix'
me_zab_url2 = 'http://172.17.234.13/zabbix'
vnk_zab_url = 'http://vnk-zabbix.abramad.com'

# Connect to Zabbix API
zapi = ZabbixAPI(vnk_zab_url)
zapi.login(username, passphrase)

# TCP Monitoring
for tcp_host in vnk_zabbix_codemeter:

    try:
        template_ids = {}
        host_group_ids = {}
        template_list = ['Lock-Server-Tpl']
        host_group_list = ['Lock-Servers']

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

        # Add new Host Group
        host_group_list.append(vnk_zabbix_codemeter[tcp_host][1])

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
        #print(hgroups_config)


        # Host information
        host_name = vnk_zabbix_codemeter[tcp_host][0]  # {HOST.HOST}
        host_visible_name = vnk_zabbix_codemeter[tcp_host][0].lower()  # {HOST.NAME}
        host_desc = f"Host Info: {host_name}"  # Host Description
        tags = [
            {"tag": "Note", "value": ""},
            {"tag": "Owner", "value": f"{vnk_zabbix_codemeter[tcp_host][1]}"}

        ]

    
        # Step 3: Create the new host
        new_pon_host = zapi.host.create({
            "host": host_name,  # Technical name of the host (internal name)
            "name": host_visible_name,  # Visible name of the host in the frontend
            "description": host_desc,  # Host description
            "groups": hgroups_config["groups"],  # Host group
            "templates": templates_config["templates"],  # Template
            "tags": tags,  # Tags
            "interfaces": [  # Add an interface to define how the host connects
                {
                    "type": 1,  # Type of interface: 1 = Agent, 2 = SNMP, 3 = IPMI, 4 = JMX
                    "main": 1,  # Main interface: 1 = Yes, 0 = No
                    "useip": 1,  # Use IP: 1 = IP address, 0 = DNS
                    "ip": vnk_zabbix_codemeter[tcp_host][2],  # IP address of the host
                    "dns": "",  # DNS name (leave empty if using IP)
                    "port": "10050"  # Default Zabbix agent port
                }
            ]

        })

        host_id = new_pon_host['hostids'][0]
        print(f"TCP Host '{host_name}' created with ID {host_id}")

    except Exception as err:
        print(f"Error: {err}")

# HTTP Monitoring
'''
for me_host in vnk_zabbix_data:

    template_ids = {}
    host_group_ids = {}
    template_list = ['Web-Service-Tpl']
    host_group_list = ['Internal_Services']

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

    # Add new Host Group
    host_group_list.append(vnk_zabbix_data[me_host][2])
    #print(me_zabbix_data[me_host][0])
    #print(host_group_list)
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
    #print(hgroups_config)


    # Host information
    host_name = vnk_zabbix_data[me_host][0]  # {HOST.HOST}
    host_visible_name = vnk_zabbix_data[me_host][0].lower()  # {HOST.NAME}
    host_desc = f"Host Info: {host_name}"  # Host Description
    host_url = vnk_zabbix_data[me_host][1]  # Host URL
    tags = [
        {"tag": "Note", "value": ""},
        {"tag": "Owner", "value": f"{vnk_zabbix_data[me_host][2]}"},
        {"tag": "Ext URL", "value": f"{host_url}"},
        {"tag": "Internal_Service", "value": ""}
    ]
    macros = [
        {"macro": "{$HOST.URL}", "value": f"{host_url}"}
    ]

    # Step 3: Create the new host
    new_pon_host = zapi.host.create({
        "host": host_name,  # Technical name of the host (internal name)
        "name": host_visible_name,  # Visible name of the host in the frontend
        "description": host_desc,  # Host description
        "groups": hgroups_config["groups"],  # Host group
        "templates": templates_config["templates"],  # Template
        "tags": tags,  # Tags
        "macros": macros
    })

    host_id = new_pon_host['hostids'][0]
    print(f"Host '{host_name}' created with ID {host_id}")

'''

