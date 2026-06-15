import sys
import time
import sinzi
from netmiko import Netmiko
from stdiomask import getpass
from csv import DictReader
import os
from jdatetime import date

# Take Data from CSV File
with open("New-MER-Customer-Network.csv") as csv_file:
    mer_customer_network = DictReader(csv_file)

    for customer_data in mer_customer_network:
        customer_data_dict = customer_data

# Variable Definition

customer_name = customer_data_dict["Customer_Name"]
network_subnet = customer_data_dict["Network_Subnet"]
vlan_id = customer_data_dict["VLAN_ID"]
ticket_no = customer_data_dict["Ticket_No"]
public_ip = customer_data_dict["Public_IP"]
product = customer_data_dict["Product"]
type = customer_data_dict["Type"]
today_date_jalali = date.today().strftime("%Y-%m-%d")
url_rahkaran = f"{customer_name}-r.abramad.cloud"
url_rahkaran_tose = f"{customer_name}-t.abramad.cloud"
url_automation = f"{customer_name}-a.abramad.cloud"
url_sahamfasl = f"{customer_name}-f.abramad.cloud"
url_bi = f"{customer_name}-b.abramad.cloud"

# Calculating IP Data
subnet_data = sinzi.calculate_subnet_info(network_subnet)
gateway_address = subnet_data["gateway_address"] + network_subnet[-3:]
usable_ips = subnet_data["usable_ips"]

# Show Sinzi Logo
sinzi.sinzi_logo()

# Create Folder for storing Logs
sinzi.create_folder("E:\\Logs")
log_path = f"E:\\Logs\\{today_date_jalali}"
os.system('cls' if os.name == 'nt' else 'clear')

# Data Validation for Customer_Name
if len(customer_name) > 10:
    print(f"\nError, Customer Name is longer than 10 characters --> {customer_name}!")
    with open(f"{log_path}\\{customer_name}-Network-Logs.txt", "a") as text_file:
        text_file.write(
            f"\n{'#' * 90}\n0) Customer Name is longer than 10 characters --> {customer_name}!\n{'#' * 90}\n")
    sys.exit()

# Credentials
#username = "sina.z"
#password = sinzi.decrypt(os.environ.get('spass'), 9999)
#full_password = password + input("2FA: ")
print("Fortigate Credentials)\n")
username = str(input("Username: ").strip())
password = getpass("Password: ")
os.system('cls' if os.name == 'nt' else 'clear')

# Connecting to FG
fortigate_fw = {
    'device_type': 'fortinet',
    'host': '172.17.242.254',
    'username': username,
    'password': password,
    'port': 2345
}

########################################################
#### Step 0: Connecting to Device and Changing VDOM ####
try:
    sinzi.print_with_delay(f"{'#' * 10} Connecting to the Device {'#' * 10}")
    ssh_to_fg1100 = Netmiko(**fortigate_fw)
    print(ssh_to_fg1100.find_prompt())
    sinzi.print_with_delay(f"{'#' * 10} Connected {'#' * 10}")
    time.sleep(2)
    os.system('cls' if os.name == 'nt' else 'clear')

except Exception as e:
    sinzi.custom_error_logger(e, f"{log_path}\\{customer_name}")
    sys.exit()

# Changing vdom
change_vdom_commands = ['config vdom', 'edit root']
change_vdom_output = ssh_to_fg1100.send_config_set(change_vdom_commands)

