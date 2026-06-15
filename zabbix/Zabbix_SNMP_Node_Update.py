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


# Get the host group ID(s) you want to filter by
host_groups = zapi.hostgroup.get(filter={"name": ["ILO"]})  # Replace with your host group name(s)
if not host_groups:
    print("Host group not found!")
    exit()

group_ids = [group["groupid"] for group in host_groups]

# Fetch hosts filtered by host group(s)
hosts = zapi.host.get(
    output=["hostid", "host"],  # Get both host ID and host name
    groupids=group_ids         # Filter by the group IDs
)

"""
# Display the results
if hosts:
    for host in hosts:
        print(f"Host ID: {host['hostid']}, Host Name: {host['host']}")
else:
    print("No hosts found in the specified host group(s).")
"""

for host in hosts[:]:

    host_id = host["hostid"]

    # Get the interfaces for the host
    interfaces = zapi.hostinterface.get(filter={"hostid": host_id, "type": 2})  # Type 2 = SNMP
    if not interfaces:
        print("No SNMP interfaces found for the host!")
        exit()

    # Assuming you are updating the first SNMP interface
    interface_id = interfaces[0]["interfaceid"]



    # Update the interface with new SNMP settings
    updated_interface = zapi.hostinterface.update({
        "interfaceid": interface_id,
        "details": {
            "version": 3,  # SNMPv3
            "bulk": 1,  # Use combined requests
            "securityname": "{$SECURITY_NAME}",  # Update as needed
            "securitylevel": 2,  # AuthPriv
            "authprotocol": 3,  # SHA512
            "authpassphrase": "{$AUTH_PASSPHARASE}",  # Update as needed
            "privprotocol": 1,  # AES256
            "privpassphrase": "{$PRIVACY_PASSPHARASE}",  # Update as needed
            "contextname": ""  # Optional SNMP context name
        }
    })

    print(f"SNMP settings updated for {host['host']}:", updated_interface)

