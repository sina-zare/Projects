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
            selectGroups=["name"],
            selectInventory=["description"]
        )

        # Format the results
        results = []
        for host in hosts:
            host_info = {
                "hostid": host["hostid"],
                "name": host["name"],
                "ip": host["interfaces"][0]["ip"] if host.get("interfaces") else "N/A",
                "description": host["inventory"].get("description", "N/A") if host.get("inventory") else "N/A",
                "group": host["groups"][0]["name"] if host.get("groups") else "N/A"
            }
            results.append(host_info)

        return results
    finally:
        zapi.user.logout()



# Zabbix server credentials
zabbix_url = "http://172.29.6.11"
hostgroup_name = "VRA Servers"

try:
    nodes = get_data_by_hostgroup(zabbix_url, username, password, hostgroup_name)
    print(f"Nodes in host group '{hostgroup_name}':")
    for node in nodes:
        print(f"{node['name'].strip('.abramad.com')},{node['ip']}")
except Exception as e:
    print(f"Error: {e}")

