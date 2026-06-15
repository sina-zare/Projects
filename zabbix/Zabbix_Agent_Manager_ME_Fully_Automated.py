# Module Imports
from cryptography.fernet import Fernet
from pyvim.connect import Disconnect
from email.mime.text import MIMEText
from email.header import Header
from pyzabbix import ZabbixAPI
from pyvim import connect
from pyVmomi import vim
import traceback
import warnings
import smtplib
import ssl
import os
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter
import traceback
import time
import os

# --- Configuration ---
script_name = 'zabbix_agent_manager_me_fully_automated'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'http://me-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
datacenter = 'miremad'
target = 'me_onprem_customers'

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

    #default_receivers = 'sina.z@abramad.com'
    default_receivers = 'abramadsysops@abramad.com'
    error_receivers = 'support@abramad.com, abramadsysops@abramad.com'
    #default_cc = 'sina.z@abramad.com'
    default_cc = 'sina.z@abramad.com'
    username = 'sysops-svc@abramad.com'
    password = decryptor('sysops-svc_enc', 'sysops-svc_key')

    zabbix_servers = [

            {
                'zabbix_address': 'http://172.17.234.23/',
                #'vcenter_abri_address': 'vra-vc01.abramad.com',
                'vcenter_onprem_address': 'me-vc01.abramad.com',
                'from_address': 'me-customerzabbix@abramad.com'
            },


        ]


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
            '''send_anonymous_email(zabbix_server, error_receivers, default_cc,
                                 f"email_sender Function Error in running Zabbix_Add_vCenter_ICMP_Fully_Automated.py",
                                 f"Error Occurred:<br><b>{err}<br>{traceback.print_exc()}<br>Exception type: {type(err).__name__}</b> Agent: {script_name}.py",
                                 'ltr')'''

            print(f"Script failed: {err}")
            success = False
            error_string_summary += f" {type(err).__name__}: {err}"

            # Get the traceback and extract the last traceback frame
            tb = traceback.extract_tb(err.__traceback__)
            last_call = tb[-1]  # the last traceback frame, where the exception occurred
            error_string_detail += f" Error 'email_sender' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"


    try:

        for iteration in zabbix_servers:

            zabbix_address = iteration['zabbix_address']
            #vcenter_abri_address = iteration['vcenter_abri_address']
            vcenter_onprem_address = iteration['vcenter_onprem_address']
            from_address = iteration['from_address']
            #print(zabbix_address)
            #print(vcenter_abri_address)
            #print(vcenter_onprem_address)
            #print(from_address)

            # ======================= First vCenter =========================
            """
            print(f'\nStarting vCenter Part on: {vcenter_abri_address}')
            # Ignore the warning
            warnings.filterwarnings("ignore", category=DeprecationWarning)
    
            # *** Connecting to ME-VC01.Abramad.Com to get the Report ***
            # Create an SSL context with no certificate verification
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            context.verify_mode = ssl.CERT_NONE
    
            # Connecting to vCenter
            vc = connect.SmartConnect(host=vcenter_abri_address,user= username,pwd= password,port=443,sslContext=context)
            vc_content = vc.RetrieveContent()
            vc_vm_view = vc_content.viewManager.CreateContainerView(vc_content.rootFolder, [vim.VirtualMachine], True)
            vc_me_vms = [vm for vm in vc_vm_view.view if ( (vm.name.lower().startswith("vra-")) or (vm.name.lower().startswith("vrf-")) or (vm.name.lower().startswith("vrt-")) ) and ('template' not in vm.name.lower())]
            sorted_abri_vms = sorted(vc_me_vms, key=lambda vm: vm.name)
    
    
            vcenter_abri_pon_vms = {}
            vcenter_abri_poff_vms = {}
            vcenter_abri_vms = {}
    
            for vm in sorted_abri_vms[:]:
    
                for device in vm.config.hardware.device:
                    if isinstance(device, vim.vm.device.VirtualEthernetCard):
                        network = device.backing
                        if isinstance(network, vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo):
                            dvs_portgroup_key = network.port.portgroupKey
                            dvs_uuid = network.port.switchUuid
                            # Retrieve the Distributed Virtual Switch
                            dvs = vc_content.dvSwitchManager.QueryDvsByUuid(dvs_uuid)
                            # Find the port group by key
                            for portgroup in dvs.portgroup:
                                vm_portgroup = ''
                                if portgroup.key == dvs_portgroup_key:
                                    # VM PortGroup Name
                                    vm_portgroup = portgroup.name
                                    break
    
    
                if vm_portgroup.startswith('RA-Customers-N1003-VM'): #and vm.name.lower() != 'vra-amini2' and vm.name.lower() != 'vra-amini3' and vm.name.lower() != 'vra-demo' and vm.name.lower() != 'vra-bi1' and not vm.name.lower().startswith('vra-haproxy'):
    
                    # VM Name
                    vm_name = vm.name
    
                    # VM Power State
                    vm_power_state = vm.runtime.powerState.lower()
    
                    # Get NIC connection status
                    vm_nic_status = ''
                    for device in vm.config.hardware.device:
                        if isinstance(device, vim.vm.device.VirtualEthernetCard):
                            # VM NIC Status
                            nic_connected = device.connectable.connected
                            vm_nic_status = "connected" if nic_connected else "disconnected"
    
    
                    #  Distinguishing VMs
                    vcenter_abri_vms[vm_name.lower()] = [vm_name]
    
                    if vm_power_state.endswith('off') or vm_nic_status == 'disconnected':
                        vcenter_abri_poff_vms[vm_name.lower()] = [vm_name]
    
                    elif vm_power_state.endswith('on') and vm_nic_status == 'connected':
                        vcenter_abri_pon_vms[vm_name.lower()] = [vm_name]
    
            Disconnect(vc)
    
            """


            # ======================= Second vCenter =========================
            print(f'\nStarting vCenter Part on: {vcenter_onprem_address}')
            # Ignore the warning
            warnings.filterwarnings("ignore", category=DeprecationWarning)

            # *** Connecting to ME-VC01.Abramad.Com to get the Report ***
            # Create an SSL context with no certificate verification
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            context.verify_mode = ssl.CERT_NONE

            # Connecting to vCenter
            vc = connect.SmartConnect(host=vcenter_onprem_address, user=username, pwd=password, port=443, sslContext=context)
            vc_content = vc.RetrieveContent()
            vc_vm_view = vc_content.viewManager.CreateContainerView(vc_content.rootFolder, [vim.VirtualMachine], True)
            vc_me_vms = [vm for vm in vc_vm_view.view if (
                        (vm.name.lower().startswith("mer-")) or
                        (vm.name.lower().startswith("merd-")) or
                        (vm.name.lower().startswith("mes-")) or
                        (vm.name.lower().startswith("mea-")) or
                        (vm.name.lower().startswith("meb-")) or
                        (vm.name.lower().startswith("mef-")) or
                        (vm.name.lower().startswith("mem-"))
                        )
                        and ('template' not in vm.name.lower())
                        and (vm.name.lower() != 'mer-refahtp-a1')
                        and (vm.name.lower() != 'mer-refahtp-db')
                        ]

            sorted_onprem_vms = sorted(vc_me_vms, key=lambda vm: vm.name)

            vcenter_onprem_pon_vms = {}
            vcenter_onprem_poff_vms = {}
            vcenter_onprem_vms = {}

            for vm in sorted_onprem_vms[:]:


                # VM Name
                vm_name = vm.name
                print(f'VM Name: {vm_name}')

                # VM Power State
                vm_power_state = vm.runtime.powerState.lower()

                # vm Hostname
                vm_hostname = vm_name
                if vm.summary.guest.hostName:
                    vm_hostname = (vm.summary.guest.hostName).split('.')[0]
                    print(f'Hostname: {vm_hostname}\n')

                # Get NIC connection status
                vm_nic_status = ''
                for device in vm.config.hardware.device:
                    if isinstance(device, vim.vm.device.VirtualEthernetCard):
                        # VM NIC Status
                        nic_connected = device.connectable.connected
                        vm_nic_status = "connected" if nic_connected else "disconnected"

                #  Distinguishing VMs
                vcenter_onprem_vms[vm_hostname.lower()] = [vm_hostname]

                if vm_power_state.endswith('off') or vm_nic_status == 'disconnected':
                    vcenter_onprem_poff_vms[vm_hostname.lower()] = [vm_hostname]

                elif vm_power_state.endswith('on') and vm_nic_status == 'connected':
                    vcenter_onprem_pon_vms[vm_hostname.lower()] = [vm_hostname]

            Disconnect(vc)




            # ======================= First Zabbix =========================

            print(f'\nStarting Zabbix Part on: {zabbix_address}')
            # Zabbix server credentials
            zabbix_user = username.split('@')[0]
            zabbix_password = password

            # Connect to Zabbix API
            zapi = ZabbixAPI(zabbix_address)
            zapi.login(zabbix_user, zabbix_password)

            # Get all hosts
            hosts = zapi.host.get(
                output=["hostid", "host", "status"]
            )

            #zabbix_abri_vms = {}
            #zabbix_abri_pon_vms = {}
            #zabbix_abri_poff_vms = {}

            zabbix_onprem_vms = {}
            zabbix_onprem_pon_vms = {}
            zabbix_onprem_poff_vms = {}

            #  Distinguishing hosts
            for host in hosts:
                #if (host['host'].lower().startswith('vra-') or
                #    host['host'].lower().startswith('vrf-') or
                #    host['host'].lower().startswith('vrt-')):

                #    zabbix_abri_vms[host['host'].lower()] = [host['host'].lower(), host['hostid'], host['status']]

                #if ((host['host'].lower().startswith('vra-') and host['status'] == '1') or
                #    (host['host'].lower().startswith('vrf-') and host['status'] == '1') or
                #    (host['host'].lower().startswith('vrt-') and host['status'] == '1')):

                #    zabbix_abri_poff_vms[host['host'].lower()] = [host['host'].lower(), host['hostid'], host['status']]

                #if ((host['host'].lower().startswith('vra-') and host['status'] == '0') or
                #    (host['host'].lower().startswith('vrf-') and host['status'] == '0') or
                #    (host['host'].lower().startswith('vrt-') and host['status'] == '0')):

                #    zabbix_abri_pon_vms[host['host'].lower()] = [host['host'].lower(), host['hostid'], host['status']]

                if (host['host'].lower().startswith('mer-') or
                    host['host'].lower().startswith('merd-') or
                    host['host'].lower().startswith('mes-') or
                    host['host'].lower().startswith('mea-') or
                    host['host'].lower().startswith('meb-') or
                    host['host'].lower().startswith('mef-') or
                    host['host'].lower().startswith('mem-')
                    ):

                    zabbix_onprem_vms[host['host'].lower()] = [host['host'].lower(), host['hostid'], host['status']]

                if ((host['host'].lower().startswith('mer-') and host['status'] == '1') or
                    (host['host'].lower().startswith('merd-') and host['status'] == '1') or
                    (host['host'].lower().startswith('mes-') and host['status'] == '1') or
                    (host['host'].lower().startswith('mea-') and host['status'] == '1') or
                    (host['host'].lower().startswith('meb-') and host['status'] == '1') or
                    (host['host'].lower().startswith('mef-') and host['status'] == '1') or
                    (host['host'].lower().startswith('mem-') and host['status'] == '1')
                    ):

                    zabbix_onprem_poff_vms[host['host'].lower()] = [host['host'].lower(), host['hostid'], host['status']]

                if ((host['host'].lower().startswith('mer-') and host['status'] == '0') or
                    (host['host'].lower().startswith('merd-') and host['status'] == '0') or
                    (host['host'].lower().startswith('mes-') and host['status'] == '0') or
                    (host['host'].lower().startswith('mea-') and host['status'] == '0') or
                    (host['host'].lower().startswith('meb-') and host['status'] == '0') or
                    (host['host'].lower().startswith('mef-') and host['status'] == '0') or
                    (host['host'].lower().startswith('mem-') and host['status'] == '0') or
                    (host['host'].lower().startswith('vmi-') and host['status'] == '0')
                    ):

                    zabbix_onprem_pon_vms[host['host'].lower()] = [host['host'].lower(), host['hostid'], host['status']]

            print(f'\nData Gathered and Distinguished')

            #  Calculation Part
            # keys_equal = set(zabbix_pon_vms.keys()) == set(vcenter_pon_vms.keys())
            #zabbix_nodes_added = []
            zabbix_nodes_enabled = []
            zabbix_nodes_disabled = []
            zabbix_nodes_deleted = []


            #  Comparison

            #  Zabbix Node Deletion
            #print(f'\nZabbix Abri Node Deletion...')
            """
            for zb_abri_node in set(zabbix_abri_vms.keys()):
                if zb_abri_node not in set(vcenter_abri_vms.keys()):  # Node Needs to be deleted
                    try:
                        # Host information
                        host_name = zabbix_abri_vms[zb_abri_node][0]
                        host_id = zabbix_abri_vms[zb_abri_node][1]
                        # Delete the host
                        zapi.host.delete(host_id)
                        print(f"Deleted host: {host_name}")
                        zabbix_nodes_deleted.append(host_name)
    
                    except Exception as node_error:
                        print(f"Error Deleting node '{zb_abri_node}': {node_error}")
                        traceback.print_exc()
                        send_anonymous_email(
                            from_email='ScriptError@abramad.com',
                            to_email=default_receivers,
                            cc_email=default_cc,
                            subject=f"Error deleting node '{zb_abri_node}' | Zabbix_Agent_Manager_ME_Fully_Automated.py",
                            html_message=f"Error deleting node:<br><b>{zb_abri_node}: {node_error} {traceback.print_exc()}</b> Agent: Zabbix_Agent_Manager_ME_Fully_Automated.py",
                            direction="ltr",
                            # attachments=[]
                        )
    
                        continue
            """

            print(f'\nZabbix OnPrem Node Deletion...')
            for zb_onprem_node in set(zabbix_onprem_vms.keys()):
                if zb_onprem_node not in set(vcenter_onprem_vms.keys()):  # Node Needs to be deleted
                    try:
                        # Host information
                        host_name = zabbix_onprem_vms[zb_onprem_node][0]
                        host_id = zabbix_onprem_vms[zb_onprem_node][1]
                        # Delete the host
                        zapi.host.delete(host_id)
                        print(f"Deleted host: {host_name}")
                        zabbix_nodes_deleted.append(host_name)

                    except Exception as node_error:
                        print(f"Error Deleting node '{zb_onprem_node}': {node_error}")
                        print(f"Exception type: {type(node_error).__name__}")
                        traceback.print_exc()
                        send_anonymous_email(
                            from_email='ScriptError@abramad.com',
                            to_email=error_receivers,
                            cc_email=default_cc,
                            subject=f"Error deleting node '{zb_onprem_node}' | Zabbix_Agent_Manager_ME_Fully_Automated.py",
                            html_message=f"Error deleting node:<br><b>{zb_onprem_node}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b> Agent: Zabbix_Agent_Manager_ME_Fully_Automated.py",
                            direction="ltr",
                            # attachments=[]
                        )

                        print(f"Script failed: {node_error}")
                        success = False
                        error_string_summary += f" {type(node_error).__name__}: {node_error}"

                        # Get the traceback and extract the last traceback frame
                        tb = traceback.extract_tb(node_error.__traceback__)
                        last_call = tb[-1]  # the last traceback frame, where the exception occurred
                        error_string_detail += f" Error 'deleting node' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"

                        continue

            # ---------------------------

            # Zabbix Node Enabling
            """
            print(f'\nZabbix Abri Node Enabling...')
            for vc_pon in set(vcenter_abri_pon_vms.keys()):
                if vc_pon in set(zabbix_abri_poff_vms.keys()):
                    try:
                        # Host information
                        host_name = zabbix_abri_poff_vms[vc_pon][0]
                        host_id = zabbix_abri_poff_vms[vc_pon][1]
                        # Disable the host
                        zapi.host.update({
                            "hostid": host_id,
                            "status": 0  # Set status to 0 to enable the host
                        })
                        print(f"Enabled host: {host_name}")
                        zabbix_nodes_enabled.append(host_name)
    
                    except Exception as node_error:
                        print(f"Error enabling node '{vc_pon}': {node_error}")
                        traceback.print_exc()
                        send_anonymous_email(
                            from_email='ScriptError@abramad.com',
                            to_email=default_receivers,
                            cc_email=default_cc,
                            subject=f"Error enabling node '{vc_pon}' | Zabbix_Agent_Manager_ME_Fully_Automated.py",
                            html_message=f"Error enabling node:<br><b>{vc_pon}: {node_error} {traceback.print_exc()}</b> Agent: Zabbix_Agent_Manager_ME_Fully_Automated.py",
                            direction="ltr",
                            # attachments=[]
                        )
    
                        continue
            """

            print(f'\nZabbix OnPrem Node Enabling...')
            for vc_pon in set(vcenter_onprem_pon_vms.keys()):
                if vc_pon in set(zabbix_onprem_poff_vms.keys()):
                    try:
                        # Host information
                        host_name = zabbix_onprem_poff_vms[vc_pon][0]
                        host_id = zabbix_onprem_poff_vms[vc_pon][1]
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
                        send_anonymous_email(
                            from_email='ScriptError@abramad.com',
                            to_email=error_receivers,
                            cc_email=default_cc,
                            subject=f"Error enabling node '{vc_pon}' | Zabbix_Agent_Manager_ME_Fully_Automated.py",
                            html_message=f"Error enabling node:<br><b>{vc_pon}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b> Agent: Zabbix_Agent_Manager_ME_Fully_Automated.py",
                            direction="ltr",
                            # attachments=[]
                        )

                        print(f"Script failed: {node_error}")
                        success = False
                        error_string_summary += f" {type(node_error).__name__}: {node_error}"

                        # Get the traceback and extract the last traceback frame
                        tb = traceback.extract_tb(node_error.__traceback__)
                        last_call = tb[-1]  # the last traceback frame, where the exception occurred
                        error_string_detail += f" Error 'enabling node' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"

                        continue

            # ---------------------------

            #  Zabbix Node Disabling
            """
            print(f'\nZabbix Abri Node Disabling...')
            for vc_poff in set(vcenter_abri_poff_vms.keys()):
                if vc_poff in set(zabbix_abri_pon_vms.keys()):  # Node Needs to be disabled
                    try:
                        # Host information
                        host_name = zabbix_abri_pon_vms[vc_poff][0]
                        host_id = zabbix_abri_pon_vms[vc_poff][1]
                        # Disable the host
                        zapi.host.update({
                            "hostid": host_id,
                            "status": 1  # Set status to 1 to disable the host
                        })
                        print(f"Disabled host: {host_name}")
                        zabbix_nodes_disabled.append(host_name)
    
                    except Exception as node_error:
                        print(f"Error disabling node '{vc_poff}': {node_error}")
                        traceback.print_exc()
                        send_anonymous_email(
                            from_email='ScriptError@abramad.com',
                            to_email=default_receivers,
                            cc_email=default_cc,
                            subject=f"Error disabling node '{vc_poff}' | Zabbix_Agent_Manager_ME_Fully_Automated.py",
                            html_message=f"Error disabling node:<br><b>{vc_poff}: {node_error} {traceback.print_exc()}</b> Agent: Zabbix_Agent_Manager_ME_Fully_Automated.py",
                            direction="ltr",
                            # attachments=[]
                        )
    
                        continue
            """

            print(f'\nZabbix Onprem Node Disabling...')
            for vc_poff in set(vcenter_onprem_poff_vms.keys()):
                if vc_poff in set(zabbix_onprem_pon_vms.keys()):  # Node Needs to be disabled
                    try:
                        # Host information
                        host_name = zabbix_onprem_pon_vms[vc_poff][0]
                        host_id = zabbix_onprem_pon_vms[vc_poff][1]
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
                        send_anonymous_email(
                            from_email='ScriptError@abramad.com',
                            to_email=error_receivers,
                            cc_email=default_cc,
                            subject=f"Error disabling node '{vc_poff}' | Zabbix_Agent_Manager_ME_Fully_Automated.py",
                            html_message=f"Error disabling node:<br><b>{vc_poff}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b> Agent: Zabbix_Agent_Manager_ME_Fully_Automated.py",
                            direction="ltr",
                            # attachments=[]
                        )

                        print(f"Script failed: {node_error}")
                        success = False
                        error_string_summary += f" {type(node_error).__name__}: {node_error}"

                        # Get the traceback and extract the last traceback frame
                        tb = traceback.extract_tb(node_error.__traceback__)
                        last_call = tb[-1]  # the last traceback frame, where the exception occurred
                        error_string_detail += f" Error 'disabling node' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"

                        continue



            #  Email Part

            #if len(zabbix_nodes_added) > 0:
            #    temp = ''
            #    for i in zabbix_nodes_added:
            #        temp += f'{i}<br>'
            #    send_anonymous_email(zserver[1], default_receivers, default_cc,
            #                         f"{len(zabbix_nodes_added)} nodes added to {zserver[1].split('@')[0]}",
            #                         f"Below nodes were added to Zabbix automatically:<br><br><b>{temp}</b> Agent: Zabbix_VRA_Fully_Automated.py",
            #                         'ltr')


            if len(zabbix_nodes_enabled) > 0:
                temp = ''
                for i in zabbix_nodes_enabled:
                    temp += f'{i}<br>'

                send_anonymous_email(
                    from_email=from_address,
                    to_email=default_receivers,
                    cc_email=default_cc,
                    subject=f"{len(zabbix_nodes_enabled)} nodes got enabled in {from_address.split('@')[0]}",
                    html_message=f"Below nodes were enabled again in {from_address.split('@')[0]} automatically:<br><br><b>{temp}</b> Agent: Zabbix_Agent_Manager_ME_Fully_Automated.py",
                    direction="ltr",
                    # attachments=[]
                )


            if len(zabbix_nodes_disabled) > 0:
                temp = ''
                for i in zabbix_nodes_disabled:
                    temp += f'{i}<br>'

                send_anonymous_email(
                    from_email=from_address,
                    to_email=default_receivers,
                    cc_email=default_cc,
                    subject=f"{len(zabbix_nodes_disabled)} nodes got disabled in {from_address.split('@')[0]}",
                    html_message=f"Below nodes were disabled in {from_address.split('@')[0]} automatically:<br><br><b>{temp}</b> Agent: Zabbix_Agent_Manager_ME_Fully_Automated.py",
                    direction="ltr",
                    # attachments=[]
                )


            if len(zabbix_nodes_deleted) > 0:
                temp = ''
                for i in zabbix_nodes_deleted:
                    temp += f'{i}<br>'

                send_anonymous_email(
                    from_email=from_address,
                    to_email=default_receivers,
                    cc_email=default_cc,
                    subject=f"{len(zabbix_nodes_deleted)} nodes got deleted from {from_address.split('@')[0]}",
                    html_message=f"Below nodes were deleted from {from_address.split('@')[0]} automatically:<br><br><b>{temp}</b> Agent: Zabbix_Agent_Manager_ME_Fully_Automated.py",
                    direction="ltr",
                    # attachments=[]
                )

        print('\nScript ended gracefully. ✅')


    except Exception as body_error:
        print(f"Body Error: {body_error}")
        print(f"Exception type: {type(body_error).__name__}")
        traceback.print_exc()
        send_anonymous_email(
            from_email='ScriptError@abramad.com',
            to_email=error_receivers,
            cc_email=default_cc,
            subject=f"Body Error in running Zabbix_Agent_Manager_ME_Fully_Automated.py",
            html_message=f"Error Occurred:<br><b>{body_error}<br>{traceback.print_exc()}<br>Exception type: {type(body_error).__name__}</b> Agent: Zabbix_Agent_Manager_ME_Fully_Automated.py",
            direction="ltr",
            # attachments=[]
        )

        print(f"Script failed: {node_error}")
        success = False
        error_string_summary += f" {type(node_error).__name__}: {node_error}"

        # Get the traceback and extract the last traceback frame
        tb = traceback.extract_tb(node_error.__traceback__)
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





