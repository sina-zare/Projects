try:
    from email.mime.multipart import MIMEMultipart
    from cryptography.fernet import Fernet
    from pyvim.connect import Disconnect
    from email.mime.text import MIMEText
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
    traceback.print_exc()

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


    username = 'sina.z@abramad.com'
    passphrase = decryptor("enc_sinaz_pass", "key_sinaz_pass")
    default_receivers = 'support@abramad.com'
    #default_cc = 'sina.z@abramad.com'
    default_cc = 'alireza.ja@abramad.com,mehdi.a@abramad.com,soroush.m@abramad.com'


    def email_sender(username, password, email_receivers, email_cc, subject, direction, html_body,
                     mail_server='mail.systemgroup.net'):
        try:
            # Create a multipart message object
            msg = MIMEMultipart()
            msg['From'] = username
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
                                    <p  style="font-family: DiodrumArabic-Regular"><b>Sina Zare<br>Support Team Lead<br>Operation Team</b></p>
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
            print(f"Mail Function Error: {err}")
            traceback.print_exc()
            email_sender(username, passphrase, default_receivers, default_cc,
                         f"Email Function Error in running Zabbix_VRA_Fully_Automated.py", "ltr",
                         f"Error Occurred:<br><b>{err}<br>{traceback.print_exc()}</b>")

