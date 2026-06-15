from pyzabbix import ZabbixAPI
import os
from cryptography.fernet import Fernet

def decryptor(enc_env_var, key_env_var):
    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = os.environ.get(enc_env_var).encode()
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())
    return decrypted_password.decode()

zabbix_servers = {
    'VNK-Zabbix': "https://vnk-zabbix.abramad.com",
    'VNK-CustomerZabbix': 'http://172.29.6.15',
    'ME-Zabbix': 'http://172.17.234.13/zabbix/',
    'ME-CustomerZabbix': 'http://172.17.234.23'
}

username = 'sysops-svc'
password = decryptor('sysops-svc_enc', 'sysops-svc_key')

tag_to_remove = '__zbx_jira_test'

for zabbix_server_name, zabbix_server_address in zabbix_servers.items():
    # Connect to Zabbix API
    zapi = ZabbixAPI(zabbix_server_address)
    zapi.login(username, password)
    print(f'\nConnected to {zabbix_server_name}')

    # Get all hosts with their current tags
    hosts = zapi.host.get(output=["hostid", "host"], selectTags="extend")

    for host in hosts[:]:
        host_id = host["hostid"]
        hostname = host["host"]

        # Clean current tags and remove 'automatic' field
        raw_tags = host.get("tags", [])
        cleaned_tags = [{"tag": t["tag"], "value": t["value"]} for t in raw_tags]

        # Filter out the tag to remove
        updated_tags = [t for t in cleaned_tags if t["tag"] != tag_to_remove]

        # Only update if a change occurred
        if len(updated_tags) != len(cleaned_tags):
            try:
                zapi.host.update(
                    hostid=host_id,
                    tags=updated_tags
                )
                print(f"[OK] Removed tag '{tag_to_remove}' from host '{hostname}' on {zabbix_server_name}")
            except Exception as e:
                print(f"[ERROR] Failed to update host '{hostname}' on {zabbix_server_name}: {e}")
        else:
            print(f"[SKIP] Tag '{tag_to_remove}' not present on host '{hostname}' on {zabbix_server_name}")