# Choosing Product
# Rahkaran
if product.upper() == "MER":

    if type.lower() == 'single-r':

        # App and DB Server
        first_server_name = f"MER-{customer_name}"
        first_server_ip = usable_ips[0]

        ################################################################
        ############### Step 1: Creating New Interface #################

        create_interface_commands = sinzi.new_interface(customer_name, gateway_address, vlan_id, username, ticket_no)
        create_interface_config = ssh_to_fg1100.send_config_set(create_interface_commands)
        sinzi.check_successful_execution(create_interface_config, "Create Interface", "1", customer_name, log_path)


        ################################################################
        ############### Step 2: Creating New Addresses #################

        create_address_commands = sinzi.new_address_custom_32(first_server_name, first_server_ip)
        create_address_config = ssh_to_fg1100.send_config_set(create_address_commands)
        sinzi.check_successful_execution(create_address_config, "Create Address", "2", customer_name, log_path)


        ################################################################
        ############ Step 3: Creating New Virtual Server ###############

        # Virtual Server for SSL Offload 443-80
        create_vserver_commands = sinzi.new_vserver_mer_443(first_server_name, url_rahkaran, public_ip, first_server_ip)
        create_vserver_config = ssh_to_fg1100.send_config_set(create_vserver_commands)
        sinzi.check_successful_execution(create_vserver_config, "Create Virtual Server for SSL Offload 443-80", "3.1", customer_name, log_path)

        # Virtual Server for HTTP Redirection 80-80
        create_vserver_commands = sinzi.new_vserver_mer_80(first_server_name, url_rahkaran, public_ip, first_server_ip)
        create_vserver_config = ssh_to_fg1100.send_config_set(create_vserver_commands)
        sinzi.check_successful_execution(create_vserver_config, "Create Virtual Server for HTTP Redirection 80-80", "3.2", customer_name, log_path)


        ################################################################
        ########### Step 4: Creating New Web Filter Policy #############

        # Getting full configuration to take out last URLFilter entry ID
        webfilter_full_config_commands = ['config webfilter urlfilter', 'show full-configuration', 'end']
        webfilter_full_config_output = ssh_to_fg1100.send_config_set(webfilter_full_config_commands)
        urlfilter_table_id = sinzi.find_last_urlfilter_policy_no(webfilter_full_config_output)

        # Creating WebFilter URLFilter Table
        create_webfilter_urlfilter_commands = sinzi.new_webfilter_urlfilter_config(urlfilter_table_id, f"{first_server_name}-URL-Filter-Table", url_rahkaran)
        create_webfilter_urlfilter_config = ssh_to_fg1100.send_config_set(create_webfilter_urlfilter_commands)
        sinzi.check_successful_execution(create_webfilter_urlfilter_config, "Create WebFilter > URLFilter", "4.1", customer_name, log_path)

        # Creating WebFilter Profile
        create_webfilter_profile_commands = sinzi.new_webfilter_profile_config(url_rahkaran, first_server_name, urlfilter_table_id, ticket_no)
        create_webfilter_profile_config = ssh_to_fg1100.send_config_set(create_webfilter_profile_commands)
        sinzi.check_successful_execution(create_webfilter_profile_config, "Create WebFilter > Profile", "4.2", customer_name, log_path)


        ################################################################
        ############### Step 5: Creating User Groups ###################

        # Creating 3 required User Groups for further SSL VPN Authentication
        create_usergroup_commands = sinzi.new_ldap_user_group_cloud_local(customer_name)
        create_usergroup_config = ssh_to_fg1100.send_config_set(create_usergroup_commands)
        sinzi.check_successful_execution(create_usergroup_config, "Create 3 User Groups {Deploy, Support, Members}", "5", customer_name, log_path)


        ################################################################
        ################# Step 6: Creating Policies ####################

        # Getting full firewall policy configuration to take out last Firewall Policy ID for Web Publish Policy creation
        fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
        fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
        firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

        # Getting full interface configuration to take out Interface Name via vlan No
        interface_full_config_commands = ['config system interface', 'show', 'end']
        interface_full_config_output = ssh_to_fg1100.send_config_set(interface_full_config_commands)
        interface_name = sinzi.find_interface_name_by_vlan_id(vlan_id, interface_full_config_output)

        # Creating Web Publish Firewall Policy
        create_webpublish_policy_commands = sinzi.new_webpublish_policy_rahkaran(firewall_policy_no, first_server_name, interface_name, url_rahkaran, username, ticket_no)
        create_webpublish_policy_config = ssh_to_fg1100.send_config_set(create_webpublish_policy_commands)
        sinzi.check_successful_execution(create_webpublish_policy_config, "Create Web Publish Policy Config", "6.1", customer_name, log_path)

        # Getting full  firewall policy configuration to take out last Firewall Policy ID for SSL VPN Policy creation
        fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
        fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
        firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

        # Creating SSL VPN Firewall Policy
        create_sslvpn_policy_commands = sinzi.new_sslvpn_policy(firewall_policy_no, customer_name, interface_name, username, ticket_no)
        create_sslvpn_policy_config = ssh_to_fg1100.send_config_set(create_sslvpn_policy_commands)
        sinzi.check_successful_execution(create_sslvpn_policy_config, "Create SSL-VPN Policy Config", "6.2", customer_name, log_path)


        ################################################################
        ######### Step 7: Append Created Addresses to groups ###########

        append_group_commands = sinzi.append_addresses_to_group("MER-Customers", [f"{first_server_name}-{first_server_ip}"])
        append_group_config = ssh_to_fg1100.send_config_set(append_group_commands)
        sinzi.check_successful_execution(append_group_config, f"Append Address '{first_server_name}-{first_server_ip}' to Group 'MER-Customers'", "7", customer_name, log_path)

    elif type.lower() == 'single-t':

        # Tose'e Server
        first_server_name = f"MER-{customer_name}-T"
        first_server_ip = usable_ips[0]


        ################################################################
        ############### Step 1: Creating New Interface #################

        create_interface_commands = sinzi.new_interface(customer_name, gateway_address, vlan_id, username, ticket_no)
        create_interface_config = ssh_to_fg1100.send_config_set(create_interface_commands)
        sinzi.check_successful_execution(create_interface_config, "Create Interface", "1", customer_name, log_path)

        ################################################################
        ############### Step 2: Creating New Addresses #################

        create_address_commands = sinzi.new_address_custom_32(first_server_name, first_server_ip)
        create_address_config = ssh_to_fg1100.send_config_set(create_address_commands)
        sinzi.check_successful_execution(create_address_config, "Create Address", "2", customer_name, log_path)

        ################################################################
        ############ Step 3: Creating New Virtual Server ###############

        # Virtual Server for SSL Offload 443-80
        create_vserver_commands = sinzi.new_vserver_mer_443(first_server_name, url_rahkaran_tose, public_ip, first_server_ip)
        create_vserver_config = ssh_to_fg1100.send_config_set(create_vserver_commands)
        sinzi.check_successful_execution(create_vserver_config, "Create Virtual Server for SSL Offload 443-80", "3.1", customer_name, log_path)

        # Virtual Server for HTTP Redirection 80-80
        create_vserver_commands = sinzi.new_vserver_mer_80(first_server_name, url_rahkaran_tose, public_ip, first_server_ip)
        create_vserver_config = ssh_to_fg1100.send_config_set(create_vserver_commands)
        sinzi.check_successful_execution(create_vserver_config, "Create Virtual Server for HTTP Redirection 80-80", "3.2", customer_name, log_path)

        ################################################################
        ########### Step 4: Creating New Web Filter Policy #############

        # Getting full configuration to take out last URLFilter entry ID
        webfilter_full_config_commands = ['config webfilter urlfilter', 'show full-configuration', 'end']
        webfilter_full_config_output = ssh_to_fg1100.send_config_set(webfilter_full_config_commands)
        urlfilter_table_id = sinzi.find_last_urlfilter_policy_no(webfilter_full_config_output)

        # Creating WebFilter URLFilter Table
        create_webfilter_urlfilter_commands = sinzi.new_webfilter_urlfilter_config(urlfilter_table_id,f"{first_server_name}-URL-Filter-Table", url_rahkaran_tose)
        create_webfilter_urlfilter_config = ssh_to_fg1100.send_config_set(create_webfilter_urlfilter_commands)
        sinzi.check_successful_execution(create_webfilter_urlfilter_config, "Create WebFilter > URLFilter", "4.1", customer_name, log_path)

        # Creating WebFilter Profile
        create_webfilter_profile_commands = sinzi.new_webfilter_profile_config(url_rahkaran_tose, first_server_name, urlfilter_table_id, ticket_no)
        create_webfilter_profile_config = ssh_to_fg1100.send_config_set(create_webfilter_profile_commands)
        sinzi.check_successful_execution(create_webfilter_profile_config, "Create WebFilter > Profile", "4.2", customer_name, log_path)

        ################################################################
        ############### Step 5: Creating User Groups ###################

        # Creating 3 required User Groups for further SSL VPN Authentication
        create_usergroup_commands = sinzi.new_ldap_user_group_cloud_local(customer_name)
        create_usergroup_config = ssh_to_fg1100.send_config_set(create_usergroup_commands)
        sinzi.check_successful_execution(create_usergroup_config, "Create 3 User Groups {Deploy, Support, Members}", "5", customer_name, log_path)

        ################################################################
        ################# Step 6: Creating Policies ####################

        # Getting full  firewall policy configuration to take out last Firewall Policy ID for Web Publish Policy creation
        fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
        fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
        firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

        # Getting full interface configuration to take out Interface Name via vlan No
        interface_full_config_commands = ['config system interface', 'show', 'end']
        interface_full_config_output = ssh_to_fg1100.send_config_set(interface_full_config_commands)
        interface_name = sinzi.find_interface_name_by_vlan_id(vlan_id, interface_full_config_output)

        # Creating Web Publish Firewall Policy
        create_webpublish_policy_commands = sinzi.new_webpublish_policy_rahkaran(firewall_policy_no, first_server_name, interface_name, url_rahkaran_tose, username, ticket_no)
        create_webpublish_policy_config = ssh_to_fg1100.send_config_set(create_webpublish_policy_commands)
        sinzi.check_successful_execution(create_webpublish_policy_config, "Create Web Publish Policy Config", "6.1", customer_name, log_path)

        # Getting full  firewall policy configuration to take out last Firewall Policy ID for SSL VPN Policy creation
        fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
        fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
        firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

        # Creating SSL VPN Firewall Policy
        create_sslvpn_policy_commands = sinzi.new_sslvpn_policy(firewall_policy_no, customer_name, interface_name, username, ticket_no)
        create_sslvpn_policy_config = ssh_to_fg1100.send_config_set(create_sslvpn_policy_commands)
        sinzi.check_successful_execution(create_sslvpn_policy_config, "Create SSL-VPN Policy Config", "6.2", customer_name, log_path)


        ################################################################
        ######### Step 7: Append Created Addresses to groups ###########

        append_group_commands = sinzi.append_addresses_to_group("MER-Customers", [f"{first_server_name}-{first_server_ip}"])
        append_group_config = ssh_to_fg1100.send_config_set(append_group_commands)
        sinzi.check_successful_execution(append_group_config, f"Append Address '{first_server_name}-{first_server_ip}' to Group 'MER-Customers'", "7", customer_name, log_path)

    elif type.lower() == 'dual':

        # App Server
        first_server_name = f"MER-{customer_name}-A1"
        first_server_ip = usable_ips[0]

        # DB Server
        second_server_name = f"MER-{customer_name}-DB"
        second_server_ip = usable_ips[1]

        ################################################################
        ############### Step 1: Creating New Interface #################

        create_interface_commands = sinzi.new_interface(customer_name, gateway_address, vlan_id, username, ticket_no)
        create_interface_config = ssh_to_fg1100.send_config_set(create_interface_commands)
        sinzi.check_successful_execution(create_interface_config, "Create Interface", "1", customer_name, log_path)

        ################################################################
        ############### Step 2: Creating New Addresses #################

        # First Address
        create_address_commands = sinzi.new_address_custom_32(first_server_name, first_server_ip)
        create_address_config = ssh_to_fg1100.send_config_set(create_address_commands)
        sinzi.check_successful_execution(create_address_config, f"Create Address of {first_server_name}", "2.1", customer_name, log_path)

        # Second Address
        create_address_commands = sinzi.new_address_custom_32(second_server_name, second_server_ip)
        create_address_config = ssh_to_fg1100.send_config_set(create_address_commands)
        sinzi.check_successful_execution(create_address_config, f"Create Address of {second_server_name}", "2.2", customer_name, log_path)

        ################################################################
        ############ Step 3: Creating New Virtual Server ###############

        # Virtual Server for SSL Offload 443-80
        create_vserver_commands = sinzi.new_vserver_mer_443(first_server_name, url_rahkaran, public_ip, first_server_ip)
        create_vserver_config = ssh_to_fg1100.send_config_set(create_vserver_commands)
        sinzi.check_successful_execution(create_vserver_config, "Create Virtual Server for SSL Offload 443-80", "3.1", customer_name, log_path)

        # Virtual Server for HTTP Redirection 80-80
        create_vserver_commands = sinzi.new_vserver_mer_80(first_server_name, url_rahkaran, public_ip, first_server_ip)
        create_vserver_config = ssh_to_fg1100.send_config_set(create_vserver_commands)
        sinzi.check_successful_execution(create_vserver_config, "Create Virtual Server for HTTP Redirection 80-80", "3.2", customer_name, log_path)

        ################################################################
        ########### Step 4: Creating New Web Filter Policy #############

        # Getting full configuration to take out last URLFilter entry ID
        webfilter_full_config_commands = ['config webfilter urlfilter', 'show full-configuration', 'end']
        webfilter_full_config_output = ssh_to_fg1100.send_config_set(webfilter_full_config_commands)
        urlfilter_table_id = sinzi.find_last_urlfilter_policy_no(webfilter_full_config_output)

        # Creating WebFilter URLFilter Table
        create_webfilter_urlfilter_commands = sinzi.new_webfilter_urlfilter_config(urlfilter_table_id,f"{first_server_name}-URL-Filter-Table", url_rahkaran)
        create_webfilter_urlfilter_config = ssh_to_fg1100.send_config_set(create_webfilter_urlfilter_commands)
        sinzi.check_successful_execution(create_webfilter_urlfilter_config, "Create WebFilter > URLFilter", "4.1", customer_name, log_path)

        # Creating WebFilter Profile
        create_webfilter_profile_commands = sinzi.new_webfilter_profile_config(url_rahkaran, first_server_name, urlfilter_table_id, ticket_no)
        create_webfilter_profile_config = ssh_to_fg1100.send_config_set(create_webfilter_profile_commands)
        sinzi.check_successful_execution(create_webfilter_profile_config, "Create WebFilter > Profile", "4.2", customer_name, log_path)

        ################################################################
        ############### Step 5: Creating User Groups ###################

        # Creating 3 required User Groups for further SSL VPN Authentication
        create_usergroup_commands = sinzi.new_ldap_user_group_cloud_local(customer_name)
        create_usergroup_config = ssh_to_fg1100.send_config_set(create_usergroup_commands)
        sinzi.check_successful_execution(create_usergroup_config, "Create 3 User Groups {Deploy, Support, Members}","5", customer_name, log_path)

        ################################################################
        ################# Step 6: Creating Policies ####################

        # Getting full  firewall policy configuration to take out last Firewall Policy ID for Web Publish Policy creation
        fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
        fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
        firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

        # Getting full interface configuration to take out Interface Name via vlan No
        interface_full_config_commands = ['config system interface', 'show', 'end']
        interface_full_config_output = ssh_to_fg1100.send_config_set(interface_full_config_commands)
        interface_name = sinzi.find_interface_name_by_vlan_id(vlan_id, interface_full_config_output)

        # Creating Web Publish Firewall Policy
        create_webpublish_policy_commands = sinzi.new_webpublish_policy_rahkaran(firewall_policy_no, first_server_name, interface_name, url_rahkaran, username, ticket_no)
        create_webpublish_policy_config = ssh_to_fg1100.send_config_set(create_webpublish_policy_commands)
        sinzi.check_successful_execution(create_webpublish_policy_config, "Create Web Publish Policy Config", "6.1", customer_name, log_path)

        # Getting full  firewall policy configuration to take out last Firewall Policy ID for SSL VPN Policy creation
        fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
        fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
        firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

        # Creating SSL VPN Firewall Policy
        create_sslvpn_policy_commands = sinzi.new_sslvpn_policy(firewall_policy_no, customer_name, interface_name, username, ticket_no)
        create_sslvpn_policy_config = ssh_to_fg1100.send_config_set(create_sslvpn_policy_commands)
        sinzi.check_successful_execution(create_sslvpn_policy_config, "Create SSL-VPN Policy Config", "6.2", customer_name, log_path)


        ################################################################
        ######### Step 7: Append Created Addresses to groups ###########

        append_group_commands = sinzi.append_addresses_to_group("MER-Customers", [f"{first_server_name}-{first_server_ip}", f"{second_server_name}-{second_server_ip}"])
        append_group_config = ssh_to_fg1100.send_config_set(append_group_commands)
        sinzi.check_successful_execution(append_group_config, f"Append Addresses to Group 'MER-Customers'","7", customer_name, log_path)


    elif type.lower() == 'multi':

        # App1 Server
        first_server_name = f"MER-{customer_name}-A1"
        first_server_ip = usable_ips[0]

        # App2 Server
        second_server_name = f"MER-{customer_name}-A2"
        second_server_ip = usable_ips[1]

        # DB Server
        third_server_name = f"MER-{customer_name}-DB"
        third_server_ip = usable_ips[2]

        # LB Server
        forth_server_name = f"MER-{customer_name}-LB"
        forth_server_ip = usable_ips[3]

        ################################################################
        ############### Step 1: Creating New Interface #################

        create_interface_commands = sinzi.new_interface(customer_name, gateway_address, vlan_id, username, ticket_no)
        create_interface_config = ssh_to_fg1100.send_config_set(create_interface_commands)
        sinzi.check_successful_execution(create_interface_config, "Create Interface", "1", customer_name, log_path)

        ################################################################
        ############### Step 2: Creating New Addresses #################

        # First Address
        create_address_commands = sinzi.new_address_custom_32(first_server_name, first_server_ip)
        create_address_config = ssh_to_fg1100.send_config_set(create_address_commands)
        sinzi.check_successful_execution(create_address_config, f"Create Address of {first_server_name}", "2.1", customer_name, log_path)

        # Second Address
        create_address_commands = sinzi.new_address_custom_32(second_server_name, second_server_ip)
        create_address_config = ssh_to_fg1100.send_config_set(create_address_commands)
        sinzi.check_successful_execution(create_address_config, f"Create Address of {second_server_name}", "2.2", customer_name, log_path)

        # Third Address
        create_address_commands = sinzi.new_address_custom_32(third_server_name, third_server_ip)
        create_address_config = ssh_to_fg1100.send_config_set(create_address_commands)
        sinzi.check_successful_execution(create_address_config, f"Create Address of {third_server_name}", "2.3", customer_name, log_path)

        # Forth Address
        create_address_commands = sinzi.new_address_custom_32(forth_server_name, forth_server_ip)
        create_address_config = ssh_to_fg1100.send_config_set(create_address_commands)
        sinzi.check_successful_execution(create_address_config, f"Create Address of {forth_server_name}", "2.4", customer_name, log_path)

        ################################################################
        ############ Step 3: Creating New Virtual Server ###############

        # Virtual Server for SSL Offload 443-80
        create_vserver_commands = sinzi.new_vserver_mer_443(forth_server_name, url_rahkaran, public_ip, forth_server_ip)
        create_vserver_config = ssh_to_fg1100.send_config_set(create_vserver_commands)
        sinzi.check_successful_execution(create_vserver_config, "Create Virtual Server for SSL Offload 443-80", "3.1", customer_name, log_path)

        # Virtual Server for HTTP Redirection 80-80
        create_vserver_commands = sinzi.new_vserver_mer_80(forth_server_name, url_rahkaran, public_ip, forth_server_ip)
        create_vserver_config = ssh_to_fg1100.send_config_set(create_vserver_commands)
        sinzi.check_successful_execution(create_vserver_config, "Create Virtual Server for HTTP Redirection 80-80", "3.2", customer_name, log_path)

        ################################################################
        ########### Step 4: Creating New Web Filter Policy #############

        # Getting full configuration to take out last URLFilter entry ID
        webfilter_full_config_commands = ['config webfilter urlfilter', 'show full-configuration', 'end']
        webfilter_full_config_output = ssh_to_fg1100.send_config_set(webfilter_full_config_commands)
        urlfilter_table_id = sinzi.find_last_urlfilter_policy_no(webfilter_full_config_output)

        # Creating WebFilter URLFilter Table
        create_webfilter_urlfilter_commands = sinzi.new_webfilter_urlfilter_config(urlfilter_table_id, f"{forth_server_name}-URL-Filter-Table", url_rahkaran)
        create_webfilter_urlfilter_config = ssh_to_fg1100.send_config_set(create_webfilter_urlfilter_commands)
        sinzi.check_successful_execution(create_webfilter_urlfilter_config, "Create WebFilter > URLFilter", "4.1", customer_name, log_path)

        # Creating WebFilter Profile
        create_webfilter_profile_commands = sinzi.new_webfilter_profile_config(url_rahkaran, forth_server_name, urlfilter_table_id, ticket_no)
        create_webfilter_profile_config = ssh_to_fg1100.send_config_set(create_webfilter_profile_commands)
        sinzi.check_successful_execution(create_webfilter_profile_config, "Create WebFilter > Profile", "4.2", customer_name, log_path)

        ################################################################
        ############### Step 5: Creating User Groups ###################

        # Creating 3 required User Groups for further SSL VPN Authentication
        create_usergroup_commands = sinzi.new_ldap_user_group_cloud_local(customer_name)
        create_usergroup_config = ssh_to_fg1100.send_config_set(create_usergroup_commands)
        sinzi.check_successful_execution(create_usergroup_config, "Create 3 User Groups {Deploy, Support, Members}", "5", customer_name, log_path)

        ################################################################
        ################# Step 6: Creating Policies ####################

        # Getting full  firewall policy configuration to take out last Firewall Policy ID for Web Publish Policy creation
        fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
        fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
        firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

        # Getting full interface configuration to take out Interface Name via vlan No
        interface_full_config_commands = ['config system interface', 'show', 'end']
        interface_full_config_output = ssh_to_fg1100.send_config_set(interface_full_config_commands)
        interface_name = sinzi.find_interface_name_by_vlan_id(vlan_id, interface_full_config_output)

        # Creating Web Publish Firewall Policy
        create_webpublish_policy_commands = sinzi.new_webpublish_policy_rahkaran(firewall_policy_no, forth_server_name, interface_name, url_rahkaran, username, ticket_no)
        create_webpublish_policy_config = ssh_to_fg1100.send_config_set(create_webpublish_policy_commands)
        sinzi.check_successful_execution(create_webpublish_policy_config, "Create Web Publish Policy Config", "6.1", customer_name, log_path)

        # Getting full  firewall policy configuration to take out last Firewall Policy ID for SSL VPN Policy creation
        fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
        fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
        firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

        # Creating SSL VPN Firewall Policy
        create_sslvpn_policy_commands = sinzi.new_sslvpn_policy(firewall_policy_no, customer_name, interface_name, username, ticket_no)
        create_sslvpn_policy_config = ssh_to_fg1100.send_config_set(create_sslvpn_policy_commands)
        sinzi.check_successful_execution(create_sslvpn_policy_config, "Create SSL-VPN Policy Config", "6.2", customer_name, log_path)


        ################################################################
        ######### Step 7: Append Created Addresses to groups ###########

        append_group_commands = sinzi.append_addresses_to_group("MER-Customers", [f"{first_server_name}-{first_server_ip}", f"{second_server_name}-{second_server_ip}", f"{third_server_name}-{third_server_ip}", f"{forth_server_name}-{forth_server_ip}"])
        append_group_config = ssh_to_fg1100.send_config_set(append_group_commands)
        sinzi.check_successful_execution(append_group_config, f"Append Addresses to Group 'MER-Customers'", "7", customer_name, log_path)


    else:
        sinzi.custom_error_logger("Wrong Type! it should be one of the following:\nSingle-A\nSingle-R\nSingle-T\nDual\nMulti\nNull", f"{log_path}\\{customer_name}")
        sys.exit()

