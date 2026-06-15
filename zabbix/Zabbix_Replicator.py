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

def zabbix_replicator(source_zabbix, destination_zabbix):

    print(f'\n{5 * '#'} Starting Replication Process {5 * '#'}')
    from pyzabbix import ZabbixAPI

    print(f'\n0) Establishing Zabbix API Connection')
    # Connect to Source Zabbix API
    source_zapi = ZabbixAPI(source_zabbix)
    source_zapi.login(username, password)

    # Connect to Destination Zabbix API
    dest_zapi = ZabbixAPI(destination_zabbix)
    dest_zapi.login(username, password)


    # HostGroup Replication
    print('\n1) HostGroup Replication')
    # Fetch only manually created host groups (excluding discovered ones)
    print('\t- Retrieving Host Groups From Source Zabbix')
    source_hostgroups = source_zapi.hostgroup.get(output=["groupid", "name"], filter={"flags": "0"})

    # Create host groups in the destination Zabbix server
    print(f'\t- Creating HostGroups on Destination Zabbix')
    for group in source_hostgroups[:]:
        try:
            dest_zapi.hostgroup.create({"name": group['name']})
            print(f"\t\t- ✅ Created host group: {group['name']}")

        except Exception as err:
            print(f"\t\t- ❌ Error Creating Host Group: {err}")



    # Template Replication
    print('\n2) Template Replication')

    source_templates =[]

    print('\t- Retrieving Templates From Source Zabbix')
    # Fetch all templates with linked hosts
    source_templates_with_hosts = source_zapi.template.get(
        selectHosts="extend",  # Get detailed host information
        output=["templateid", "name"]  # Only fetch template ID and name
    )

    # Find templates that have at least one host attached
    print('\t- Exporting Active Templates From Source Zabbix')
    source_templates_with_at_least_one_host = [
        [template['name'], template['templateid']] for template in source_templates_with_hosts if template['hosts']
    ]

    # Export templates with at least one host attached
    if source_templates_with_at_least_one_host:
        for template in source_templates_with_at_least_one_host:

            template_name = template[0]
            template_id = template[1]

            try:
                # Export template by ID
                export_data = source_zapi.configuration.export(
                    format="json",  # Export format (xml or json)
                    options={
                        "templates": [template_id],  # Specify templates to export
                        "hosts": []  # Include the hosts in the export
                    }
                )
                source_templates.append([template_name, export_data])

            except Exception as err:
                print(f"\t\t- ❌ Error exporting template {template_name}: {err}")

    # Import Templates into Target Zabbix
    print('\t- Importing Templates Into Destination Zabbix')

    for template_json in source_templates[:]:
        try:
            # Use do_request to call 'configuration.import' directly
            import_result = dest_zapi.do_request(
                method="configuration.import",
                params={
                    "format": "json",
                    "rules": {
                        "templates": {"createMissing": True, "updateExisting": True}
                    },
                    "source": template_json[1]
                }
            )
            print(f"\t\t- ✅ Template {template_json[0]} imported successfully")
        except Exception as err:
            print(f"\t\t- ❌ Error importing template {template_json[0]}: {err}")


    # Host Replication
    print('\n3) Host Replication')

    # Retrieve all hosts with full configuration
    print('\t- Retrieving Hosts From Source Zabbix')
    source_hosts = source_zapi.host.get(
        output="extend",  # Get all host details
        selectParentTemplates=["templateid", "name"],  # Linked templates
        selectGroups=["groupid", "name"],  # Host groups
        selectTags="extend",  # Host tags
        selectInterfaces="extend",  # Network interfaces
        selectMacros="extend",  # User-defined macros
        selectInventory="extend",  # Inventory data (optional)
        selectHostDiscovery="extend",  # Auto-discovery data (if any)
        filter = {"flags": 0}  # Exclude auto-created hosts
    )



    # Step 1: Retrieve Existing Host Groups and Templates from Destination Zabbix
    print("\t- Fetching host groups and templates from destination Zabbix")

    # Fetch all host groups from destination
    dest_host_groups = dest_zapi.hostgroup.get(output=["groupid", "name"])
    dest_host_group_map = {group["name"]: group["groupid"] for group in dest_host_groups}

    # Fetch all templates from destination
    dest_templates = dest_zapi.template.get(output=["templateid", "name"])
    dest_template_map = {template["name"]: template["templateid"] for template in dest_templates}

    # Step 2: Process and Create Hosts in Destination Zabbix
    print("\t- Processing and Creating Hosts in Destination Zabbix")
    for host in source_hosts[:]:
        host_name = host["host"]


        # Map host groups (Convert names to correct group IDs)
        group_ids = [dest_host_group_map[group["name"]] for group in host["groups"] if
                     group["name"] in dest_host_group_map]

        # Map templates (Convert names to correct template IDs)
        template_ids = [{"templateid": dest_template_map[tpl["name"]]} for tpl in host["parentTemplates"] if
                        tpl["name"] in dest_template_map]


        # Process interfaces: Remove 'interfaceid' and ensure required fields exist
        from collections import defaultdict

        # Ensure only one default interface per type
        interface_defaults = defaultdict(lambda: False)

        cleaned_interfaces = []
        for interface in host.get("interfaces", []):
            interface_data = {
                "type": interface["type"],  # 1=Agent, 2=SNMP, 3=IPMI, 4=JMX
                "main": 0,  # Set as non-default initially
                "useip": interface["useip"],
                "ip": interface["ip"],
                "dns": interface["dns"],
                "port": interface["port"],
            }

            # Check if this is the first interface of its type
            if not interface_defaults[interface["type"]]:
                interface_data["main"] = 1  # Mark the first one as default
                interface_defaults[interface["type"]] = True  # Set flag for this type

            # If it's an SNMP interface, add SNMP-specific details
            if interface["type"] == "2":  # SNMP
                snmp_details = interface.get("details", {})
                snmp_version = snmp_details.get("version", 3)  # Default to SNMPv3

                interface_data["details"] = {
                    "version": snmp_version,
                    "bulk": snmp_details.get("bulk", 1),
                }

                if snmp_version == 3:
                    interface_data["details"].update({
                        "contextname": snmp_details.get("contextname", ""),
                        "securityname": snmp_details.get("securityname", "zabbix"),
                        "securitylevel": snmp_details.get("securitylevel", 2),
                        "authprotocol": snmp_details.get("authprotocol", 0),
                        "authpassphrase": snmp_details.get("authpassphrase", "authpassword"),
                        "privprotocol": snmp_details.get("privprotocol", 0),
                        "privpassphrase": snmp_details.get("privpassphrase", "privpassword"),
                    })
                else:
                    interface_data["details"]["community"] = snmp_details.get("community", "public")

            cleaned_interfaces.append(interface_data)

            # Process macros: Remove 'hostmacroid' if it exists
            cleaned_macros = []
            for macro in host.get("macros", []):
                cleaned_macros.append({
                    "macro": macro["macro"],
                    "value": macro["value"],
                    "type": macro.get("type", 0),  # Keep type if available
                    "description": macro.get("description", "")  # Keep description if available
                })

            # Prepare Host Data for Creation
            host_data = {
                "host": host_name,
                "name": host["name"],
                "interfaces": cleaned_interfaces,  # Use cleaned interfaces
                "groups": [{"groupid": gid} for gid in group_ids],
                "templates": template_ids,
                "macros": cleaned_macros,  # Use cleaned macros
                "tags": host.get("tags", []),
                "inventory": host.get("inventory", {})
            }
            #result = dest_zapi.host.create(host_data)
            # Create Host in Destination Zabbix
            try:
                result = dest_zapi.host.create(host_data)
                print(f"\t\t✅ Host '{host_name}' created successfully with ID: {result['hostids'][0]}")
            except Exception as e:
                print(f"\t\t❌ Failed to create host '{host_name}': {e}")







# Zabbix server details
username = 'sysops-svc'
password = decryptor('sysops-svc_enc', 'sysops-svc_key')

zabbix_servers = [

            # Primary Zabbix                # Secondary Zabbix
        ['http://zab.abramad.com/zabbix', 'http://172.17.234.13/zabbix'],

    ]


for zabbix_server in zabbix_servers:

    zabbix_replicator(zabbix_server[0], zabbix_server[1])

