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

# Zabbix server details
username = 'sysops-svc'
password = decryptor('sysops-svc_enc', 'sysops-svc_key')

def zabbix_node_adder(hosts, template_list, host_group_list, tag_list, api):

    template_ids = []
    for t in template_list:
        tpl = api.template.get(output=["templateid"], filter={"host": t})
        if not tpl:
            raise Exception(f"Template '{t}' not found")
        template_ids.append({"templateid": tpl[0]["templateid"]})

    group_ids = []
    for g in host_group_list:
        grp = api.hostgroup.get(output=["groupid"], filter={"name": g})
        if not grp:
            raise Exception(f"Group '{g}' not found")
        group_ids.append({"groupid": grp[0]["groupid"]})

    for host in hosts:
        host_name = host["name"]
        host_ip = host["ip"]

        existing = api.host.get(filter={"host": host_name})
        if existing:
            print(f"Skipping existing host: {host_name}")
            continue

        api.host.create({
            "host": host_name,
            "name": host_name,
            "groups": group_ids,
            "templates": template_ids,
            "tags": tag_list,
            "interfaces": [{
                "type": 1,
                "main": 1,
                "useip": 1,
                "ip": host_ip,
                "dns": "",
                "port": "10050"
            }]
        })

        print(f"### Host '{host_name}' created ###")



def get_data_by_hostgroup(zabbix_url, zabbix_user, zabbix_password, hostgroup_name):
    # Connect to Zabbix API
    zapi = ZabbixAPI(zabbix_url)
    zapi.login(zabbix_user, zabbix_password)

    try:
        # Get host group ID for "vcenter"
        hostgroups = zapi.hostgroup.get(filter={"name": hostgroup_name})
        if not hostgroups:
            raise Exception(f"Host group '{hostgroup_name}' not found.")

        hostgroup_id = hostgroups[0]['groupid']

        # Get hosts in the "vcenter" host group
        hosts = zapi.host.get(
            groupids=hostgroup_id,
            output=["hostid", "host", "name"],
            selectInterfaces=["ip"],
        )

        # Format the results
        results = []
        for host in hosts:
            host_info = {
                "hostid": host["hostid"],
                "name": host["name"],
                "ip": host["interfaces"][0]["ip"] if host.get("interfaces") else "0.0.0.0",
            }
            results.append(host_info)

        return results

    finally:
        zapi.user.logout()



# Zabbix server credentials
zabbix_urls = {
    'ME-Zabbix': 'https://me-zabbix.abramad.com/zabbix',
    'VNK-Zabbix': 'https://vnk-zabbix.abramad.com',
}

hostgroup_name = "Hypervisors"

zabbix_templates = ["ICMP Ping IP"]

zabbix_tags = [
    {"tag": "Note", "value": ""},
    {"tag": "Owner", "value": "CSB_Team"},
    {"tag": "__zbx_jira", "value": "1"}
]

vnk_zabbix_host_groups = ["Hypervisors-Miremad"]
me_zabbix_host_groups = ["Hypervisors-Vanak"]

try:
    for zbx_name, zbx_url in zabbix_urls.items():
        if zbx_name == 'ME-Zabbix':
            print(f"\n{zbx_name}")

            me_nodes = get_data_by_hostgroup(zabbix_urls['ME-Zabbix'], username, password, hostgroup_name)

            vnk_zapi = ZabbixAPI(zabbix_urls['VNK-Zabbix'])
            vnk_zapi.login(username, password)

            zabbix_node_adder(me_nodes, zabbix_templates, vnk_zabbix_host_groups, zabbix_tags, vnk_zapi)

        elif zbx_name == 'VNK-Zabbix':
            print(f"\n{zbx_name}")

            vnk_nodes = get_data_by_hostgroup(zabbix_urls['VNK-Zabbix'], username, password, hostgroup_name)

            me_zapi = ZabbixAPI(zabbix_urls['ME-Zabbix'])
            me_zapi.login(username, password)

            zabbix_node_adder(vnk_nodes, zabbix_templates, me_zabbix_host_groups, zabbix_tags, me_zapi)


except Exception as e:
    print(f"Error: {e}")

