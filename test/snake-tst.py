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
    default_receivers = 'sina.z@abramad.com'
    default_cc = 'sina.z@abramad.com'
    #default_cc = 'alireza.ja@abramad.com,mehdi.a@abramad.com,abramadsysops@abramad.com'


    def email_sender(username, password, email_receivers, email_cc, subject, direction, html_body,
                     mail_server='mail.systemgroup.net'):
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
            print(f"Mail Function Error: {err}")
            traceback.print_exc()
            email_sender(username, passphrase, default_receivers, default_cc,
                         f"Email Function Error in running Zabbix_RA_Fully_Automated.py", "ltr",
                         f"Error Occurred:<br><b>{err}<br>{traceback.print_exc()}</b>")


    def days_between_persian_dates(persian_date_str):
        print(persian_date_str)
        # Parse the input Persian date string
        persian_year, persian_month, persian_day = map(int, persian_date_str.split('/'))

        # Create a jdatetime date object from the input date
        input_date = jdatetime.date(persian_year, persian_month, persian_day)

        # Get today's date in Persian calendar
        today_date = jdatetime.date.today()

        # Calculate the difference in days
        delta = (today_date - input_date).days
        print(f'Delta: {delta}')
        #print('###########\n')
        return delta


    def decryptor(enc_env_var, key_env_var):
        # Load the key
        key = os.environ.get(key_env_var)
        encryption_key = Fernet(key)
        encrypted_password = (os.environ.get(enc_env_var)).encode()
        # Decrypt Data
        decrypted_password = encryption_key.decrypt(encrypted_password.decode())

        # print(f"Decryped Text: {decrypted_password}")
        return decrypted_password.decode()



except Exception as function_error:
    print(f"Function Error: {function_error}")
    traceback.print_exc()
    email_sender(username, passphrase, default_receivers, default_cc,
                 f"Email Function Error in running Zabbix_RA_Fully_Automated.py", "ltr",
                 f"Error Occurred:<br><b>{function_error}<br>{traceback.print_exc()}</b>")

#################################################
################ Data Gathering #################


# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)
# *** Connecting to ME-VC01.Abramad.Com to get the Report ***
# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

# Connecting to vCenter
me_vc = connect.SmartConnect(host='me-vc01.abramad.com', user=username, pwd=passphrase, port=443, sslContext=context)
me_content = me_vc.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if
          (vm.name.lower().startswith("mer-")) or (vm.name.lower().startswith("merd-")) or (vm.name.lower().startswith("mea-"))]
sorted_vms = sorted(me_vms, key=lambda vm: vm.name.lower())
sorted_vms_fnl = []

# Pruning VM list
for vm in sorted_vms:
    if not vm.name.lower().endswith('-t') and not vm.name.lower().endswith('-db') and not vm.name.lower().endswith('-a2') and not vm.name.lower().endswith('-a3') and not vm.name.lower().endswith('-a4') and not vm.name.lower().endswith('-a5') and not vm.name.lower().endswith('-a6'):
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
            vm_url = i.value
    if vm_url != "No_URL":
        # Amend URL if needed
        if not vm_url.lower().strip().startswith('http'):
            vm_url = 'https://' + vm_url.lower().strip()

    # VM FQDN
    try:
        vm_fqdn = vm.summary.guest.hostName.lower()
    except:
        vm_fqdn = f"{vm_name}.cloud.local"

    # Get VM Persian Name
    vm_persian_name = ""
    custom_value = vm.summary.customValue
    for i in custom_value:
        if i.key == 103:
            vm_persian_name = i.value

    # Get VM Public IP
    vm_public_ip = ""
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
        vcenter_vms[vm_name] = [vm_name, vm_url, vm_fqdn, vm_persian_name, vm_public_ip, vm_national_id, vm_vip_status, vm_not_monitored_status]

        if vm_power_state == 'poweredoff':
            vcenter_poff_vms[vm_name] = [vm_name, vm_url, vm_fqdn, vm_persian_name, vm_public_ip, vm_national_id, vm_vip_status, vm_not_monitored_status]


        # Check if app is deployed
        if vm_power_state == 'poweredon':

            print(vm_name)
            custom_value = vm.summary.customValue
            for i in custom_value:
                print(f'key: {i.key}\nvalue: {i.value}')


            if days_between_persian_dates(vm_creation_date) > 20:
                print('#############\n')
                # Find powered-on VMs
                vcenter_pon_vms[vm_name] = [vm_name, vm_url, vm_fqdn, vm_persian_name, vm_public_ip, vm_national_id, vm_vip_status, vm_not_monitored_status]

                # Find powered-on VMs with disconnected NICs
                if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                    for device in vm.config.hardware.device:
                        if isinstance(device, vim.vm.device.VirtualEthernetCard):
                            if not device.connectable.connected:
                                vcenter_in_debt_vms[vm_name] = [vm_name, vm_url, vm_fqdn, vm_persian_name, vm_public_ip, vm_national_id, vm_vip_status, vm_not_monitored_status]
                                break



    except Exception as body_error:
        print(f"Body Error: {body_error}")
        traceback.print_exc()
        email_sender(username, passphrase, default_receivers, default_cc,
             f"Body Error in running Zabbix_OnPrem_Fully_Automated.py", "ltr",
             f"Error Occurred:<br><b>{body_error}<br>{traceback.print_exc()}<br>{vm.name}</b>")


Disconnect(me_vc)