# Automation
elif product.upper() == "MEA":

    # Automation Server
    first_server_name = f"MEA-{customer_name}"
    first_server_ip = usable_ips[0]

    ################################################################
    ############### Step 1: Creating New Interface #################

    create_interface_commands = sinzi.new_interface(customer_name, gateway_address, vlan_id, username, ticket_no)
    create_interface_config = ssh_to_fg1100.send_config_set(create_interface_commands)
    sinzi.check_successful_execution(create_interface_config, "Create Interface", "1", customer_name, log_path)

    ################################################################
    ############### Step 2: Creating New Addresses #################

    create_address_commands = sinzi.new_address_custom_32(first_server_name, first_server_ip)
    create_address_config = ssh_to_fg1100.send_config_set(create_address_commands)
    sinzi.check_successful_execution(create_address_config, "Create Address", "2", customer_name, log_path)

    ################################################################
    ############ Step 3: Creating New Virtual Server ###############

    # Virtual Server for SSL Offload 443-80
    create_vserver_commands = sinzi.new_vserver_mea_443(first_server_name, url_automation, public_ip, first_server_ip)
    create_vserver_config = ssh_to_fg1100.send_config_set(create_vserver_commands)
    sinzi.check_successful_execution(create_vserver_config, "Create Virtual Server for SSL Offload 443-80", "3.1", customer_name, log_path)

    # Virtual Server for HTTP Redirection 80-80
    create_vserver_commands = sinzi.new_vserver_mea_80(first_server_name, url_automation, public_ip, first_server_ip)
    create_vserver_config = ssh_to_fg1100.send_config_set(create_vserver_commands)
    sinzi.check_successful_execution(create_vserver_config, "Create Virtual Server for HTTP Redirection 80-80","3.2", customer_name, log_path)

    ################################################################
    ########### Step 4: Creating New Web Filter Policy #############

    # Getting full configuration to take out last URLFilter entry ID
    webfilter_full_config_commands = ['config webfilter urlfilter', 'show full-configuration', 'end']
    webfilter_full_config_output = ssh_to_fg1100.send_config_set(webfilter_full_config_commands)
    urlfilter_table_id = sinzi.find_last_urlfilter_policy_no(webfilter_full_config_output)

    # Creating WebFilter URLFilter Table
    create_webfilter_urlfilter_commands = sinzi.new_webfilter_urlfilter_config(urlfilter_table_id, f"{first_server_name}-URL-Filter-Table",url_automation)
    create_webfilter_urlfilter_config = ssh_to_fg1100.send_config_set(create_webfilter_urlfilter_commands)
    sinzi.check_successful_execution(create_webfilter_urlfilter_config, "Create WebFilter > URLFilter", "4.1", customer_name, log_path)

    # Creating WebFilter Profile
    create_webfilter_profile_commands = sinzi.new_webfilter_profile_config(url_automation, first_server_name, urlfilter_table_id, ticket_no)
    create_webfilter_profile_config = ssh_to_fg1100.send_config_set(create_webfilter_profile_commands)
    sinzi.check_successful_execution(create_webfilter_profile_config, "Create WebFilter > Profile", "4.2", customer_name, log_path)

    ################################################################
    ############### Step 5: Creating User Groups ###################

    # Creating 3 required User Groups for further SSL VPN Authentication
    create_usergroup_commands = sinzi.new_ldap_user_group_cloud_local(customer_name)
    create_usergroup_config = ssh_to_fg1100.send_config_set(create_usergroup_commands)
    sinzi.check_successful_execution(create_usergroup_config, "Create 3 User Groups {Deploy, Support, Members}", "5", customer_name, log_path)

    ################################################################
    ################# Step 6: Creating Policies ####################

    # Getting full firewall policy configuration to take out last Firewall Policy ID for Web Publish Policy creation
    fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
    fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
    firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

    # Getting full interface configuration to take out Interface Name via vlan No
    interface_full_config_commands = ['config system interface', 'show', 'end']
    interface_full_config_output = ssh_to_fg1100.send_config_set(interface_full_config_commands)
    interface_name = sinzi.find_interface_name_by_vlan_id(vlan_id, interface_full_config_output)

    # Creating Web Publish Firewall Policy
    create_webpublish_policy_commands = sinzi.new_webpublish_policy_automation(firewall_policy_no, first_server_name, interface_name, url_automation, username, ticket_no)
    create_webpublish_policy_config = ssh_to_fg1100.send_config_set(create_webpublish_policy_commands)
    sinzi.check_successful_execution(create_webpublish_policy_config, "Create Web Publish Policy Config", "6.1", customer_name, log_path)

    # Getting full  firewall policy configuration to take out last Firewall Policy ID for SSL VPN Policy creation
    fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
    fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
    firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

    # Creating SSL VPN Firewall Policy
    create_sslvpn_policy_commands = sinzi.new_sslvpn_policy_limited(firewall_policy_no, customer_name, interface_name, username, ticket_no)
    create_sslvpn_policy_config = ssh_to_fg1100.send_config_set(create_sslvpn_policy_commands)
    sinzi.check_successful_execution(create_sslvpn_policy_config, "Create SSL-VPN Policy Config", "6.2", customer_name, log_path)

    ################################################################
    ######### Step 7: Append Created Addresses to groups ###########

    append_group_commands = sinzi.append_addresses_to_group("MEA-Customers", [f"{first_server_name}-{first_server_ip}"])
    append_group_config = ssh_to_fg1100.send_config_set(append_group_commands)
    sinzi.check_successful_execution(append_group_config, f"Append Address '{first_server_name}-{first_server_ip}' to Group 'MEA-Customers'", "7", customer_name, log_path)

