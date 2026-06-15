try:
    from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter
    from email.mime.multipart import MIMEMultipart
    from cryptography.fernet import Fernet
    from pyvim.connect import Disconnect
    from email.mime.text import MIMEText
    from email.header import Header
    from pyzabbix import ZabbixAPI
    from pyvim import connect
    from pyVmomi import vim
    import traceback
    import jdatetime
    import warnings
    import smtplib
    import time
    import ssl
    import os

except Exception as module_err:
    print(f"Module Error: {module_err}")
    print(f"Exception type: {type(module_err).__name__}")
    traceback.print_exc()

# --- Configuration ---
script_name = 'zabbix_vra_fully_automated'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'http://me-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
datacenter = 'vanak'
target = 'vnk_rahkaran_abri_url'

# Create a registry for our custom metrics
registry = CollectorRegistry()

# Define metrics
duration_gauge = Gauge('script_exec_duration_seconds', 'Duration of my script', registry=registry)
status_gauge = Gauge('script_success', 'Whether script succeeded (1) or failed (0)', registry=registry)
total_execution_counter = Counter('script_total_execs', 'Total number of times the script has run', registry=registry)
total_failed_execution_counter = Counter('script_total_failed_execs',
                                         'Total number of times the script has failed to finish gracefully',
                                         registry=registry)
last_error_message = Gauge('script_last_error_message', 'The last error message encountered during script execution',
                           ['error_summary', 'error_detail'], registry=registry)

# Simulate your script logic
start_time = time.time()
success = True
error_string_summary = ""
error_string_detail = ""

