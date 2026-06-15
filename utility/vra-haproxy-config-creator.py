try:
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from pyvim.connect import Disconnect
    from pyvim import connect
    from pyVmomi import vim
    import subprocess
    import jdatetime
    import warnings
    import smtplib
    import socket
    import ssl
    import sys
    import os

    reci = "support@abramad.com,alireza.ja@abramad.com"
    cc = "mohammadhossein.kh@abramad.com,hossein.a@abramad.com"

    def is_resolvable(fqdn):
        try:
            # Attempt to resolve the FQDN to an IP address
            ip_address = socket.gethostbyname(fqdn)
            return True
        except socket.gaierror as e:
            # Handle the error if the FQDN cannot be resolved
            return False


    def email_sender(username, password, email_receivers, email_cc, subject, direction, html_body,
                     mail_server='mail.abramad.com'):

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
            print(f"Function Error: {err}")
            email_sender(username, password, reci, cc,
                         f"Function Error in running config-creator.py | {hostname}", "ltr",
                         f"Error Occurred:<br><b>{err}</b>")


    # Credentials
    from cryptography.fernet import Fernet


    def decryptor(enc_env_var, key_env_var):

        # Load the key
        key = os.environ.get(key_env_var)
        encryption_key = Fernet(key)
        encrypted_password = (os.environ.get(enc_env_var)).encode()
        # Decrypt Data
        decrypted_password = encryption_key.decrypt(encrypted_password)

        return decrypted_password.decode()


    username = decryptor("enc_sinaz_abramad", "key_sinaz_abramad")
    password = decryptor("enc_sinaz_pass", "key_sinaz_pass")

    # Date Info
    today_date_jalali_full = '~~~~~~~~~~ ' + str(jdatetime.datetime.now())[:-7] + ' ~~~~~~~~~~'
    with open("/etc/haproxy/haproxy-config.log", "a") as log:
        log.write(today_date_jalali_full + "\n")

    # Hostname
    hostname = socket.gethostname()

    # Ignore the warning
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    # *** Connecting to ME-VC01.Abramad.Com to get the Report ***

    # Create an SSL context with no certificate verification
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.verify_mode = ssl.CERT_NONE

    ME_VC = connect.SmartConnect(host='vra-vc01.abramad.com', user=username, pwd=password, port=443, sslContext=context)
    me_content = ME_VC.RetrieveContent()
    me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
    me_vms = [vm for vm in me_vm_view.view if (vm.name.startswith("VRA-") and not vm.name.startswith("VRA-HAProxy"))]
    # Sort the me_vms list based on VM names
    sorted_vms = sorted(me_vms, key=lambda vm: vm.name.lower())
    ra_dict = {}

    for vm in sorted_vms:

        vm_power_state = vm.runtime.powerState  # Power State
        if vm_power_state.lower() == "poweredon":

            # Iterate through the hardware devices to find network adapters
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                    # Checking if vm is in 'VRA-1003-Customers' PortGroup
                    if device.backing.port.portgroupKey == 'dvportgroup-4018':

                        '''
                        # retrieve vm IP address
                        vm_ip = ""
                        if vm.guest is not None:
                            for nic in vm.guest.net:
                                if nic.ipConfig is not None:
                                    for ip in nic.ipConfig.ipAddress:
                                        if not ip.ipAddress.startswith('169.254') and not ip.ipAddress.startswith('fe80'):
                                            vm_ip = ip.ipAddress
            
                        # vm FQDN
                        vm_fqdn = vm.summary.guest.hostName
                        '''

                        # VM Information
                        vm_info = [vm.name]  # , vm_fqdn, vm_ip]

                        # Filling RA VMs Dictionary
                        ra_dict[f"{vm_info[0]}"] = vm_info

    Disconnect(ME_VC)

    ra_servers_count = len(ra_dict)

    # Keeping Track of number of RA VMs and Their Names
    with open("/etc/haproxy/ra-vms-name.txt", "r") as file1:
        ra_vms_name_file = file1.readlines()
    ra_vms_name_file = [item.strip().rstrip("\n") for item in ra_vms_name_file]

    with open("/etc/haproxy/ra-vms-count.txt", "r") as file2:
        ra_vms_count_file = file2.read()

    # Config Fractures
    full_cfg = ""
    part1_cfg = """
global

    log /dev/log    local0
    log /dev/log    local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    daemon


defaults

    errorfile 403 /etc/haproxy/errors/403.http
    log global
    mode http
    option httplog
    option dontlognull
    timeout connect 5000
    timeout client  50000
    timeout server  50000

#frontend http_front
#    bind *:80
#    mode http

    # Redirect HTTP traffic to HTTPS
#    http-request redirect location https://%[hdr(host)]%[capture.req.uri] code 301 if !{ ssl_fc }


frontend http_front

    bind 0.0.0.0:80
    #:443 ssl crt /etc/haproxy/certificates/certificate.pem crt /etc/haproxy/certificates/abri2cer.pem crt /etc/haproxy/certificates/abri3cer.pem alpn h2,http/1.1
    
    http-request deny if { path -i -m beg /zzz }

    """
    part2_cfg = ""
    part3_cfg = ""

    # if new servers were created, create new config file
    if ra_servers_count != int(ra_vms_count_file):
        # Log
        print(f"Count not equal Live) {ra_servers_count} != File) {ra_vms_count_file}\nNew 'haproxy' config needed")
        with open("/etc/haproxy/haproxy-config.log", "a") as log:
            log.write(
                f"Count not equal Live) {ra_servers_count} != File) {ra_vms_count_file}\nNew 'haproxy' config needed\n")


        ### Config Creation ###
        for vm in ra_dict:

            # Check if backend server is resolvable
            if is_resolvable(f"{(ra_dict[vm][0]).lower()}.cloud.local"):

                part2_configlet = f"""
    ##################### {ra_dict[vm][0]}.Cloud.Local #####################
    acl {(ra_dict[vm][0][4:]).lower()}_acl hdr(host) -i -m reg ^{((ra_dict[vm][0])[4:]).lower()}\.servehttp\.com$
    use_backend {(ra_dict[vm][0])} if {(ra_dict[vm][0][4:]).lower()}_acl

"""
                part2_cfg += part2_configlet

                part3_configlet = f"""
############### {ra_dict[vm][0]}.Cloud.Local #################
backend {(ra_dict[vm][0])}
    server {ra_dict[vm][0]} {(ra_dict[vm][0]).lower()}.cloud.local:80

"""
                part3_cfg += part3_configlet

            else:  # backend not resolvable
                print(f"{vm} was not Resolvable\nRolling back the configuration\nHAProxy service left untouched.\n")

                with open("/etc/haproxy/haproxy-config.log", "a") as log:
                    log.write(
                        f"{vm} was not Resolvable\nRolling back the configuration\nHAProxy service left untouched.\n\n")

                email_sender(username, password, reci, cc,f"Name Resolution unsuccessful on {vm} | {hostname}", "ltr", f"{today_date_jalali_full}<br><b>{vm}</b> was not Resolvable<br>Rolling back the configuration<br>HAProxy service left untouched.<br>")

                sys.exit()  # Exiting the application


        # Updating VM count and Names
        with open("/etc/haproxy/ra-vms-name.txt", "w") as file:
            for vm in ra_dict:
                file.write(ra_dict[vm][0] + '\n')

        with open("/etc/haproxy/ra-vms-count.txt", "w") as file:
            file.write(str(ra_servers_count))


        # Full config creation and Saving
        full_cfg = part1_cfg + part2_cfg + part3_cfg

        with open("/etc/haproxy/haproxy.cfg", "w") as file:
            file.write(full_cfg)

        # Reloading HAProxy service
        command = "sudo systemctl reload haproxy"

        # Execute the command
        try:
            subprocess.run(command, shell=True, check=True)
            print("HAProxy service reloaded successfully.")
            with open("/etc/haproxy/haproxy-config.log", "a") as log:
                log.write("HAProxy service reloaded successfully.\n")

            mail_body = f"{today_date_jalali_full}<br>Number of VMs in cache file was not equal to vCenter VMs  --> <b>vCenter: {ra_servers_count}  !=  File: {ra_vms_count_file}</b><br>Generating New 'haproxy' config<br>HAProxy service reloaded successfully.<br>"
            email_sender(username, password, reci, cc,
                         f"New HAProxy Config Creation Succeeded | {hostname}", "ltr", mail_body)


        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to reload HAProxy service: {e}")
            with open("/etc/haproxy/haproxy-config.log", "a") as log:
                log.write(f"Error: Failed to reload HAProxy service: {e}\n")

            email_sender(username, password, reci, cc,
                         f"Failure in Reloading HAProxy Service | {hostname}", "ltr",
                         f"<b>Critical Error!<br>Check {hostname} HAProxy Logs ASAP.</b>")




    elif ra_servers_count == int(ra_vms_count_file):
        print(f"Count was equal --> Live) {ra_servers_count} : File) {ra_vms_count_file}")
        with open("/etc/haproxy/haproxy-config.log", "a") as log:
            log.write(f"Count was equal --> Live) {ra_servers_count} : File) {ra_vms_count_file}\n")

        flag = 0
        for virtual_machine in ra_dict:
            if (flag == 0) and (virtual_machine not in ra_vms_name_file):
                print(f"{virtual_machine} was not in 'ra-vms-name' file\nNew 'haproxy' Config needed")
                with open("/etc/haproxy/haproxy-config.log", "a") as log:
                    log.write(f"{virtual_machine} was not in 'ra-vms-name' file\nNew 'haproxy' Config needed\n")



                ### Config Creation ###
                for vm in ra_dict:

                    # Check if backend server is resolvable
                    if is_resolvable(f"{(ra_dict[vm][0]).lower()}.cloud.local"):

                        part2_configlet = f"""
    ##################### {ra_dict[vm][0]}.Cloud.Local #####################
    acl {(ra_dict[vm][0][4:]).lower()}_acl hdr(host) -i -m reg ^{((ra_dict[vm][0])[4:]).lower()}\.servehttp\.com$
    use_backend {(ra_dict[vm][0])} if {(ra_dict[vm][0][4:]).lower()}_acl

"""
                        part2_cfg += part2_configlet

                        part3_configlet = f"""
############### {ra_dict[vm][0]}.Cloud.Local #################
backend {(ra_dict[vm][0])}
    server {ra_dict[vm][0]} {(ra_dict[vm][0]).lower()}.cloud.local:80

"""
                        part3_cfg += part3_configlet

                    else:  # backend not resolvable
                        print(f"{vm} was not Resolvable\nRolling back the configuration\nHAProxy service left untouched.\n")

                        with open("/etc/haproxy/haproxy-config.log", "a") as log:
                            log.write(
                                f"{vm} was not Resolvable\nRolling back the configuration\nHAProxy service left untouched.\n\n")

                        email_sender(username, password, reci, cc,
                                     f"Name Resolution unsuccessful on {vm} | {hostname}", "ltr",
                                     f"{today_date_jalali_full}<br><b>{vm}</b> was not Resolvable<br>Rolling back the configuration<br>HAProxy service left untouched.<br>")

                        sys.exit()  # Exiting the application


                # Updating VM count and Names
                with open("/etc/haproxy/ra-vms-name.txt", "w") as file:
                    for vm in ra_dict:
                        file.write(ra_dict[vm][0] + '\n')

                with open("/etc/haproxy/ra-vms-count.txt", "w") as file:
                    file.write(str(ra_servers_count))


                # Full config creation and Saving
                full_cfg = part1_cfg + part2_cfg + part3_cfg

                with open("/etc/haproxy/haproxy.cfg", "w") as file:
                    file.write(full_cfg)

                # Reloading HAProxy service
                command = "sudo systemctl reload haproxy"

                # Execute the command
                try:
                    subprocess.run(command, shell=True, check=True)
                    print("HAProxy service reloaded successfully.")
                    with open("/etc/haproxy/haproxy-config.log", "a") as log:
                        log.write("HAProxy service reloaded successfully.\n")

                    mail_body = f"{today_date_jalali_full}<br>Number of VMs in cache file was equal to vCenter VMs, but VM names were not the same.<br><b>{virtual_machine}</b> was not in cache file<br>Generating New 'haproxy' config<br>HAProxy service reloaded successfully.<br>"
                    email_sender(username, password, reci, cc,
                                 f"New HAProxy Config Creation Succeeded | {hostname}", "ltr", mail_body)


                except subprocess.CalledProcessError as e:
                    print(f"Error: Failed to reload HAProxy service: {e}")
                    with open("/etc/haproxy/haproxy-config.log", "a") as log:
                        log.write(f"Error: Failed to reload HAProxy service: {e}\n")

                    email_sender(username, password, reci, cc,
                                 f"Failure in Reloading HAProxy Service | {hostname}", "ltr",
                                 f"<b>Critical Error!<br>Check {hostname} HAProxy Logs ASAP.</b>")

                flag = 1

        if flag == 0:
            print("VM names were equal\nNo New 'haproxy' Config Needed")
            with open("/etc/haproxy/haproxy-config.log", "a") as log:
                log.write("VM names were equal\nNo New 'haproxy' Config Needed\n")

    print(50 * "~" + "\n")
    with open("/etc/haproxy/haproxy-config.log", "a") as log:
        log.write(40 * "~" + "\n\n\n")

except Exception as err:
    print(f"General Error: {err}")
    with open("/etc/haproxy/haproxy-config.log", "a") as log:
        log.write(f"General Error: {err}\n\n")
    email_sender(username, password, reci, cc,
                 f"General Error on running config-creator.py | {hostname}", "ltr", f"Error Occurred:<br><b>{err}</b>")
