import ipaddress
import time
import os
from netmiko import Netmiko
from stdiomask import getpass
from email.header import Header
import re
from jdatetime import date
from cryptography.fernet import Fernet
import subprocess

#### SZ Functions ####

# Logo
def sinzi_logo():

    logo = """

                              ____
                     ____ \__ \\
                     \__ \__/ / __
                     __/ ____ \ \ \    ____
                    / __ \__ \ \/ / __ \__ \\
               ____ \ \ \__/ / __ \/ / __/ / __
          ____ \__ \ \/ ____ \/ / __/ / __ \ \ \\
          \__ \__/ / __ \__ \__/ / __ \ \ \ \/
          __/ ____ \ \ \__/ ____ \ \ \ \/ / __
         / __ \__ \ \/ ____ \__ \ \/ / __ \/ /                                --    ____   _____ 
         \ \ \__/ / __ \__ \__/ / __ \ \ \__/                              -- --   / ___| |__  / 
          \/ ____ \/ / __/ ____ \ \ \ \/ ____                           ---   --   \___ \   / / 
             \__ \__/ / __ \__ \ \/ / __ \__ \\                             -- --    ___) | / /_  
             __/ ____ \ \ \__/ / __ \/ / __/ / __                             --   |____(_)____| 
            / __ \__ \ \/ ____ \/ / __/ / __ \/ /
            \/ / __/ / __ \__ \__/ / __ \/ / __/
            __/ / __ \ \ \__/ ____ \ \ \__/ / __
           / __ \ \ \ \/ ____ \__ \ \/ ____ \/ /
           \ \ \ \/ / __ \__ \__/ / __ \__ \__/
            \/ / __ \/ / __/ ____ \ \ \__/
               \ \ \__/ / __ \__ \ \/
                \/      \ \ \__/ / __
                         \/ ____ \/ /
                            \__ \__/
                            __/

        """

    print(logo)
    time.sleep(2)
    os.system('cls' if os.name == 'nt' else 'clear')


# Encryption/Decryption

def encryptor_env(password, env_enc, env_key):
    # Generate a key and store it securely
    key = Fernet.generate_key()

    # Encrypt sensitive data
    encryption_key = Fernet(key)
    encrypted_password = encryption_key.encrypt(password.encode())

    # Saving Enc_Password and key to System Envs
    subprocess.run(['setx', '/M', env_enc, f'{str(encrypted_password)[2:-1]}'], check=True)
    subprocess.run(['setx', '/M', env_key, f'{str(key)[2:-1]}'], check=True)

    print(f"Password Encrypted.")

def encryptor(password, key_name):
    # Generate a key and store it securely
    key = Fernet.generate_key()
    with open(f"{key_name}.key", "wb") as key_file:
        key_file.write(key)

    # Encrypt sensitive data
    encryption_key = Fernet(key)
    encrypted_password = encryption_key.encrypt(password.encode())

    print(f"Encryped Text: {encrypted_password}")
    return encrypted_password


def decryptor(enc_env_var, key_env_var):

    # Load the key
    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = (os.environ.get(enc_env_var)).encode()
    # Decrypt Data
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())

    #print(f"Decryped Text: {decrypted_password}")
    return decrypted_password.decode()


# Decryption Function
def decrypt(cipher_text, key):
    plain_text = ""
    for i in range(len(cipher_text)):
        char = cipher_text[i]
        plain_int = ord(char) - key
        plain_text += chr(plain_int)
    return plain_text

# Printing with a bit of delay
def print_with_delay(text):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(0.02)
    print("\n")




################## FortiGate ###################
################################################

# Connect to Fortigate
def connect_to_fg1100():

    def decrypt(cipher_text, key):
        plain_text = ""
        for i in range(len(cipher_text)):
            char = cipher_text[i]
            plain_int = ord(char) - key
            plain_text += chr(plain_int)
        return plain_text

    def print_with_delay(text):
        for char in text:
            print(char, end='', flush=True)
            time.sleep(0.03)
        print("\n")

    # Credentials
    #username = "sina.z"
    #password = decrypt(os.environ.get('spass'), 9999)
    username = str(input("Username: ").strip())
    password = getpass("Password: ")
    os.system('cls' if os.name == 'nt' else 'clear')


    fortigate_fw = {
        'device_type': 'fortinet',
        'host': '172.17.242.254',
        'username': username,
        'password': password,
        'port': 2345
    }

    print_with_delay(f"{'#' * 10} Connecting to the Device {'#' * 10}")
    global ssh_to_fg1100
    ssh_to_fg1100 = Netmiko(**fortigate_fw)

    print(ssh_to_fg1100.find_prompt())
    print_with_delay(f"{'#' * 10} Connected {'#' * 10}")
    time.sleep(2)
    os.system('cls' if os.name == 'nt' else 'clear')

# Create New Interface
def new_interface(interface_name, interface_ip, vlan_id, creator_username, ticket_no):

    commands = [
        'config system interface',
        f'edit "{interface_name}"',
        'set vdom "root"',
        f'set ip {interface_ip}',
        'set allowaccess ping',
        f'set description "Tech: {creator_username}; Ticket: {ticket_no}"',
        'set device-identification enable',
        'set role lan',
        'set interface "Downlink"',
        f'set vlanid {vlan_id}',
        'next',
        'end'
    ]

    return commands

# Create New Address
def new_address(address_name, address_type, address_value, color="0"):

    if address_type.lower() == "ip":
        commands = [
          'config firewall address',
          f'edit "{address_name}"',
          'set type ipmask',
          f'set color {color}',
          f'set subnet {address_value}',
          'end'
        ]

        return commands

    elif address_type.lower() == "fqdn":
        commands = [
            'config firewall address',
            f'edit "{address_name}"',
            'set type fqdn',
            f'set color {color}',
            f'set fqdn {address_value}',
            'end'
        ]

        return commands

    else:

        return "Invalid Type"

# Create New Address
def new_address_custom_32(vm_name, private_ip):

    commands = [
      'config firewall address',
      f'edit "{vm_name}-{private_ip}"',
      'set type ipmask',
      f'set subnet {private_ip}/32',
      'end'
    ]

    return commands




# Append Addresses to a Group
def append_addresses_to_group(group_name, address_name_list, color="0"):

    # Check if address_names is a list
    if not isinstance(address_name_list, list):
        raise ValueError("The 'address_names' parameter must be a list.")

    commands = [
        'config firewall addrgrp',
        f'edit "{group_name}"',
        f'set color {color}'
    ]

    for address_name in address_name_list:
        commands.append(f'append member "{address_name}"')

    commands.extend(['next', 'end'])

    return commands


