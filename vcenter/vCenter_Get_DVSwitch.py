from pyvim.connect import SmartConnect, Disconnect
from cryptography.fernet import Fernet
from pyVmomi import vim
import time
import ssl
import sys
import os

# Bypass SSL certificate validation (for lab/test environments)
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE


def get_dvs_portgroups(content):
    """
    Retrieve all distributed virtual switches (DVS) and their port groups.
    """
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.DistributedVirtualSwitch], True
    )
    dvs_list = container.view
    container.Destroy()

    for dvs in dvs_list:
        print(f"Distributed Virtual Switch: {dvs.name}")
        for portgroup in dvs.portgroup:
            vlan_config = portgroup.config.defaultPortConfig.vlan
            if isinstance(vlan_config, vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec):
                vlan_id = vlan_config.vlanId
            else:
                vlan_id = "Unknown/None"
            print(f"  Port Group: {portgroup.name}, VLAN ID: {vlan_id}")


def decryptor(enc_env_var, key_env_var):
    try:
        # Check if Env Variables are Null
        if os.environ.get(enc_env_var) == None or os.environ.get(key_env_var) == None:
            print("No Env Found or You need to Run the script as Administrator")
            time.sleep(10)
            sys.exit()

        # Load the key
        key = os.environ.get(key_env_var)
        encryption_key = Fernet(key)
        encrypted_password = (os.environ.get(enc_env_var)).encode()
        # Decrypt Data
        decrypted_password = encryption_key.decrypt(encrypted_password.decode())

        #print(f"Decryped Text: {decrypted_password}")
        return decrypted_password.decode()

    except Exception as e:
        print("Error in decryptor Function.")
        print("An error occurred:", e)
        time.sleep(10)


username = 'sysops-svc@abramad.com'
password = decryptor('sysops-svc_enc', 'sysops-svc_key')
vcenter_host = "me-vc01.abramad.com"


# Connect to vCenter
si = SmartConnect(host=vcenter_host, user=username, pwd=password, sslContext=context)
try:
    content = si.RetrieveContent()
    get_dvs_portgroups(content)
finally:
    Disconnect(si)