try:
    try:
        # --- Read script run counter from file ---
        def read_value_from_file(file_path):
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                os.makedirs(directory)  # Create the directory if it doesn't exist

            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    f.write('0')
                return 0

            try:
                with open(file_path, 'r') as f:
                    return int(f.read().strip())
            except ValueError:
                # In case of a corrupt or non-integer value
                return 0


        # --- Write updated count to file ---
        def write_value_to_file(file_path, value):
            with open(file_path, 'w') as f:
                f.write(str(value))


        def decryptor(enc_env_var, key_env_var):
            # Load the key
            key = os.environ.get(key_env_var)
            encryption_key = Fernet(key)
            encrypted_password = (os.environ.get(enc_env_var)).encode()
            # Decrypt Data
            decrypted_password = encryption_key.decrypt(encrypted_password.decode())

            # print(f"Decryped Text: {decrypted_password}")
            return decrypted_password.decode()


        username = 'sysops-svc@abramad.com'
        password = decryptor('sysops-svc_enc', 'sysops-svc_key')
        from_email = 'me-customerzabbix@abramad.com'
        default_receivers = 'abramadsysops@abramad.com'
        error_receivers = 'abramadsysops@abramad.com, support@abramad.com'
        # default_cc = 'sina.z@abramad.com'
        default_cc = 'sina.z@abramad.com'


        def send_anonymous_email(from_email, to_email, cc_email, subject, html_message, direction,
                                 mail_server='mail.abramad.com'):
            try:
                global success
                global error_string_summary
                global error_string_detail

                ##############################################
                ######### HTML Body Begin For Email ##########
                html_line_break = '''
                                        <p><br></p>
                                    '''
                html_msg_1 = f'''
                                    <html dir={direction}>
                                      <body>
                                    '''
                html_msg_2 = f'''
                                        <p  style="font-family: DiodrumArabic-Regular">{html_message}</p>
                                    '''

                html_msg_3 = f'''

                                        '''
                html_msg_4 = '''
                                      </body>
                                    </html>
                                    '''
                ######### HTML Body End For Email ##########
                ############################################

                email_body = html_msg_1 + html_msg_2 + html_line_break + html_line_break + html_msg_3 + html_msg_4

                # Split email addresses into lists
                to_email_list = to_email.split(",") if to_email else []
                cc_email_list = cc_email.split(",") if cc_email else []
                all_recipients = to_email_list + cc_email_list

                # Create the MIME email object with HTML content
                msg = MIMEText(email_body, "html", "utf-8")
                msg["From"] = Header(from_email, "utf-8")
                msg["To"] = Header(", ".join(to_email_list), "utf-8")  # For display purposes
                msg["CC"] = Header(", ".join(cc_email_list), "utf-8")  # For display purposes
                msg["Subject"] = Header(subject, "utf-8")

                # Connect to the mail server and send the email
                with smtplib.SMTP(mail_server, 25) as server:
                    server.sendmail(from_email, all_recipients, msg.as_string())
                    print("Email sent successfully.")


            except Exception as err:
                print(f"email_sender Function Error: {err}")
                print(f"Exception type: {type(err).__name__}")
                traceback.print_exc()
                """
                send_anonymous_email('ScriptError@abramad.com', error_receivers, default_cc,
                                     f"email_sender Function Error in running Zabbix_Add_vCenter_ICMP_Fully_Automated.py",
                                     f"Error Occurred:<br><b>{err}<br>{traceback.print_exc()}<br>Exception type: {type(err).__name__}</b> Agent: {script_name}.py",
                                     'ltr')"""

                print(f"Script failed: {err}")
                success = False
                error_string_summary += f" {type(err).__name__}: {err}"

                # Get the traceback and extract the last traceback frame
                tb = traceback.extract_tb(err.__traceback__)
                last_call = tb[-1]  # the last traceback frame, where the exception occurred
                error_string_detail += f" Error 'email_sender' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"


    except Exception as function_error:
        print(f"Function Error: {function_error}")
        print(f"Exception type: {type(function_error).__name__}")
        traceback.print_exc()
        send_anonymous_email(from_email, error_receivers, default_cc,
                             f"Email Function Error in running Zabbix_VRA_Fully_Automated.py",
                             f"Error Occurred:<br><b>{function_error}<br>{traceback.print_exc()}<br>Exception type: {type(function_error).__name__}</b> Agent: Zabbix_VRA_Fully_Automated.py",
                             'ltr')

        print(f"Script failed: {function_error}")
        success = False
        error_string_summary += f" {type(function_error).__name__}: {function_error}"

        # Get the traceback and extract the last traceback frame
        tb = traceback.extract_tb(function_error.__traceback__)
        last_call = tb[-1]  # the last traceback frame, where the exception occurred
        error_string_detail += f" Error 'Function Section' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"

    #################################################
    ################ Data Gathering #################

    try:
        print('Starting vCenter data gathering')
        # Ignore the warning
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        # *** Connecting to ME-VC01.Abramad.Com to get the Report ***
        # Create an SSL context with no certificate verification
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.verify_mode = ssl.CERT_NONE

        # Connecting to vCenter
        vra_vc = connect.SmartConnect(host='vra-vc01.abramad.com', user=username, pwd=password, port=443,
                                      sslContext=context)
        vra_content = vra_vc.RetrieveContent()
        vra_vm_view = vra_content.viewManager.CreateContainerView(vra_content.rootFolder, [vim.VirtualMachine], True)
        vra_vms = [vm for vm in vra_vm_view.view if (vm.name.startswith("VRA-"))]
        # vra_vms = [vm for vm in vra_vm_view.view if (vm.name.lower().startswith("vra-nabigol"))]
        sorted_vms = sorted(vra_vms, key=lambda vm: vm.name.lower())

        vcenter_pon_vms = {}
        vcenter_poff_vms = {}
        vcenter_vra_vms = {}

        for vm in sorted_vms:

            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                    network = device.backing
                    if isinstance(network, vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo):
                        dvs_portgroup_key = network.port.portgroupKey
                        dvs_uuid = network.port.switchUuid
                        # Retrieve the Distributed Virtual Switch
                        dvs = vra_content.dvSwitchManager.QueryDvsByUuid(dvs_uuid)
                        # Find the port group by key
                        for portgroup in dvs.portgroup:
                            vm_portgroup = ''
                            if portgroup.key == dvs_portgroup_key:
                                # VM PortGroup Name
                                vm_portgroup = portgroup.name
                                break

            # Checking if vm is in 'VRA-1003-Customers' PortGroup
            if vm_portgroup.startswith(
                    'RA-Customers-N1003-VM') and vm.name.lower() != 'vra-amini2' and vm.name.lower() != 'vra-amini3' and vm.name.lower() != 'vra-demo' and vm.name.lower() != 'vra-bi1' and not vm.name.lower().startswith(
                    'vra-haproxy') and vm.name.lower() != 'vra-pentest' and vm.name.lower() != 'vra-gildatest':

                # VM Name
                vm_name = vm.name.lower()

                # VM Note (Persian Name)
                try:
                    vm_note = vm.config.annotation.split("\n")[0].strip()
                except AttributeError:
                    vm_note = 'فاقد نام فارسی'

                # vm FQDN
                try:
                    vm_fqdn = vm.summary.guest.hostName.lower()
                except:
                    vm_fqdn = f"{vm_name}.cloud.local"

                # VM Power State
                vm_power = power_state = vm.runtime.powerState.lower()

                # Taking URL
                custom_value = vm.summary.customValue
                default_url = f'https://{vm_name.lower().split("-")[1]}.rahkaran.ir'
                vm_url = default_url

                # Look for custom key 902
                for i in custom_value:
                    if i.key == 902:
                        raw_value = i.value.strip().lower()
                        print(f"{vm_name}\n\t{i.key}: {i.value}\n")
                        if raw_value:
                            vm_url = raw_value

                # Normalize
                vm_url = vm_url.strip().lower()

                # Ensure https
                if not vm_url.startswith('https://'):
                    vm_url = 'https://' + vm_url.lstrip('http://')

                # Remove trailing slash for clean comparison
                url_wo_scheme = vm_url.replace('https://', '').rstrip('/')

                # If it's empty or just `.rahkaran.ir`, fall back to default
                if url_wo_scheme in ['', '.rahkaran.ir']:
                    vm_url = default_url
                elif not url_wo_scheme.endswith('.rahkaran.ir'):
                    vm_url = f'https://{url_wo_scheme}.rahkaran.ir'

                # Get NIC connection status
                vm_nic_status = ''
                for device in vm.config.hardware.device:
                    if isinstance(device, vim.vm.device.VirtualEthernetCard):
                        # VM NIC Status
                        nic_connected = device.connectable.connected
                        vm_nic_status = "connected" if nic_connected else "disconnected"

                #  Distinguishing VMs
                vcenter_vra_vms[vm_name] = [vm_name, vm_url, vm_note, vm_fqdn, vm_power]

                if vm_power.endswith('off') or vm_nic_status == 'disconnected':
                    vcenter_poff_vms[vm_name] = [vm_name, vm_url, vm_note, vm_fqdn, vm_power]
                elif vm_power.endswith('on') and vm_nic_status == 'connected':
                    vcenter_pon_vms[vm_name] = [vm_name, vm_url, vm_note, vm_fqdn, vm_power]

        Disconnect(vra_vc)

        #  Gathering Data from Zabbix
        zabbix_user = username.split('@')[0]

        zabbix_servers = [
            ['http://172.17.234.23', 'me-customerzabbix@abramad.com'],
            # ['http://172.17.234.13/zabbix', 'me-zabbix@abramad.com'],
            # ['http://zab.abramad.com/zabbix', 'zab-zabbix@abramad.com'],

        ]

        for zserver in zabbix_servers:

            print(f'\nStarting: {zserver[1]}')
            # Connect to Zabbix API
            zapi = ZabbixAPI(zserver[0])
            zapi.login(zabbix_user, password)

            # Get all hosts
            hosts = zapi.host.get(
                output=["hostid", "host", "status"]
            )

            zabbix_vra_vms = {}
            zabbix_pon_vms = {}
            zabbix_poff_vms = {}

            for host in hosts:
                hostid = host['hostid']
                hostname = host['host']
                status = host['status']

                # Get macros for this host
                macros = zapi.usermacro.get(hostids=hostid, output=['macro', 'value'])
                host_url_macro = None
                for m in macros:
                    if m['macro'] == '{$HOST.URL}':
                        host_url_macro = m['value']
                        break

                # Create a value structure including the macro
                host_info = [hostname, hostid, status, host_url_macro]

                # Categorize based on naming and status
                if hostname.startswith('vra-') or hostname.startswith('vps-'):
                    zabbix_vra_vms[hostname] = host_info

                if ((hostname.startswith('vra-') or hostname.startswith('vps-')) and status == '1'):
                    zabbix_poff_vms[hostname] = host_info

                elif ((hostname.startswith('vra-') or hostname.startswith('vps-')) and status == '0'):
                    zabbix_pon_vms[hostname] = host_info

            #  Taking Group and Template IDs(host['host'].startswith('vra-') and host['status'] == '0')
            # Template and Host Group
            template_name = "Rahkaran-Abri-Tpl"  # Template name
            host_group_name1 = "Rahkaran-Abri-Grp"  # Host group name
            host_group_name2 = "Support_Team"  # Host group name
            host_group_name3 = "Rahkaran-Abri-Different_URL"

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

            # Get or create the group "Rahkaran-Abri-Different_URL"
            host_group3 = zapi.hostgroup.get(filter={"name": host_group_name3})
            if host_group3:
                different_url_group_id = host_group3[0]['groupid']
            else:
                group_create = zapi.hostgroup.create(name=host_group_name3)
                different_url_group_id = group_create['groupids'][0]

            #  Calculation Part
            # keys_equal = set(zabbix_pon_vms.keys()) == set(vcenter_pon_vms.keys())
            zabbix_nodes_added = []
            zabbix_nodes_enabled = []
            zabbix_nodes_disabled = []
            zabbix_nodes_deleted = []
            zabbix_nodes_updated = []

            #  Comparison

            #  Zabbix Node Update
            for zb_node in set(zabbix_vra_vms.keys()):
                if zb_node in vcenter_vra_vms:
                    try:
                        zb_host_info = zabbix_vra_vms[zb_node]
                        zb_hostid = zb_host_info[1]
                        zb_macro_url = zb_host_info[3]

                        vc_vm_url = vcenter_vra_vms[zb_node][1]  # URL from vCenter

                        if zb_macro_url != vc_vm_url:
                            print(f"{zb_host_info[0]}:\n\tOld URL: {zb_macro_url}\n\tNew URL: {vc_vm_url}")
                            print(f"[UPDATE] {zb_node} – Zabbix macro: {zb_macro_url} | vCenter: {vc_vm_url}")

                            # 1. Update Macro
                            # Get macroid to update (only if it already exists)
                            macro_info = zapi.usermacro.get(
                                hostids=zb_hostid,
                                filter={"macro": "{$HOST.URL}"},
                                output=["hostmacroid", "macro", "value"]
                            )
                            if macro_info and 'hostmacroid' in macro_info[0]:
                                zapi.usermacro.update(
                                    hostmacroid=macro_info[0]['hostmacroid'],
                                    value=vc_vm_url
                                )
                            else:
                                # create if absent
                                zapi.usermacro.create(
                                    hostid=zb_hostid,
                                    macro="{$HOST.URL}",
                                    value=vc_vm_url
                                )

                            # 2. Update Host Tag "Ext URL"
                            zapi.host.update(
                                hostid=zb_hostid,
                                tags=[{
                                    "tag": "Ext URL",
                                    "value": vc_vm_url
                                }]
                            )

                            # 3. Update Host Group
                            # Get current groups of the host
                            host_info = zapi.host.get(hostids=zb_hostid, output=["hostid"], selectGroups=["groupid"])
                            current_group_ids = [g['groupid'] for g in host_info[0]['groups']]

                            # If not already in the group, add it
                            if different_url_group_id not in current_group_ids:
                                updated_group_ids = current_group_ids + [different_url_group_id]
                                zapi.host.update(
                                    hostid=zb_hostid,
                                    groups=[{"groupid": gid} for gid in updated_group_ids]
                                )

                            zabbix_nodes_updated.append(zb_node)


                    except Exception as node_error:
                        print(f"Error Updating node '{zb_node}': {node_error}")
                        print(f"Exception type: {type(node_error).__name__}")
                        traceback.print_exc()
                        send_anonymous_email(zserver[1], error_receivers, default_cc,
                                             f"Error updating node '{zb_node}' | Zabbix_VRA_Fully_Automated.py",
                                             f"Error updating node:<br><b>{zb_node}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b> Agent: Zabbix_VRA_Fully_Automated.py",
                                             'ltr')

                        print(f"Script failed: {node_error}")
                        success = False
                        error_string_summary += f" {type(node_error).__name__}: {node_error}"

                        # Get the traceback and extract the last traceback frame
                        tb = traceback.extract_tb(node_error.__traceback__)
                        last_call = tb[-1]  # the last traceback frame, where the exception occurred
                        error_string_detail += f" Error 'deleting node' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"

                        continue

            #  Zabbix Node Deletion
            for zb_vra_node in set(zabbix_vra_vms.keys()):
                if zb_vra_node not in set(vcenter_vra_vms.keys()):  # Node Needs to be deleted
                    try:
                        # Host information
                        host_name = zabbix_vra_vms[zb_vra_node][0]
                        host_id = zabbix_vra_vms[zb_vra_node][1]
                        # Delete the host
                        zapi.host.delete(host_id)
                        print(f"Deleted host: {host_name}")
                        zabbix_nodes_deleted.append(host_name)

                    except Exception as node_error:
                        print(f"Error Deleting node '{zb_vra_node}': {node_error}")
                        print(f"Exception type: {type(node_error).__name__}")
                        traceback.print_exc()
                        send_anonymous_email(zserver[1], error_receivers, default_cc,
                                             f"Error deleting node '{zb_vra_node}' | Zabbix_VRA_Fully_Automated.py",
                                             f"Error deleting node:<br><b>{zb_vra_node}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b> Agent: Zabbix_VRA_Fully_Automated.py",
                                             'ltr')

                        print(f"Script failed: {node_error}")
                        success = False
                        error_string_summary += f" {type(node_error).__name__}: {node_error}"

                        # Get the traceback and extract the last traceback frame
                        tb = traceback.extract_tb(node_error.__traceback__)
                        last_call = tb[-1]  # the last traceback frame, where the exception occurred
                        error_string_detail += f" Error 'deleting node' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"

                        continue

            #  Zabbix Node Addition
            for vc_pon in set(vcenter_pon_vms.keys()):
                # print(vcenter_pon_vms[vc_pon][0])
                if vc_pon not in set(zabbix_pon_vms.keys()) and vc_pon not in set(
                        zabbix_poff_vms.keys()):  # Node needs to be added to zabbix
                    try:
                        # print(vcenter_pon_vms[vc_pon][0])
                        # print('\n')
                        # Host information  [vm_name, vm_url, vm_note, vm_fqdn, vm_power]
                        host_name = vcenter_pon_vms[vc_pon][0]  # {HOST.HOST}
                        host_visible_name = vcenter_pon_vms[vc_pon][0]  # {HOST.NAME}
                        host_desc = vcenter_pon_vms[vc_pon][2]  # Host Description
                        host_url = vcenter_pon_vms[vc_pon][1]  # Host URL
                        host_fqdn = vcenter_pon_vms[vc_pon][3]
                        tags = [
                            {"tag": "Note", "value": ""},
                            {"tag": "Owner", "value": "Support_Team"},
                            {"tag": "Ext URL", "value": f"{host_url}"},
                            {"tag": "Int URL", "value": f"http://{host_fqdn}"},
                            {"tag": "__zbx_jira", "value": "1"}
                        ]
                        macros = [
                            {"macro": "{$HOST.URL}", "value": f"{host_url}"}
                        ]

                        # Step 3: Create the new host with description and visible name
                        new_pon_host = zapi.host.create({
                            "host": host_name,  # Technical name of the host (internal name)
                            "name": host_visible_name,  # Visible name of the host in the frontend
                            "description": host_desc,  # Host description
                            "groups": [{"groupid": host_group_id1}, {"groupid": host_group_id2}],  # Host group
                            "templates": [{"templateid": template_id}],  # Template
                            "tags": tags,
                            "macros": macros
                        })

                        host_id = new_pon_host['hostids'][0]
                        print(f"Host '{host_name}' created with ID {host_id}")
                        zabbix_nodes_added.append(host_name)

                    except Exception as node_error:
                        print(f"Error adding node '{vc_pon}': {node_error}")
                        print(f"Exception type: {type(node_error).__name__}")
                        traceback.print_exc()
                        send_anonymous_email(zserver[1], error_receivers, default_cc,
                                             f"Error adding node '{vc_pon}' | Zabbix_VRA_Fully_Automated.py",
                                             f"Error adding node:<br><b>{vc_pon}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b> Agent: Zabbix_VRA_Fully_Automated.py",
                                             'ltr')

                        print(f"Script failed: {node_error}")
                        success = False
                        error_string_summary += f" {type(node_error).__name__}: {node_error}"

                        # Get the traceback and extract the last traceback frame
                        tb = traceback.extract_tb(node_error.__traceback__)
                        last_call = tb[-1]  # the last traceback frame, where the exception occurred
                        error_string_detail += f" Error 'adding node' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"

                        continue  # Continue to the next node even if an error occurs

                # Zabbix Node Enabling
                elif vc_pon in set(zabbix_poff_vms.keys()):
                    try:
                        # Host information
                        host_name = zabbix_poff_vms[vc_pon][0]
                        host_id = zabbix_poff_vms[vc_pon][1]
                        # Disable the host
                        zapi.host.update({
                            "hostid": host_id,
                            "status": 0  # Set status to 0 to enable the host
                        })
                        print(f"Enabled host: {host_name}")
                        zabbix_nodes_enabled.append(host_name)

                    except Exception as node_error:
                        print(f"Error enabling node '{vc_pon}': {node_error}")
                        print(f"Exception type: {type(node_error).__name__}")
                        traceback.print_exc()
                        send_anonymous_email(zserver[1], error_receivers, default_cc,
                                             f"Error enabling node '{vc_pon}' | Zabbix_VRA_Fully_Automated.py",
                                             f"Error enabling node:<br><b>{vc_pon}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b> Agent: Zabbix_VRA_Fully_Automated.py",
                                             'ltr')

                        print(f"Script failed: {node_error}")
                        success = False
                        error_string_summary += f" {type(node_error).__name__}: {node_error}"

                        # Get the traceback and extract the last traceback frame
                        tb = traceback.extract_tb(node_error.__traceback__)
                        last_call = tb[-1]  # the last traceback frame, where the exception occurred
                        error_string_detail += f" Error 'enabling node' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"

                        continue

            #  Zabbix Node Disabling
            for vc_poff in set(vcenter_poff_vms.keys()):
                if vc_poff in set(zabbix_pon_vms.keys()):  # Node Needs to be disabled
                    try:
                        # Host information
                        host_name = zabbix_pon_vms[vc_poff][0]
                        host_id = zabbix_pon_vms[vc_poff][1]
                        # Disable the host
                        zapi.host.update({
                            "hostid": host_id,
                            "status": 1  # Set status to 1 to disable the host
                        })
                        print(f"Disabled host: {host_name}")
                        zabbix_nodes_disabled.append(host_name)

                    except Exception as node_error:
                        print(f"Error disabling node '{vc_poff}': {node_error}")
                        print(f"Exception type: {type(node_error).__name__}")
                        traceback.print_exc()
                        send_anonymous_email(zserver[1], error_receivers, default_cc,
                                             f"Error disabling node '{vc_poff}' | Zabbix_VRA_Fully_Automated.py",
                                             f"Error disabling node:<br><b>{vc_poff}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b> Agent: Zabbix_VRA_Fully_Automated.py",
                                             'ltr')

                        print(f"Script failed: {node_error}")
                        success = False
                        error_string_summary += f" {type(node_error).__name__}: {node_error}"

                        # Get the traceback and extract the last traceback frame
                        tb = traceback.extract_tb(node_error.__traceback__)
                        last_call = tb[-1]  # the last traceback frame, where the exception occurred
                        error_string_detail += f" Error 'disabling node' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"

                        continue

            #  Email Part
            if len(zabbix_nodes_added) > 0:
                temp = ''
                for i in zabbix_nodes_added:
                    temp += f'{i}<br>'
                send_anonymous_email(zserver[1], default_receivers, default_cc,
                                     f"{len(zabbix_nodes_added)} nodes added to {zserver[1].split('@')[0]}",
                                     f"Below nodes were added to {zserver[1].split('@')[0]} automatically:<br><br><b>{temp}</b> Agent: Zabbix_VRA_Fully_Automated.py",
                                     'ltr')

            if len(zabbix_nodes_enabled) > 0:
                temp = ''
                for i in zabbix_nodes_enabled:
                    temp += f'{i}<br>'
                send_anonymous_email(zserver[1], default_receivers, default_cc,
                                     f"{len(zabbix_nodes_enabled)} nodes got enabled in {zserver[1].split('@')[0]}",
                                     f"Below nodes were enabled again in {zserver[1].split('@')[0]} automatically:<br><br><b>{temp}</b> Agent: Zabbix_VRA_Fully_Automated.py",
                                     'ltr')

            if len(zabbix_nodes_disabled) > 0:
                temp = ''
                for i in zabbix_nodes_disabled:
                    temp += f'{i}<br>'
                send_anonymous_email(zserver[1], default_receivers, default_cc,
                                     f"{len(zabbix_nodes_disabled)} nodes got disabled in {zserver[1].split('@')[0]}",
                                     f"Below nodes were disabled in {zserver[1].split('@')[0]} automatically:<br><br><b>{temp}</b> Agent: Zabbix_VRA_Fully_Automated.py",
                                     'ltr')

            if len(zabbix_nodes_deleted) > 0:
                temp = ''
                for i in zabbix_nodes_deleted:
                    temp += f'{i}<br>'
                send_anonymous_email(zserver[1], default_receivers, default_cc,
                                     f"{len(zabbix_nodes_deleted)} nodes got deleted from {zserver[1].split('@')[0]}",
                                     f"Below nodes were deleted from {zserver[1].split('@')[0]} automatically:<br><br><b>{temp}</b> Agent: Zabbix_VRA_Fully_Automated.py",
                                     'ltr')

            if len(zabbix_nodes_updated) > 0:
                temp = ''
                for i in zabbix_nodes_updated:
                    temp += f'{i}<br>'
                send_anonymous_email(zserver[1], default_receivers, default_cc,
                                     f"{len(zabbix_nodes_updated)} nodes got updated from {zserver[1].split('@')[0]}",
                                     f"Below nodes were zabbix_nodes_updated from {zserver[1].split('@')[0]} automatically:<br><br><b>{temp}</b> Agent: Zabbix_VRA_Fully_Automated.py",
                                     'ltr')

            # Logout from the Zabbix API session
            zapi.user.logout()
            print('\nScript ended gracefully. ✅')

            print(f'Done: {zserver[1]}')


    except Exception as body_error:
        print(f"Body Error: {body_error}")
        print(f"Exception type: {type(body_error).__name__}")
        traceback.print_exc()
        send_anonymous_email(from_email, error_receivers, default_cc,
                             f"Body Error in running Zabbix_VRA_Fully_Automated.py",
                             f"Error Occurred:<br><b>{body_error}<br>{traceback.print_exc()}<br>Exception type: {type(body_error).__name__}</b> Agent: Zabbix_VRA_Fully_Automated.py",
                             'ltr')

        print(f"Script failed: {body_error}")
        success = False
        error_string_summary += f" {type(body_error).__name__}: {body_error}"

        # Get the traceback and extract the last traceback frame
        tb = traceback.extract_tb(body_error.__traceback__)
        last_call = tb[-1]  # the last traceback frame, where the exception occurred
        error_string_detail += f" Error occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"