# Append Address to a Group
def append_address_to_group(group_name, address_name, color="0"):

    commands = [
        'config firewall addrgrp',
        f'edit "{group_name}"',
        f'set color {color}',
        f'append member "{address_name}"',
        'next',
        'end'
    ]

    return commands



# Get from IP address to its corresponding address name #
def ip_to_address_converter():

    search = input("Enter IP to Search: ")
    address_name_pattern = re.compile(r"edit (.+)")

    command = f"show firewall address | grep -f {search}"
    output = ssh_to_fg1100.send_command(command)

    address_names = address_name_pattern.finditer((output))

    # in case more than one address name gets matched
    match = False
    for i in address_names:
        print(i.group(1))
        match = True
    if not match:
        print("No Address Objects Found")

# IP Calculator
def calculate_subnet_info(subnet):
    # Create an IPv4Network object
    network = ipaddress.IPv4Network(subnet, strict=False)

    # Get the broadcast address
    broadcast_address = network.broadcast_address

    # Get the usable IP addresses
    usable_ips_obj = list(network.hosts())
    raw_usable_ips = [str(ip) for ip in usable_ips_obj]

    # Get Gateway IP Address
    gateway_address = raw_usable_ips[-1]

    # Get Pruned Usable IPs
    pruned_usable_ips = raw_usable_ips[:-1]

    ip_info = {
        'subnet': str(network.network_address),
        'broadcast_address': str(broadcast_address),
        'gateway_address': str(gateway_address),
        'usable_ips': pruned_usable_ips
    }
    return ip_info

#  Check Successful Execution
def check_successful_execution(response, subject, stage, customer_name, log_file_path):
  if ("unknown" in response.lower()) or ("command parse error" in response.lower() or ("command fail." in response.lower()) or ("invalid" in response.lower())):
    print(f"\nexecution of {subject} commands failed with error for {customer_name}!")
    with open(f"{log_file_path}\\{customer_name}-Network-Logs.txt", "a") as text_file:
      text_file.write(f"\n{'#' * 110}\n{stage}) Execution of {subject} commands failed with error for {customer_name}!\n{'#' * 110}\n")
      text_file.write(response + "\n")
  else:
    print(f"\n{subject} config executed successfully for {customer_name}.")
    with open(f"{log_file_path}\\{customer_name}-Network-Logs.txt", "a") as text_file:
      text_file.write(f"\n{'#' * 110}\n{stage}) {subject} Config executed successfully for {customer_name}.\n{'#' * 110}\n")


#  Check Successful Execution General
def check_successful_execution_g(response, subject, stage, customer_name, log_file_path):
  if ("unknown" in response.lower()) or ("command parse error" in response.lower() or ("command fail." in response.lower()) or ("invalid" in response.lower())):
    print(f"\nexecution of {subject} commands failed with error for {customer_name}!")
    with open(log_file_path, "a") as text_file:
      text_file.write(f"\n{'#' * 110}\n{stage}) Execution of {subject} commands failed with error for {customer_name}!\n{'#' * 110}\n")
      text_file.write(response + "\n")
  else:
    print(f"\n{subject} config executed successfully for {customer_name}.")
    with open(log_file_path, "a") as text_file:
      text_file.write(f"\n{'#' * 110}\n{stage}) {subject} Config executed successfully for {customer_name}.\n{'#' * 110}\n")



#  Writes the Error in a text file
def custom_error_logger(error, log_file_path):

    with open(f"{log_file_path}-Network-Logs.txt", "a") as text_file:
      text_file.write(f"\n{'#' * 90}\nThe Following Error Occurred:\n{error}\n{'#' * 90}\n")

    print(f"\n{'#' * 90}\nThe Following Error Occurred:\n{error}\n{'#' * 90}\n")


# Takes Last URL_Filter Policy ID and sums it with 1 for preventing duplicate policy creation
def find_last_urlfilter_policy_no(exported_config):

    # Define the regular expression pattern
    pattern = re.compile(r'edit (\d+)(?!.*\s*edit\s*\d+\s*\n\s*set name)', re.DOTALL)

    # Find the last match in the text
    match = pattern.search(exported_config)

    # Get the captured number from the match
    last_edit_number = match.group(1) if match else None

    return str((int(last_edit_number) + 1))

# Create New WebFilter URLFilter
def new_webfilter_urlfilter_config(entry_id, urlfilter_name, valid_url):

    commands = [
        'config webfilter urlfilter',
        f'edit {entry_id}',
        f'set name "{urlfilter_name}"',
        f'set comment "{valid_url}"',
        'set one-arm-ips-urlfilter disable',
        'set ip-addr-block disable',
        'set ip4-mapped-ip6 disable',
        'config entries',
        'edit 1',
        f'set url "{valid_url}"',
        'set type regex',
        'set action allow',
        'set antiphish-action block',
        'set status enable',
        'set web-proxy-profile ""',
        'next',
        'edit 2',
        'set url "."',
        'set type regex',
        'set action block',
        'set antiphish-action block',
        'set status enable',
        'next',
        'end',
        'end'
    ]

    return commands

# Create New WebFilter Profile
def new_webfilter_profile_config(url, published_server_name, urlfilter_table_id, ticket_no):

    commands = [
        'config webfilter profile',
        f'edit "{url}"',
        f'set comment "{published_server_name}; {ticket_no}"',
        'config web',
        f'set urlfilter-table {urlfilter_table_id}',
        'end',
        'config ftgd-wf',
        'set options ftgd-disable',
        'end',
        'end'
    ]

    return commands

# Create New Virtual Server 443 to 80 with "Abramad.Cloud" SSL Offload for Rahkaran Publishing
def new_vserver_mer_443(vm_name, url, public_ip, private_ip):

    commands = [
        'config firewall vip',
        f'edit "{vm_name}-443"',
        f'set comment "{url}"',
        'set type server-load-balance',
        f'set extip {public_ip}',
        'set extintf "any"',
        'set server-type https',
        'set extport 443',
        'config realservers',
        'edit 1',
        f'set ip {private_ip}',
        'set port 80',
        'next',
        'end',
        'set http-supported-max-version http1',
        'set ssl-certificate "AbramadCloud-2023-2024"',
        'next',
        'end'
    ]

    return commands