except Exception as function_error:
    print(f"Function Error: {function_error}")
    traceback.print_exc()
    email_sender(username, passphrase, default_receivers, default_cc,
                 f"Email Function Error in running Zabbix_VRA_Fully_Automated.py", "ltr",
                 f"Error Occurred:<br><b>{function_error}<br>{traceback.print_exc()}</b>")

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
    vra_vc = connect.SmartConnect(host='vra-vc01.abramad.com', user=username, pwd=passphrase, port=443, sslContext=context)
    vra_content = vra_vc.RetrieveContent()
    vra_vm_view = vra_content.viewManager.CreateContainerView(vra_content.rootFolder, [vim.VirtualMachine], True)
    vra_vms = [vm for vm in vra_vm_view.view if (vm.name.startswith("VRA-"))]
    sorted_vms = sorted(vra_vms, key=lambda vm: vm.name.lower())

    vcenter_pon_vms = {}
    vcenter_poff_vms = {}
    vcenter_vra_vms = {}

    for vm in sorted_vms:

        # Iterate through the hardware devices to find network adapters
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                # Checking if vm is in 'VRA-1003-Customers' PortGroup
                if device.backing.port.portgroupKey == 'dvportgroup-7117' and vm.name.lower() != 'vra-amini2' and vm.name.lower() != 'vra-amini3' and vm.name.lower() != 'vra-demo' and not vm.name.lower().startswith('vra-haproxy'):

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
                    vm_url = f'https://{vm_name.lower().split('-')[1]}.rahkaran.ir'
                    for i in custom_value:
                        if i.key == 601:
                            vm_url = (i.value).strip().lower()
                    if not vm_url.lower().strip().startswith('https://'):
                        vm_url = 'https://' + vm_url.lower().strip()
                    if not vm_url.lower().strip().endswith('.rahkaran.ir'):
                        vm_url = vm_url.lower().strip() + '.rahkaran.ir'
                    if vm_url.lower().strip() == 'https://.rahkaran.ir':
                        vm_url = f'https://{vm_name.lower().split('-')[1]}.rahkaran.ir'


                    #  Distinguishing VMs
                    vcenter_vra_vms[vm_name] = [vm_name, vm_url, vm_note, vm_fqdn,vm_power]

                    if vm_power.endswith('off'):
                        vcenter_poff_vms[vm_name] = [vm_name, vm_url, vm_note, vm_fqdn,vm_power]
                    elif vm_power.endswith('on'):
                        vcenter_pon_vms[vm_name] = [vm_name, vm_url, vm_note, vm_fqdn, vm_power]

    Disconnect(vra_vc)


    #  Gathering Data from Zabbix

    # Zabbix server credentials
    zabbix_url = "http://zab.abramad.com/zabbix"
    zabbix_user = "sina.z"
    zabbix_password = passphrase

    # Connect to Zabbix API
    zapi = ZabbixAPI(zabbix_url)
    zapi.login(zabbix_user, zabbix_password)

    # Get all hosts
    hosts = zapi.host.get(
        output=["hostid", "host", "status"]
    )

    zabbix_vra_vms = {}
    zabbix_pon_vms = {}
    zabbix_poff_vms = {}

    #  Distinguishing hosts
    for host in hosts:
        if host['host'].startswith('vra-'):
            zabbix_vra_vms[host['host']] = [host['host'], host['hostid'], host['status']]
        if host['host'].startswith('vra-') and host['status'] == '1':
            zabbix_poff_vms[host['host']] = [host['host'], host['hostid'], host['status']]
        elif host['host'].startswith('vra-') and host['status'] == '0':
            zabbix_pon_vms[host['host']] = [host['host'], host['hostid'], host['status']]


    #  Taking Group and Template IDs
    # Template and Host Group
    template_name = "Rahkaran-Abri-Tpl"     # Template name
    host_group_name1 = "Rahkaran-Abri-Grp"  # Host group name
    host_group_name2 = "ServiceDesk"        # Host group name


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




    #  Calculation Part
    # keys_equal = set(zabbix_pon_vms.keys()) == set(vcenter_pon_vms.keys())
    zabbix_nodes_added = []
    zabbix_nodes_enabled = []
    zabbix_nodes_disabled = []
    zabbix_nodes_deleted = []

    """
    with open('D:\\OneDrive\\Python Projects\\Zabbix_VRA\\zabbix_current_enabled_nodes_list', 'r') as zcen:
        zab_cur_enbl_nodes_list_from_file = zcen.readlines()
        zab_cur_enbl_nodes_list_from_file = set(
            [item.strip().rstrip("\n") for item in zab_cur_enbl_nodes_list_from_file])

    with open('D:\\OneDrive\\Python Projects\\Zabbix_VRA\\zabbix_current_enabled_nodes_count', 'r') as zcen:
        zab_cur_enbl_nodes_count_from_file = zcen.readlines()
        zab_cur_enbl_nodes_count_from_file = [item.strip().rstrip("\n") for item in zab_cur_enbl_nodes_count_from_file]

    with open('D:\\OneDrive\\Python Projects\\Zabbix_VRA\\zabbix_current_disabled_nodes_list', 'r') as zcdn:
        zab_cur_dsbl_nodes_list_from_file = zcdn.readlines()
        zab_cur_dsbl_nodes_list_from_file = set([item.strip().rstrip("\n") for item in zab_cur_dsbl_nodes_list_from_file])

    with open('D:\\OneDrive\\Python Projects\\Zabbix_VRA\\zabbix_current_enabled_nodes_count', 'r') as zcdn:
        zab_cur_dsbl_nodes_count_from_file = zcdn.readlines()
        zab_cur_dsbl_nodes_count_from_file = [item.strip().rstrip("\n") for item in zab_cur_dsbl_nodes_count_from_file]

    """

    #  Comparison
    #  Zabbix Node Addition
    for vc_pon in set(vcenter_pon_vms.keys()):
        if vc_pon not in set(zabbix_pon_vms.keys()) and vc_pon not in set(zabbix_poff_vms.keys()):  # Node needs to be added to zabbix
            try:
                # Host information
                host_name = vcenter_pon_vms[vc_pon][0]  # {HOST.HOST}
                host_visible_name = vcenter_pon_vms[vc_pon][1].replace('https://', '').replace('.rahkaran.ir', '')  # {HOST.NAME}
                host_desc = vcenter_pon_vms[vc_pon][2]  # Host Description
                host_url = vcenter_pon_vms[vc_pon][1]  # Host URL
                host_fqdn = vcenter_pon_vms[vc_pon][3]
                tags = [
                    {"tag": "Note", "value": ""},
                    {"tag": "Owner", "value": "ServiceDesk"},
                    {"tag": "Ext URL", "value": f"{host_url}"},
                    {"tag": "Int URL", "value": f"http://{host_fqdn}"}
                ]

                # Step 3: Create the new host with description and visible name
                new_pon_host = zapi.host.create({
                    "host": host_name,  # Technical name of the host (internal name)
                    "name": host_visible_name,  # Visible name of the host in the frontend
                    "description": host_desc,  # Host description
                    "groups": [{"groupid": host_group_id1}, {"groupid": host_group_id2}],  # Host group
                    "templates": [{"templateid": template_id}],  # Template
                    "tags": tags
                })

                host_id = new_pon_host['hostids'][0]
                print(f"Host '{host_name}' created with ID {host_id}")
                zabbix_nodes_added.append(host_name)

            except Exception as node_error:
                print(f"Error adding node '{vc_pon}': {node_error}")
                traceback.print_exc()
                email_sender(username, passphrase, default_receivers, default_cc,
                             f"Error adding node '{vc_pon}' | Zabbix_VRA_Fully_Automated.py", "ltr",
                             f"Error adding node:<br><b>{vc_pon}: {node_error} {traceback.print_exc()}</b>")
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
                traceback.print_exc()
                email_sender(username, passphrase, default_receivers, default_cc,
                             f"Error enabling node '{vc_pon}' | Zabbix_VRA_Fully_Automated.py", "ltr",
                             f"Error enabling node:<br><b>{vc_pon}: {node_error} {traceback.print_exc()}</b>")
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
                traceback.print_exc()
                email_sender(username, passphrase, default_receivers, default_cc,
                             f"Error disabling node '{vc_poff}' | Zabbix_VRA_Fully_Automated.py", "ltr",
                             f"Error disabling node:<br><b>{vc_poff}: {node_error} {traceback.print_exc()}</b>")
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
                traceback.print_exc()
                email_sender(username, passphrase, default_receivers, default_cc,
                             f"Error deleting node '{zb_vra_node}' | Zabbix_VRA_Fully_Automated.py", "ltr",
                             f"Error deleting node:<br><b>{zb_vra_node}: {node_error} {traceback.print_exc()}</b>")
                continue



    #  Email Part
    if len(zabbix_nodes_added) > 0:
        temp = ''
        for i in zabbix_nodes_added:
            temp += f'{i}<br>'
        email_sender(username, passphrase, default_receivers, default_cc,
                     f"{len(zabbix_nodes_added)} nodes added to Zabbix", "ltr",
                     f"Below nodes were added to Zabbix automatically:<br><br><b>{temp}</b>")

    if len(zabbix_nodes_enabled) > 0:
        temp = ''
        for i in zabbix_nodes_enabled:
            temp += f'{i}<br>'
        email_sender(username, passphrase, default_receivers, default_cc,
                     f"{len(zabbix_nodes_enabled)} nodes got enabled in Zabbix", "ltr",
                     f"Below nodes were enabled again in Zabbix automatically:<br><br><b>{temp}</b>")

    if len(zabbix_nodes_disabled) > 0:
        temp = ''
        for i in zabbix_nodes_disabled:
            temp += f'{i}<br>'
        print(temp)
        email_sender(username, passphrase, default_receivers, default_cc,
                     f"{len(zabbix_nodes_disabled)} nodes got disabled in Zabbix", "ltr",
                     f"Below nodes were disabled in Zabbix automatically:<br><br><b>{temp}</b>")

    if len(zabbix_nodes_deleted) > 0:
        temp = ''
        for i in zabbix_nodes_deleted:
            temp += f'{i}<br>'
        email_sender(username, passphrase, default_receivers, default_cc,
                     f"{len(zabbix_nodes_deleted)} nodes got deleted from Zabbix", "ltr",
                     f"Below nodes were deleted from Zabbix automatically:<br><br><b>{temp}</b>")


    # Logout from the Zabbix API session
    zapi.user.logout()

except Exception as body_error:
    print(f"Body Error: {body_error}")
    traceback.print_exc()
    email_sender(username, passphrase, default_receivers, default_cc,
                 f"Body Error in running Zabbix_VRA_Fully_Automated.py", "ltr",
                 f"Error Occurred:<br><b>{body_error}<br>{traceback.print_exc()}</b>")
