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

# Define the host group names
remove_host_group_name = "ServiceDesk"  # Host group to be removed
add_host_group_name_support = "Support_Team"  # Host group to be added
add_host_group_name_mer = "MER-Grp"  # Host group to be added


# Get the host group IDs
remove_host_group = zapi.hostgroup.get(filter={"name": remove_host_group_name})
if not remove_host_group:
    raise Exception(f"Host group '{remove_host_group_name}' not found.")
remove_host_group_id = remove_host_group[0]["groupid"]

add_host_group_support = zapi.hostgroup.get(filter={"name": add_host_group_name_support})
if not add_host_group_support:
    raise Exception(f"Host group '{add_host_group_name_support}' not found.")
add_host_group_id_support = add_host_group_support[0]["groupid"]

add_host_group_mer = zapi.hostgroup.get(filter={"name": add_host_group_name_mer})
if not add_host_group_mer:
    raise Exception(f"Host group '{add_host_group_name_mer}' not found.")
add_host_group_id_mer = add_host_group_mer[0]["groupid"]


# Get all hosts
hosts = zapi.host.get(
    output=["hostid", "host"],  # Get both host ID and host name
    selectTags="extend"        # Include existing tags in the response
)

mer_hosts = []
for host in hosts:
    if host['host'].startswith('mer-') or host['host'].startswith('merd-'):# or host['host'].startswith('mea-'):
        mer_hosts.append([host['host'], host['hostid'], host.get("tags", [])])  # Include existing tags


# Remove the specified host group and add new ones
for h in mer_hosts:
    # Fetch current host groups for the host
    current_groups = zapi.host.get(
        output=["hostid"],
        selectGroups="extend",  # Include current host groups
        filter={"hostid": h[1]}
    )[0]["groups"]


    # Prepare the list of group IDs for the update
    current_group_ids = {group['groupid'] for group in current_groups}

    # Delete ServiceDesk group if present
    if remove_host_group_id in current_group_ids:
        current_group_ids.discard(remove_host_group_id)

    # Add new groups if not already present
    if add_host_group_id_support not in current_group_ids:
        current_group_ids.add(add_host_group_id_support)

    if add_host_group_id_mer not in current_group_ids:
        current_group_ids.add(add_host_group_id_mer)

    # Prepare the updated groups for the API call
    updated_groups = [{"groupid": group_id} for group_id in current_group_ids]

    # Update the host with the new group list
    zapi.host.update({
        "hostid": h[1],
        "groups": updated_groups  # Updated groups (only group IDs)
    })
    print(f"{h[0]} updated with new groups.")
