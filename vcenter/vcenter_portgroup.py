from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import warnings
import os


# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)
# *** Connecting to ME-VC01.Abramad.Com to get the Report ***

# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

ME_VC = connect.SmartConnect(host='vra-vc01.abramad.com', user="sina.z@abramad.com", pwd="S@Bw00fer20936743", port=443, sslContext=context)
me_content = ME_VC.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if (vm.name.startswith("VRA-"))]
# Sort the me_vms list based on VM names
sorted_vms = sorted(me_vms, key=lambda vm: vm.name.lower())
ra_dict = {}

for vm in sorted_vms:
    vm_power_state = vm.runtime.powerState  # Power State
    if vm_power_state.lower() == "poweredon":
        print(f"VM Name: {vm.name}")

        # Iterate through the hardware devices to find network adapters
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                print(f"  Device: {device.backing.port.portgroupKey}\n")


# Disconnect from vCenter
Disconnect(ME_VC)
