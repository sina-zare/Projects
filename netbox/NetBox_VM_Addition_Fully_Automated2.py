from pyvim.connect import SmartConnect, Disconnect
from cryptography.fernet import Fernet
from pyVmomi import vim
import ipaddress
import pynetbox
import time
import ssl
import sys
import os


def decryptor(enc_env_var, key_env_var):


# ... (keep your existing decryptor function) ...

def calculate_subnet_info(subnet):


# ... (keep your existing subnet calculator) ...

# ... (rest of your configuration and setup code) ...

# Connect to NetBox
nb = pynetbox.api(netbox_url, token=netbox_token)

# Fetch existing NetBox VMs and create a lookup dictionary
existing_vms = {}
for nb_vm in nb.virtualization.virtual_machines.all():
    key = (nb_vm.name.lower(), nb_vm.cluster.id)
    existing_vms[key] = nb_vm

# Fetch existing prefixes and other data
# ... (keep your existing prefix/cluster/platform loading code) ...

# vCenter data collection
# ... (keep your existing vCenter connection and data collection code) ...

# NetBox operations
print(f'\nStarting NetBox operations. Total VMs: {len(vms_dict)}\n')

for vm_name, vm_data in vms_dict.items():
    # Extract VM data from your dictionary
    (
        name, cluster_id, status, site_id, platform_id, vcpus,
        memory, disk_size, cidr_ip, vrf_id, fqdn,
        portgroup, vlan_id, subnet_ip, os_name
    ) = vm_data

    # Lookup existing VM
    nb_vm = existing_vms.get((name.lower(), cluster_id))

    if nb_vm:  # Update existing VM
        # Prepare update data
        update_data = {}
        if nb_vm.vcpus != vcpus:
            update_data['vcpus'] = vcpus
        if nb_vm.memory != memory:
            update_data['memory'] = memory
        if nb_vm.disk != disk_size:
            update_data['disk'] = disk_size
        if nb_vm.status.value.lower() != status:
            update_data['status'] = status
        if (nb_vm.platform.id if nb_vm.platform else None) != platform_id:
            update_data['platform'] = platform_id
        if (nb_vm.site.id if nb_vm.site else None) != site_id:
            update_data['site'] = site_id

        # Perform update if needed
        if update_data:
            try:
                nb_vm.update(update_data)
                print(f"Updated VM {name} with: {update_data}")
            except Exception as e:
                print(f"Error updating {name}: {str(e)}")
                continue

        # Handle interfaces
        interface = next((intf for intf in nb_vm.interfaces if intf.name == "eth0"), None)
        if not interface:
            try:
                interface = nb.virtualization.interfaces.create({
                    "name": "eth0",
                    "virtual_machine": nb_vm.id,
                    "type": "virtual"
                })
                print(f"Created interface eth0 for {name}")
            except Exception as e:
                print(f"Error creating interface for {name}: {str(e)}")
                continue

        # IP Address management
        if status == 'active' and cidr_ip != '0.0.0.0/0':
            ip_address = cidr_ip.split('/')[0]
            try:
                # Check for existing IP assignment
                existing_ip = nb.ipam.ip_addresses.get(address=cidr_ip, vrf_id=vrf_id or None)

                if existing_ip:
                    # Update existing IP
                    if (existing_ip.assigned_object_id != interface.id or
                            existing_ip.dns_name != fqdn):
                        existing_ip.assigned_object_id = interface.id
                        existing_ip.assigned_object_type = "virtualization.vminterface"
                        existing_ip.dns_name = fqdn
                        existing_ip.save()
                        print(f"Updated IP {cidr_ip} for {name}")
                else:
                    # Create new IP
                    ip_data = {
                        "address": cidr_ip,
                        "assigned_object_type": "virtualization.vminterface",
                        "assigned_object_id": interface.id,
                        "dns_name": fqdn,
                        "status": "active"
                    }
                    if vrf_id != 'None':
                        ip_data["vrf"] = vrf_id
                    nb.ipam.ip_addresses.create(ip_data)
                    print(f"Created IP {cidr_ip} for {name}")

                # Update primary IP
                if nb_vm.primary_ip4 is None or nb_vm.primary_ip4.address != cidr_ip:
                    ip_obj = nb.ipam.ip_addresses.get(address=cidr_ip)
                    nb_vm.primary_ip4 = ip_obj.id
                    nb_vm.save()

            except Exception as e:
                print(f"IP management error for {name}: {str(e)}")
        elif status == 'offline' and nb_vm.primary_ip4:
            # Remove primary IP for offline VMs
            nb_vm.primary_ip4 = None
            nb_vm.save()

    else:  # Create new VM
# ... (keep your existing VM creation code) ...

# ... (rest of your error reporting code) ...