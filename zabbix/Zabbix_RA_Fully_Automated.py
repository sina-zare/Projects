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

except Exception as module_err:
    print(f"Module Error: {module_err}")
    print(f"Exception type: {type(module_err).__name__}")
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


    username = 'sysops-svc@abramad.com'
    passphrase = decryptor('sysops-svc_enc', 'sysops-svc_key')
    default_receivers = 'abramadsysops@abramad.com'
    error_receivers = 'abramadsysops@abramad.com, support@abramad.com'
    #default_cc = 'sina.z@abramad.com'
    default_cc = 'sina.z@abramad.com'
    zabbix_server = 'VNK-CustomerZabbix@abramad.com'


    def send_anonymous_email(from_email, to_email, cc_email, subject, html_message, direction,
                             mail_server='mail.abramad.com', attachments=None):
        try:
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

            # Create the email message
            msg = MIMEMultipart()
            msg["From"] = Header(from_email, "utf-8")
            msg["To"] = Header(", ".join(to_email_list), "utf-8")  # For display purposes
            msg["CC"] = Header(", ".join(cc_email_list), "utf-8")  # For display purposes
            msg["Subject"] = Header(subject, "utf-8")

            # Attach HTML body
            msg.attach(MIMEText(email_body, "html", "utf-8"))

            # Attach files if any
            if attachments:
                for attachment in attachments:
                    if os.path.exists(attachment):
                        with open(attachment, 'rb') as f:
                            part = MIMEApplication(f.read(), Name=os.path.basename(attachment))
                            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment)}"'
                            msg.attach(part)
                    else:
                        print(f"Warning: Attachment {attachment} not found.")

            # Connect to the mail server and send the email
            with smtplib.SMTP(mail_server, 25) as server:
                server.sendmail(from_email, all_recipients, msg.as_string())
                print("Email sent successfully.")

        except Exception as err:
            print(f"email_sender Function Error: {err}")
            print(f"Exception type: {type(err).__name__}")
            send_anonymous_email(from_email, error_receivers, 'sina.z@abramad.com',
                                 f"email_sender Function Error in running All_VMs_Info.py",
                                 f"Error Occurred:<br><b>{err}<br>Exception type: {type(err).__name__}<br></b> Agent: Zabbix_RA_Fully_Automated.py",
                                 'ltr')