# Business Intelligent
elif product.upper() == "MEB":

    # BI Server
    first_server_name = f"MEB-{customer_name}"
    first_server_ip = usable_ips[0]

    ################################################################
    ############### Step 1: Creating New Interface #################

    create_interface_commands = sinzi.new_interface(customer_name, gateway_address, vlan_id, username, ticket_no)
    create_interface_config = ssh_to_fg1100.send_config_set(create_interface_commands)
    sinzi.check_successful_execution(create_interface_config, "Create Interface", "1", customer_name, log_path)

    ################################################################
    ############### Step 2: Creating New Addresses #################

    create_address_commands = sinzi.new_address_custom_32(first_server_name, first_server_ip)
    create_address_config = ssh_to_fg1100.send_config_set(create_address_commands)
    sinzi.check_successful_execution(create_address_config, "Create Address", "2", customer_name, log_path)

    ################################################################
    ############ Step 3: Creating New Virtual Server ###############

    # Virtual Server for SSL Offload 443-80
    create_vserver_commands = sinzi.new_vserver_mer_443(first_server_name, url_bi, public_ip, first_server_ip)
    create_vserver_config = ssh_to_fg1100.send_config_set(create_vserver_commands)
    sinzi.check_successful_execution(create_vserver_config, "Create Virtual Server for SSL Offload 443-80", "3.1", customer_name, log_path)

    # Virtual Server for HTTP Redirection 80-80
    create_vserver_commands = sinzi.new_vserver_mer_80(first_server_name, url_bi, public_ip, first_server_ip)
    create_vserver_config = ssh_to_fg1100.send_config_set(create_vserver_commands)
    sinzi.check_successful_execution(create_vserver_config, "Create Virtual Server for HTTP Redirection 80-80", "3.2", customer_name, log_path)

    ################################################################
    ########### Step 4: Creating New Web Filter Policy #############

    # Getting full configuration to take out last URLFilter entry ID
    webfilter_full_config_commands = ['config webfilter urlfilter', 'show full-configuration', 'end']
    webfilter_full_config_output = ssh_to_fg1100.send_config_set(webfilter_full_config_commands)
    urlfilter_table_id = sinzi.find_last_urlfilter_policy_no(webfilter_full_config_output)

    # Creating WebFilter URLFilter Table
    create_webfilter_urlfilter_commands = sinzi.new_webfilter_urlfilter_config(urlfilter_table_id, f"{first_server_name}-URL-Filter-Table", url_bi)
    create_webfilter_urlfilter_config = ssh_to_fg1100.send_config_set(create_webfilter_urlfilter_commands)
    sinzi.check_successful_execution(create_webfilter_urlfilter_config, "Create WebFilter > URLFilter", "4.1", customer_name, log_path)

    # Creating WebFilter Profile
    create_webfilter_profile_commands = sinzi.new_webfilter_profile_config(url_bi, first_server_name, urlfilter_table_id, ticket_no)
    create_webfilter_profile_config = ssh_to_fg1100.send_config_set(create_webfilter_profile_commands)
    sinzi.check_successful_execution(create_webfilter_profile_config, "Create WebFilter > Profile", "4.2", customer_name, log_path)

    ################################################################
    ############### Step 5: Creating User Groups ###################

    # Creating 3 required User Groups for further SSL VPN Authentication
    create_usergroup_commands = sinzi.new_ldap_user_group_cloud_local(customer_name)
    create_usergroup_config = ssh_to_fg1100.send_config_set(create_usergroup_commands)
    sinzi.check_successful_execution(create_usergroup_config, "Create 3 User Groups {Deploy, Support, Members}", "5", customer_name, log_path)

    ################################################################
    ################# Step 6: Creating Policies ####################

    # Getting full firewall policy configuration to take out last Firewall Policy ID for Web Publish Policy creation
    fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
    fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
    firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

    # Getting full interface configuration to take out Interface Name via vlan No
    interface_full_config_commands = ['config system interface', 'show', 'end']
    interface_full_config_output = ssh_to_fg1100.send_config_set(interface_full_config_commands)
    interface_name = sinzi.find_interface_name_by_vlan_id(vlan_id, interface_full_config_output)

    # Creating Web Publish Firewall Policy
    create_webpublish_policy_commands = sinzi.new_webpublish_policy_rahkaran(firewall_policy_no, first_server_name, interface_name, url_rahkaran, username, ticket_no)
    create_webpublish_policy_config = ssh_to_fg1100.send_config_set(create_webpublish_policy_commands)
    sinzi.check_successful_execution(create_webpublish_policy_config, "Create Web Publish Policy Config", "6.1", customer_name, log_path)

    # Getting full  firewall policy configuration to take out last Firewall Policy ID for SSL VPN Policy creation
    fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
    fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
    firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

    # Creating SSL VPN Firewall Policy
    create_sslvpn_policy_commands = sinzi.new_sslvpn_policy_limited(firewall_policy_no, customer_name, interface_name, username, ticket_no)
    create_sslvpn_policy_config = ssh_to_fg1100.send_config_set(create_sslvpn_policy_commands)
    sinzi.check_successful_execution(create_sslvpn_policy_config, "Create SSL-VPN Policy Config", "6.2", customer_name, log_path)

    ################################################################
    ######### Step 7: Append Created Addresses to groups ###########

    append_group_commands = sinzi.append_addresses_to_group("MEB-Customers", [f"{first_server_name}-{first_server_ip}"])
    append_group_config = ssh_to_fg1100.send_config_set(append_group_commands)
    sinzi.check_successful_execution(append_group_config,f"Append Address '{first_server_name}-{first_server_ip}' to Group 'MEB-Customers'", "7", customer_name, log_path)

