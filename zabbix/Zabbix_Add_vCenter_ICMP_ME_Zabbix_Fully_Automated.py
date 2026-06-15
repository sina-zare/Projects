# Module Imports
import sys
from email.mime.multipart import MIMEMultipart
from cryptography.fernet import Fernet
from pyVim.connect import Disconnect
from email.mime.text import MIMEText
from email.header import Header
from pyzabbix import ZabbixAPI
from pyVim import connect
from pyVmomi import vim
import traceback
import warnings
import smtplib
import ssl
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter
import traceback
import random
import time
import os

# --- Configuration ---
script_name = 'zabbix_add_vcenter_icmp_me_zabbix_fully_automated'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'http://me-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
datacenter = 'miremad'
target = 'me-vc01_mgmt_vms'



# Create a registry for our custom metrics
registry = CollectorRegistry()

# Define metrics
duration_gauge = Gauge('script_exec_duration_seconds', 'Duration of my script', registry=registry)
status_gauge = Gauge('script_success', 'Whether script succeeded (1) or failed (0)', registry=registry)
total_execution_counter = Counter('script_total_execs', 'Total number of times the script has run', registry=registry)
total_failed_execution_counter = Counter('script_total_failed_execs', 'Total number of times the script has failed to finish gracefully', registry=registry)
last_error_message = Gauge('script_last_error_message','The last error message encountered during script execution',['error_summary', 'error_detail'], registry=registry)


