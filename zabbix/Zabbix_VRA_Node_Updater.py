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

password = decryptor("enc_sinaz_pass", "key_sinaz_pass")

# Zabbix server credentials
zabbix_url = "http://zab.abramad.com/zabbix"
zabbix_user = "sina.z"
zabbix_password = password

# Connect to Zabbix API
zapi = ZabbixAPI(zabbix_url)
zapi.login(zabbix_user, zabbix_password)

host_group_name1 = "Rahkaran-Abri-Grp"  # Host group name
host_group_name2 = "ServiceDesk"  # Host group name


# Step 2: Get the host group ID
host_group1 = zapi.hostgroup.get(filter={"name": host_group_name1})
if not host_group1:
    raise Exception(f"Host group '{host_group_name1}' not found.")
host_group_id1 = host_group1[0]["groupid"]

host_group2 = zapi.hostgroup.get(filter={"name": host_group_name2})
if not host_group2:
    raise Exception(f"Host group '{host_group_name2}' not found.")
host_group_id2 = host_group2[0]["groupid"]



# Get all hosts
hosts = zapi.host.get(
    output=["hostid", "host"]     # Get both host ID and host name
)

vra_hosts = []
for host in hosts:
    if host['host'].startswith('vra-'):
      vra_hosts.append([host['host'], host['hostid']])


print(len(vra_hosts))
for i in vra_hosts:
    print(i)
"""
for h in vra_hosts:

    tags = [
        {"tag": "Note", "value": ""},
        {"tag": "Owner", "value": "ServiceDesk"},
        {"tag": "Ext URL", "value": f"https://{h[0].split('-')[1]}.rahkaran.ir"},
        {"tag": "Int URL", "value": f"http://{h[0]}.cloud.local"}
    ]

    zapi.host.update({
    "hostid": h[1],
    "groups": [{"groupid": host_group_id1}, {"groupid": host_group_id2}],
    "tags": tags
            })
    print(f"{h[0]} updated.")
"""

# Logout from the Zabbix API session
zapi.user.logout()

