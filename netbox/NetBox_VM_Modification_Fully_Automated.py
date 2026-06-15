from pyvim.connect import SmartConnect, Disconnect
from cryptography.fernet import Fernet
from pyVmomi import vim
import ipaddress
import pynetbox
import time
import ssl
import sys
import os

#def get_vcenter_vms(vc):
#    content = vc.RetrieveContent()
#    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
#    vms = container.view
#    container.Destroy()
#    return vms

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

def calculate_subnet_info(subnet):
    # Create an IPv4Network object
    network = ipaddress.IPv4Network(subnet, strict=False)

    # Get the broadcast address
    broadcast_address = network.broadcast_address

    # Get the usable IP addresses
    usable_ips_obj = list(network.hosts())
    raw_usable_ips = [str(ip) for ip in usable_ips_obj]

    # Get Gateway IP Address
    gateway_address = raw_usable_ips[-1]

    # Get Pruned Usable IPs
    pruned_usable_ips = raw_usable_ips[:-1]

    ip_info = {
        'subnet': str(network.network_address),
        'broadcast_address': str(broadcast_address),
        'gateway_address': str(gateway_address),
        'usable_ips': pruned_usable_ips
    }
    return ip_info

def get_netbox_data(nb):

    # Make Dictionary of all netbox clusters
    nb_cluster_dict = {}
    clusters = nb.virtualization.clusters.all()
    for cluster in clusters:
        nb_cluster_dict[cluster.name.lower()] = cluster.id

    # Make Dictionary of all platforms (OS)
    nb_platform_dict = {}
    platforms = nb.dcim.platforms.all()
    for platform in platforms:
        nb_platform_dict[platform.name.lower()] = platform.id

    # Make Dictionary of all Prefixes, VRF Names and VLANs
    prefixes = nb.ipam.prefixes.all()
    prefix_dict = {}
    # Iterate through prefixes and collect VRF and VLAN information
    for prefix in prefixes:
        nb_vrf_name = prefix.vrf.name if prefix.vrf else "None"
        nb_vrf_id = prefix.vrf.id if prefix.vrf else "None"
        nb_vlan_name = prefix.vlan.display if prefix.vlan else "None"
        nb_vlan_id = prefix.vlan.id if prefix.vlan else "None"
        nb_vid = prefix.vlan.vid if prefix.vlan else "None"

        prefix_dict[prefix.prefix] = {

            'prefix_name': prefix.prefix,  # prefix name
            'vrf_name': nb_vrf_name,  # vrf name
            'nb_vrf_id': nb_vrf_id,  # netbox vrf id
            'vlan_name': nb_vlan_name,  # vlan name
            'nb_vlan_id': nb_vlan_id,  # netbox vlan id
            'vlan_id': nb_vid  # actual vlan id
        }

    return {
        'clusters': nb_cluster_dict,
        'platforms': nb_platform_dict,
        'prefixes': prefix_dict
    }