# Saham Fasl
elif product.upper() == "MEF":

    # Saham Fasl Server
    first_server_name = f"MEF-{customer_name}"
    first_server_ip = usable_ips[0]

    ################################################################
    ############### Step 1: Creating New Interface #################

    create_interface_commands = sinzi.new_interface(customer_name, gateway_address, vlan_id, username, ticket_no)
    create_interface_config = ssh_to_fg1100.send_config_set(create_interface_commands)
    sinzi.check_successful_execution(create_interface_config, "Create Interface", "1", customer_name, log_path)

    ################################################################
    ############### Step 2: Creating New Addresses #################

    create_address_commands = sinzi.new_address_custom_32(first_server_name, first_server_ip)
    create_address_config = ssh_to_fg1100.send_config_set(create_address_commands)
    sinzi.check_successful_execution(create_address_config, "Create Address", "2", customer_name, log_path)

    ################################################################
    ############ Step 3: Creating New Virtual Server ###############

    # Virtual Server for SSL Offload 443-80
    create_vserver_commands = sinzi.new_vserver_mer_443(first_server_name, url_sahamfasl, public_ip, first_server_ip)
    create_vserver_config = ssh_to_fg1100.send_config_set(create_vserver_commands)
    sinzi.check_successful_execution(create_vserver_config, "Create Virtual Server for SSL Offload 443-80", "3.1", customer_name, log_path)

    # Virtual Server for HTTP Redirection 80-80
    create_vserver_commands = sinzi.new_vserver_mer_80(first_server_name, url_sahamfasl, public_ip, first_server_ip)
    create_vserver_config = ssh_to_fg1100.send_config_set(create_vserver_commands)
    sinzi.check_successful_execution(create_vserver_config, "Create Virtual Server for HTTP Redirection 80-80", "3.2", customer_name, log_path)

    ################################################################
    ########### Step 4: Creating New Web Filter Policy #############

    # Getting full configuration to take out last URLFilter entry ID
    webfilter_full_config_commands = ['config webfilter urlfilter', 'show full-configuration', 'end']
    webfilter_full_config_output = ssh_to_fg1100.send_config_set(webfilter_full_config_commands)
    urlfilter_table_id = sinzi.find_last_urlfilter_policy_no(webfilter_full_config_output)

    # Creating WebFilter URLFilter Table
    create_webfilter_urlfilter_commands = sinzi.new_webfilter_urlfilter_config(urlfilter_table_id, f"{first_server_name}-URL-Filter-Table", url_sahamfasl)
    create_webfilter_urlfilter_config = ssh_to_fg1100.send_config_set(create_webfilter_urlfilter_commands)
    sinzi.check_successful_execution(create_webfilter_urlfilter_config, "Create WebFilter > URLFilter", "4.1", customer_name, log_path)

    # Creating WebFilter Profile
    create_webfilter_profile_commands = sinzi.new_webfilter_profile_config(url_sahamfasl, first_server_name, urlfilter_table_id, ticket_no)
    create_webfilter_profile_config = ssh_to_fg1100.send_config_set(create_webfilter_profile_commands)
    sinzi.check_successful_execution(create_webfilter_profile_config, "Create WebFilter > Profile", "4.2", customer_name, log_path)

    ################################################################
    ############### Step 5: Creating User Groups ###################

    # Creating 3 required User Groups for further SSL VPN Authentication
    create_usergroup_commands = sinzi.new_ldap_user_group_cloud_local(customer_name)
    create_usergroup_config = ssh_to_fg1100.send_config_set(create_usergroup_commands)
    sinzi.check_successful_execution(create_usergroup_config, "Create 3 User Groups {Deploy, Support, Members}", "5", customer_name, log_path)

    ################################################################
    ################# Step 6: Creating Policies ####################

    # Getting full firewall policy configuration to take out last Firewall Policy ID for Web Publish Policy creation
    fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
    fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
    firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

    # Getting full interface configuration to take out Interface Name via vlan No
    interface_full_config_commands = ['config system interface', 'show', 'end']
    interface_full_config_output = ssh_to_fg1100.send_config_set(interface_full_config_commands)
    interface_name = sinzi.find_interface_name_by_vlan_id(vlan_id, interface_full_config_output)

    # Creating Web Publish Firewall Policy
    create_webpublish_policy_commands = sinzi.new_webpublish_policy_rahkaran(firewall_policy_no, first_server_name, interface_name, url_sahamfasl, username, ticket_no)
    create_webpublish_policy_config = ssh_to_fg1100.send_config_set(create_webpublish_policy_commands)
    sinzi.check_successful_execution(create_webpublish_policy_config, "Create Web Publish Policy Config", "6.1", customer_name, log_path)

    # Getting full  firewall policy configuration to take out last Firewall Policy ID for SSL VPN Policy creation
    fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
    fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
    firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

    # Creating SSL VPN Firewall Policy
    create_sslvpn_policy_commands = sinzi.new_sslvpn_policy_limited(firewall_policy_no, customer_name, interface_name, username, ticket_no)
    create_sslvpn_policy_config = ssh_to_fg1100.send_config_set(create_sslvpn_policy_commands)
    sinzi.check_successful_execution(create_sslvpn_policy_config, "Create SSL-VPN Policy Config", "6.2", customer_name, log_path)

    ################################################################
    ######### Step 7: Append Created Addresses to groups ###########

    append_group_commands = sinzi.append_addresses_to_group("MEF-Customers", [f"{first_server_name}-{first_server_ip}"])
    append_group_config = ssh_to_fg1100.send_config_set(append_group_commands)
    sinzi.check_successful_execution(append_group_config,f"Append Address '{first_server_name}-{first_server_ip}' to Group 'MEF-Customers'", "7", customer_name, log_path)

