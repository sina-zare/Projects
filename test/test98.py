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

username = 'sina.z@abramad.com'
passphrase = "S@Bw00fer20936744"


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
me_vms = [vm for vm in me_vm_view.view if (vm.name.lower().startswith("me-")) or (vm.name.lower().startswith("ast-"))]
sorted_vms = sorted(me_vms, key=lambda vm: vm.name.lower())

with open("C:\\Temp\\vms.txt", 'r') as file:
    lst = []
    for i in file:
        lst.append(i.strip('\n'))

fnl_lst = []
# Pruning VM list
for vm in sorted_vms:
    for k in lst:
        if vm.name == k:

            vm_ip = ""
            if vm.guest is not None:
                for nic in vm.guest.net:
                    if nic.ipConfig is not None:
                        for ip in nic.ipConfig.ipAddress:
                            if not ip.ipAddress.startswith('169.254') and not ip.ipAddress.startswith(
                                    'fe80'):
                                vm_ip = ip.ipAddress

            fnl_lst.append([k, vm_ip])
            continue


for j in fnl_lst:
    print(j)