def process_vm(vm, site_id, nb_data):
    # Initialize lists for reporting
    vms_without_ip = []
    vlans_not_found_in_netbox = []

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
        'vlan_id': 'N/A',
        'portgroup': 'N/A',
        'interfaces': []
    }

    # Calculate disk space
    for device in vm.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualDisk):
            vm_info['disk'] += round((device.capacityInBytes / 1073741824) * 1000)

    # IP address detection
    if vm.guest and vm.guest.ipAddress:
        for nic in vm.guest.net:
            for ip in nic.ipConfig.ipAddress:
                if ip.ipAddress.startswith(('172.17', '172.20', '172.21', '172.29', '10.', '192.168')):
                    vm_info['ip'] = ip.ipAddress
                    break
    if vm_info['ip'] == "0.0.0.0" and vm_info['ip'] == 'active':
        vms_without_ip.append(vm_info['name'])

    # Get PortGroup and Vlan ID and NIC connection status
    for device in vm.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualEthernetCard):

            # VM NIC Status
            nic_connected = device.connectable.connected
            vm_nic_status = "connected" if nic_connected else "disconnected"

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

                        # VM VLAN ID
                        if isinstance(vlan_config, vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec):
                            vm_info['vlan_id'] = vlan_config.vlanId
                        else:
                            vm_info['vlan_id'] = "N/A"

                        # VM PortGroup Name
                        vm_info['portgroup'] = portgroup.name
                        break
            else:
                print(f"  {vm.name}: Network: Non-distributed virtual port group or no backing info")

    # NetBox mapping
    vm_info['cluster_id'] = nb_data['clusters'].get(vm_info['cluster'], None)

    # VM NetBox Platform ID (OS)
    vm_info['platform_id'] = 18  # default value: other 3.x or later linux (64-bit)
    for name, plt_id in nb_data['platforms'].items():
        if name in vm_info['os']:
            vm_info['platform_id'] = plt_id
            break

    # VM NetBox Site ID
    vm_info['site_id'] = site_id

    # VM NetBox Prefix, VRF ID, VLAN ID
    # Find matching prefix information
    vm_info['prefix_info'] = None
    if vm_info['vlan_id'] != 'N/A':
        for prefix, prefix_data in nb_data['prefixes'].items():
            if prefix_data['vlan_id'] == vm_info['vlan_id']:
                vm_info['prefix_info'] = {
                    'prefix_name': prefix_data['prefix_name'],
                    'vrf_name': prefix_data['vrf_name'],
                    'nb_vrf_id': prefix_data['nb_vrf_id'],
                    'vlan_name': prefix_data['vlan_name'],
                    'nb_vlan_id': prefix_data['nb_vlan_id'],
                    'vlan_id': prefix_data['vlan_id'],
                    'vm_cidr_ip': f"{vm_info['ip']}/{prefix.split('/')[1]}",
                    'vm_subnet_info': calculate_subnet_info(f"{vm_info['ip']}/{prefix.split('/')[1]}"),
                    'vm_subnet_ip': None
                }
                if vm_info['prefix_info']['vm_subnet_info']:
                    vm_info['prefix_info']['vm_subnet_ip'] = vm_info['prefix_info']['vm_subnet_info']['subnet']
                break

        if not vm_info['prefix_info']:
            print(f'VLAN not found in NetBox: {vm_info["name"]} - {vm_info["vlan_id"]}')
            vlans_not_found_in_netbox.append([vm_info['name'], vm_info['vlan_id']])
    else:
        print(f'VM "{vm_info["name"]}" isn\'t bound to any VLAN: {vm_info["vlan_id"]}')


    return vm_info, vms_without_ip, vlans_not_found_in_netbox

def sync_vm_to_netbox(vm_info, nb, existing_vms):
    # Check if VM exists in NetBox
    nb_vm = existing_vms.get((vm_info['name'].lower(), vm_info['cluster_id']))




# ========================================================================================
# Configuration
total_vms_without_ip = []
total_vlans_not_found_in_netbox = []


# SSL context for vCenter connections
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

# Decrypt credentials
username = 'sysops-svc@abramad.com'
password = decryptor('sysops-svc_enc', 'sysops-svc_key')


netbox_url = "https://netbox.abramad.com"
netbox_token = "57b72dfc7c90922839fbd9dc8b7e2a244fc0c4c2"
vcenters = ['mra-vc01.abramad.com', 'mev-vc01.abramad.com', 'me-vc01.abramad.com']
vcenters = ['mra-vc01.abramad.com']

# Initialize NetBox connection

nb_login_info = pynetbox.api(netbox_url, token=netbox_token)
nb_data = get_netbox_data(nb_login_info)

# Get existing NetBox VMs
nb_existing_vms = {}  # Create an empty dictionary
nb_all_vms = nb_login_info.virtualization.virtual_machines.all()

for vm in nb_all_vms:
    #cluster_id = vm.cluster.id
    nb_existing_vms[vm.name.lower()] = vm

"""
for dict_k, dict_v in nb_data.items():
    print(f'{dict_k}')
    for nested_dict_k, nested_dict_v in dict_v.items():
        if dict_k == 'prefixes':
            print(f'    {nested_dict_k}')
            for nested_nested_dict_k, nested_nested_dict_v in nested_dict_v.items():
                print(f'        {nested_nested_dict_k}: {nested_nested_dict_v}')
        else:
            print(f'    {nested_dict_k}: {nested_dict_v}')

    print('\n')

"""

# Process each vCenter
for vcenter in vcenters:
    # VM NetBox Site
    site_id = 2 if vcenter.lower().startswith('m') else 4

    vc_login_info = SmartConnect(host=vcenter, user=username, pwd=password, sslContext=context)
    content = vc_login_info.RetrieveContent()
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    vms = container.view
    container.Destroy()


    for vm in vms[0:0]:
        vm_info, vm_no_ip, vlan_not_found = process_vm(vm, site_id, nb_data)
        total_vms_without_ip.extend(vm_no_ip)
        total_vlans_not_found_in_netbox.extend(vlan_not_found)

        for k, v in vm_info.items():
            if k == 'name':
                print(f'{k}: {v}')
            elif k != 'name' and k != 'prefix_info':
                print(f'    {k}: {v}')
            elif k == 'prefix_info':
                print(f'    {k}')
                for nk, nv in v.items():
                    print(f'        {nk}: {nv}')

        Disconnect(vc_login_info)

    for k, v in nb_existing_vms.items():
        print(f'{k}: {v.get((vm_info['name'].lower()))}')



