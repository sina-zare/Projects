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
    try:
        if os.environ.get(enc_env_var) is None or os.environ.get(key_env_var) is None:
            print("Missing environment variables or insufficient permissions")
            time.sleep(10)
            sys.exit()

        key = os.environ.get(key_env_var)
        encryption_key = Fernet(key)
        encrypted_password = os.environ.get(enc_env_var).encode()
        decrypted_password = encryption_key.decrypt(encrypted_password).decode()
        return decrypted_password

    except Exception as e:
        print(f"Decryption error: {str(e)}")
        time.sleep(10)
        sys.exit()


def calculate_subnet_info(subnet):
    network = ipaddress.IPv4Network(subnet, strict=False)
    return {
        'subnet': str(network.network_address),
        'broadcast_address': str(network.broadcast_address),
        'gateway_address': str(list(network.hosts())[-1]),
        'usable_ips': [str(ip) for ip in list(network.hosts())[:-1]]
    }


def get_netbox_data(nb):
    return {
        'clusters': {c.name.lower(): c.id for c in nb.virtualization.clusters.all()},
        'platforms': {p.name.lower(): p.id for p in nb.dcim.platforms.all()},
        'prefixes': {
            p.prefix: [
                p.prefix,
                p.vrf.name if p.vrf else None,
                p.vrf.id if p.vrf else None,
                p.vlan.name if p.vlan else None,
                p.vlan.id if p.vlan else None,
                p.vlan.vid if p.vlan else None
            ] for p in nb.ipam.prefixes.all()
        }
    }


def get_vcenter_vms(si):
    content = si.RetrieveContent()
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    vms = container.view
    container.Destroy()
    return vms


def process_vm(vm, site_id, nb_data):
    # Extract basic VM information
    vm_info = {
        'name': vm.name,
        'fqdn': vm.summary.guest.hostName or '',
        'os': vm.config.guestFullName.lower(),
        'status': 'active' if vm.runtime.powerState.lower() == 'poweredon' else 'offline',
        'cluster': vm.runtime.host.parent.name.lower(),
        'cpu': vm.config.hardware.numCPU,
        'memory': int((vm.config.hardware.memoryMB / 1024) * 1000),
        'disk': 0,
        'ip': '0.0.0.0',
        'vlan_id': None,
        'portgroup': None,
        'interfaces': []
    }

    # Calculate disk space
    for device in vm.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualDisk):
            vm_info['disk'] += round((device.capacityInBytes / 1073741824) * 1000)

    # Network information
    for device in vm.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualEthernetCard):
            nic_info = {
                'connected': device.connectable.connected,
                'network': None,
                'vlan': None
            }

            if isinstance(device.backing, vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo):
                dvs = content.dvSwitchManager.QueryDvsByUuid(device.backing.port.switchUuid)
                for pg in dvs.portgroup:
                    if pg.key == device.backing.port.portgroupKey:
                        vm_info['portgroup'] = pg.name
                        if isinstance(pg.config.defaultPortConfig.vlan,
                                      vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec):
                            vm_info['vlan_id'] = pg.config.defaultPortConfig.vlan.vlanId
                        break

    # IP address detection
    if vm.guest and vm.guest.ipAddress:
        for nic in vm.guest.net:
            for ip in nic.ipConfig.ipAddress:
                if ip.ipAddress.startswith(('172.17', '172.20', '172.21', '172.29', '10.', '192.168')):
                    vm_info['ip'] = ip.ipAddress
                    break

    # NetBox mapping
    vm_info['cluster_id'] = nb_data['clusters'].get(vm_info['cluster'], None)
    vm_info['platform_id'] = next((pid for name, pid in nb_data['platforms'].items()
                                   if name in vm_info['os']), 18)
    vm_info['site_id'] = site_id

    # Prefix and VLAN mapping
    vm_info['prefix_info'] = next((p for prefix, p in nb_data['prefixes'].items()
                                   if p[5] == vm_info['vlan_id']), None)

    return vm_info


