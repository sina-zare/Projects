try:
    import sys
    sys.path.append(r'E:\IaaC') # to use sinzi
    import sinzi
    from netmiko import Netmiko
    from stdiomask import getpass
    import time
    import os
    import re
    from jdatetime import date, datetime


    # Log Path
    today_date_jalali = date.today().strftime("%Y-%m-%d")
    current_time = (str(datetime.now())[11:19]).replace(":", "-")
    log_path = f"E:\\IaaC\\Block_IPs\\Logs\\{today_date_jalali}"
    full_log_path = f"{log_path}\\{current_time}-BlockIP-Log.txt"
    os.system('cls' if os.name == 'nt' else 'clear')


    # Ensure log directory exists, create if it doesn't
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    # Taking IPs from file
    with open("IP_List.txt", "r") as file:
        ips_to_block_list = [ip.strip("\n") for ip in file.readlines()]

    # Check if IPs are more than 600
    if len(ips_to_block_list) > 600:
        with open(f"{log_path}\\{current_time}-FG1100-BlockIP-Log.txt", "a") as text_file:
            text_file.write(
                f"\n{'#' * 90}\nError, IP_List.txt can at most have 600 entries.\nThere are now {len(ips_to_block_list)}\n{'#' * 90}\n")
        sys.exit()

    fg_devices = {
        #'ME-FW200.Abramad.Com': ['172.17.249.97', '2354', '374', '373'],
        #'ME-FW1100.Abramad.Com': ['172.17.242.254', '2345', '1484', '1485']
        #'ME-FW600A.Abramad.Com': ['172.17.249.99', '2354', '74']
        'SG-FW600.SGCloud.Local': ['192.168.175.18', '2354', '195']
        }



    # Show Sinzi Logo
    sinzi.sinzi_logo()


    # Data Validation
    for ip in ips_to_block_list:
        if not "/" in ip:
            print(f"\nError, No Subnet Mask for {ip}")
            with open(f"{log_path}\\{current_time}-BlockIP-Log.txt", "a") as text_file:
                text_file.write(
                    f"\n{'#' * 90}\nError, No Subnet Mask for {ip}\n{'#' * 90}\n")
            sys.exit()


    # Credentials
    print("Fortigate Credentials)\n")
    username = str(input("Username: ").strip())
    password = getpass("Password Without 2FA: ")



    for device in fg_devices:

        # Taking OTP
        full_password = password + input("2FA: ")
        os.system('cls' if os.name == 'nt' else 'clear')

        # Connecting to FG
        fortigate_fw = {
            'device_type': 'fortinet',
            'host': fg_devices[device][0],
            'username': username,
            'password': full_password,
            'port': fg_devices[device][1]
        }

        # Connecting to Device and Changing VDOM
        try:
            sinzi.print_with_delay(f"{'#' * 10} Connecting to the {device} <{fg_devices[device][0]}> {'#' * 10}")
            ssh_to_device = Netmiko(**fortigate_fw)
            print(ssh_to_device.find_prompt())
            sinzi.print_with_delay(f"{'#' * 10} Connected {'#' * 10}")
            with open(f"{full_log_path}", "a") as text_file:
                text_file.write(f"\n{'#' * 90}\nConnected to {fg_devices[device][0]}\n{'#' * 90}\n")
            time.sleep(2)
            os.system('cls' if os.name == 'nt' else 'clear')

        except Exception as e:
            sinzi.custom_error_logger2(e, f"{log_path}\\{current_time}-BlockIP-Log.txt")
            sys.exit()

        # Changing vdom
        change_vdom_commands = ['config vdom', 'edit root']
        change_vdom_output = ssh_to_device.send_config_set(change_vdom_commands)

        # Getting all firewall groups to take out last BlackListIPs
        fw_full_groups_commands = ['config firewall addrgrp', 'show', 'end']
        fw_full_groups_output = ssh_to_device.send_config_set(fw_full_groups_commands)

        # Taking Last BlackListIPs group name
        # Find all occurrences of "BlackIPs" followed by a number using regex
        matches = re.findall(r"BlackListIPs(\d+)", fw_full_groups_output)

        # Taking All "BlackListIPSX" Group names for later to add them to policy source
        group_name_pattern = r'BlackListIPs\d*'

        '''
        # Use re.findall to find all occurrences of the pattern in the string
        black_ips_list = re.findall(group_name_pattern, fw_full_groups_output)
        src_or_dst_addresses = ''
        for src_addr in black_ips_list:
            src_or_dst_addresses += f'"{src_addr}" '
        '''

        # Get the maximum number from the matches
        latest_number = max([int(match) for match in matches])
        latest_number_plus_one = str(int(latest_number) + 1)

        # Getting number of Last BlackListIPs's members
        fw_last_blacklistips_commands = ['config firewall addrgrp', f'edit "BlackListIPs{latest_number}"','show', 'end']
        fw_last_blacklistips_output = ssh_to_device.send_config_set(fw_last_blacklistips_commands)
        number_of_members = int(((fw_last_blacklistips_output.count('"') / 2) - 1))


        #print(f"fw_full_groups_output:\n {fw_full_groups_output}\n\n\n\n")
        #print(f"src_or_dst_addresses: {src_or_dst_addresses}\n")
        #print(f"latest_number: {latest_number}\n")
        #print(f"latest_number_plus_one: {latest_number_plus_one}\n")
        #print(f"number_of_members: {number_of_members}\n")

        # Main Functionality

        # Address Creation
        for ip in ips_to_block_list:
            # Create Address Based on file
            create_address_commands = sinzi.new_address(ip, "ip", ip, "6")
            create_address_config = ssh_to_device.send_config_set(create_address_commands)
            sinzi.check_successful_execution_g(create_address_config, "Create Address", "1)", ip, full_log_path)

        # check if new group is needed or we can append the same group
        if (600 - (number_of_members + len(ips_to_block_list))) < 0:
            print("\nNew Group Needs to be Created.\n")
            # Additional IPs
            overflow = 600 - (number_of_members + len(ips_to_block_list))
            # New List Creation for storing additional IPs
            ips_to_block_list_redundant = []
            # Storing Additional IPs in New List
            for additional_ip in ips_to_block_list[overflow:]:
                ips_to_block_list_redundant.append(additional_ip)
            # Shrinking Original List
            ips_to_block_list = ips_to_block_list[:overflow]

            # Appending Addresses to Old BlackListIPs Group
            append_group_commands = sinzi.append_addresses_to_group(f"BlackListIPs{latest_number}", ips_to_block_list, "6")
            append_group_config = ssh_to_device.send_config_set(append_group_commands)
            sinzi.check_successful_execution_g(append_group_config, f"Append {len(ips_to_block_list)} IPs to Old Group", "2)",f"BlackListIPs{latest_number}", full_log_path)


            # Create new group
            create_group_commands = ['config firewall addrgrp', f'edit "BlackListIPs{latest_number_plus_one}"','set color 6', 'end']
            create_group_config = ssh_to_device.send_config_set(create_group_commands)
            sinzi.check_successful_execution_g(create_group_config, "Create New Group", "3)",f"BlackListIPs{latest_number_plus_one}", full_log_path)

            # Group Appending
            append_group_commands = sinzi.append_addresses_to_group(f"BlackListIPs{latest_number_plus_one}", ips_to_block_list_redundant, "6")
            append_group_config = ssh_to_device.send_config_set(append_group_commands)
            sinzi.check_successful_execution_g(append_group_config, f"Append {len(ips_to_block_list_redundant)} IPs to New Group", "4)", f"BlackListIPs{latest_number_plus_one}", full_log_path)

        else:
            print("\nNo New Group Needed.\n")
            # Appending Addresses to Old BlackListIPs Group
            append_group_commands = sinzi.append_addresses_to_group(f"BlackListIPs{latest_number}", ips_to_block_list, "6")
            append_group_config = ssh_to_device.send_config_set(append_group_commands)
            sinzi.check_successful_execution_g(append_group_config, f"Append {len(ips_to_block_list)} IPs to Old Group", "2)", f"BlackListIPs{latest_number}", full_log_path)


        if device == "ME-FW600A.Abramad.Com":

            # Use re.findall to find all occurrences of the pattern in the string
            black_ips_list = re.findall(group_name_pattern, fw_full_groups_output)
            src_or_dst_addresses = ''
            for src_addr in black_ips_list:
                src_or_dst_addresses += f'"{src_addr}" '

            # Appending source & destination to policies
            appending_src_to_policy_commands = ['config firewall policy', f'edit {fg_devices[device][2]}', f'set srcaddr {src_or_dst_addresses}', 'end']
            appending_src_to_policy_config = ssh_to_device.send_config_set(appending_src_to_policy_commands)
            sinzi.check_successful_execution_g(append_group_config, "Append src to policy", "FNL", f"Policy No {fg_devices[device][2]}", full_log_path)

        elif device == "SG-FW600.SGCloud.Local":

            # Use re.findall to find all occurrences of the pattern in the string
            black_ips_list = re.findall(group_name_pattern, fw_full_groups_output)
            src_or_dst_addresses = ''
            for src_addr in black_ips_list:
                src_or_dst_addresses += f'"{src_addr}" '

            # Appending source & destination to policies
            appending_src_to_policy_commands = ['config firewall policy', f'edit {fg_devices[device][2]}', f'set srcaddr {src_or_dst_addresses}', 'end']
            appending_src_to_policy_config = ssh_to_device.send_config_set(appending_src_to_policy_commands)
            sinzi.check_successful_execution_g(append_group_config, "Append src to policy", "FNL", f"Policy No {fg_devices[device][2]}", full_log_path)

        else:

            # Use re.findall to find all occurrences of the pattern in the string
            black_ips_list = re.findall(group_name_pattern, fw_full_groups_output)
            src_or_dst_addresses = ''
            for src_addr in black_ips_list:
                src_or_dst_addresses += f'"{src_addr}" '

            # Appending source & destination to policies
            appending_src_to_policy_commands = ['config firewall policy', f'edit {fg_devices[device][2]}', f'set srcaddr {src_or_dst_addresses}', 'end']
            appending_src_to_policy_config = ssh_to_device.send_config_set(appending_src_to_policy_commands)
            sinzi.check_successful_execution_g(append_group_config, "Append src to policy", "*",  f"Policy No {fg_devices[device][2]}", full_log_path)

            appending_dst_to_policy_commands = ['config firewall policy', f'edit {fg_devices[device][3]}', f'set dstaddr {src_or_dst_addresses}', 'end']
            appending_dst_to_policy_config = ssh_to_device.send_config_set(appending_dst_to_policy_commands)
            sinzi.check_successful_execution_g(append_group_config, "Append dst to policy", "*", f"Policy No {fg_devices[device][3]}", full_log_path)

            #os.system('cls' if os.name == 'nt' else 'clear')

        with open(f"{full_log_path}", "a") as text_file:
            text_file.write(f"\n\n\n")
        print(f"\nIPs in {device} Blocked Successfully!")


    input("\nPress Anything to Exit.")

except Exception as e:
    sinzi.custom_error_logger2(e, f"{log_path}\\{current_time}-BlockIP-Log.txt")
    print(e)
    time.sleep(10)
    sys.exit()