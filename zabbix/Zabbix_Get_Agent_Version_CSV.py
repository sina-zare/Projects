#!/usr/bin/env python3
from pyzabbix import ZabbixAPI
import os
from cryptography.fernet import Fernet
import csv

def decryptor(enc_env_var, key_env_var):

    # Load the key
    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = (os.environ.get(enc_env_var)).encode()
    # Decrypt Data
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())

    #print(f"Decryped Text: {decrypted_password}")
    return decrypted_password.decode()

###  User Parameters  ###
item_key = 'agent.version'


host_status_dict = {
    '1': 'Off',
    '0': 'On',
    '3': 'Template'
}

zabbix_url_dict = {
    'ME-Zabbix' : 'http://172.17.234.13/zabbix/',
    'ME-CustomerZabbix' : 'https://me-customerzabbix.abramad.com',
    'VNK-Zabbix' : 'https://vnk-zabbix.abramad.com',
    'VNK-CustomerZabbix' : 'https://vnk-customerzabbix.abramad.com',
}

username = 'sysops-svc'
password = decryptor('sysops-svc_enc', 'sysops-svc_key')


for url_key, url_value in zabbix_url_dict.items():

    # Connect to Zabbix API
    zapi = ZabbixAPI(url_value)
    zapi.session.verify = False  # tell requests not to verify TLS
    zapi.login(username, password)

    csv_file_path = f"C://Temp//{url_key}_agent_versions.csv"

    print(f'\n\n######### {url_key} Connected #########')
    # Get all 'agent.version' items for all hosts
    # Step 1: get items
    items = zapi.item.get(
        search={"key_": item_key},
        output=["hostid", "name", "lastvalue"],
        selectHosts=["hostid", "name", "status"]
    )

    # Step 2: get all host IDs
    host_ids = list({item["hosts"][0]["hostid"] for item in items})

    # Step 3: get host tags
    hosts_with_tags = zapi.host.get(
        hostids=host_ids,
        output=["hostid", "name", "status"],
        selectTags="extend"
    )

    # Map hostid -> tags
    host_tags_map = {}
    for h in hosts_with_tags:
        host_id = h["hostid"]  # get the host ID
        tags = h.get("tags", [])  # get the host's tags, or [] if none
        host_tags_map[host_id] = tags  # add to the dictionary

    # Print host name and agent version
    with open(csv_file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Host", "Agent Version", "Power Status", "Owner"])

        for item in items:
            host = item["hosts"][0]
            host_id = host["hostid"]
            item_value = item["lastvalue"]
            host_name = host["name"]
            host_status = host["status"]

            # Step 4: get Owner tag from the map
            tags = host_tags_map.get(host_id, [])
            owner = next((t["value"] for t in tags if t["tag"] == "Owner"), "")

            print(f"{host_status_dict[host_status]}) {host_name}: {item_value}, {owner}")
            if host_status_dict[host_status] != 'Template':
                #if item_value != '7.0.18':
                writer.writerow([host_name, item_value, host_status_dict[host_status], owner])

    # Logout
    zapi.user.logout()
