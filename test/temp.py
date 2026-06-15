import sys
import sinzi
from netmiko import Netmiko
from stdiomask import getpass
import time
import os
import re
from jdatetime import date, datetime

# Connecting to FG
fortigate_fw = {
    'device_type': 'fortinet',
    'host': '172.17.255.254',
    'username': 'sina.z',
    'password': 'S@Bw00fer20936743'+input("MFA: "),
    'port': '2345'
}

ssh_to_device = Netmiko(**fortigate_fw)
print(ssh_to_device.find_prompt())