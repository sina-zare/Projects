#!/usr/bin/env python3
from pyzabbix import ZabbixAPI
import os
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

username = 'sysops-svc'
password = decryptor('sysops-svc_enc', 'sysops-svc_key')

# Zabbix connection details
zabbix_url = "https://vnk-customerzabbix.abramad.com"

# Connect to Zabbix API
zapi = ZabbixAPI(zabbix_url)
zapi.login(username, password)

# Get all 'agent.version' items for all hosts

key = "system.sw.os"


items = zapi.item.get(
    search={"key_": key},
    output=["hostid", "name", "lastvalue"],
    selectHosts=["host", "name"]
)

# Print host name and agent version
updated = 0
not_updated = 0
for item in items:
    host = item["hosts"][0]
    if item['lastvalue'] == 'Windows Server 2019 Standard 17763.1.amd64fre.rs5_release.180914-1434 Build 17763.7678':
        updated += 1
        print(f"{host['name']}: {item.get('lastvalue', 'Not found')}")
    else:
        not_updated += 1
        #print(f"{host['name']}: {item.get('lastvalue', 'Not found')}")

#print(f'\n\nZabbix Agent 2 Update Status\nSuccess: {updated}\nFail: {not_updated}')
# Logout
zapi.user.logout()
