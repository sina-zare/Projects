from netmiko import Netmiko
from stdiomask import getpass
import time
import os
import re

from cryptography.fernet import Fernet
def decryptor(enc_env_var, key_env_var):

    # Load the key
    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = (os.environ.get(enc_env_var)).encode()
    # Decrypt Data
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())

    #print(f"Decryped Text: {decrypted_password}")
    return decrypted_password.decode()


fg_user = "behzad.az"
#fg_pass = decryptor("enc_sinaz_pass","key_sinaz_pass")
fg_pass = ''























fg_full_pass = fg_pass # + input("2FA: ")
fg_ips = {
    'ME-FW1100': '172.17.242.254',
    'VNK-FW1800': '192.168.254.3'
}

# Connecting to FG
fortigate_fw = {
    'device_type': 'fortinet',
    'host': fg_ips['VNK-FW1800'],
    'username': fg_user,
    'password': fg_full_pass,
    'port': '2345'
}

ssh_to_device = Netmiko(**fortigate_fw)
print(f'VNK-FW1800\n{ssh_to_device.find_prompt()}\n')

# Changing vdom
change_vdom_commands = ['config vdom', 'edit root']
change_vdom_output = ssh_to_device.send_config_set(change_vdom_commands)

show_all_vips_commands = ['config firewall vip', 'show', 'end']
show_all_vips_output = ssh_to_device.send_config_set(show_all_vips_commands)

#print(show_all_vips_output)

_2024_2025_members = []
_2024_2025_waf_members = []
_2025_2026_members = []
_2025_2026_waf_members = []
show_all_vips_list = show_all_vips_output.splitlines()

current_block = []
inside_block = False

for idx, line in enumerate(show_all_vips_list):
    line = line.strip()

    if line.startswith('edit "'):
        inside_block = True
        current_block = [line]

    elif inside_block:
        current_block.append(line)

        # if not the last block
        if (idx + 1) < len(show_all_vips_list):
            # end of a block

            if line == 'next' and (show_all_vips_list[idx + 1]).strip().startswith('edit "'):
                # Join the collected lines into a full block of text
                block_text = "\n".join(current_block)
                #print(block_text)
                # Check if the block contains the desired SSL certificate
                if 'set ssl-certificate "Abramad-com-2024-2025"' in block_text:

                    if 'set ip 192.168.' in block_text:
                        # Extract the phrase from the 'edit' line at the start of the block
                        edit_match = re.search(r'(?<=edit\s).*', block_text)
                        if edit_match:
                            _2024_2025_waf_members.append(edit_match.group(0))
                    else:
                        # Extract the phrase from the 'edit' line at the start of the block
                        edit_match = re.search(r'(?<=edit\s).*', block_text)
                        if edit_match:
                            _2024_2025_members.append(edit_match.group(0))

                # Reset for the next block
                inside_block = False
                current_block = []

# handling last block of config:
if 'set ssl-certificate "Abramad-com-2024-2025"' in show_all_vips_list[-3]:

    if 'set ip 192.168.' in show_all_vips_list[-8]:
        edit_match = re.search(r'(?<=edit\s).*', show_all_vips_list[-17].strip())
        if edit_match:
            _2024_2025_waf_members.append(edit_match.group(0))
    else:
        edit_match = re.search(r'(?<=edit\s).*', show_all_vips_list[-17].strip())
        if edit_match:
            _2024_2025_members.append(edit_match.group(0))


# Abramad-com-2024-2025

# Abramad.cloud-2025-2026-FullPath

#print('_2024_2025_members:')
#for i in _2024_2025_members:
#    print(i)
#print(len(_2024_2025_members))



current_block = []
inside_block = False

for idx, line in enumerate(show_all_vips_list):
    line = line.strip()

    if line.startswith('edit "'):
        inside_block = True
        current_block = [line]

    elif inside_block:
        current_block.append(line)

        # if not the last block
        if (idx + 1) < len(show_all_vips_list):
            # end of a block

            if line == 'next' and (show_all_vips_list[idx + 1]).strip().startswith('edit "'):
                # Join the collected lines into a full block of text
                block_text = "\n".join(current_block)
                #print(block_text)
                # Check if the block contains the desired SSL certificate
                if 'set ssl-certificate "Abramad.com-2025-2026"' in block_text:

                    if 'set ip 192.168.' in block_text:
                        # Extract the phrase from the 'edit' line at the start of the block
                        edit_match = re.search(r'(?<=edit\s).*', block_text)
                        if edit_match:
                            _2025_2026_waf_members.append(edit_match.group(0))
                    else:
                        # Extract the phrase from the 'edit' line at the start of the block
                        edit_match = re.search(r'(?<=edit\s).*', block_text)
                        if edit_match:
                            _2025_2026_members.append(edit_match.group(0))

                # Reset for the next block
                inside_block = False
                current_block = []

# handling last block of config:
if 'set ssl-certificate "Abramad.com-2025-2026"' in show_all_vips_list[-3]:

    if 'set ip 192.168.' in show_all_vips_list[-8]:
        edit_match = re.search(r'(?<=edit\s).*', show_all_vips_list[-17].strip())
        if edit_match:
            _2025_2026_waf_members.append(edit_match.group(0))
    else:
        edit_match = re.search(r'(?<=edit\s).*', show_all_vips_list[-17].strip())
        if edit_match:
            _2025_2026_members.append(edit_match.group(0))


# 'set ssl-certificate "Abramad.cloud-2024-2025"'

final_cert_name = 'Abramad.com-2025-2026'

for node in _2024_2025_members[:]:
    #if not 'mahya' in node.lower():
    print(f"Working on: {node}")
    # Getting all firewall groups to take out last BlackListIPs
    set_certificate_commands = ['config firewall vip', f'edit {node}', f'set ssl-certificate "{final_cert_name}"', 'end']
    set_certificate_output = ssh_to_device.send_config_set(set_certificate_commands)
    print(f"\t{node} Success.\n")
        #break



#print(f"\n\nCustomers on Old Certificate: {len(_2023_2024_members)}")
#print(f"Customers on New Certificate: {len(_2024_2025_members)}")
print(f"\n\n ---------------------  ")
#print(f"| WAF 2023-2024: {len(_2023_2024_waf_members)}   |")
print(f"| 2025-2026: {len(_2025_2026_members)}        |\n|---------------------|")
#print(f"| WAF 2024-2025: {len(_2024_2025_waf_members)}    |")
print(f"| 2024-2025: {len(_2024_2025_members)}       |")
print(f" ---------------------  ")


print(_2024_2025_members)