# Create New Virtual Server 80 to 80 with "HTTP Redirect" for Rahkaran Publishing
def new_vserver_mer_80(vserver_name, url, public_ip, private_ip):

    commands = [
        'config firewall vip',
        f'edit "{vserver_name}-80"',
        f'set comment "{url}"',
        'set type server-load-balance',
        f'set extip {public_ip}',
        'set extintf "any"',
        'set server-type http',
        'set http-redirect enable',
        'set extport 80',
        'config realservers',
        'edit 1',
        f'set ip {private_ip}',
        'set port 80',
        'next',
        'end',
        'set http-supported-max-version http1',
        'next',
        'end'
    ]

    return commands

# Create New Virtual Server 443 to 7001 with "Abramad.Cloud" SSL Offload for Automation Publishing
def new_vserver_mea_443(vm_name, url, public_ip, private_ip):

    commands = [
        'config firewall vip',
        f'edit "{vm_name}-443"',
        f'set comment "{url}"',
        'set type server-load-balance',
        f'set extip {public_ip}',
        'set extintf "any"',
        'set server-type https',
        'set extport 443',
        'config realservers',
        'edit 1',
        f'set ip {private_ip}',
        'set port 7001',
        'next',
        'end',
        'set http-supported-max-version http1',
        'set ssl-certificate "AbramadCloud-2023-2024"',
        'next',
        'end'
    ]

    return commands

# Create New Virtual Server 80 to 7001 with "HTTP Redirect" for Automation Publishing
def new_vserver_mea_80(vserver_name, url, public_ip, private_ip):

    commands = [
        'config firewall vip',
        f'edit "{vserver_name}-80"',
        f'set comment "{url}"',
        'set type server-load-balance',
        f'set extip {public_ip}',
        'set extintf "any"',
        'set server-type http',
        'set http-redirect enable',
        'set extport 80',
        'config realservers',
        'edit 1',
        f'set ip {private_ip}',
        'set port 7001',
        'next',
        'end',
        'set http-supported-max-version http1',
        'next',
        'end'
    ]

    return commands

# Create New Virtual Server
def new_vserver(vserver_name, url, protocol_type, public_ip, ext_port, private_ip, priv_port):

    commands = [
        'config firewall vip',
        f'edit "{vserver_name}"',
        f'set comment "{url}"',
        'set type server-load-balance',
        f'set extip {public_ip}',
        'set extintf "any"',
        f'set server-type {protocol_type}',
        f'set extport {ext_port}',
        'config realservers',
        'edit 1',
        f'set ip {private_ip}',
        f'set port {priv_port}',
        'next',
        'end',
        'next',
        'end'
    ]

    return commands

# Create New LDAP User Group from "cloud.local" which contains creation of all 3 required customer groups
def new_ldap_user_group_cloud_local(customer_name):

    command_set = []
    variables = ["Deploy", "Support", "Members"]

    for variable in variables:
        commands = [
            'config user group',
            f'edit "{customer_name}{variable}"',
            'set member "Cloud.Local"',
            'config match',
            'edit 1',
            'set server-name "Cloud.Local"',
            f'set group-name "CN={customer_name}{variable},OU={customer_name},OU=Customers,DC=cloud,DC=local"',
            'next',
            'end',
            'next',
            'end'
        ]

        for command in commands:
            command_set.append(command)

    return command_set

# Create New LDAP User Group
def new_ldap_user_group(group_name, ldap_name, distinguished_name):

    commands = [
        'config user group',
        f'edit "{group_name}"',
        f'set member "{ldap_name}"',
        'config match',
        'edit 1',
        f'set server-name "{ldap_name}"',
        f'set group-name "{distinguished_name}',
        'next',
        'end',
        'next',
        'end'
    ]

    return commands

# Takes Last Firewall Policy ID and sums it with 1 for preventing duplicate policy creation
def find_last_fwpolicy_no(exported_config):
    # Define the regular expression pattern
    pattern = re.compile(r'edit (\d+)(?=.*(\s*set name|\s*set status disable))', re.MULTILINE)

    # Find all matches in the text
    matches = pattern.findall(exported_config)

    # Convert the matches to a list of integers
    numbers = [int(match) for match, _ in matches]

    policy_no_to_create = max(numbers) + 1

    print(f"\n{50 * '#'}\nNumber of Policies created so far: {len(numbers)}\nLast Policy No + 1: {policy_no_to_create}\n{50 * '#'}")

    return policy_no_to_create

# Find Interface Name by vlan ID
def find_interface_name_by_vlan_id(vlan_id, exported_config):
    # Split the text into lines
    lines = exported_config.strip().split('\n')

    # Initialize variables
    current_edit = None
    current_vlan_id = None

    # Iterate through each line
    for line in lines:
        line = line.strip()
        if line.startswith("edit "):
            current_edit = line[len("edit "):]
            current_vlan_id = None  # Reset the current_vlan_id for the new "edit"
        elif line.startswith("set vlanid "):
            current_vlan_id = line[len("set vlanid "):]
        elif line.startswith("next"):
            # Check if the current "edit" entry has the desired vlan_id
            if current_vlan_id == vlan_id:
                return current_edit.strip('"')

    # If no match is found, return None
    return "No Interface Match Found"

# Find Address Name by IP Address
def find_address_name_by_ip(ip_address, subnet_mask, exported_config):
    # Split the text into lines
    lines = exported_config.strip().split('\n')

    # Initialize variables
    current_edit = None
    current_ip_address = None

    # Iterate through each line
    for line in lines:
        line = line.strip()
        if line.startswith("edit "):
            current_edit = line[len("edit "):]
            current_ip_address = None  # Reset the current_private_ip for the new "edit"
        elif line.startswith("set subnet "):
            current_ip_address = line[len("set subnet "):]
        elif line.startswith("next"):
            # Check if the current "edit" entry has the desired vlan_id
            if current_ip_address == f"{ip_address} {subnet_mask}":
                return current_edit

    # If no match is found, return None
    return "No Policy Match Found"

# Create New Virtual IP
def new_vip(vm_name, public_ip, private_ip):

    commands = [
        'config firewall vip',
        f'edit "{vm_name}-{public_ip}"',
        f'set comment "{vm_name}: {public_ip} --> {private_ip}"',
        f'set extip {public_ip}',
        f'set mappedip "{private_ip}"',
        'set extintf "any"',
        'next',
        'end'
    ]

    return commands

# Create New NAT Pool
def new_natpool(customer_name, public_ip):

    commands = [
        'config firewall ippool',
        f'edit "{customer_name}-NATPool-{public_ip}"',
        f'set startip {public_ip}',
        f'set endip {public_ip}',
        'next',
        'end'
    ]

    return commands

