import sys
#sys.path.append(r'E:\IaaC') # to use sinzi
#from sinzi import print_with_delay
from netmiko import Netmiko
from stdiomask import getpass
import time
import os
import re
from jdatetime import date, datetime

username = "sina.z"
password = "S@Bw00fer20936744"
full_password = password + input("2FA: ")


# Connecting to FG
fortigate_fw = {
    'device_type': 'fortinet',
    'host': "me-fw200.abramad.com",
    'username': username,
    'password': full_password,
    'port': '2354'
}

# Connecting to Device and Changing VDOM

print(f"{'#' * 10} Connecting to FG600 <172.17.249.99> {'#' * 10}")
ssh_to_device = Netmiko(**fortigate_fw)
print(ssh_to_device.find_prompt())
print(f"{'#' * 10} Connected {'#' * 10}")

# Changing vdom
change_vdom_commands = ['config vdom', 'edit root']
change_vdom_output = ssh_to_device.send_config_set(change_vdom_commands)

lst = []
for i in range(1, 43):
    if i == 1:

        groups_commands = ['config firewall addrgrp', 'edit "BlackListIPs"', 'show', 'end']
        groups_output = ssh_to_device.send_config_set(groups_commands)
        print('\n')
        temp_lst = []
        temp_lst = ((groups_output.split('\n')[8]).strip().split(' '))[2:]
        for i in temp_lst:
            lst.append(i)

    else:

        groups_commands = ['config firewall addrgrp', f'edit "BlackListIPs{i}"', 'show', 'end']
        groups_output = ssh_to_device.send_config_set(groups_commands)
        print('\n')
        temp_lst = []
        temp_lst = ((groups_output.split('\n')[8]).strip().split(' '))[2:]
        for i in temp_lst:
            lst.append(i)

with open("behzad.txt", 'w') as file:
    for j in lst:
        file.write(j + '\n')
        """if j.endswith('/32'):
            file.write(j[:-3] + '\n')
        else:
            file.write(j.strip('"') + '\n')
        """

