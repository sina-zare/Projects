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

    #print(f"Decryped Text: {decrypted_password}")
    return decrypted_password.decode()

# ================================================================================ #

# Configuration
ZABBIX_URL = "http://172.17.234.13/zabbix"
USERNAME = 'sysops-svc'
PASSWORD = decryptor('sysops-svc_enc', 'sysops-svc_key')
HOST_GROUP_NAME = "ME_OnPrem_ICMP"

# Connect to Zabbix API
zapi = ZabbixAPI(ZABBIX_URL)
zapi.login(USERNAME, PASSWORD)

print(f"Connected to Zabbix API. Version: {zapi.api_version()}")

try:
    # Get the host group ID by name
    host_group = zapi.hostgroup.get(filter={"name": HOST_GROUP_NAME})
    if not host_group:
        print(f"Host group '{HOST_GROUP_NAME}' not found.")
        exit(1)

    host_group_id = host_group[0]['groupid']

    # Get all hosts in the host group
    hosts = zapi.host.get(groupids=host_group_id, output=["hostid", "name"])
    if not hosts:
        print(f"No hosts found in host group '{HOST_GROUP_NAME}'.")
        exit(0)

    print(f"Found {len(hosts)} hosts in the group '{HOST_GROUP_NAME}'. Deleting...")

    # Collect host IDs
    host_ids = [host['hostid'] for host in hosts]
    for i in host_ids[:]:

        result = zapi.host.delete(i)
        print(f"Successfully deleted host: {result['hostids']}")
    # Delete hosts
    #result = zapi.host.delete(*host_ids)
    #print(f"Successfully deleted hosts: {result['hostids']}")

except Exception as e:
    print(f"An error occurred: {e}")

