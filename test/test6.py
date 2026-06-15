from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl

context = ssl._create_unverified_context()

si = SmartConnect(
    host="vcenter.example.com",
    user="administrator@vsphere.local",
    pwd="PASSWORD",
    sslContext=context
)

content = si.RetrieveContent()

vm_name = "VM_NAME"

for dc in content.rootFolder.childEntity:
    for vm in dc.vmFolder.childEntity:
        if vm.name == vm_name:
            print("Instance UUID:", vm.config.instanceUuid)
            print("BIOS UUID:", vm.config.uuid)

Disconnect(si)