# Sepidar
elif product.upper() == "MES":

    # Sepidar Server
    first_server_name = f"MES-{customer_name}"
    first_server_ip = usable_ips[0]

    ################################################################
    ############### Step 1: Creating New Interface #################

    create_interface_commands = sinzi.new_interface(customer_name, gateway_address, vlan_id, username, ticket_no)
    create_interface_config = ssh_to_fg1100.send_config_set(create_interface_commands)
    sinzi.check_successful_execution(create_interface_config, "Create Interface", "1", customer_name, log_path)

    ################################################################
    ############### Step 2: Creating New Addresses #################

    create_address_commands = sinzi.new_address_custom_32(first_server_name, first_server_ip)
    create_address_config = ssh_to_fg1100.send_config_set(create_address_commands)
    sinzi.check_successful_execution(create_address_config, "Create Address", "2", customer_name, log_path)

    ################################################################
    ############### Step 3: Creating User Groups ###################

    # Creating 3 required User Groups for further SSL VPN Authentication
    create_usergroup_commands = sinzi.new_ldap_user_group_cloud_local(customer_name)
    create_usergroup_config = ssh_to_fg1100.send_config_set(create_usergroup_commands)
    sinzi.check_successful_execution(create_usergroup_config, "Create 3 User Groups {Deploy, Support, Members}", "3", customer_name, log_path)

    ################################################################
    ################# Step 4: Creating Policies ####################

    # Getting full firewall policy configuration to take out last Firewall Policy ID for Web Publish Policy creation
    fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
    fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
    firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

    # Getting full interface configuration to take out Interface Name via vlan No
    interface_full_config_commands = ['config system interface', 'show', 'end']
    interface_full_config_output = ssh_to_fg1100.send_config_set(interface_full_config_commands)
    interface_name = sinzi.find_interface_name_by_vlan_id(vlan_id, interface_full_config_output)

    # Creating SSL VPN Firewall Policy
    create_sslvpn_policy_commands = sinzi.new_sslvpn_policy_open(firewall_policy_no, customer_name, interface_name, username, ticket_no)
    create_sslvpn_policy_config = ssh_to_fg1100.send_config_set(create_sslvpn_policy_commands)
    sinzi.check_successful_execution(create_sslvpn_policy_config, "Create SSL-VPN Policy Config", "4", customer_name, log_path)

    ################################################################
    ######### Step 5: Append Created Addresses to groups ###########

    append_group_commands = sinzi.append_addresses_to_group("MES-Customers", [f"{first_server_name}-{first_server_ip}"])
    append_group_config = ssh_to_fg1100.send_config_set(append_group_commands)
    sinzi.check_successful_execution(append_group_config, f"Append Address '{first_server_name}-{first_server_ip}' to Group 'MES-Customers'","5", customer_name, log_path)

