try:

    try:
        from email.mime.multipart import MIMEMultipart
        from cryptography.fernet import Fernet
        from pyvim.connect import Disconnect
        from email.mime.text import MIMEText
        from pyzabbix import ZabbixAPI
        from pyvim import connect
        from pyVmomi import vim
        import smtplib
        import os
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.application import MIMEApplication
        from email.header import Header
        import traceback
        import jdatetime
        import warnings
        import smtplib
        import time
        import ssl
        import os
        from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter
        import traceback
        import time

        # --- Configuration ---
        script_name = 'zabbix_onprem_url_me_fully_automated'
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
        total_execution_counter = Counter('script_total_execs', 'Total number of times the script has run',
                                          registry=registry)
        total_failed_execution_counter = Counter('script_total_failed_execs',
                                                 'Total number of times the script has failed to finish gracefully',
                                                 registry=registry)
        last_error_message = Gauge('script_last_error_message',
                                   'The last error message encountered during script execution',
                                   ['error_summary', 'error_detail'], registry=registry)

        # Simulate your script logic
        start_time = time.time()
        success = True
        error_string_summary = ""
        error_string_detail = ""


    except Exception as module_err:
        print(f"Module Error: {module_err}")
        print(f"Exception type: {type(module_err).__name__}")
        traceback.print_exc()

        print(f"Script failed: {module_err}")
        success = False
        error_string_summary += f" {type(module_err).__name__}: {module_err}"

        # Get the traceback and extract the last traceback frame
        tb = traceback.extract_tb(module_err.__traceback__)
        last_call = tb[-1]  # the last traceback frame, where the exception occurred
        error_string_detail += f" Error occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"

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
        passphrase = decryptor('sysops-svc_enc', 'sysops-svc_key')
        default_receivers = 'abramadsysops@abramad.com'
        error_receivers = 'abramadsysops@abramad.com, support@abramad.com'
        # default_cc = 'sina.z@abramad.com'
        default_cc = 'sina.z@abramad.com'
        zabbix_server = "vnk-customerzabbix@abramad.com"


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
                send_anonymous_email('ScriptError@abramad.com', error_receivers, default_cc,
                                     f"email_sender Function Error in running Zabbix_Add_vCenter_ICMP_Fully_Automated.py",
                                     f"Error Occurred:<br><b>{err}<br>{traceback.print_exc()}<br>Exception type: {type(err).__name__}</b> Agent: {script_name}.py",
                                     'ltr')

                print(f"Script failed: {err}")
                success = False
                error_string_summary += f" {type(err).__name__}: {err}"

                # Get the traceback and extract the last traceback frame
                tb = traceback.extract_tb(err.__traceback__)
                last_call = tb[-1]  # the last traceback frame, where the exception occurred
                error_string_detail += f" Error 'email_sender' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"


        def days_between_persian_dates(persian_date_str, vm_name):

            try:
                # Parse the input Persian date string
                persian_year, persian_month, persian_day = map(int, persian_date_str.split('/'))

                # Create a jdatetime date object from the input date
                input_date = jdatetime.date(persian_year, persian_month, persian_day)

                # Get today's date in Persian calendar
                today_date = jdatetime.date.today()

                # Calculate the difference in days
                delta = (today_date - input_date).days

                return delta

            except Exception as err:
                print(f"days_between_persian_dates Function Error: {err}")
                print(f"Exception type: {type(err).__name__}")
                send_anonymous_email('ScriptError@abramad.com', error_receivers, 'sina.z@abramad.com',
                                     f"days_between_persian_dates Function Error in running Zabbix_OnPrem_URL_VNK_Fully_Automated.py",
                                     f"Error Occurred:<br><br>{err}<br>Exception type: {type(err).__name__}<br><br>Description:<br><b>Evaluation error while calculating whether at least 0 days is passing since VM creation.<br>VM: {vm_name}<br>Creation Date Custom Attribute: {persian_date_str}</b><br><br>Agent: Zabbix_OnPrem_VNK_Fully_Automated.py",
                                     'ltr')

                print(f"Script failed: {err}")
                success = False
                error_string_summary += f" {type(err).__name__}: {err}"

                # Get the traceback and extract the last traceback frame
                tb = traceback.extract_tb(err.__traceback__)
                last_call = tb[-1]  # the last traceback frame, where the exception occurred
                error_string_detail += f" Error occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"



    except Exception as function_error:
        print(f"Function Error: {function_error}")
        print(f"Exception type: {type(function_error).__name__}")
        traceback.print_exc()
        send_anonymous_email(
            from_email='ScriptError@abramad.com',
            to_email=error_receivers,
            cc_email=default_cc,
            subject=f"Email Function Error in running Zabbix_OnPrem_ME_Fully_Automated.py",
            html_message=f"Error Occurred:<br><b>{function_error}<br>{traceback.print_exc()}<br>Exception type: {type(function_error).__name__}</b>",
            direction="ltr",
            # attachments=[]
        )

        print(f"Script failed: {function_error}")
        success = False
        error_string_summary += f" {type(function_error).__name__}: {function_error}"

        # Get the traceback and extract the last traceback frame
        tb = traceback.extract_tb(function_error.__traceback__)
        last_call = tb[-1]  # the last traceback frame, where the exception occurred
        error_string_detail += f" Error 'email function' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"

    #################################################
    ################ Data Gathering #################

    try:
        # Ignore the warning
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        # *** Connecting to ME-VC01.Abramad.Com to get the Report ***
        # Create an SSL context with no certificate verification
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.verify_mode = ssl.CERT_NONE

        # Connecting to vCenter
        me_vc = connect.SmartConnect(host='me-vc01.abramad.com', user=username, pwd=passphrase, port=443,
                                     sslContext=context)
        me_content = me_vc.RetrieveContent()
        me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
        me_vms = [vm for vm in me_vm_view.view if
                  (vm.name.lower().startswith("mer-")) or (vm.name.lower().startswith("merd-")) or (
                      vm.name.lower().startswith("mea-"))]
        sorted_vms = sorted(me_vms, key=lambda vm: vm.name.lower())
        sorted_vms_fnl = []

        # Pruning VM list
        for vm in sorted_vms:
            if not vm.name.lower().endswith('-t') and not vm.name.lower().endswith(
                    '-db') and not vm.name.lower().endswith('-a2') and not vm.name.lower().endswith(
                    '-a3') and not vm.name.lower().endswith('-a4') and not vm.name.lower().endswith(
                    '-a5') and not vm.name.lower().endswith('-a6'):
                sorted_vms_fnl.append(vm)

        vcenter_pon_vms = {}
        vcenter_poff_vms = {}
        vcenter_in_debt_vms = {}
        vcenter_vms = {}

        for vm in sorted_vms_fnl:
            # VM Name
            vm_name = vm.name.lower()

            # Get VM URL
            vm_url = "No_URL"
            vm_custom_attr = vm.summary.customValue
            for i in vm_custom_attr:
                if i.key == 604:
                    vm_url = i.value.lower().strip()

            # VM FQDN
            try:
                vm_fqdn = vm.summary.guest.hostName.lower()
            except:
                vm_fqdn = f"{vm_name}.cloud.local"

            # Get VM Persian Name
            vm_persian_name = "No_Persian_Name"
            custom_value = vm.summary.customValue
            for i in custom_value:
                if i.key == 103:
                    vm_persian_name = i.value

            # Get VM Public IP
            vm_public_ip = "No_Public_IP"
            vm_custom_attr = vm.summary.customValue
            for i in vm_custom_attr:
                if i.key == 603:
                    vm_public_ip = i.value

            # Get National ID Status
            vm_national_id = "No_National_ID"
            custom_value = vm.summary.customValue
            for i in custom_value:
                if i.key == 611:
                    vm_national_id = i.value

            # Check if node needs to be monitored
            custom_value = vm.summary.customValue
            vm_not_monitored_status = '0'
            for i in custom_value:
                if i.key == 902:
                    vm_not_monitored_status = i.value

            # VM Power State
            vm_power_state = vm.runtime.powerState.lower()

            # Get VM Creation Date
            vm_creation_date = ""
            custom_value = vm.summary.customValue
            for i in custom_value:
                if i.key == 104:
                    vm_creation_date = i.value.strip()

            # Get VM VIP Status
            vm_vip_status = "0"
            custom_value = vm.summary.customValue
            for i in custom_value:
                if i.key == 1003:
                    vm_vip_status = i.value

            # Distinguishing VMs
            try:
                # Taking All Customers
                vcenter_vms[vm_name] = [vm_name, vm_url, vm_fqdn, vm_persian_name, vm_public_ip, vm_national_id,
                                        vm_vip_status, vm_not_monitored_status]

                if vm_power_state == 'poweredoff':
                    vcenter_poff_vms[vm_name] = [vm_name, vm_url, vm_fqdn, vm_persian_name, vm_public_ip,
                                                 vm_national_id, vm_vip_status, vm_not_monitored_status]

                # Check if app is deployed
                if vm_power_state == 'poweredon':

                    # print(vm_name)
                    # custom_value = vm.summary.customValue
                    # for i in custom_value:
                    #    print(f'key: {i.key}\nvalue: {i.value}')

                    try:
                        if days_between_persian_dates(vm_creation_date, vm_name) > 0:
                            # print('#############\n')
                            # Find powered-on VMs
                            vcenter_pon_vms[vm_name] = [vm_name, vm_url, vm_fqdn, vm_persian_name, vm_public_ip,
                                                        vm_national_id, vm_vip_status, vm_not_monitored_status]

                            # Find powered-on VMs with disconnected NICs
                            if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                                for device in vm.config.hardware.device:
                                    if isinstance(device, vim.vm.device.VirtualEthernetCard):
                                        if not device.connectable.connected:
                                            vcenter_in_debt_vms[vm_name] = [vm_name, vm_url, vm_fqdn, vm_persian_name,
                                                                            vm_public_ip, vm_national_id, vm_vip_status,
                                                                            vm_not_monitored_status]
                                            break
                    except Exception as calc_err:
                        print(f"Calculation Error: {calc_err}")
                        print(f"Exception type: {type(calc_err).__name__}")
                        send_anonymous_email('ScriptError@abramad.com', error_receivers, 'sina.z@abramad.com',
                                             f"Calculation Error in running Zabbix_OnPrem_URL_ME_Fully_Automated.py",
                                             f"Error Occurred:<br><br>{calc_err}<br>Exception type: {type(calc_err).__name__}<br><br>Description:<br><b>Calculation error occurred, Check the 'Creation Date' attribute in vCenter on {vm_name}</b><br><br>Agent: Zabbix_OnPrem_ME_Fully_Automated.py",
                                             'ltr')

                        print(f"Script failed: {calc_err}")
                        success = False
                        error_string_summary += f" {type(calc_err).__name__}: {calc_err}"

                        # Get the traceback and extract the last traceback frame
                        tb = traceback.extract_tb(calc_err.__traceback__)
                        last_call = tb[-1]  # the last traceback frame, where the exception occurred
                        error_string_detail += f" Error 'calculation error' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"




            except Exception as body_error:
                print(f"Body Error: {body_error}")
                print(f"Exception type: {type(body_error).__name__}")
                traceback.print_exc()
                send_anonymous_email(
                    from_email='ScriptError@abramad.com',
                    to_email=error_receivers,
                    cc_email=default_cc,
                    subject=f"Body Error in running Zabbix_OnPrem_URL_ME_Fully_Automated.py",
                    html_message=f"Error Occurred:<br><b>{body_error}<br>{traceback.print_exc()}<br>{vm.name}<br>Exception type: {type(body_error).__name__}</b>",
                    direction="ltr",
                    # attachments=[]
                )

                print(f"Script failed: {body_error}")
                success = False
                error_string_summary += f" {type(body_error).__name__}: {body_error}"

                # Get the traceback and extract the last traceback frame
                tb = traceback.extract_tb(body_error.__traceback__)
                last_call = tb[-1]  # the last traceback frame, where the exception occurred
                error_string_detail += f" Error occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"

        Disconnect(me_vc)

        #  Gathering Data from Zabbix

        zabbix_url = "http://172.29.6.15"
        zabbix_user = "sysops-svc"
        zabbix_password = passphrase

        # Connect to Zabbix API
        zapi = ZabbixAPI(zabbix_url)
        zapi.login(zabbix_user, zabbix_password)
        # print('\nConnected to Zabbix')

        hosts = zapi.host.get(
            output=["hostid", "host", "status"],
            selectTags="extend"  # Fetches tags associated with each host
        )

        zabbix_vms = {}
        zabbix_enabled_vms = {}
        zabbix_disabled_vms = {}

        for host in hosts:
            if host['host'].startswith('mer-') or host['host'].startswith('merd-') or host['host'].startswith('mea-'):

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

                #  Distinguishing hosts
                zabbix_vms[hostname] = host_info

                if host['status'] == '1':
                    zabbix_disabled_vms[hostname] = host_info

                elif host['status'] == '0':
                    zabbix_enabled_vms[hostname] = host_info

        # Template and Host Group
        template_mer = "Rahkaran-OnPrem-Tpl-Far"  # Template name
        template_mea = "Automation-OnPrem-Tpl"  # Template name
        host_group_mer = "MER-Grp"  # Host group name
        host_group_servicedesk = "Support_Team"  # Host group name
        host_group_mervip = "MER-VIP-Grp"  # Host group name
        host_group_mea = "MEA-Grp"  # Host group name
        host_group_url = "Rahkaran-Abri-Different_URL"

        # Step 1: Get the template ID
        template1 = zapi.template.get(filter={"host": template_mer})
        if not template1:
            raise Exception(f"Template '{template_mer}' not found.")
        template_mer_id = template1[0]["templateid"]

        template2 = zapi.template.get(filter={"host": template_mea})
        if not template2:
            raise Exception(f"Template '{template_mea}' not found.")
        template_mea_id = template2[0]["templateid"]

        # Step 2: Get the host group ID
        host_group1 = zapi.hostgroup.get(filter={"name": host_group_mer})
        if not host_group1:
            raise Exception(f"Host group '{host_group_mer}' not found.")
        host_group_mer_id = host_group1[0]["groupid"]

        host_group2 = zapi.hostgroup.get(filter={"name": host_group_servicedesk})
        if not host_group2:
            raise Exception(f"Host group '{host_group_servicedesk}' not found.")
        host_group_servicedesk_id = host_group2[0]["groupid"]

        host_group3 = zapi.hostgroup.get(filter={"name": host_group_mervip})
        if not host_group3:
            raise Exception(f"Host group '{host_group_mervip}' not found.")
        host_group_mervip_id = host_group3[0]["groupid"]

        host_group4 = zapi.hostgroup.get(filter={"name": host_group_mea})
        if not host_group4:
            raise Exception(f"Host group '{host_group_mea}' not found.")
        host_group_mea_id = host_group4[0]["groupid"]

        # Get or create the group "Rahkaran-Abri-Different_URL"
        host_group8 = zapi.hostgroup.get(filter={"name": host_group_url})
        if host_group8:
            different_url_group_id = host_group8[0]['groupid']
        else:
            group_create = zapi.hostgroup.create(name=host_group_url)
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
        for zb_node in set(zabbix_vms.keys()):
            if zb_node in vcenter_vms:
                try:
                    zb_host_info = zabbix_vms[zb_node]
                    zb_hostid = zb_host_info[1]
                    zb_macro_url = zb_host_info[3]

                    vc_vm_url = vcenter_vms[zb_node][1]  # URL from vCenter
                    host_int_url = f'http://{(zb_host_info[0]).split('-')[1]}.cloud.local/{vc_vm_url.split('/')[-1]}'

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
                        tags = [
                            {"tag": "Note", "value": ""},
                            {"tag": "Owner", "value": "Support_Team"},
                            {"tag": "Ext URL", "value": f"{vc_vm_url}"},
                            {"tag": "Int URL", "value": f"{host_int_url}"},
                            {"tag": "__zbx_jira", "value": "1"}
                        ]
                        zapi.host.update(
                            hostid=zb_hostid,
                            tags=tags
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
                    send_anonymous_email(zabbix_server, error_receivers, default_cc,
                                         f"Error updating node '{zb_node}' | {script_name}",
                                         f"Error updating node:<br><b>{zb_node}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b> Agent: {script_name}",
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
        for zb_node in set(zabbix_vms.keys()):
            if zb_node not in set(vcenter_vms.keys()):  # Node Needs to be deleted
                try:
                    # Host information
                    host_name = zabbix_vms[zb_node][0]
                    host_id = zabbix_vms[zb_node][1]
                    # Delete the host
                    zapi.host.delete(host_id)
                    print(f"Deleted host: {host_name}")
                    zabbix_nodes_deleted.append(host_name)

                except Exception as node_error:
                    print(f"Error Deleting node '{zb_node}': {node_error}")
                    print(f"Exception type: {type(node_error).__name__}")
                    traceback.print_exc()
                    send_anonymous_email(
                        from_email='ScriptError@abramad.com',
                        to_email=error_receivers,
                        cc_email=default_cc,
                        subject=f"Error deleting node '{zb_node}' | Zabbix_OnPrem_ME_Fully_Automated.py",
                        html_message=f"Error deleting node:<br><b>{zb_node}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b>",
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

        #  Zabbix Node Addition
        for vc_pon in set(vcenter_pon_vms.keys()):
            if vc_pon not in set(zabbix_enabled_vms.keys()) and vc_pon not in set(
                    zabbix_disabled_vms.keys()):  # Node needs to be added to zabbix
                try:
                    # Handling MER Creation
                    if (vcenter_pon_vms[vc_pon][0].startswith('mer-') or vcenter_pon_vms[vc_pon][0].startswith(
                            'merd-')) and vcenter_pon_vms[vc_pon][7] != '1':  # Excluding not monitored

                        #  [vm_name, vm_url, vm_fqdn, vm_persian_name, vm_public_ip, vm_national_id, vm_vip_status, vm_not_monitored_status]

                        if vcenter_pon_vms[vc_pon][6] == '1' and vcenter_pon_vms[vc_pon][
                            1] != 'No_URL':  # Distinguishing VIPs
                            # Host information
                            host_name = vcenter_pon_vms[vc_pon][0]  # {HOST.HOST}
                            host_visible_name = vcenter_pon_vms[vc_pon][0]  # {HOST.NAME}
                            host_desc = f"Persian Name: {vcenter_pon_vms[vc_pon][3]}, National ID: {vcenter_pon_vms[vc_pon][5]}, Public IP: {vcenter_pon_vms[vc_pon][4]}"  # Host Description
                            host_url = vcenter_pon_vms[vc_pon][1]  # Host URL
                            host_fqdn = vcenter_pon_vms[vc_pon][2]
                            tags = [
                                {"tag": "Note", "value": ""},
                                {"tag": "Owner", "value": "Support_Team"},
                                {"tag": "Ext URL", "value": f"{host_url}"},
                                {"tag": "Int URL", "value": f"http://{host_fqdn}/{host_url.split('/')[-1]}"},
                                {"tag": "VIP", "value": ""},
                                {"tag": "__zbx_jira", "value": "1"}
                            ]
                            macros = [
                                {"macro": "{$HOST.URL}", "value": f"{host_url}"}
                            ]

                            # Step 3: Create the new host
                            new_pon_host = zapi.host.create({
                                "host": host_name,  # Technical name of the host (internal name)
                                "name": host_visible_name,  # Visible name of the host in the frontend
                                "description": host_desc,  # Host description
                                "groups": [{"groupid": host_group_mer_id}, {"groupid": host_group_servicedesk_id},
                                           {"groupid": host_group_mervip_id}],  # Host group
                                "templates": [{"templateid": template_mer_id}],  # Template
                                "tags": tags,  # Tags
                                "macros": macros
                            })

                            host_id = new_pon_host['hostids'][0]
                            print(f"VIP Host '{host_name}' created with ID {host_id}")
                            zabbix_nodes_added.append(host_name)

                        if vcenter_pon_vms[vc_pon][6] == '0' and vcenter_pon_vms[vc_pon][
                            1] != 'No_URL':  # Distinguishing Non VIPs
                            # Host information
                            host_name = vcenter_pon_vms[vc_pon][0]  # {HOST.HOST}
                            host_visible_name = vcenter_pon_vms[vc_pon][0]  # {HOST.NAME}
                            host_desc = f"Persian Name: {vcenter_pon_vms[vc_pon][3]}, National ID: {vcenter_pon_vms[vc_pon][5]}, Public IP: {vcenter_pon_vms[vc_pon][4]}"  # Host Description
                            host_url = vcenter_pon_vms[vc_pon][1]  # Host URL
                            host_fqdn = vcenter_pon_vms[vc_pon][2]
                            tags = [
                                {"tag": "Note", "value": ""},
                                {"tag": "Owner", "value": "Support_Team"},
                                {"tag": "Ext URL", "value": f"{host_url}"},
                                {"tag": "Int URL", "value": f"http://{host_fqdn}/{host_url.split('/')[-1]}"},
                                {"tag": "__zbx_jira", "value": "1"}
                            ]
                            macros = [
                                {"macro": "{$HOST.URL}", "value": f"{host_url}"}
                            ]

                            # Step 3: Create the new host
                            new_pon_host = zapi.host.create({
                                "host": host_name,  # Technical name of the host (internal name)
                                "name": host_visible_name,  # Visible name of the host in the frontend
                                "description": host_desc,  # Host description
                                "groups": [{"groupid": host_group_mer_id}, {"groupid": host_group_servicedesk_id}],
                                # Host group
                                "templates": [{"templateid": template_mer_id}],  # Template
                                "tags": tags,  # Tags
                                "macros": macros
                            })

                            host_id = new_pon_host['hostids'][0]
                            print(f"Host '{host_name}' created with ID {host_id}")
                            zabbix_nodes_added.append(host_name)

                    #  Handling MEA Creation
                    if vcenter_pon_vms[vc_pon][0].startswith('mea-') and vcenter_pon_vms[vc_pon][
                        7] != '1':  # Excluding not monitored
                        # Host information
                        host_name = vcenter_pon_vms[vc_pon][0]  # {HOST.HOST}
                        host_visible_name = vcenter_pon_vms[vc_pon][0]  # {HOST.NAME}
                        host_desc = f"Persian Name: {vcenter_pon_vms[vc_pon][3]}, National ID: {vcenter_pon_vms[vc_pon][5]}, Public IP: {vcenter_pon_vms[vc_pon][4]}"  # Host Description
                        host_url = vcenter_pon_vms[vc_pon][1]  # Host URL
                        host_fqdn = vcenter_pon_vms[vc_pon][2]
                        tags = [
                            {"tag": "Note", "value": ""},
                            {"tag": "Owner", "value": "Support_Team"},
                            {"tag": "Ext URL", "value": f"{host_url}"},
                            {"tag": "Int URL", "value": f"http://{host_fqdn}:7001/{host_url.split('/')[-1]}"},
                            {"tag": "__zbx_jira", "value": "1"}
                        ]
                        macros = [
                            {"macro": "{$HOST.URL}", "value": f"{host_url}"}
                        ]

                        # Step 3: Create the new host
                        new_pon_host = zapi.host.create({
                            "host": host_name,  # Technical name of the host (internal name)
                            "name": host_visible_name,  # Visible name of the host in the frontend
                            "description": host_desc,  # Host description
                            "groups": [{"groupid": host_group_mea_id}, {"groupid": host_group_servicedesk_id}],
                            # Host group
                            "templates": [{"templateid": template_mea_id}],  # Template
                            "tags": tags,  # Tags
                            "macros": macros
                        })

                        host_id = new_pon_host['hostids'][0]
                        print(f"Host '{host_name}' created with ID {host_id}")
                        zabbix_nodes_added.append(host_name)



                except Exception as node_error:
                    print(f"Error adding node '{vc_pon}': {node_error}")
                    print(f"Exception type: {type(node_error).__name__}")
                    traceback.print_exc()
                    send_anonymous_email(
                        from_email='ScriptError@abramad.com',
                        to_email=error_receivers,
                        cc_email=default_cc,
                        subject=f"Error adding node '{vc_pon}' | Zabbix_OnPrem_ME_Fully_Automated.py",
                        html_message=f"Error adding node:<br><b>{vc_pon}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b>",
                        direction="ltr",
                        # attachments=[]
                    )

                    print(f"Script failed: {node_error}")
                    success = False
                    error_string_summary += f" {type(node_error).__name__}: {node_error}"

                    # Get the traceback and extract the last traceback frame
                    tb = traceback.extract_tb(node_error.__traceback__)
                    last_call = tb[-1]  # the last traceback frame, where the exception occurred
                    error_string_detail += f" Error 'adding node' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"

                    continue  # Continue to the next node even if an error occurs

            # Zabbix Node Enabling
            if vc_pon not in set(vcenter_in_debt_vms.keys()):
                if vc_pon in set(zabbix_disabled_vms.keys()) and vcenter_pon_vms[vc_pon][7] != '1':
                    try:
                        # Host information
                        host_name = zabbix_disabled_vms[vc_pon][0]
                        host_id = zabbix_disabled_vms[vc_pon][1]
                        # enable the host
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
                            subject=f"Error enabling node '{vc_pon}' | Zabbix_OnPrem_ME_Fully_Automated.py",
                            html_message=f"Error enabling node:<br><b>{vc_pon}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b>",
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

        #  Zabbix Node Disabling
        #  Powered Off
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
                    send_anonymous_email(
                        from_email='ScriptError@abramad.com',
                        to_email=error_receivers,
                        cc_email=default_cc,
                        subject=f"Error disabling node '{vc_poff}' | Zabbix_OnPrem_ME_Fully_Automated.py",
                        html_message=f"Error disabling node:<br><b>{vc_poff}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b>",
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

        #  NIC Disconnected
        for vc_disconnect in set(vcenter_in_debt_vms.keys()):
            if vc_disconnect in set(zabbix_enabled_vms.keys()):  # Node Needs to be disabled
                try:
                    # Host information
                    host_name = zabbix_enabled_vms[vc_disconnect][0]
                    host_id = zabbix_enabled_vms[vc_disconnect][1]
                    # Disable the host
                    zapi.host.update({
                        "hostid": host_id,
                        "status": 1  # Set status to 1 to disable the host
                    })
                    print(f"Disabled host: {host_name}")
                    zabbix_nodes_disabled.append(host_name)

                except Exception as node_error:
                    print(f"Error disabling node '{vc_disconnect}': {node_error}")
                    print(f"Exception type: {type(node_error).__name__}")
                    traceback.print_exc()
                    send_anonymous_email(
                        from_email='ScriptError@abramad.com',
                        to_email=error_receivers,
                        cc_email=default_cc,
                        subject=f"Error disabling node '{vc_disconnect}' | Zabbix_OnPrem_ME_Fully_Automated.py",
                        html_message=f"Error disabling node:<br><b>{vc_disconnect}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b>",
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

        #  Not Monitored
        for vc_not_monitored in set(vcenter_pon_vms.keys()):
            if (vc_not_monitored in set(zabbix_enabled_vms.keys()) and vcenter_pon_vms[vc_not_monitored][
                7] == '1'):  # Node Needs to be disabled
                try:
                    # Host information
                    host_name = zabbix_enabled_vms[vc_not_monitored][0]
                    host_id = zabbix_enabled_vms[vc_not_monitored][1]
                    # Disable the host
                    zapi.host.update({
                        "hostid": host_id,
                        "status": 1  # Set status to 1 to disable the host
                    })
                    print(f"Disabled host: {host_name}")
                    zabbix_nodes_disabled.append(host_name)

                except Exception as node_error:
                    print(f"Error disabling node '{vc_not_monitored}': {node_error}")
                    print(f"Exception type: {type(node_error).__name__}")
                    traceback.print_exc()
                    send_anonymous_email(
                        from_email='ScriptError@abramad.com',
                        to_email=error_receivers,
                        cc_email=default_cc,
                        subject=f"Error disabling node '{vc_not_monitored}' | Zabbix_OnPrem_ME_Fully_Automated.py",
                        html_message=f"Error disabling node:<br><b>{vc_not_monitored}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b>",
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
        if len(zabbix_nodes_added) > 0:
            temp = ''
            for i in zabbix_nodes_added:
                temp += f'{i}<br>'

            send_anonymous_email(
                from_email=zabbix_server,
                to_email=default_receivers,
                cc_email=default_cc,
                subject=f"{len(zabbix_nodes_added)} nodes added to VNK-CustomerZabbix",
                html_message=f"Below nodes were added to VNK-CustomerZabbix automatically:<br><br><b>{temp}</b><br><br>Agent: {script_name}",
                direction="ltr",
                # attachments=[]
            )

        if len(zabbix_nodes_enabled) > 0:
            temp = ''
            for i in zabbix_nodes_enabled:
                temp += f'{i}<br>'

            send_anonymous_email(
                from_email=zabbix_server,
                to_email=default_receivers,
                cc_email=default_cc,
                subject=f"{len(zabbix_nodes_enabled)} nodes got enabled in VNK-CustomerZabbix",
                html_message=f"Below nodes were enabled again in VNK-CustomerZabbix automatically:<br><br><b>{temp}</b><br><br>Agent: {script_name}",
                direction="ltr",
                # attachments=[]
            )

        if len(zabbix_nodes_disabled) > 0:
            temp = ''
            for i in zabbix_nodes_disabled:
                temp += f'{i}<br>'

            send_anonymous_email(
                from_email=zabbix_server,
                to_email=default_receivers,
                cc_email=default_cc,
                subject=f"{len(zabbix_nodes_disabled)} nodes got disabled in VNK-CustomerZabbix",
                html_message=f"Below nodes were disabled in VNK-CustomerZabbix automatically:<br><br><b>{temp}</b><br><br>Agent: {script_name}",
                direction="ltr",
                # attachments=[]
            )

        if len(zabbix_nodes_deleted) > 0:
            temp = ''
            for i in zabbix_nodes_deleted:
                temp += f'{i}<br>'

            send_anonymous_email(
                from_email=zabbix_server,
                to_email=default_receivers,
                cc_email=default_cc,
                subject=f"{len(zabbix_nodes_deleted)} nodes got deleted from VNK-CustomerZabbix",
                html_message=f"Below nodes were deleted from VNK-CustomerZabbix automatically:<br><br><b>{temp}</b><br><br>Agent: {script_name}",
                direction="ltr",
                # attachments=[]
            )

        if len(zabbix_nodes_updated) > 0:
            temp = ''
            for i in zabbix_nodes_updated:
                temp += f'{i}<br>'
            send_anonymous_email(
                from_email=zabbix_server,
                to_email=default_receivers,
                cc_email=default_cc,
                subject=f"{len(zabbix_nodes_updated)} nodes got updated from VNK-CustomerZabbix",
                html_message=f"Below nodes were updated in VNK-CustomerZabbix automatically:<br><br><b>{temp}</b>Agent: {script_name}",
                direction="ltr",
                # attachments=[]
            )

        # Logout from the Zabbix API session
        zapi.user.logout()
        print('\nScript ended gracefully. ✅')



    except Exception as body_error:
        print(f"Body Error: {body_error}")
        print(f"Exception type: {type(body_error).__name__}")
        traceback.print_exc()
        send_anonymous_email(
            from_email='ScriptError@abramad.com',
            to_email=error_receivers,
            cc_email=default_cc,
            subject=f"Body Error in running Zabbix_OnPrem_URL_ME_Fully_Automated.py",
            html_message=f"Error Occurred:<br><b>{body_error}<br>{traceback.print_exc()}<br>Exception type: {type(body_error).__name__}</b>",
            direction="ltr",
            # attachments=[]
        )

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






