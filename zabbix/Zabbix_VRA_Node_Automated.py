try:
    from pyzabbix import ZabbixAPI
    from cryptography.fernet import Fernet
    import os
    from pyvim.connect import Disconnect
    from pyvim import connect
    from pyVmomi import vim
    import traceback
    import warnings
    import time
    import ssl
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

        # print(f"Decryped Text: {decrypted_password}")
        return decrypted_password.decode()

except Exception as f_err:
    print(f'Function Error: {f_err}')

try:
    # Nodes Information Gathering
    password = decryptor("enc_sinaz_pass", "key_sinaz_pass")

    # Ignore the warning
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    # *** Connecting to ME-VC01.Abramad.Com to get the Report ***

    # Create an SSL context with no certificate verification
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.verify_mode = ssl.CERT_NONE

    ME_VC = connect.SmartConnect(host='vra-vc01.abramad.com', user='sina.z@abramad.com', pwd=password, port=443, sslContext=context)
    me_content = ME_VC.RetrieveContent()
    me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
    me_vms = [vm for vm in me_vm_view.view if (vm.name.startswith("VRA-") and not vm.name.startswith("VRA-HAProxy") and not vm.name.startswith("VRA-Template"))]
    # Sort the me_vms list based on VM names
    sorted_vms = sorted(me_vms, key=lambda vm: vm.name.lower())

    vra_on_dict = {}
    vra_off_dict = {}

    for vm in sorted_vms:


        # Iterate through the hardware devices to find network adapters
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                # Checking if vm is in 'VRA-1003-Customers' PortGroup
                if device.backing.port.portgroupKey == 'dvportgroup-7117':

                    # VM Note (Persian Name)
                    vm_note = 'فاقد نام فارسی'
                    vm_note = vm.config.annotation.split("\n")[0].strip()

                    vm_name = vm.name

                    vm_url = f"https://{vm_name.lower().split('-')[1]}.rahkaran.ir"

                    vm_info = [vm_name.lower(), vm_url, vm_note]

                    # Power State
                    vm_power_state = vm.runtime.powerState

                    if vm_power_state.lower() == "poweredon":

                        # Filling Powered On VRA VMs Dictionary
                        vra_on_dict[f"{vm_info[0].lower()}"] = vm_info

                    elif vm_power_state.lower() == "poweredoff":

                        # Filling Powered Off VRA VMs Dictionary
                        vra_off_dict[f"{vm_info[0].lower()}"] = vm_info

    Disconnect(ME_VC)

    """    
    for k, v in vra_on_dict.items():
        print(f"{k}: {v}")

    print(40 * '*')

    for k, v in vra_off_dict.items():
        print(f"{k}: {v}")"""


    # Zabbix Node Addition
    # Zabbix server credentials
    zabbix_url = "http://zab.abramad.com/zabbix"
    zabbix_user = "sina.z"
    zabbix_password = password

    # Template and Host Group
    template_name = "Rahkaran-Abri-Tpl"  # Template name
    host_group_name1 = "Rahkaran-Abri-Grp"  # Host group name
    host_group_name2 = "ServiceDesk"  # Host group name

    # Connect to Zabbix API
    zapi = ZabbixAPI(zabbix_url)
    zapi.login(zabbix_user, zabbix_password)

    # Step 1: Get the template ID
    template = zapi.template.get(filter={"host": template_name})
    if not template:
        raise Exception(f"Template '{template_name}' not found.")
    template_id = template[0]["templateid"]

    # Step 2: Get the host group ID
    host_group1 = zapi.hostgroup.get(filter={"name": host_group_name1})
    if not host_group1:
        raise Exception(f"Host group '{host_group_name1}' not found.")
    host_group_id1 = host_group1[0]["groupid"]

    host_group2 = zapi.hostgroup.get(filter={"name": host_group_name2})
    if not host_group2:
        raise Exception(f"Host group '{host_group_name2}' not found.")
    host_group_id2 = host_group2[0]["groupid"]
    
    

    # Powered On Node Addition (Enabled)
    for pon_node in list(vra_on_dict.keys())[999:]:
        try:
            # Host information
            host_name = vra_on_dict[pon_node][0]         # {HOST.HOST}
            host_visible_name = host_name.split("-")[1]  # {HOST.NAME}
            host_desc = vra_on_dict[pon_node][2]         # Host Description
            host_url = vra_on_dict[pon_node][1]          # Host URL
            tags = [
                {"tag": "Note", "value": ""},
                {"tag": "Owner", "value": "ServiceDesk"},
                {"tag": "Ext URL", "value": f"https://{host_name.lower().split('-')[1]}.rahkaran.ir"},
                {"tag": "Int URL", "value": f"http://{host_name.lower()}.cloud.local"}
            ]

            # Step 3: Create the new host with description and visible name
            new_pon_host = zapi.host.create({
                "host": host_name,                           # Technical name of the host (internal name)
                "name": host_visible_name,                   # Visible name of the host in the frontend
                "description": host_desc,                    # Host description
                "groups": [{"groupid": host_group_id1}, {"groupid": host_group_id2}],      # Host group
                "templates": [{"templateid": template_id}],  # Template
                "tags": tags
            })

            host_id = new_pon_host['hostids'][0]
            print(f"Host '{host_name}' created with ID {host_id}")

        except Exception as node_error:
            print(f"Error adding node '{pon_node}': {node_error}")
            continue  # Continue to the next node even if an error occurs


    print(f"\n{50 * '#'}\n")

    # Powered Off Node Addition (Enabled)
    for poff_node in list(vra_off_dict.keys())[0:0]:
        try:
            # Host information
            host_name = vra_off_dict[poff_node][0]        # {HOST.HOST}
            host_visible_name = host_name.split("-")[1]   # {HOST.NAME}
            host_desc = vra_off_dict[poff_node][2]        # Host Description
            host_url = vra_off_dict[poff_node][1]         # Host URL
            tags = [
                {"tag": "Note", "value": ""},
                {"tag": "Owner", "value": "ServiceDesk"},
                {"tag": "Ext URL", "value": f"https://{host_name.lower().split('-')[1]}.rahkaran.ir"},
                {"tag": "Int URL", "value": f"http://{host_name.lower()}.cloud.local"}
            ]

            # Step 3: Create the new host with description and visible name
            new_poff_host = zapi.host.create({
                "host": host_name,                           # Technical name of the host (internal name)
                "name": host_visible_name,                   # Visible name of the host in the frontend
                "description": host_desc,                    # Host description
                "groups": [{"groupid": host_group_id1}, {"groupid": host_group_id2}],      # Host group
                "templates": [{"templateid": template_id}],  # Template
                "tags": tags
            })

            host_id = new_poff_host['hostids'][0]
            print(f"Host '{host_name}' created with ID {host_id}", end=" ")


            # Step 4: Disable the host
            zapi.host.update({
                "hostid": host_id,
                "status": 1  # Set status to 1 to disable the host
            })

            print(f"Host '{host_name}' with ID {host_id} has been disabled.")

        except Exception as node_error:
            print(f"Error adding node '{poff_node}': {node_error}")
            continue  # Continue to the next node even if an error occurs

    # Logout from the Zabbix API session
    zapi.user.logout()

    print(f"\nOn: {len(vra_on_dict)}\nOff: {len(vra_off_dict)}")

except Exception as b_err:
    print(f'Main Body Error: {b_err}')
    traceback.print_exc()  # This will print the full traceback including the line number