# Managed IaaS
elif product.upper() == "MEM":

    # MEM Server
    first_server_name = f"MEM-{customer_name}"
    first_server_ip = usable_ips[0]

    ################################################################
    ############### Step 1: Creating New Interface #################

    create_interface_commands = sinzi.new_interface(customer_name, gateway_address, vlan_id, username, ticket_no)
    create_interface_config = ssh_to_fg1100.send_config_set(create_interface_commands)
    sinzi.check_successful_execution(create_interface_config, "Create Interface", "1", customer_name, log_path)

    ################################################################
    ############### Step 2: Creating New Addresses #################

    create_address_commands = sinzi.new_address_custom_32(first_server_name, first_server_ip)
    create_address_config = ssh_to_fg1100.send_config_set(create_address_commands)
    sinzi.check_successful_execution(create_address_config, "Create Address", "2", customer_name, log_path)

    ################################################################
    ############## Step 3: Creating New Virtual IP #################

    # Virtual IP for DNAT Purposes
    create_vip_commands = sinzi.new_vip(first_server_name, public_ip, first_server_ip)
    create_vip_config = ssh_to_fg1100.send_config_set(create_vip_commands)
    sinzi.check_successful_execution(create_vip_config, "Create Virtual IP", "3", customer_name, log_path)

    ################################################################
    ############### Step 4: Creating User Groups ###################

    # Creating 3 required User Groups for further SSL VPN Authentication
    create_usergroup_commands = sinzi.new_ldap_user_group_cloud_local(customer_name)
    create_usergroup_config = ssh_to_fg1100.send_config_set(create_usergroup_commands)
    sinzi.check_successful_execution(create_usergroup_config, "Create 3 User Groups {Deploy, Support, Members}", "4",customer_name, log_path)

    ################################################################
    ################# Step 5: Creating Policies ####################

    # Getting full firewall policy configuration to take out last Firewall Policy ID for Web Publish Policy creation
    fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
    fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
    firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

    # Getting full interface configuration to take out Interface Name via vlan No
    interface_full_config_commands = ['config system interface', 'show', 'end']
    interface_full_config_output = ssh_to_fg1100.send_config_set(interface_full_config_commands)
    interface_name = sinzi.find_interface_name_by_vlan_id(vlan_id, interface_full_config_output)

    # Creating Web Publish Firewall Policy
    create_webpublish_policy_commands = sinzi.new_fw_policy(firewall_policy_no, f"{first_server_name}-Publish", "Uplink", interface_name, ["all"], [f"{first_server_name}-{public_ip}"], ["Web_Default"], username, ticket_no)
    create_webpublish_policy_config = ssh_to_fg1100.send_config_set(create_webpublish_policy_commands)
    sinzi.check_successful_execution(create_webpublish_policy_config, "Create Web Publish Policy Config", "5.1", customer_name, log_path)

    # Getting full firewall policy configuration to take out last Firewall Policy ID for SSL VPN Policy creation
    fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
    fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
    firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

    # Creating SSL VPN Firewall Policy
    create_sslvpn_policy_commands = sinzi.new_sslvpn_policy_open(firewall_policy_no, customer_name, interface_name, username, ticket_no)
    create_sslvpn_policy_config = ssh_to_fg1100.send_config_set(create_sslvpn_policy_commands)
    sinzi.check_successful_execution(create_sslvpn_policy_config, "Create SSL-VPN Policy Config", "5.2", customer_name,log_path)

    ################################################################
    ######### Step 6: Append Created Addresses to groups ###########

    append_group_commands = sinzi.append_addresses_to_group("MEM-Customers", [f"{first_server_name}-{first_server_ip}"])
    append_group_config = ssh_to_fg1100.send_config_set(append_group_commands)
    sinzi.check_successful_execution(append_group_config, f"Append Address '{first_server_name}-{first_server_ip}' to Group 'MEM-Customers'", "6", customer_name, log_path)

