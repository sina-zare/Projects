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
zabbix_url = "http://vnk-zabbix.abramad.com"
zabbix_user = "sina.z"
zabbix_password = password


# Connect to Zabbix API
zapi = ZabbixAPI(zabbix_url)
zapi.login(zabbix_user, zabbix_password)



# Get all hosts
hosts = zapi.host.get(
    output=["hostid", "host"],  # Get both host ID and host name
    selectTags="extend"        # Include existing tags in the response
)

vra_hosts = []
for host in hosts:
    if host['host'].startswith('ra-') or host['host'].startswith('rap-'):
        vra_hosts.append([host['host'], host['hostid'], host.get("tags", [])])  # Include existing tags

mer_hosts = []
for host in hosts:
    if host['host'].startswith('mer-') or host['host'].startswith('merd-'):# or host['host'].startswith('mea-'):
        mer_hosts.append([host['host'], host['hostid'], host.get("tags", [])])  # Include existing tags


for h in mer_hosts:
    # Get existing tags
    existing_tags = h[2]

    # Remove unnecessary fields (keep only "tag" and "value")
    cleaned_tags = [{"tag": tag["tag"], "value": tag["value"]} for tag in existing_tags]

    #for tag in cleaned_tags:
    #   print(tag)


    # Remove a specific tag by filtering (e.g., remove tag "Owner")
    cleaned_tags = [tag for tag in cleaned_tags if tag["tag"] != "Owner"]

    # Add a new tag
    new_tag = {"tag": "Owner", "value": "Support_Team"}
    cleaned_tags.append(new_tag)

    # Update the host
    zapi.host.update({
        "hostid": h[1],
        "tags": cleaned_tags,  # Updated tags

    })
    print(f"{h[0]} updated with new tags.")

