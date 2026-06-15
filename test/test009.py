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
    'host': "172.17.249.99",
    'username': username,
    'password': full_password,
    'port': '2354'
}

# Connecting to Device and Changing VDOM

print(f"{'#' * 10} Connecting {'#' * 10}")
ssh_to_device = Netmiko(**fortigate_fw)
print(ssh_to_device.find_prompt())
print(f"{'#' * 10} Connected {'#' * 10}")

# Changing vdom
change_vdom_commands = ['config vdom', 'edit root']
change_vdom_output = ssh_to_device.send_config_set(change_vdom_commands)

lst = []
for i in range(1, 43):
    if i == 1:

        groups_commands = ['config firewall addrgrp', 'edit "BlackListIPs"', 'set member "SinaTest"', 'end']
        groups_output = ssh_to_device.send_config_set(groups_commands)


    else:

        groups_commands = ['config firewall addrgrp', f'edit "BlackListIPs{i}"', 'set member "SinaTest"', 'end']
        groups_output = ssh_to_device.send_config_set(groups_commands)