# Unmanaged IaaS
elif product.upper() == "MEI":

    # MEI Server
    first_server_name = f"MEI-{customer_name}"
    first_server_ip = usable_ips[0]

    ################################################################
    ############### Step 1: Creating New Interface #################

    create_interface_commands = sinzi.new_interface(customer_name, gateway_address, vlan_id, username, ticket_no)
    create_interface_config = ssh_to_fg1100.send_config_set(create_interface_commands)
    sinzi.check_successful_execution(create_interface_config, "Create Interface", "1", customer_name, log_path)

    ################################################################
    ############### Step 2: Creating New Addresses #################

    create_address_commands = sinzi.new_address_custom_32(first_server_name, first_server_ip)
    create_address_config = ssh_to_fg1100.send_config_set(create_address_commands)
    sinzi.check_successful_execution(create_address_config, "Create Address", "2", customer_name, log_path)

    ################################################################
    ############## Step 3: Creating New Virtual IP #################

    # Virtual IP for DNAT Purposes
    create_vip_commands = sinzi.new_vip(first_server_name, public_ip, first_server_ip)
    create_vip_config = ssh_to_fg1100.send_config_set(create_vip_commands)
    sinzi.check_successful_execution(create_vip_config, "Create Virtual IP", "3", customer_name, log_path)

    ################################################################
    ############### Step 4: Creating New NAT Pool ##################

    # NAT Pool for Internet Access
    create_natpool_commands = sinzi.new_natpool(customer_name, public_ip)
    create_natpool_config = ssh_to_fg1100.send_config_set(create_natpool_commands)
    sinzi.check_successful_execution(create_natpool_config, "Create NAT Pool", "4", customer_name, log_path)

    ################################################################
    ############### Step 5: Creating User Groups ###################

    # Creating 3 required User Groups for further SSL VPN Authentication
    create_usergroup_commands = sinzi.new_ldap_user_group_cloud_local(customer_name)
    create_usergroup_config = ssh_to_fg1100.send_config_set(create_usergroup_commands)
    sinzi.check_successful_execution(create_usergroup_config, "Create 3 User Groups {Deploy, Support, Members}", "5", customer_name, log_path)

    ################################################################
    ################# Step 6: Creating Policies ####################

    # Getting full firewall policy configuration to take out last Firewall Policy ID for Web Publish Policy creation
    fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
    fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
    firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

    # Getting full interface configuration to take out Interface Name via vlan No
    interface_full_config_commands = ['config system interface', 'show', 'end']
    interface_full_config_output = ssh_to_fg1100.send_config_set(interface_full_config_commands)
    interface_name = sinzi.find_interface_name_by_vlan_id(vlan_id, interface_full_config_output)

    # Creating Web Publish Firewall Policy
    create_webpublish_policy_commands = sinzi.new_fw_policy(firewall_policy_no, f"{first_server_name}-Publish", "Uplink", interface_name, ["all"], [f"{first_server_name}-{public_ip}"], ["Web_Default"], username, ticket_no)
    create_webpublish_policy_config = ssh_to_fg1100.send_config_set(create_webpublish_policy_commands)
    sinzi.check_successful_execution(create_webpublish_policy_config, "Create Web Publish Policy Config", "6.1", customer_name, log_path)

    # Getting full firewall policy configuration to take out last Firewall Policy ID for SSL VPN Policy creation
    fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
    fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
    firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

    # Creating SSL VPN Firewall Policy
    create_sslvpn_policy_commands = sinzi.new_sslvpn_policy_open(firewall_policy_no, customer_name, interface_name, username, ticket_no)
    create_sslvpn_policy_config = ssh_to_fg1100.send_config_set(create_sslvpn_policy_commands)
    sinzi.check_successful_execution(create_sslvpn_policy_config, "Create SSL-VPN Policy Config", "6.2", customer_name, log_path)

    # Getting full firewall policy configuration to take out last Firewall Policy ID for SSL VPN Policy creation
    fwpolicy_full_config_commands = ['config firewall policy', 'show', 'end']
    fwpolicy_full_config_output = ssh_to_fg1100.send_config_set(fwpolicy_full_config_commands)
    firewall_policy_no = sinzi.find_last_fwpolicy_no(fwpolicy_full_config_output)

    # Creating Internet Access Policy
    create_internetaccess_policy_commands = sinzi.new_snat_policy(firewall_policy_no, f"{first_server_name}-To-Internet", interface_name, "Uplink", [f"{first_server_name}-{first_server_ip}"], ["all"], ["ALL"], f"{customer_name}-NATPool-{public_ip}", username, ticket_no)
    create_internetaccess_policy_config = ssh_to_fg1100.send_config_set(create_internetaccess_policy_commands)
    sinzi.check_successful_execution(create_internetaccess_policy_config, "Create Web Publish Policy Config", "6.3", customer_name, log_path)

    ################################################################
    ######### Step 7: Append Created Addresses to groups ###########

    append_group_commands = sinzi.append_addresses_to_group("MEI-Customers", [f"{first_server_name}-{first_server_ip}"])
    append_group_config = ssh_to_fg1100.send_config_set(append_group_commands)
    sinzi.check_successful_execution(append_group_config, f"Append Address '{first_server_name}-{first_server_ip}' to Group 'MEI-Customers'", "7", customer_name, log_path)

# Any Wrong Product Value
else:
    sinzi.custom_error_logger("Wrong Product! it should be one of the following:\nMER\nMEA\nMEB\nMEF\nMES\nMEM\nMEI\n", f"{log_path}\\{customer_name}")
    sys.exit()

# Close FG Session
ssh_to_fg1100.disconnect()
input(f"\n\n\n\n{'#' * 20} Press Anything to Exit {'#' * 20}")