# Create SSL-VPN Firewall Policy
def new_sslvpn_policy(policy_no, customer_name, dst_int, username, ticket_no):

    commands = [
        'config firewall policy',
        f'edit {policy_no}',
        f'set name "{customer_name}-SSLVPN"',
        'set srcintf "ssl.root"',
        f'set dstintf "{dst_int}"',
        'set action accept',
        'set srcaddr "all"',
        f'set dstaddr "{customer_name} address"',
        'set schedule "always"',
        'set service "PING" "RDP" "Web_Default" "MS-SQL"',
        'set logtraffic all',
        f'set groups "{customer_name}Deploy" "{customer_name}Members" "{customer_name}Support"',
        f'set comments "Tech: {username}; {ticket_no}"',
        'next',
        'end'
    ]

    return commands

# Create SSL-VPN Firewall Policy Limited to RDP, PING
def new_sslvpn_policy_limited(policy_no, customer_name, dst_int, username, ticket_no):

    commands = [
        'config firewall policy',
        f'edit {policy_no}',
        f'set name "{customer_name}-SSLVPN"',
        'set srcintf "ssl.root"',
        f'set dstintf "{dst_int}"',
        'set action accept',
        'set srcaddr "all"',
        f'set dstaddr "{customer_name} address"',
        'set schedule "always"',
        'set service "PING" "RDP"',
        'set logtraffic all',
        f'set groups "{customer_name}Deploy" "{customer_name}Members" "{customer_name}Support"',
        f'set comments "Tech: {username}; {ticket_no}"',
        'next',
        'end'
    ]

    return commands

# Create SSL-VPN Firewall Policy open
def new_sslvpn_policy_open(policy_no, customer_name, dst_int, username, ticket_no):

    commands = [
        'config firewall policy',
        f'edit {policy_no}',
        f'set name "{customer_name}-SSLVPN"',
        'set srcintf "ssl.root"',
        f'set dstintf "{dst_int}"',
        'set action accept',
        'set srcaddr "all"',
        f'set dstaddr "{customer_name} address"',
        'set schedule "always"',
        'set service "ALL"',
        'set logtraffic all',
        f'set groups "{customer_name}Deploy" "{customer_name}Members" "{customer_name}Support"',
        f'set comments "Tech: {username}; {ticket_no}"',
        'next',
        'end'
    ]

    return commands

# Create Web Publish Firewall Policy
def new_webpublish_policy_rahkaran(policy_no, vm_name, dst_int, webfilter_profile, username, ticket_no):

    commands = [
        'config firewall policy',
        f'edit {policy_no}',
        'set status disable',
        f'set name "{vm_name}-Publish"',
        'set srcintf "Uplink"',
        f'set dstintf "{dst_int}"',
        'set action accept',
        'set srcaddr "all"',
        f'set dstaddr "{vm_name}-443" "{vm_name}-80"',
        'set schedule "always"',
        'set service "Web_Default"',
        'set utm-status enable',
        'set inspection-mode proxy',
        'set ssl-ssh-profile "certificate-inspection"',
        f'set webfilter-profile "{webfilter_profile}"',
        'set logtraffic all',
        f'set comments "Tech: {username}; {ticket_no}"',
        'next',
        'end'
    ]

    return commands

# Create Web Publish Firewall Policy
def new_webpublish_policy_automation(policy_no, vm_name, dst_int, webfilter_profile, username, ticket_no):

    commands = [
        'config firewall policy',
        f'edit {policy_no}',
        f'set name "{vm_name}-Publish"',
        'set srcintf "Uplink"',
        f'set dstintf "{dst_int}"',
        'set action accept',
        'set srcaddr "IRAN-IP-Addreses"',
        f'set dstaddr "{vm_name}-443" "{vm_name}-80"',
        'set schedule "always"',
        'set service "7001" "Web_Default"',
        'set utm-status enable',
        'set inspection-mode proxy',
        'set ssl-ssh-profile "certificate-inspection"',
        f'set webfilter-profile "{webfilter_profile}"',
        'set ips-sensor "Automation_WindowsBased"',
        'set logtraffic all',
        f'set comments "Tech: {username}; {ticket_no}"',
        'next',
        'end'
    ]

    return commands

# Create New Firewall Policy
def new_fw_policy(policy_no, policy_name, src_int, dst_int, src_addr_list, dst_addr_list, service_list, username, ticket_no):

    source_addresses = ''
    for address in src_addr_list:
        source_addresses += f"{address} "

    destination_addresses = ''
    for address in dst_addr_list:
        destination_addresses += f"{address} "

    services = ''
    for service in service_list:
        services += f"{service} "

    commands = [
        'config firewall policy',
        f'edit {policy_no}',
        f'set name "{policy_name}"',
        f'set srcintf "{src_int}"',
        f'set dstintf "{dst_int}"',
        'set action accept',
        f'set srcaddr {source_addresses}',
        f'set dstaddr {destination_addresses}',
        'set schedule "always"',
        f'set service {services}',
        'set logtraffic all',
        f'set comments "Tech: {username}; {ticket_no}"',
        'next',
        'end'
    ]

    return commands

# Create New SNAT Policy
def new_snat_policy(policy_no, policy_name, src_int, dst_int, src_addr_list, dst_addr_list, service_list, natpool_name, username, ticket_no):

    source_addresses = ''
    for address in src_addr_list:
        source_addresses += f"{address} "

    destination_addresses = ''
    for address in dst_addr_list:
        destination_addresses += f"{address} "

    services = ''
    for service in service_list:
        services += f"{service} "

    commands = [
        'config firewall policy',
        f'edit {policy_no}',
        f'set name "{policy_name}"',
        f'set srcintf "{src_int}"',
        f'set dstintf "{dst_int}"',
        'set action accept',
        f'set srcaddr {source_addresses}',
        f'set dstaddr {destination_addresses}',
        'set schedule "always"',
        f'set service {services}',
        'set logtraffic all',
        'set nat enable',
        'set ippool enable',
        f'set poolname "{natpool_name}"',
        f'set comments "Tech: {username}; {ticket_no}"',
        'next',
        'end'
    ]

    return commands

# Delete a Firewall Policy
def del_fwpolicy(policy_no):

    commands = [
        'config firewall policy',
        f'delete {policy_no}',
        'end'
    ]

    return commands

# Delete a Virtual Server
def del_vserver(verver_name):

    commands = [
        'config firewall vip',
        f'delete {verver_name}',
        'end'
    ]

    return commands

# Delete a Virtual IP
def del_vip(vip_name):

    commands = [
        'config firewall vip',
        f'delete {vip_name}',
        'end'
    ]

    return commands