# Simulate your script logic
start_time = time.time()
success = True
error_string_summary = ""
error_string_detail = ""

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

        #print(f"Decryped Text: {decrypted_password}")
        return decrypted_password.decode()

    # ================================================================================ #

    zabbix_server = 'me-zabbix@abramad.com'
    error_receivers = 'abramadsysops@abramad.com, support@abramad.com'
    default_receivers = 'abramadsysops@abramad.com'
    #default_cc = 'sina.z@abramad.com'
    default_cc = 'sina.z@abramad.com'
    username = 'sysops-svc@abramad.com'
    password = decryptor('sysops-svc_enc', 'sysops-svc_key')

    # ================================================================================ #
    """
    def email_sender(username, password, email_receivers, email_cc, subject, direction, html_body, mail_server='mail.systemgroup.net'):
        try:
            # Create a multipart message object
            msg = MIMEMultipart()
            msg['From'] = 'zabbix@abramad.com'
            msg['To'] = email_receivers
            msg['CC'] = email_cc
            msg['Subject'] = subject
    
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
                                    <p  style="font-family: DiodrumArabic-Regular">{html_body}</p>
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
            msg.attach(MIMEText(email_body, 'html'))
    
            # Connect to the SMTP server and send the email on 587 TCP
            smtp_server = mail_server
            smtp_port = 587
    
            # Send email function
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.sendmail(username, email_receivers.split(",") + email_cc.split(','), msg.as_string())
    
        except Exception as err:
            print(f"email_sender Function Error: {err}")
            traceback.print_exc()
            email_sender(username, password, default_receivers, default_cc,
                         f"email_sender Function Error in running {script_name}.py", "ltr",
                         f"Error Occurred:<br><b>{err}<br>{traceback.print_exc()}</b> Agent: {script_name}.py")
    
    """

    def send_anonymous_email(from_email, to_email, cc_email, subject, html_message, direction, mail_server='mail.abramad.com'):
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
            send_anonymous_email(zabbix_server, error_receivers, default_cc, f"email_sender Function Error in running {script_name}.py",
                                 f"Error Occurred:<br><b>{err}<br>{traceback.print_exc()}<br>Exception type: {type(err).__name__}</b> Agent: {script_name}.py", 'ltr')

            print(f"Script failed: {err}")
            success = False
            error_string_summary += f" {type(err).__name__}: {err}"

            # Get the traceback and extract the last traceback frame
            tb = traceback.extract_tb(err.__traceback__)
            last_call = tb[-1]  # the last traceback frame, where the exception occurred
            error_string_detail += f" Error 'email_sender' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"


    def zabbix_node_adder(hosts_dict, template_list, host_group_list, tag_list):

        try:
            global success
            global error_string_summary
            global error_string_detail

            #  host_dict involves key values, that the values are a list consisting of 3 indexes ['Host Name', 'IP Address', 'Description']
            template_ids = {}
            host_group_ids = {}

            # Connect to Zabbix API
            #zapi = ZabbixAPI(url)
            #zapi.login(username, password)

            # Step 1: Get the Template ID
            for template_name in template_list:
                template = zapi.template.get(filter={"host": template_name})
                if not template:
                    raise Exception(f"Template '{template_name}' not found.")
                template_ids[template_name] = template[0]["templateid"]
            # Create the "groups" list dynamically
            templates = [{"templateid": tpl_id} for tpl_id in template_ids.values()]
            # Create the final config
            templates_config = {"templates": templates}


            # Step 2: Get the Host Group ID
            for host_group_name in host_group_list:
                host_group = zapi.hostgroup.get(filter={"name": host_group_name})
                if not host_group:
                    raise Exception(f"Host group '{host_group_name}' not found.")
                host_group_ids[host_group_name] = host_group[0]["groupid"]
            # Create the "groups" list dynamically
            hgroups = [{"groupid": group_id} for group_id in host_group_ids.values()]
            # Create the final config
            hgroups_config = {"groups": hgroups}


            # Step 3: Create the new host with description and visible name

            try:

                # Host information
                host_name = hosts_dict[0]  # {HOST.HOST}
                #host_fqdn = hosts_dict[host][0].strip()
                host_visible_name = hosts_dict[0]  # {HOST.NAME}
                host_ip = hosts_dict[1].strip()
                host_desc = f"{hosts_dict[2]}"  # Host Description

                new_host = zapi.host.create({
                    "host": host_name,
                    "name": host_visible_name,
                    "description": host_desc,
                    "groups": hgroups_config["groups"],
                    "templates": templates_config["templates"],
                    "tags": tag_list,
                    "interfaces": [{
                        "type": 1,  # Type 2 = SNMP
                        "main": 1,  # Mark this as the main interface
                        "useip": 1,  # Use IP address for connection
                        "ip": host_ip,
                        "dns": "",
                        "port": "10050"
                    }]
                })


                print(f"Host '{host_name}' created with ID {new_host['hostids'][0]}")
                print('#############\n')
                return True

            except Exception as loop_err:
                print(f"Error adding host '{host_name}': {loop_err}")
                print(f"Exception type: {type(loop_err).__name__}")
                send_anonymous_email(zabbix_server, error_receivers, default_cc,
                                     f"zabbix_node_adder Function Error in running {script_name}.py",
                                     f"Error Occurred:<br><b>{loop_err}<br>{traceback.print_exc()}<br>Exception type: {type(loop_err).__name__}</b> Agent: {script_name}.py",
                                     'ltr')

                print(f"Script failed: {loop_err}")
                success = False
                error_string_summary += f" {type(loop_err).__name__}: {loop_err}"

                # Get the traceback and extract the last traceback frame
                tb = traceback.extract_tb(loop_err.__traceback__)
                last_call = tb[-1]  # the last traceback frame, where the exception occurred
                error_string_detail += f" Error 'zabbix_node_adder' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"

        except Exception as err:
            print(f"zabbix_node_adder Function Error: {err}")
            print(f"Exception type: {type(err).__name__}")
            traceback.print_exc()
            send_anonymous_email(zabbix_server, error_receivers, default_cc,
                                 f"zabbix_node_adder Function Error in running {script_name}.py",
                                 f"Error Occurred:<br><b>{err}<br>{traceback.print_exc()}<br>Exception type: {type(err).__name__}</b> Agent: {script_name}.py",
                                 'ltr')

            print(f"Script failed: {err}")
            success = False
            error_string_summary += f" {type(err).__name__}: {err}"

            # Get the traceback and extract the last traceback frame
            tb = traceback.extract_tb(err.__traceback__)
            last_call = tb[-1]  # the last traceback frame, where the exception occurred
            error_string_detail += f" Error 'zabbix_node_adder' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"


    #username = "sina.z@abramad.com"
    #password = decryptor("enc_sinaz_pass","key_sinaz_pass")

    try:

        # Ignore the warning
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # *** Connecting to ME-VC01.Abramad.Com to get the Report ***
        # Create an SSL context with no certificate verification
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.verify_mode = ssl.CERT_NONE

        # Connecting to vCenter
        vc = connect.SmartConnect(host='me-vc01.abramad.com',user= username,pwd= password,port=443,sslContext=context)
        vc_content = vc.RetrieveContent()
        vc_vm_view = vc_content.viewManager.CreateContainerView(vc_content.rootFolder, [vim.VirtualMachine], True)
        prefixes = ("me-")
        trash_prefixes = ["template", "malekzade", "vc01", "me-bckcustomer"]

        vms = [
            vm for vm in vc_vm_view.view
            if vm.name.lower().startswith(prefixes)
               and not any(trash in vm.name.lower() for trash in trash_prefixes)
        ]

        sorted_vms = sorted(vms, key=lambda vm: vm.name)


        sorted_vms_narrow = []

        vcenter_pon_vms = {}
        vcenter_poff_vms = {}
        vcenter_me_vms = {}

        for vm in sorted_vms:

            try:
                # VM Name
                vm_name = vm.name

                #VM Power State
                vm_power_state = vm.runtime.powerState.lower()

                # Get NIC connection status
                vm_nic_status = ''
                for device in vm.config.hardware.device:
                    if isinstance(device, vim.vm.device.VirtualEthernetCard):
                        # VM NIC Status
                        nic_connected = device.connectable.connected
                        vm_nic_status = "connected" if nic_connected else "disconnected"

                # retrieve vm IP address
                vm_ip = "0.0.0.0"
                if vm.guest is not None:
                    for nic in vm.guest.net:
                        if nic.ipConfig is not None:
                            for ip in nic.ipConfig.ipAddress:
                                if ip.ipAddress.startswith('172.17') or ip.ipAddress.startswith('172.21'):
                                    vm_ip = ip.ipAddress

                # Get VM Persian Name
                vm_persian_name = "No Persian Name Specified."
                custom_value_n = vm.summary.customValue
                for i in custom_value_n:
                    if i.key == 103:
                        vm_persian_name = i.value


                #  Distinguishing VMs
                vcenter_me_vms[vm_name.lower()] = [vm_name, vm_ip, vm_persian_name]

                if vm_power_state.endswith('off') or vm_nic_status == 'disconnected':
                    vcenter_poff_vms[vm_name.lower()] = [vm_name, vm_ip, vm_persian_name]
                elif vm_power_state.endswith('on') and vm_nic_status == 'connected':
                    vcenter_pon_vms[vm_name.lower()] = [vm_name, vm_ip, vm_persian_name]

            except Exception as err:
                print(vm_name)

                send_anonymous_email(zabbix_server, error_receivers, default_cc,
                                     f"Error on node '{vm_name}' | {script_name}.py",
                                     f"Error on node:<br><b>{vm_name}: {err} {traceback.print_exc()}<br>Exception type: {type(err).__name__}</b> Agent: {script_name}.py",
                                     'ltr')

                print(f"Script failed: {err}")
                success = False
                error_string_summary += f" {type(err).__name__}: {err}"

                # Get the traceback and extract the last traceback frame
                tb = traceback.extract_tb(err.__traceback__)
                last_call = tb[-1]  # the last traceback frame, where the exception occurred
                error_string_detail += f" Error on {vm_name} occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"

                continue  # Continue to the next node even if an error occurs

        Disconnect(vc)


        #  Gathering Data from Zabbix

        # Zabbix server credentials
        zabbix_url = "http://172.17.234.13/zabbix"
        zabbix_user = username.split('@')[0]
        zabbix_password = password

        # Connect to Zabbix API
        zapi = ZabbixAPI(zabbix_url)
        zapi.login(zabbix_user, zabbix_password)


        # Get group IDs for "Management_ICMP" and "ME_OnPrem_ICMP"
        hostgroups = zapi.hostgroup.get(
            filter={"name": ["Management_ICMP", "ME_OnPrem_ICMP"]},  # Filter by host group names
            output=["groupid"]
        )

        # Extract group IDs
        group_ids = [group['groupid'] for group in hostgroups]

        # Get hosts in the specified host groups
        hosts = zapi.host.get(
            groupids=group_ids,          # Filter by group IDs
            output=["hostid", "host", "status"]
        )

        # Getting hosts placed in Zabbix Active Linux or Windows Templates
        zabbix_active_agent_template_names = ["Linux by Zabbix agent active", "Windows by Zabbix agent active", "Windows by Zabbix agent active Managed_Services_Team", "Windows by Zabbix agent active CSB_Backup_Team_MA", "Windows by Zabbix agent active CSB_Backup_Team_BCK"]

        # Fetch zabbix_active_templates to get their IDs
        zabbix_active_templates = zapi.template.get(
            filter={"host": zabbix_active_agent_template_names},
            output=["templateid", "name"]
        )

        zabbix_active_template_ids = [template["templateid"] for template in zabbix_active_templates]

        # Fetch hosts linked to the templates
        zabbix_active_template_hosts = zapi.host.get(
            templateids=zabbix_active_template_ids,
            output=["hostid", "host", "status"],  # Host ID, name, and status
            selectParentTemplates=["name"]  # To confirm linked templates if needed
        )

        zabbix_active_linwin_template_vms = {}
        zabbix_me_vms = {}
        zabbix_enabled_vms = {}
        zabbix_disabled_vms = {}
        zabbix_icmp_vms = {}

        # Taking Zabbix Active Template Hosts
        for zahost in zabbix_active_template_hosts:
            zabbix_active_linwin_template_vms[zahost['host'].lower()] = [zahost['host'].lower(), zahost['hostid'], zahost['status']]


        #  Distinguishing hosts
        for host in hosts:
            zabbix_icmp_vms[host['host'].lower()] = [host['host'].lower(), host['hostid'], host['status']]
            if host['host'].lower().startswith('me'):
                zabbix_me_vms[host['host'].lower()] = [host['host'].lower(), host['hostid'], host['status']]
            if host['host'].lower().startswith('me') and host['status'] == '1':
                zabbix_disabled_vms[host['host'].lower()] = [host['host'].lower(), host['hostid'], host['status']]
            elif host['host'].lower().startswith('me') and host['status'] == '0':
                zabbix_enabled_vms[host['host'].lower()] = [host['host'].lower(), host['hostid'], host['status']]



        #  Calculation Part
        # keys_equal = set(zabbix_pon_vms.keys()) == set(vcenter_pon_vms.keys())
        zabbix_nodes_added = []
        zabbix_nodes_enabled = []
        zabbix_nodes_disabled = []
        zabbix_nodes_deleted = []

        zabbix_templates = ["ICMP Ping IP"]

        me_onprem_zabbix_tags = [
            {"tag": "Note", "value": ""},
            {"tag": "Owner", "value": "Support_Team"},
            {"tag": "__zbx_jira", "value": "1"}
        ]
        me_mgmt_zabbix_tags = [
            {"tag": "Note", "value": ""},
            {"tag": "Owner", "value": "Management"},
            {"tag": "__zbx_jira", "value": "1"}
        ]

        mer_zabbix_host_groups = ["MER", "ME_OnPrem_ICMP"]
        mes_zabbix_host_groups = ["MES", "ME_OnPrem_ICMP"]
        mef_zabbix_host_groups = ["MEF", "ME_OnPrem_ICMP"]
        mea_zabbix_host_groups = ["MEA", "ME_OnPrem_ICMP"]
        meb_zabbix_host_groups = ["MEB", "ME_OnPrem_ICMP"]
        mesa_zabbix_host_groups = ["MESA", "ME_OnPrem_ICMP"]
        mem_zabbix_host_groups = ["MEM", "ME_OnPrem_ICMP"]
        mei_zabbix_host_groups = ["MEI", "ME_OnPrem_ICMP"]
        me_mgmt_zabbix_host_groups = ["Management_ICMP"]


        #  Comparison Part

        #  Zabbix Node Deletion
        for icmp_node in zabbix_icmp_vms:
            if icmp_node in set(zabbix_active_linwin_template_vms.keys()):

                try:
                    # Host information
                    host_name = zabbix_me_vms[icmp_node][0]
                    host_id = zabbix_me_vms[icmp_node][1]
                    # Delete the host
                    zapi.host.delete(host_id)
                    print(f"Deleted host: {host_name}")
                    zabbix_nodes_deleted.append(host_name)

                except Exception as node_error:
                    print(f"Error Deleting node '{icmp_node}': {node_error}")
                    print(f"Exception type: {type(node_error).__name__}")
                    traceback.print_exc()
                    send_anonymous_email(zabbix_server, error_receivers, default_cc,
                                 f"Error deleting node '{icmp_node}' | {script_name}.py",
                                 f"Error deleting node:<br><b>{icmp_node}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b> Agent: {script_name}.py",
                                 'ltr')

                    print(f"Script failed: {node_error}")
                    success = False
                    error_string_summary += f" {type(node_error).__name__}: {node_error}"

                    # Get the traceback and extract the last traceback frame
                    tb = traceback.extract_tb(node_error.__traceback__)
                    last_call = tb[-1]  # the last traceback frame, where the exception occurred
                    error_string_detail += f" Error 'deleting node' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"

                    continue
        
        for zb_me_node in set(zabbix_me_vms.keys()):
            if zb_me_node not in set(vcenter_me_vms.keys()):  # Node Needs to be deleted
                try:
                    # Host information
                    host_name = zabbix_me_vms[zb_me_node][0]
                    host_id = zabbix_me_vms[zb_me_node][1]
                    # Delete the host
                    zapi.host.delete(host_id)
                    print(f"Deleted host: {host_name}")
                    zabbix_nodes_deleted.append(host_name)

                except Exception as node_error:
                    print(f"Error Deleting node '{zb_me_node}': {node_error}")
                    print(f"Exception type: {type(node_error).__name__}")
                    traceback.print_exc()
                    send_anonymous_email(zabbix_server, error_receivers, default_cc,
                                 f"Error deleting node '{zb_me_node}' | {script_name}.py",
                                 f"Error deleting node:<br><b>{zb_me_node}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b> Agent: {script_name}.py",
                                 'ltr')

                    print(f"Script failed: {node_error}")
                    success = False
                    error_string_summary += f" {type(node_error).__name__}: {node_error}"

                    # Get the traceback and extract the last traceback frame
                    tb = traceback.extract_tb(node_error.__traceback__)
                    last_call = tb[-1]  # the last traceback frame, where the exception occurred
                    error_string_detail += f" Error 'deleting node' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"

                    continue

        print(f'vCenter Power On:\n{set(vcenter_pon_vms.keys())}')
        print(f'vCenter Power Off:\n{set(vcenter_poff_vms.keys())}')
        print(f'Zabbix Enabled:\n{set(zabbix_enabled_vms.keys())}')
        print(f'Zabbix Disabled:\n{set(zabbix_disabled_vms.keys())}')
        print('\n\n')

        #sys.exit()
        #  Zabbix Node Addition
        for vc_pon in set(vcenter_pon_vms.keys()):
            if vc_pon not in set(zabbix_enabled_vms.keys()) and vc_pon not in set(zabbix_disabled_vms.keys()):  # Node needs to be added to zabbix
                try:
                    # Host information
                    host_name = vcenter_pon_vms[vc_pon][0]  # {HOST.HOST} VM Hostname not lower case
                    """
                    # MER and MERD
                    if host_name.lower().startswith('mer-') or host_name.lower().startswith('merd-'):
                        added_successfully = False
                        added_successfully = zabbix_node_adder(vcenter_pon_vms[vc_pon], zabbix_templates, mer_zabbix_host_groups, me_onprem_zabbix_tags)
                        if added_successfully:
                            zabbix_nodes_added.append(host_name)
                    # MES
                    elif host_name.lower().startswith('mes-'):
                        added_successfully = False
                        added_successfully = zabbix_node_adder(vcenter_pon_vms[vc_pon], zabbix_templates, mes_zabbix_host_groups, me_onprem_zabbix_tags)
                        if added_successfully:
                            zabbix_nodes_added.append(host_name)
                    # MEF
                    elif host_name.lower().startswith('mef-'):
                        added_successfully = False
                        added_successfully = zabbix_node_adder(vcenter_pon_vms[vc_pon], zabbix_templates, mef_zabbix_host_groups, me_onprem_zabbix_tags)
                        if added_successfully:
                            zabbix_nodes_added.append(host_name)
                    # MEA
                    elif host_name.lower().startswith('mea-'):
                        added_successfully = False
                        added_successfully = zabbix_node_adder(vcenter_pon_vms[vc_pon], zabbix_templates, mea_zabbix_host_groups, me_onprem_zabbix_tags)
                        if added_successfully:
                            zabbix_nodes_added.append(host_name)
                    # MEB
                    elif host_name.lower().startswith('meb-'):
                        added_successfully = False
                        added_successfully = zabbix_node_adder(vcenter_pon_vms[vc_pon], zabbix_templates, meb_zabbix_host_groups, me_onprem_zabbix_tags)
                        if added_successfully:
                            zabbix_nodes_added.append(host_name)
                    # MESA
                    elif host_name.lower().startswith('mesa-'):
                        added_successfully = False
                        added_successfully = zabbix_node_adder(vcenter_pon_vms[vc_pon], zabbix_templates, mesa_zabbix_host_groups, me_onprem_zabbix_tags)
                        if added_successfully:
                            zabbix_nodes_added.append(host_name)
                    # MEM
                    elif host_name.lower().startswith('mem-'):
                        added_successfully = False
                        added_successfully = zabbix_node_adder(vcenter_pon_vms[vc_pon], zabbix_templates, mem_zabbix_host_groups, me_onprem_zabbix_tags)
                        if added_successfully:
                            zabbix_nodes_added.append(host_name)
                    """
                    # MEI
                    if host_name.lower().startswith('mei-'):
                        added_successfully = False
                        added_successfully = zabbix_node_adder(vcenter_pon_vms[vc_pon], zabbix_templates, mei_zabbix_host_groups, me_onprem_zabbix_tags)
                        if added_successfully:
                            zabbix_nodes_added.append(host_name)
                    # ME_MGMT
                    elif host_name.lower().startswith('me'):

                        if host_name.lower() in set(zabbix_active_linwin_template_vms.keys()):
                            print(f'Skipping Node Creation: {host_name.lower()}')

                        elif host_name.lower().startswith('me-rahlock') or host_name.lower().startswith('me-seplock') or host_name.lower().startswith('me-buildlock'):
                            #zabbix_node_adder(vcenter_pon_vms[vc_pon], ["ICMP Ping IP", "Lock-Server-Tpl"], ["Management_ICMP", "Internal_Services", "Lock-Servers", "Support_Team"], [{"tag": "Note", "value": ""}, {"tag": "Owner", "value": "Support_Team"}, {"tag": "Internal_Service", "value": ""}])
                            #zabbix_nodes_added.append(host_name)
                            print(f'Skipping Node Creation: {host_name.lower()}')

                        else:
                            added_successfully = False
                            added_successfully = zabbix_node_adder(vcenter_pon_vms[vc_pon], zabbix_templates, me_mgmt_zabbix_host_groups, me_mgmt_zabbix_tags)
                            if added_successfully:
                                zabbix_nodes_added.append(host_name)



                except Exception as node_error:
                    print(f"Error adding node '{vc_pon}': {node_error}")
                    print(f"Exception type: {type(node_error).__name__}")
                    traceback.print_exc()
                    send_anonymous_email(zabbix_server, error_receivers, default_cc,
                                         f"Error adding node '{vc_pon}' | {script_name}.py",
                                         f"Error adding node:<br><b>{vc_pon}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b> Agent: {script_name}.py",
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
            elif vc_pon in set(zabbix_disabled_vms.keys()):
                try:
                    # Host information
                    host_name = zabbix_disabled_vms[vc_pon][0]
                    host_id = zabbix_disabled_vms[vc_pon][1]
                    # Enable the host
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
                    send_anonymous_email(zabbix_server, error_receivers, default_cc,
                                         f"Error enabling node '{vc_pon}' | {script_name}.py",
                                         f"Error enabling node:<br><b>{vc_pon}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b> Agent: {script_name}.py",
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
            if vc_poff in set(zabbix_enabled_vms.keys()):  # Node Needs to be disabled
                try:
                    # Host information
                    host_name = zabbix_enabled_vms[vc_poff][0]
                    host_id = zabbix_enabled_vms[vc_poff][1]
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
                    send_anonymous_email(zabbix_server, error_receivers, default_cc,
                                         f"Error disabling node '{vc_poff}' | {script_name}.py",
                                         f"Error disabling node:<br><b>{vc_poff}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b> Agent: {script_name}.py",
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
            send_anonymous_email(zabbix_server, default_receivers, default_cc,
                                 f"{len(zabbix_nodes_added)} vCenter ICMP nodes added to ME-Zabbix",
                                 f"Below ICMP nodes were added to ME-Zabbix automatically:<br><br><b>{temp}</b> Agent: {script_name}.py",
                                 'ltr')


        if len(zabbix_nodes_enabled) > 0:
            temp = ''
            for i in zabbix_nodes_enabled:
                temp += f'{i}<br>'
            send_anonymous_email(zabbix_server, default_receivers, default_cc,
                                 f"{len(zabbix_nodes_enabled)} vCenter ICMP nodes got enabled in ME-Zabbix",
                                 f"Below ICMP nodes were enabled again in ME-Zabbix automatically:<br><br><b>{temp}</b> Agent: {script_name}.py",
                                 'ltr')


        if len(zabbix_nodes_disabled) > 0:
            temp = ''
            for i in zabbix_nodes_disabled:
                temp += f'{i}<br>'
            send_anonymous_email(zabbix_server, default_receivers, default_cc,
                                 f"{len(zabbix_nodes_disabled)} vCenter ICMP nodes got disabled in ME-Zabbix",
                                 f"Below ICMP nodes were disabled in ME-Zabbix automatically:<br><br><b>{temp}</b> Agent: {script_name}.py",
                                 'ltr')


        if len(zabbix_nodes_deleted) > 0:
            temp = ''
            for i in zabbix_nodes_deleted:
                temp += f'{i}<br>'
            send_anonymous_email(zabbix_server, default_receivers, default_cc,
                                 f"{len(zabbix_nodes_deleted)} vCenter ICMP nodes got deleted from ME-Zabbix",
                                 f"Below ICMP nodes were deleted from ME-Zabbix automatically:<br><br><b>{temp}</b> Agent: {script_name}.py",
                                 'ltr')


        # Logout from the Zabbix API session
        zapi.user.logout()
        print('\nScript ended gracefully. ✅')


    except Exception as body_error:
        print(f"Body Error: {body_error}")
        print(f"Exception type: {type(body_error).__name__}")
        traceback.print_exc()
        send_anonymous_email(zabbix_server, error_receivers, default_cc,
                             f"Body Error in running {script_name}.py",
                             f"Error Occurred:<br><b>{body_error}<br>{traceback.print_exc()}<br>Exception type: {type(body_error).__name__}</b> Agent: {script_name}.py",
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

    #Script Success Status
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