def sync_vm_to_netbox(vm_info, nb, existing_vms):
    # Check if VM exists in NetBox
    nb_vm = existing_vms.get((vm_info['name'].lower(), vm_info['cluster_id']))

    if nb_vm:
        # Update existing VM
        update_data = {}
        fields_to_check = [
            ('vcpus', 'cpu'),
            ('memory', 'memory'),
            ('disk', 'disk'),
            ('status', 'status'),
            ('platform', 'platform_id'),
            ('site', 'site_id')
        ]

        for nb_field, vm_field in fields_to_check:
            current_value = getattr(nb_vm, nb_field)
            new_value = vm_info[vm_field]
            if current_value != new_value:
                update_data[nb_field] = new_value

        if update_data:
            try:
                nb_vm.update(update_data)
                print(f"Updated VM {vm_info['name']}: {update_data}")
            except Exception as e:
                print(f"Error updating {vm_info['name']}: {str(e)}")
                return

        # Manage interfaces
        interface = next((intf for intf in nb_vm.interfaces if intf.name == "eth0"), None)
        if not interface:
            try:
                interface = nb.virtualization.interfaces.create({
                    "name": "eth0",
                    "virtual_machine": nb_vm.id,
                    "type": "virtual"
                })
                print(f"Created interface eth0 for {vm_info['name']}")
            except Exception as e:
                print(f"Error creating interface for {vm_info['name']}: {str(e)}")
                return

        # IP address management
        if vm_info['status'] == 'active' and vm_info['ip'] != '0.0.0.0':
            cidr = f"{vm_info['ip']}/24"  # Adjust CIDR based on your network
            try:
                ip_address = nb.ipam.ip_addresses.get(address=cidr)
                vrf_id = vm_info['prefix_info'][2] if vm_info['prefix_info'] else None

                if ip_address:
                    update_data = {
                        "assigned_object_type": "virtualization.vminterface",
                        "assigned_object_id": interface.id,
                        "dns_name": vm_info['fqdn']
                    }
                    if vrf_id:
                        update_data["vrf"] = vrf_id

                    if any(getattr(ip_address, k) != v for k, v in update_data.items()):
                        ip_address.update(update_data)
                        print(f"Updated IP {cidr} for {vm_info['name']}")
                else:
                    ip_data = {
                        "address": cidr,
                        "assigned_object_type": "virtualization.vminterface",
                        "assigned_object_id": interface.id,
                        "dns_name": vm_info['fqdn'],
                        "status": "active"
                    }
                    if vrf_id:
                        ip_data["vrf"] = vrf_id
                    nb.ipam.ip_addresses.create(ip_data)
                    print(f"Created IP {cidr} for {vm_info['name']}")

                # Update primary IP
                if not nb_vm.primary_ip4 or nb_vm.primary_ip4.address != cidr:
                    ip_obj = nb.ipam.ip_addresses.get(address=cidr)
                    nb_vm.primary_ip4 = ip_obj.id
                    nb_vm.save()

            except Exception as e:
                print(f"IP management error for {vm_info['name']}: {str(e)}")
        elif vm_info['status'] == 'offline' and nb_vm.primary_ip4:
            nb_vm.primary_ip4 = None
            nb_vm.save()
    else:
        # Create new VM
        vm_data = {
            "name": vm_info['name'],
            "cluster": vm_info['cluster_id'],
            "status": vm_info['status'],
            "site": vm_info['site_id'],
            "platform": vm_info['platform_id'],
            "vcpus": vm_info['cpu'],
            "memory": vm_info['memory'],
            "disk": vm_info['disk']
        }

        try:
            new_vm = nb.virtualization.virtual_machines.create(vm_data)
            print(f"Created new VM: {vm_info['name']}")
        except Exception as e:
            print(f"Error creating VM {vm_info['name']}: {str(e)}")



# Configuration
netbox_url = "https://netbox.abramad.com"
netbox_token = "57b72dfc7c90922839fbd9dc8b7e2a244fc0c4c2"
vcenters = ['mra-vc01.abramad.com', 'mev-vc01.abramad.com', 'me-vc01.abramad.com']

# Initialize NetBox connection
nb = pynetbox.api(netbox_url, token=netbox_token)
nb_data = get_netbox_data(nb)

# Get existing NetBox VMs
existing_vms = {(vm.name.lower(), vm.cluster.id): vm
                for vm in nb.virtualization.virtual_machines.all()}

# SSL context for vCenter connections
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

# Decrypt credentials
username = 'sysops-svc@abramad.com'
password = decryptor('sysops-svc_enc', 'sysops-svc_key')

# Process each vCenter
for vcenter in vcenters:
    try:
        si = SmartConnect(
            host=vcenter,
            user=username,
            pwd=password,
            sslContext=context
        )

        site_id = 2 if vcenter.lower().startswith('m') else 4
        vms = get_vcenter_vms(si)

        for vm in vms:
            vm_info = process_vm(vm, site_id, nb_data)
            sync_vm_to_netbox(vm_info, nb, existing_vms)

        Disconnect(si)

    except Exception as e:
        print(f"Error connecting to {vcenter}: {str(e)}")
        continue