# Delete a Firewall Address
def del_address(address_name):

    commands = [
        'config firewall address',
        f'delete {address_name}',
        'end'
    ]

    return commands

# Delete a WebFilter Profile (Includes URLFilter)
def del_webfilter_profile(profile_name):

    commands = [
        'config webfilter profile',
        f'delete {profile_name}',
        'end'
    ]

    return commands

# Delete a User Group
def del_group(group_name):

    commands = [
        'config user group',
        f'delete {group_name}',
        'end'
    ]

    return commands






#  Writes the Error in a text file
def custom_error_logger2(error, log_file_path):

    with open(f"{log_file_path}", "a") as text_file:
      text_file.write(f"\n{'#' * 90}\nThe Following Error Occurred:\n{error}\n{'#' * 90}\n")

    print(f"\n{'#' * 90}\nThe Following Error Occurred:\n{error}\n{'#' * 90}\n")

################## Fortigate #################
##############################################




# Folder Creator
def create_folder(folder_path, folder_name=""):

    # Get today's date in the Jalali calendar
    today_date_jalali = date.today().strftime("%Y-%m-%d")

    # Create a folder with today's date as its name
    if folder_name == "":
        folder_full_name = f"{today_date_jalali}"
    else:
        folder_full_name = f"{folder_name}_{today_date_jalali}"

    # Specify the path where you want to create the folder
    folder_full_path = os.path.join(folder_path, folder_full_name)

    # Create the folder
    try:
        os.mkdir(folder_full_path)
        print(f"Folder '{folder_full_name}' created successfully at '{folder_full_path}'")
    except FileExistsError:
        print(f"Folder '{folder_full_name}' already exists at '{folder_full_path}'")
    except Exception as e:
        print(f"An error occurred: {e}")


# Email Sender
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

def email_sender(username, password, email_receivers, email_cc, subject, direction, html_body, mail_server='mail.abramad.com'):

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



# Date and Time Converter from +3:00 to +3:30
import datetime
import pytz
import jdatetime

def convert_miladi_to_shamsi(miladi_date_str, time_str):
    # Define the format for input date and time
    miladi_format = "%Y-%m-%d %H:%M:%S"

    # Combine date and time strings into a single datetime string
    miladi_datetime_str = f"{miladi_date_str} {time_str}"

    # Parse the datetime string into a datetime object
    miladi_datetime = datetime.datetime.strptime(miladi_datetime_str, miladi_format)

    # Define the +3:00 timezone
    timezone_3 = pytz.timezone('Etc/GMT-3')

    # Localize the datetime object to the +3:00 timezone
    localized_datetime = timezone_3.localize(miladi_datetime)

    # Convert the localized datetime to the +3:30 timezone
    timezone_330 = pytz.timezone('Asia/Tehran')
    converted_datetime = localized_datetime.astimezone(timezone_330)

    # Extract the date part for Shamsi conversion
    converted_date = converted_datetime.date()

    # Convert the Gregorian date to Shamsi date
    shamsi_date = jdatetime.date.fromgregorian(date=converted_date)

    # Format the Shamsi date and time to desired output format
    shamsi_date_str = shamsi_date.strftime("%Y-%m-%d")
    time_str_330 = converted_datetime.strftime("%H:%M:%S")

    return shamsi_date_str, time_str_330

# Pinbar Finder
def is_pin_bar(candle):
    open_price = candle['open']
    close_price = candle['close']
    high_price = candle['high']
    low_price = candle['low']

    body_length = abs(close_price - open_price)
    upper_wick = high_price - max(open_price, close_price)
    lower_wick = min(open_price, close_price) - low_price
    candle_length = high_price - low_price

    # Avoid division by zero
    if candle_length == 0 or body_length == 0:
        return False

    # Define the pin bar conditions
    body_to_candle_ratio = body_length / candle_length
    wick_to_body_ratio = max(upper_wick, lower_wick) / body_length
    value_at_65_percent = low_price + 0.65 * (high_price - low_price)

    # Check if the body is in the upper half of the candle
    body_upper_than_65_percent = open_price >= value_at_65_percent and close_price >= value_at_65_percent

    # Check if it matches a pin bar, body_upper_than_center_condition conditions
    is_pin_bar = body_to_candle_ratio < 0.3 and wick_to_body_ratio > 2.0
    body_is_upper_than_65_percent = body_upper_than_65_percent

    return is_pin_bar and body_is_upper_than_65_percent


# MT5, Perfect Pin Bar Finder
def is_perfect_pin_bar(candle):
    open_price = candle['open']
    close_price = candle['close']
    high_price = candle['high']
    low_price = candle['low']

    body_length = abs(close_price - open_price)
    upper_wick = high_price - max(open_price, close_price)
    lower_wick = min(open_price, close_price) - low_price
    candle_length = high_price - low_price

    # Avoid division by zero
    if candle_length == 0 or body_length == 0:
        return False

    # Define the pin bar conditions
    body_to_candle_ratio = body_length / candle_length
    wick_to_body_ratio = max(upper_wick, lower_wick) / body_length

    # Check if the body is in the upper half of the candle
    body_upper_than_center_condition = (open_price + close_price) / 2 > (high_price + low_price) / 2

    # Check for perfect pin bar (no upper wick)
    perfect_pin_bar_condition = upper_wick == 0

    # Check if it matches a pin bar, body_upper_than_center_condition conditions
    is_pin_bar = body_to_candle_ratio < 0.3 and wick_to_body_ratio > 2.0
    body_is_upper_than_center = body_upper_than_center_condition
    is_perfect_pin_bar = perfect_pin_bar_condition

    return is_pin_bar and body_is_upper_than_center and is_perfect_pin_bar

# MT5, Hammer Finder
def is_hammer(candle):
    open_price = candle['open']
    close_price = candle['close']
    high_price = candle['high']
    low_price = candle['low']

    body_length = abs(close_price - open_price)
    upper_wick = high_price - max(open_price, close_price)
    lower_wick = min(open_price, close_price) - low_price
    candle_length = high_price - low_price

    # Avoid division by zero
    if candle_length == 0 or body_length == 0:
        return False

    # Define the hammer conditions
    body_to_candle_ratio = body_length / candle_length
    wick_to_body_ratio = max(upper_wick, lower_wick) / body_length
    value_at_35_percent = low_price + 0.35 * (high_price - low_price)

    # Check if the body is in the upper half of the candle
    body_lower_than_35_percent = open_price <= value_at_35_percent and close_price <= value_at_35_percent

    # Check if it matches a hammer, body_lower_than_center_condition conditions
    is_hammer = body_to_candle_ratio < 0.3 and wick_to_body_ratio > 2.0
    body_is_lower_than_35_percent = body_lower_than_35_percent

    return is_hammer and body_is_lower_than_35_percent