except Exception as err:
    print(f"Script failed: {err}")
    success = False
    error_string_summary += f" {type(err).__name__}: {err}"

    # Get the traceback and extract the last traceback frame
    tb = traceback.extract_tb(err.__traceback__)
    last_call = tb[-1]  # the last traceback frame, where the exception occurred
    error_string_detail += f" Error occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"



finally:
    # Finalizing Metrics
    # Script Duration
    duration = time.time() - start_time
    duration_gauge.set(duration)

    # Script Success Status
    status_gauge.set(1 if success else 0)

    # Script Total Executions
    total_exec_counts = read_value_from_file(total_exec_counter_file) + 1
    write_value_to_file(total_exec_counter_file, total_exec_counts)
    total_execution_counter.inc(total_exec_counts)

    if not success:
        # Script Total Failed Executions
        total_failed_exec_counts = read_value_from_file(total_failed_exec_counter_file) + 1
        write_value_to_file(total_failed_exec_counter_file, total_failed_exec_counts)
        total_failed_execution_counter.inc(total_failed_exec_counts)

        # Script Last Error Message
        last_error_message.labels(error_summary=error_string_summary, error_detail=error_string_detail).set(1)

    elif success:
        # Script Total Failed Executions
        total_failed_exec_counts = read_value_from_file(total_failed_exec_counter_file)
        total_failed_execution_counter.inc(total_failed_exec_counts)

        # Script Last Error Message
        last_error_message.labels(error_summary="None", error_detail="None").set(0)

    # Push metrics to Pushgateway
    push_to_gateway(
        gateway=pushgateway_url,
        job=job_name,
        grouping_key={'instance': instance, 'target': target, 'datacenter': datacenter},
        registry=registry
    )

    print('✅ Metrics Sent.')



