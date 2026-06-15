
from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import warnings
import os

username = 'sina.z@abramad.com'
password = 'S@Bw00fer20936744'

from pyvim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl

'''
def get_vms_in_folder(vcenter_ip, username, password, folder_name):
    # Disable SSL warnings for self-signed certificates
    context = ssl._create_unverified_context()

    # Connect to vCenter
    si = SmartConnect(host=vcenter_ip, user=username, pwd=password, sslContext=context)

    # Get content from service instance
    content = si.RetrieveContent()

    # Helper function to find a folder by name
    def find_folder_by_name(folder, name):
        if isinstance(folder, vim.Folder) and folder.name == name:
            return folder
        for child in folder.childEntity:
            if isinstance(child, vim.Folder):
                result = find_folder_by_name(child, name)
                if result:
                    return result
        return None

    # Find the specific folder
    root_folder = content.rootFolder
    target_folder = find_folder_by_name(root_folder, folder_name)

    # Check if the folder was found
    if not target_folder:
        print(f"Folder '{folder_name}' not found in vCenter.")
        Disconnect(si)
        return []

    # Get names of VMs within the target folder
    vm_names = [vm.name for vm in target_folder.childEntity if isinstance(vm, vim.VirtualMachine)]

    # Disconnect from vCenter
    Disconnect(si)

    return vm_names


# Parameters
vcenter_ip = "vra-vc01.abramad.com"
folder_name = "AbramadOPS"

# Get VM names in the folder
vm_names = get_vms_in_folder(vcenter_ip, username, password, folder_name)
print("VMs in folder:", vm_names)
'''


def print_all_folders(vcenter_ip, username, password):
    # Disable SSL warnings for self-signed certificates
    context = ssl._create_unverified_context()

    # Connect to vCenter
    si = SmartConnect(host=vcenter_ip, user=username, pwd=password, sslContext=context)

    # Get content from service instance
    content = si.RetrieveContent()

    # Recursive function to print folder names
    def list_folders(entity, indent=0):
        # If the entity is a folder, print its name and look for child folders
        if isinstance(entity, vim.Folder):
            print("  " * indent + f"- Folder: {entity.name}")
            for child in entity.childEntity:
                list_folders(child, indent + 1)
        # If the entity is a data center, look into its VM and host folders
        elif isinstance(entity, vim.Datacenter):
            print("  " * indent + f"- Datacenter: {entity.name}")
            list_folders(entity.vmFolder, indent + 1)
            list_folders(entity.hostFolder, indent + 1)

    # Start with the 'Datacenters' folder
    datacenters_folder = content.rootFolder.childEntity
    print("Folders in vCenter:")
    for datacenter in datacenters_folder:
        list_folders(datacenter)

    # Disconnect from vCenter
    Disconnect(si)


# Parameters
vcenter_ip = "vra-vc01.abramad.com"


# Print all folder names
print_all_folders(vcenter_ip, username, password)