# MT5, Perfect Hammer Finder
def is_perfect_hammer(candle):
    open_price = candle['open']
    close_price = candle['close']
    high_price = candle['high']
    low_price = candle['low']

    body_length = abs(close_price - open_price)
    upper_wick = high_price - max(open_price, close_price)
    lower_wick = min(open_price, close_price) - low_price
    candle_length = high_price - low_price

    # Avoid division by zero
    if candle_length == 0 or body_length == 0:
        return False

    # Define the hammer conditions
    body_to_candle_ratio = body_length / candle_length
    wick_to_body_ratio = max(upper_wick, lower_wick) / body_length

    # Check if the body is in the lower half of the candle
    body_lower_than_center_condition = (open_price + close_price) / 2 < (high_price + low_price) / 2

    # Check for perfect hammer (no lower wick)
    perfect_hammer_condition = lower_wick == 0

    # Check if it matches a hammer, body_lower_than_center_condition conditions
    is_hammer = body_to_candle_ratio < 0.3 and wick_to_body_ratio > 2.0
    body_is_lower_than_center = body_lower_than_center_condition
    is_perfect_hammer = perfect_hammer_condition

    return is_hammer and body_is_lower_than_center and is_perfect_hammer

# MT5, Bullish Engulfing Finder 1x
def is_bullish_engulfing_1x(candle1, candle2):
    """
    Determines if the second candle is a bullish engulfing pattern.

    Parameters:
    candle1 (dict): Dictionary containing 'open', 'close', 'high', 'low' for the first candle.
    candle2 (dict): Dictionary containing 'open', 'close', 'high', 'low' for the second candle.

    Returns:
    bool: True if the second candle is a bullish engulfing pattern, False otherwise.
    """
    # Check if the first candle is bearish (open > close)
    is_candle1_bearish = candle1['open'] > candle1['close']
    # Check if the second candle is bullish (open < close)
    is_candle2_bullish = candle2['open'] < candle2['close']
    # Check if the body of the second candle engulfs the body of the first candle
    is_body_engulfing = candle2['open'] < candle1['close'] and candle2['close'] > candle1['open']

    return is_candle1_bearish and is_candle2_bullish and is_body_engulfing

# MT5, Bullish Engulfing Finder 2x
def is_bullish_engulfing_2x(candle1, candle2, candle3):

    # Check if the first candle is bearish (open > close)
    is_candle1_bearish = candle1['open'] > candle1['close']
    # Check if the second candle is bearish (open > close)
    is_candle2_bearish = candle2['open'] > candle2['close']
    # Check if the third candle is bullish (open < close)
    is_candle3_bullish = candle3['open'] < candle3['close']
    # Check if the body of the third candle engulfs the body of the two previous candles
    is_body_engulfing = candle3['open'] < candle1['close'] and candle3['open'] < candle2['close'] and candle3['close'] > candle1['open'] and candle3['close'] > candle2['open']

    return is_candle1_bearish and is_candle2_bearish and is_candle3_bullish and is_body_engulfing

# MT5, Bullish Engulfing Finder 3x
def is_bullish_engulfing_3x(candle1, candle2, candle3, candle4):

    # Check if the first candle is bearish (open > close)
    is_candle1_bearish = candle1['open'] > candle1['close']
    # Check if the second candle is bearish (open > close)
    is_candle2_bearish = candle2['open'] > candle2['close']
    # Check if the third candle is bearish (open > close)
    is_candle3_bearish = candle3['open'] > candle3['close']
    # Check if the third candle is bullish (open < close)
    is_candle4_bullish = candle4['open'] < candle4['close']
    # Check if the body of the third candle engulfs the body of the previous candles
    is_body_engulfing = candle4['open'] < candle1['close'] and candle4['open'] < candle2['close'] and candle4['open'] < candle3['close'] and candle4['close'] > candle1['open'] and candle4['close'] > candle2['open'] and candle4['close'] > candle3['open']

    return is_candle1_bearish and is_candle2_bearish and is_candle3_bearish and is_candle4_bullish and is_body_engulfing

# MT5, Bearish Engulfing Finder 1x
def is_bearish_engulfing_1x(candle1, candle2):
    """
    Determines if the second candle is a bearish engulfing pattern.

    Parameters:
    candle1 (dict): Dictionary containing 'open', 'close', 'high', 'low' for the first candle.
    candle2 (dict): Dictionary containing 'open', 'close', 'high', 'low' for the second candle.

    Returns:
    bool: True if the second candle is a bearish engulfing pattern, False otherwise.
    """
    # Check if the first candle is bullish (open < close)
    is_candle1_bullish = candle1['open'] < candle1['close']
    # Check if the second candle is bearish (open > close)
    is_candle2_bearish = candle2['open'] > candle2['close']
    # Check if the body of the second candle engulfs the body of the first candle
    is_body_engulfing = candle2['open'] > candle1['close'] and candle2['close'] < candle1['open']

    return is_candle1_bullish and is_candle2_bearish and is_body_engulfing

# MT5, Bearish Engulfing Finder 2x
def is_bearish_engulfing_2x(candle1, candle2, candle3):

    # Check if the first candle is bullish (open < close)
    is_candle1_bullish = candle1['open'] < candle1['close']
    # Check if the second candle is bullish (open < close)
    is_candle2_bullish = candle2['open'] < candle2['close']
    # Check if the third candle is bearish (open > close)
    is_candle3_bearish = candle3['open'] > candle3['close']
    # Check if the body of the third candle engulfs the body of the previous candle
    is_body_engulfing = candle3['open'] > candle1['close'] and candle3['open'] > candle2['close'] and candle3['close'] < candle1['open'] and candle3['close'] < candle2['open']

    return is_candle1_bullish and is_candle2_bullish and is_candle3_bearish and is_body_engulfing

