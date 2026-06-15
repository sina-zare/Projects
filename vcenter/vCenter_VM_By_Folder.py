from pyvim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl


def get_vms_in_specific_folder(vcenter_ip, username, password, target_folder_name):
    # Disable SSL warnings for self-signed certificates
    context = ssl._create_unverified_context()

    # Connect to vCenter
    si = SmartConnect(host=vcenter_ip, user=username, pwd=password, sslContext=context)

    # Get content from service instance
    content = si.RetrieveContent()

    # Recursive function to find the specified folder
    def find_folder_by_name(entity, target_name):
        if isinstance(entity, vim.Folder) and entity.name == target_name:
            return entity
        elif hasattr(entity, 'childEntity'):
            for child in entity.childEntity:
                result = find_folder_by_name(child, target_name)
                if result:
                    return result
        return None

    # Start with the 'Datacenters' folder
    datacenters_folder = content.rootFolder.childEntity
    target_folder = None
    for datacenter in datacenters_folder:
        target_folder = find_folder_by_name(datacenter, target_folder_name)
        if target_folder:
            break

    # Check if the target folder was found
    if not target_folder:
        print(f"Folder '{target_folder_name}' not found in vCenter.")
        Disconnect(si)
        return []

    # Get names of VMs within the target folder
    vm_names = [vm.name for vm in target_folder.childEntity if isinstance(vm, vim.VirtualMachine)]

    # Disconnect from vCenter
    Disconnect(si)

    return vm_names


# Parameters
vcenter_ip = "vra-vc01.abramad.com"
username = "sina.z@abramad.com"
password = "S@Bw00fer20936744"
target_folder_name = "TemporaryShutdown"

# Get VM names in the folder
vm_names = get_vms_in_specific_folder(vcenter_ip, username, password, target_folder_name)
print("VMs in folder:", vm_names)
