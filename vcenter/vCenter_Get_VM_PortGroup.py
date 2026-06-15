from pyvim.connect import SmartConnect, Disconnect
from cryptography.fernet import Fernet
import time
import sys
import os
from pyVmomi import vim
import ssl

# Bypass SSL certificate validation (for lab/test environments)
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE


def get_vm_portgroup_info(content):
    """
    Retrieve all virtual machines, their NICs' connection statuses,
    connected port groups, and VLAN IDs.
    """
    # Retrieve all Virtual Machines
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.VirtualMachine], True
    )
    vm_list = container.view
    container.Destroy()

    for vm in vm_list:
        print(f"VM Name: {vm.name}")
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                nic_connected = device.connectable.connected
                nic_status = "Connected" if nic_connected else "Disconnected"
                print(f"  NIC Status: {nic_status}")

                network = device.backing
                if isinstance(network, vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo):
                    dvs_portgroup_key = network.port.portgroupKey
                    dvs_uuid = network.port.switchUuid

                    # Retrieve the Distributed Virtual Switch
                    dvs = content.dvSwitchManager.QueryDvsByUuid(dvs_uuid)

                    # Find the port group by key
                    for portgroup in dvs.portgroup:
                        if portgroup.key == dvs_portgroup_key:
                            vlan_config = portgroup.config.defaultPortConfig.vlan
                            if isinstance(vlan_config, vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec):
                                vlan_id = vlan_config.vlanId
                            else:
                                vlan_id = "Unknown/None"
                            print(f"  Port Group: {portgroup.name}, VLAN ID: {vlan_id}")
                            break
                else:
                    print("  Network: Non-distributed virtual port group or no backing info")

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

# Connect to vCenter and run the function
try:
    si = SmartConnect(
        host="me-vc01.abramad.com",
        user=username,
        pwd=password,
        sslContext=context,
    )
    content = si.RetrieveContent()
    get_vm_portgroup_info(content)
finally:
    Disconnect(si)