# MT5, Bearish Engulfing Finder 3x
def is_bearish_engulfing_3x(candle1, candle2, candle3, candle4):

    # Check if the first candle is bullish (open < close)
    is_candle1_bullish = candle1['open'] < candle1['close']
    # Check if the second candle is bullish (open < close)
    is_candle2_bullish = candle2['open'] < candle2['close']
    # Check if the third candle is bullish (open < close)
    is_candle3_bullish = candle3['open'] < candle3['close']
    # Check if the third candle is bearish (open > close)
    is_candle4_bearish = candle4['open'] > candle4['close']
    # Check if the body of the forth candle engulfs the body of the previous candles
    is_body_engulfing = candle4['open'] > candle1['close'] and candle4['open'] > candle2['close'] and candle4['open'] > candle3['close'] and candle4['close'] < candle1['open'] and candle4['close'] < candle2['open'] and candle4['close'] < candle3['open']

    return is_candle1_bullish and is_candle2_bullish and is_candle3_bullish and is_candle4_bearish and is_body_engulfing

# MT5, Marubozu Finder
def is_marubozu_test(candle, tolerance=0.001):
    """
    Determine if a candlestick is a Marubozu.

    Parameters:
    open_price (float): The opening price of the candlestick.
    high_price (float): The highest price of the candlestick.
    low_price (float): The lowest price of the candlestick.
    close_price (float): The closing price of the candlestick.
    tolerance (float): The allowable difference for considering the shadows negligible.

    Returns:
    bool: True if the candlestick is a Marubozu, False otherwise.
    """
    open_price = candle['open']
    close_price = candle['close']
    high_price = candle['high']
    low_price = candle['low']

    # Calculate the size of the upper and lower shadows
    upper_shadow = high_price - max(open_price, close_price)
    lower_shadow = min(open_price, close_price) - low_price

    # Check if the shadows are within the tolerance
    if upper_shadow <= tolerance and lower_shadow <= tolerance:
        return True
    return False


def is_marubozu(candle):
    open_price = candle['open']
    close_price = candle['close']
    high_price = candle['high']
    low_price = candle['low']

    upper_wick = high_price - max(open_price, close_price)
    lower_wick = min(open_price, close_price) - low_price
    body_length = abs(close_price - open_price)
    wicks_sum = upper_wick + lower_wick

    wick_to_body_ratio = (round((wicks_sum / body_length), 2) * 100)

    if wick_to_body_ratio <= 20:
        return True
    else:
        return False

import socket
def is_resolvable(fqdn):
    try:
        # Attempt to resolve the FQDN to an IP address
        ip_address = socket.gethostbyname(fqdn)
        return True
    except socket.gaierror as e:
        # Handle the error if the FQDN cannot be resolved
        return False


def find_duplicates(major_list):
    # Step 1: Create an empty set to keep track of elements we've seen
    seen = set()

    # Optional: Create a set to keep track of duplicates if we want to know what they are
    duplicates = set()

    # Step 2: Iterate over each sublist in the major list
    for sublist in major_list:
        # Step 3: Check if the sublist has at least one element to avoid IndexError
        if sublist:
            # Get the first item of the sublist
            node_name = sublist[0]
            node_id = sublist[1]
            #print(node_name + ': ' + str(node_id))

            # Step 4: Check if the first item is already in the 'seen' set
            if node_name in seen:
                # If it is, it's a duplicate, so add it to the duplicates set
                duplicates.add(f"{node_name}, {node_id}")
            else:
                # If it's not, add it to the 'seen' set
                seen.add(node_name)

    # Step 5: Check if we found any duplicates
    # Return True if the duplicates set has any elements, otherwise False
    return len(duplicates) > 0, duplicates



def days_between_persian_dates(persian_date_str):
    # Parse the input Persian date string
    persian_year, persian_month, persian_day = map(int, persian_date_str.split('/'))

    # Create a jdatetime date object from the input date
    input_date = jdatetime.date(persian_year, persian_month, persian_day)

    # Get today's date in Persian calendar
    today_date = jdatetime.date.today()

    # Calculate the difference in days
    delta = (today_date - input_date).days
    return delta

reci = "y@abramad.com"
cc = "x@abramad.com"
hostname = socket.gethostname()

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


import jdatetime
from datetime import datetime

def miladi_to_shamsi_date_converter(miladi_date):
    # Given date in "DD/Mon/YY" format
    # Parse the date string to a Python datetime object
    gregorian_date = datetime.strptime(miladi_date, "%d/%b/%y")

    # Convert the Gregorian date to Shamsi (Jalali) date
    shamsi_date = jdatetime.date.fromgregorian(date=gregorian_date)

    return shamsi_date



import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header

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
        send_anonymous_email(from_email, 'abramadsysops@abramad.com', 'sina.z@abramad.com',
                             f"email_sender Function Error in running All_VMs_Info.py",
                             f"Error Occurred:<br><b>{err}<br></b> Agent: All_VMs_Info.py",
                             'ltr')



def zabbix_node_adder(hosts_dict, template_list, host_group_list, tag_list):

    try:
        #  host_dict involves key values, that the values are a list consisting of 3 indexes ['Host Name', 'IP Address', 'Description']
        template_ids = {}
        host_group_ids = {}

        # Connect to Zabbix API
        zapi = ZabbixAPI(url)
        zapi.login(username, password)

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

    except Exception as err:
        print(f"zabbix_node_adder Function Error: {err}")
        traceback.print_exc()
        send_anonymous_email(zabbix_server, default_receivers, default_cc,
                             f"zabbix_node_adder Function Error in running Zabbix_Add_vCenter_ICMP_Fully_Automated.py",
                             f"Error Occurred:<br><b>{err}<br>{traceback.print_exc()}</b> Agent: Zabbix_Add_vCenter_ICMP_Fully_Automated.py",
                             'ltr')


# Function Definition
import secrets
import string
def generate_password(length=15):
    if length < 4:
        raise ValueError("Password length must be at least 4 to include all required character types.")

    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = "!@#$%^&*()-_=+"

    # Ensure at least one character from each category
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(symbols)
    ]

    # Fill the rest of the password length with a mix of all characters
    all_chars = lowercase + uppercase + digits + symbols
    password += [secrets.choice(all_chars) for _ in range(length - 4)]

    # Shuffle the result to avoid predictable patterns
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)

import subprocess
import sys
def run_command(command, capture_output=True, check=True, text=True, shell=False):
    try:
        result = subprocess.run(
            command,
            shell=shell,
            check=check,
            capture_output=capture_output,
            text=text,
        )
        return result.stdout if capture_output else None
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(e.cmd) if isinstance(e.cmd, list) else e.cmd}")
        print(e.output)
        sys.exit(1)

"""
# Example usage
subnet_info = calculate_subnet_info('172.27.27.0/29')

subnet_ip = subnet_info['subnet']
broadcast_ip = subnet_info['broadcast_address']
usable_ips = subnet_info['usable_ips']
"""