print("\n\n=== Report ===")
if total_vms_without_ip:
    print("\nVMs without IP addresses:")
    for vm_name in sorted(total_vms_without_ip):
        print(f" - {vm_name}")

if total_vlans_not_found_in_netbox:
    print("\nVMs with VLANs not found in NetBox:")
    for vm_name, vlan_id in sorted(total_vlans_not_found_in_netbox):
        print(f" - {vm_name} (VLAN ID: {vlan_id})")



'''        
        
def sync_vm_to_netbox(vm, cluster, nb, nb_existing_vms):
    """
    Sync a single VM to NetBox. VM names are assumed unique globally (not namespaced by cluster).
    Args:
        vm: VM object (with attributes name, vcpus, memory, power_state, ip_address, mac_address).
        cluster: NetBox cluster object (with attributes id and site.id).
        nb: Pynetbox API instance for NetBox.
        nb_existing_vms: dict mapping vm_name.lower() to existing NetBox VM record.
    """
    # Lowercase VM name for consistent lookup
    vm_name_key = vm.name.lower()

    # Determine VM status for NetBox ('active' vs 'offline')
    if hasattr(vm, 'power_state') and vm.power_state.lower() == 'poweredon':
        status = 'active'
    else:
        status = 'offline'

    # Prepare common payload for creation or update
    vm_data = {
        'name': vm.name,
        'cluster': cluster.id,
        'site': cluster.site.id,
        'vcpus': vm.vcpus,
        'memory': vm.memory,
        'status': status,
    }

    # If VM already exists in NetBox, update it
    if vm_name_key in nb_existing_vms:
        nb_vm = nb_existing_vms[vm_name_key]
        update_data = {}

        # Check and update each field as needed
        if nb_vm.vcpus != vm.vcpus:
            update_data['vcpus'] = vm.vcpus
        if nb_vm.memory != vm.memory:
            update_data['memory'] = vm.memory
        # Status might be an object or string, convert to string for comparison
        existing_status = str(nb_vm.status) if hasattr(nb_vm, 'status') else nb_vm.status
        if existing_status.lower() != status:
            update_data['status'] = status
        # Ensure VM is assigned to the correct cluster
        if hasattr(nb_vm, 'cluster') and nb_vm.cluster and nb_vm.cluster.id != cluster.id:
            update_data['cluster'] = cluster.id
        # Ensure correct site (if clusters can move sites)
        if hasattr(nb_vm, 'site') and nb_vm.site and nb_vm.site.id != cluster.site.id:
            update_data['site'] = cluster.site.id

        # Apply updates in NetBox if needed
        if update_data:
            nb.virtualization.virtual_machines.update(nb_vm.id, **update_data)
    else:
        # Create a new VM in NetBox
        nb_vm = nb.virtualization.virtual_machines.create(**vm_data)
        # Add the new VM to existing dict for later reference
        nb_existing_vms[vm_name_key] = nb_vm

    # Handle networking: interface and IP assignment
    # Only assign IP if VM is active and has an IP address
    vm_ip = getattr(vm, 'ip_address', None)
    if status == 'active' and vm_ip:
        # Find or create a VM interface by MAC address
        existing_ifaces = nb.virtualization.interfaces.filter(virtual_machine_id=nb_vm.id)
        nb_interface = None
        for iface in existing_ifaces:
            if hasattr(iface, 'mac_address') and iface.mac_address == vm.mac_address:
                nb_interface = iface
                break
        # If no matching interface, create a new one
        if not nb_interface:
            interface_data = {
                'name': 'eth0',  # default interface name
                'virtual_machine': nb_vm.id,
                'mac_address': vm.mac_address,
            }
            nb_interface = nb.virtualization.interfaces.create(**interface_data)

        # Assign IP to the interface (use /32 for a single IPv4 address)
        ip_str = f"{vm_ip}/32"
        existing_ips = nb.ipam.ip_addresses.filter(address=ip_str)
        if existing_ips:
            nb_ip = existing_ips[0]
        else:
            ip_data = {
                'address': ip_str,
                'assigned_object_type': 'virtualization.vminterface',
                'assigned_object_id': nb_interface.id
            }
            nb_ip = nb.ipam.ip_addresses.create(**ip_data)

        # Set the VM's primary IP to this address
        nb.virtualization.virtual_machines.update(nb_vm.id, primary_ip4=nb_ip.id)

    elif status == 'offline':
        # VM is offline: clear its primary IP if set
        if hasattr(nb_vm, 'primary_ip4') and nb_vm.primary_ip4:
            nb.virtualization.virtual_machines.update(nb_vm.id, primary_ip4=None)
'''