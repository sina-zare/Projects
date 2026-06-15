try:
    from pyzabbix import ZabbixAPI
    from cryptography.fernet import Fernet
    import os
except Exception as m_err:
    print(f'Module Import Error: {m_err}')


try:
    def decryptor(enc_env_var, key_env_var):

        # Load the key
        key = os.environ.get(key_env_var)
        encryption_key = Fernet(key)
        encrypted_password = (os.environ.get(enc_env_var)).encode()
        # Decrypt Data
        decrypted_password = encryption_key.decrypt(encrypted_password.decode())

        #print(f"Decryped Text: {decrypted_password}")
        return decrypted_password.decode()

except Exception as f_err:
    print(f'Function Error: {f_err}')


try:
    # Zabbix server credentials
    zabbix_url = "http://zabbix.url/zabbix"
    zabbix_user = "username"
    zabbix_password = decryptor("pass-val","pass-key")


    # Template and Host Group
    template_name = "template-name"  # Template name
    host_group_name = "host-group-name"  # Host group name

    # Host information
    host_name = "my-hostname"  # {HOST.HOST}
    host_visible_name = host_name.split("-")[1]  # {HOST.NAME}
    host_desc = "Added via API"  # Host Description
    tags = [
        {"tag": "Note", "value": ""},
        {"tag": "Owner", "value": "ServiceDesk"}
    ]

    # Connect to Zabbix API
    zapi = ZabbixAPI(zabbix_url)
    zapi.login(zabbix_user, zabbix_password)


    # Step 1: Get the template ID
    template = zapi.template.get(filter={"host": template_name})
    if not template:
        raise Exception(f"Template '{template_name}' not found.")
    template_id = template[0]["templateid"]


    # Step 2: Get the host group ID
    host_group = zapi.hostgroup.get(filter={"name": host_group_name})
    if not host_group:
        raise Exception(f"Host group '{host_group_name}' not found.")
    host_group_id = host_group[0]["groupid"]

    # Step 3: Create the new host with description and visible name
    new_host = zapi.host.create({
        "host": host_name,                          # Technical name of the host (internal name)
        "name": host_visible_name,                  # Visible name of the host in the frontend
        "description": host_desc,                   # Host description
        "groups": [{"groupid": host_group_id}],     # Host group
        "templates": [{"templateid": template_id}],  # Template
        "tags": tags
    })

    print(f"Host '{host_name}' created with ID {new_host['hostids'][0]}")
    print('\n#############\n')

except Exception as b_err:
    print(f'Main Body Error: {b_err}')