######################## Example Usage #########################

################################################################
############### Step 1: Creating New Interface #################

#create_interface_commands = sinzi.new_interface(customer_name, gateway_address, vlan_id, username, ticket_no)
#create_interface_config = ssh_to_fg1100.send_config_set(create_interface_commands)
#sinzi.check_successful_execution(create_interface_config, "Create Interface", "1", customer_name, log_path)


################################################################
############### Step 2: Creating New Addresses #################

#create_address_commands = sinzi.new_address_custom_32(first_server_name, first_server_ip)
#create_address_config = ssh_to_fg1100.send_config_set(create_address_commands)
#sinzi.check_successful_execution(create_address_config, "Create Address", "2", customer_name, log_path)


################################################################
############ Step 3: Creating New Virtual Server ###############

# Virtual Server for SSL Offload 443-80
#create_vserver_commands = sinzi.new_vserver_mer_443(f"MER-{customer_name}", ticket_no, public_ip, usable_ips[0])
#create_vserver_config = ssh_to_fg1100.send_config_set(create_vserver_commands)
#sinzi.check_successful_execution(create_vserver_config, "Create Virtual Server for SSL Offload 443-80", "3.1", customer_name, log_path)

# Virtual Server for HTTP Redirection 80-80
#create_vserver_commands = sinzi.new_vserver_mer_80(f"MER-{customer_name}", ticket_no, public_ip, usable_ips[0])
#create_vserver_config = ssh_to_fg1100.send_config_set(create_vserver_commands)
#sinzi.check_successful_execution(create_vserver_config, "Create Virtual Server for HTTP Redirection 80-80", "3.2", customer_name, log_path)


# Virtual Server
#create_vserver_commands = sinzi.new_vserver(f"MER-{customer_name}-1433", ticket_no, "tcp", public_ip, "1433", usable_ips[0], "1433")
#create_vserver_config = ssh_to_fg1100.send_config_set(create_vserver_commands)
#sinzi.check_successful_execution(create_vserver_config, "Create Virtual Server", "3.3", customer_name, log_path)



################################################################
########### Step 4: Creating New Web Filter Policy #############

# Getting full configuration to take out last URLFilter entry ID
#webfilter_full_config_commands = ['config webfilter urlfilter', 'show full-configuration', 'end']
#webfilter_full_config_output = ssh_to_fg1100.send_config_set(webfilter_full_config_commands)
#urlfilter_table_id = sinzi.find_last_urlfilter_policy_no(webfilter_full_config_output)

# Creating WebFilter URLFilter Table
#create_webfilter_urlfilter_commands = sinzi.new_webfilter_urlfilter_config(urlfilter_table_id, f"{first_server_name}-URL-Filter-Table",url)
#create_webfilter_urlfilter_config = ssh_to_fg1100.send_config_set(create_webfilter_urlfilter_commands)
#sinzi.check_successful_execution(create_webfilter_urlfilter_config, "Create WebFilter > URLFilter", "4.1", customer_name, log_path)

# Creating WebFilter Profile
#create_webfilter_profile_commands = sinzi.new_webfilter_profile_config(f"{customer_name}.abramad.cloud", f"MER-{customer_name}", urlfilter_table_id, ticket_no)
#create_webfilter_profile_config = ssh_to_fg1100.send_config_set(create_webfilter_profile_commands)
#sinzi.check_successful_execution(create_webfilter_profile_config, "Create WebFilter > Profile", "4.2", customer_name, log_path)



################################################################
############### Step 5: Creating User Groups ###################

# Creating 3 required User Groups for further SSL VPN Authentication
#create_usergroup_commands = sinzi.new_ldap_user_group_cloud_local(customer_name)
#create_usergroup_config = ssh_to_fg1100.send_config_set(create_usergroup_commands)
#sinzi.check_successful_execution(create_usergroup_config, "Create 3 User Groups {Deploy, Support, Members}", "5", customer_name, log_path)



################################################################
################ Step Y: Creating Virtual IP ###################

# Creating New Virtual IP
#create_vip_commands = sinzi.new_vip(f"MER-{customer_name}", public_ip, usable_ips[0])
#create_vip_config = ssh_to_fg1100.send_config_set(create_vip_commands)
#sinzi.check_successful_execution(create_vip_config, "Create Virtual IP", "Y", customer_name, log_path)



################################################################
################# Step K: Creating NAT Pool ####################

# Creating New NAT Pool
#create_natpool_commands = sinzi.new_natpool(customer_name, public_ip)
#create_natpool_config = ssh_to_fg1100.send_config_set(create_natpool_commands)
#sinzi.check_successful_execution(create_natpool_config, "Create NAT Pool", "K", customer_name, log_path)




################################################################
################# Step 6: Creating Policies ####################

# Getting full  firewall policy configuration to take out last Firewall Policy ID
#fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
#fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
#firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

# Getting full interface configuration to take out Interface Name via vlan No
#interface_full_config_commands = ['config system interface', 'show', 'end']
#interface_full_config_output = ssh_to_fg1100.send_config_set(interface_full_config_commands)
#interface_name = sinzi.find_interface_name_by_vlan_id(vlan_id, interface_full_config_output)

# Creating Web Publish Firewall Policy
#create_webpublish_policy_commands = sinzi.new_webpublish_policy_rahkaran(firewall_policy_no, f'MER-{customer_name}', interface_name, url, username, ticket_no)
#create_webpublish_policy_config = ssh_to_fg1100.send_config_set(create_webpublish_policy_commands)
#sinzi.check_successful_execution(create_webpublish_policy_config, "Create Web Publish Policy Config", "6.1", customer_name, log_path)

# Creating SSL VPN Firewall Policy
#create_sslvpn_policy_commands = sinzi.new_sslvpn_policy(firewall_policy_no, customer_name, interface_name, username, ticket_no)
#create_sslvpn_policy_config = ssh_to_fg1100.send_config_set(create_sslvpn_policy_commands)
#sinzi.check_successful_execution(create_sslvpn_policy_config, "Create SSL-VPN Policy Config", "6.2", customer_name, log_path)




################################################################
######### Step 7: Append Created Addresses to groups ###########

#append_group_commands = sinzi.append_addresses_to_group("MER-Customers", [f"{first_server_name}-{first_server_ip}"])
#append_group_config = ssh_to_fg1100.send_config_set(append_group_commands)
#sinzi.check_successful_execution(append_group_config, f"Append Address '{first_server_name}-{first_server_ip}' to Group 'MER-Customers'", "7", customer_name, log_path)