except Exception as function_error:
    print(f"Function Error: {function_error}")
    print(f"Exception type: {type(function_error).__name__}")
    traceback.print_exc()
    send_anonymous_email(
        from_email=zabbix_server,
        to_email=error_receivers,
        cc_email=default_cc,
        subject=f"Email Function Error in running Zabbix_RA_Fully_Automated.py",
        html_message=f"Error Occurred:<br><b>{function_error}<br>{traceback.print_exc()}<br>Exception type: {type(function_error).__name__}</b>",
        direction="ltr",
        # attachments=[]
    )


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
    mra_vc = connect.SmartConnect(host='mra-vc01.abramad.com', user=username, pwd=passphrase, port=443, sslContext=context)
    mra_content = mra_vc.RetrieveContent()
    mra_vm_view = mra_content.viewManager.CreateContainerView(mra_content.rootFolder, [vim.VirtualMachine], True)
    mra_vms = [vm for vm in mra_vm_view.view if (vm.name.lower().startswith("ra-")) or (vm.name.lower().startswith("rap-"))]
    sorted_vms = sorted(mra_vms, key=lambda vm: vm.name.lower())

    vcenter_pon_vms = {}
    vcenter_poff_vms = {}
    vcenter_ra_vms = {}

    for vm in sorted_vms:

        if not vm.name.lower().startswith('ra-mistest') and not vm.name.lower() == 'ra-test1' and not vm.name.lower() == 'ra-test2' and not vm.name.lower().startswith('ra-ansible') and not vm.name.lower() == 'rap-amini10' and not vm.name.lower() == 'ra-pentest':

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
                if i.key == 301:
                    vm_url = (i.value).strip().lower()
            if not vm_url.lower().strip().startswith('https://'):
                vm_url = 'https://' + vm_url.lower().strip()
            if not vm_url.lower().strip().endswith('.rahkaran.ir'):
                vm_url = vm_url.lower().strip() + '.rahkaran.ir'
            if vm_url.lower().strip() == 'https://.rahkaran.ir':
                vm_url = f'https://{vm_name.lower().split('-')[1]}.rahkaran.ir'

            # Get NIC connection status
            vm_nic_status = ''
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                    # VM NIC Status
                    nic_connected = device.connectable.connected
                    vm_nic_status = "connected" if nic_connected else "disconnected"

            #  Distinguishing VMs
            vcenter_ra_vms[vm_name] = [vm_name, vm_url, vm_note, vm_fqdn, vm_power]

            if vm_power.endswith('off') or vm_nic_status == 'disconnected':
                vcenter_poff_vms[vm_name] = [vm_name, vm_url, vm_note, vm_fqdn,vm_power]
            elif vm_power.endswith('on') and vm_nic_status == 'connected':
                vcenter_pon_vms[vm_name] = [vm_name, vm_url, vm_note, vm_fqdn, vm_power]

    Disconnect(mra_vc)


    #  Gathering Data from Zabbix

    # Zabbix server credentials
    zabbix_url = "http://172.29.6.15"
    zabbix_user = "sysops-svc"
    zabbix_password = passphrase

    # Connect to Zabbix API
    zapi = ZabbixAPI(zabbix_url)
    zapi.login(zabbix_user, zabbix_password)

    # Get all hosts
    hosts = zapi.host.get(
        output=["hostid", "host", "status"]
    )

    zabbix_ra_vms = {}
    zabbix_pon_vms = {}
    zabbix_poff_vms = {}

    #  Distinguishing hosts
    for host in hosts:
        if host['host'].startswith('ra-') or host['host'].startswith('rap-'):
            zabbix_ra_vms[host['host']] = [host['host'], host['hostid'], host['status']]
        if (host['host'].startswith('ra-') and host['status'] == '1') or (host['host'].startswith('rap-') and host['status'] == '1'):
            zabbix_poff_vms[host['host']] = [host['host'], host['hostid'], host['status']]
        elif (host['host'].startswith('ra-') and host['status'] == '0') or (host['host'].startswith('rap-') and host['status'] == '0'):
            zabbix_pon_vms[host['host']] = [host['host'], host['hostid'], host['status']]


    #  Taking Group and Template IDs(host['host'].startswith('vra-') and host['status'] == '0')
    # Template and Host Group
    template_name = "Rahkaran-Abri-Tpl-Far"     # Template name
    host_group_name1 = "Rahkaran-Abri-Grp"  # Host group name
    host_group_name2 = "Support_Team"        # Host group name


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


    #  Comparison

    #  Zabbix Node Deletion
    for zb_ra_node in set(zabbix_ra_vms.keys()):
        if zb_ra_node not in set(vcenter_ra_vms.keys()):  # Node Needs to be deleted
            try:
                # Host information
                host_name = zabbix_ra_vms[zb_ra_node][0]
                host_id = zabbix_ra_vms[zb_ra_node][1]
                # Delete the host
                zapi.host.delete(host_id)
                print(f"Deleted host: {host_name}")
                zabbix_nodes_deleted.append(host_name)

            except Exception as node_error:
                print(f"Error Deleting node '{zb_ra_node}': {node_error}")
                print(f"Exception type: {type(node_error).__name__}")
                traceback.print_exc()
                send_anonymous_email(
                    from_email=zabbix_server,
                    to_email=error_receivers,
                    cc_email=default_cc,
                    subject=f"Error deleting node '{zb_ra_node}' | Zabbix_RA_Fully_Automated.py",
                    html_message=f"Error deleting node:<br><b>{zb_ra_node}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b>",
                    direction="ltr",
                    # attachments=[]
                )

                continue


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
                    {"tag": "Owner", "value": "Support_Team"},
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
                print(f"Exception type: {type(node_error).__name__}")
                traceback.print_exc()
                send_anonymous_email(
                    from_email=zabbix_server,
                    to_email=error_receivers,
                    cc_email=default_cc,
                    subject=f"Error adding node '{vc_pon}' | Zabbix_RA_Fully_Automated.py",
                    html_message=f"Error adding node:<br><b>{vc_pon}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b>",
                    direction="ltr",
                    # attachments=[]
                )

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
                send_anonymous_email(
                    from_email=zabbix_server,
                    to_email=error_receivers,
                    cc_email=default_cc,
                    subject=f"Error enabling node '{vc_pon}' | Zabbix_RA_Fully_Automated.py",
                    html_message=f"Error enabling node:<br><b>{vc_pon}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b>",
                    direction="ltr",
                    # attachments=[]
                )

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
                send_anonymous_email(
                    from_email=zabbix_server,
                    to_email=error_receivers,
                    cc_email=default_cc,
                    subject=f"Error disabling node '{vc_poff}' | Zabbix_RA_Fully_Automated.py",
                    html_message=f"Error disabling node:<br><b>{vc_poff}: {node_error} {traceback.print_exc()}<br>Exception type: {type(node_error).__name__}</b>",
                    direction="ltr",
                    # attachments=[]
                )

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
            subject=f"{len(zabbix_nodes_added)} nodes added to VNK-Zabbix",
            html_message=f"Below nodes were added to VNK-Zabbix automatically:<br><br><b>{temp}</b>",
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
            subject=f"{len(zabbix_nodes_enabled)} nodes got enabled in VNK-Zabbix",
            html_message=f"Below nodes were enabled again in VNK-Zabbix automatically:<br><br><b>{temp}</b>",
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
            subject=f"{len(zabbix_nodes_disabled)} nodes got disabled in VNK-Zabbix",
            html_message=f"Below nodes were disabled in VNK-Zabbix automatically:<br><br><b>{temp}</b>",
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
            subject=f"{len(zabbix_nodes_deleted)} nodes got deleted from VNK-Zabbix",
            html_message=f"Below nodes were deleted from VNK-Zabbix automatically:<br><br><b>{temp}</b>",
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
        from_email=zabbix_server,
        to_email=error_receivers,
        cc_email=default_cc,
        subject=f"Body Error in running Zabbix_RA_Fully_Automated.py",
        html_message=f"Error Occurred:<br><b>{body_error}<br>{traceback.print_exc()}<br>Exception type: {type(body_error).__name__}</b>",
        direction="ltr",
        # attachments=[]
    )








