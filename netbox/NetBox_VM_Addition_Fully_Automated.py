from pyvim.connect import SmartConnect, Disconnect
from cryptography.fernet import Fernet
from pyVmomi import vim
import ipaddress
import pynetbox
import time
import ssl
import sys
import os
import requests


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


username = 'sysops-svc@abramad.com'
password = decryptor('sysops-svc_enc', 'sysops-svc_key')


# Netbox Data Gathering
# Configuration
netbox_url = "https://netbox.abramad.com"
netbox_token = "57b72dfc7c90922839fbd9dc8b7e2a244fc0c4c2"
# Disable SSL verification
session = requests.Session()
session.verify = False  # <-- Ignore SSL errors
# Connect to NetBox
nb = pynetbox.api(netbox_url, token=netbox_token)
nb.http_session = session

# Make Dictionary of all clusters
nb_cluster_dict = {}
clusters = nb.virtualization.clusters.all()
for cluster in clusters:
    nb_cluster_dict[cluster.name.lower()] = cluster.id

# Make Dictionary of all platforms (OS)
nb_platform_dict = {}
platforms = nb.dcim.platforms.all()
for platform in platforms:
    nb_platform_dict[platform.name.lower()] = platform.id

#for key, value in nb_platform_dict.items():
#    print(f'{key}: {value}')


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

    prefix_dict[prefix.prefix] = [

        prefix.prefix, # prefix name
        nb_vrf_name, # vrf name
        nb_vrf_id,  # netbox vrf if
        nb_vlan_name, # vlan name
        nb_vlan_id, # netbox vlan id
        nb_vid  # actual vlan id
    ]

#for key, value in prefix_dict.items():
#    print(f'{key}: {value}')



# vCenter Data Gathering
# Bypass SSL certificate validation (for lab/test environments)
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

vcenter_list = ['vts-vc01.abramad.com', 'vab-vc01.abramad.com', 'vra-vc01.abramad.com','mra-vc01.abramad.com', 'mev-vc01.abramad.com', 'me-vc01.abramad.com']
vcenter_list = ['vab-vc01.abramad.com']


vms_dict = {}
vm_counter = 0

vms_without_ip = []
vlans_not_found_in_netbox = []

for vcenter in vcenter_list:

    si = SmartConnect(host=vcenter, user=username, pwd=password, sslContext=context)
    content = si.RetrieveContent()
    # Retrieve all Virtual Machines
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    vm_list = container.view
    container.Destroy()
    print(f'\nNumber of VMs in {vcenter}: {len(vm_list)}\n')
    for vm in vm_list[:]:
        #if vm.name == 'ME-Kibana':
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f'VMs Proccessed: {vm.name}: {vm_counter}')

        # VM Name
        vm_name = vm.name

        # VM FQDN
        vm_fqdn = vm.summary.guest.hostName

        # VM Guest OS
        vm_os = vm.config.guestFullName.lower()

        # VM Power State
        vm_power_state = vm.runtime.powerState.lower()

        # Find Compute Cluster Name
        vm_cluster_name = vm.runtime.host.parent.name.lower()

        # Get VM CPU Core
        vm_cpu_core = vm.config.hardware.numCPU

        # VM Memory
        vm_memory = int((vm.config.hardware.memoryMB) / 1024) * 1000

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
                                vm_vlan_id = vlan_config.vlanId
                            else:
                                vm_vlan_id = "N/A"

                            # VM PortGroup Name
                            vm_portgroup = portgroup.name
                            break
                else:
                    print(f"  {vm.name}: Network: Non-distributed virtual port group or no backing info")

        # Calculate Disk Size
        vm_disk_size = 0
        vm_disk_size_mb = 0
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualDisk):
                vm_disk_size += round(device.capacityInBytes) # --> MiB # in MB # / 1024 / 1024 / 1024 in GB # 1073741824 in GiB
                vm_disk_size_mb = round((vm_disk_size / 1073741824) * 1000)
        #print(vm.name)
        #print(vm_disk_size)
        #print(vm_disk_size_mb)
        #print(vm_disk_size / 1000000)
        #print('--------------------')
        #sys.exit()

        #print(vm_disk_size)

        # retrieve vm IP address
        vm_ip = "0.0.0.0"
        if vm.guest is not None:
            candidate_ips = []
            for nic in vm.guest.net:
                if nic.ipConfig is not None:
                    for ip in nic.ipConfig.ipAddress:
                        candidate_ips.append(ip.ipAddress)

            # First, prefer IPs starting with 172.17
            for ip in candidate_ips:
                if ip.startswith('172.17'):
                    vm_ip = ip
                    break
            else:
                # Then, if no 172.17 found, pick other allowed IPs
                for ip in candidate_ips:
                    if ip.startswith(('172.20', '172.21', '172.29', '10.', '192.168')):
                        vm_ip = ip
                        break

        if vm_ip == "0.0.0.0" and vm_power_state == 'poweredon':
            vms_without_ip.append(vm_name)


        # VM NetBox Variables
        # VM NetBox Site
        vm_site = 2 if vcenter.lower().startswith('m') else 4  # 2 --> ME. 4 --> Vanak

        # VM NetBox Cluster ID
        vm_cluster_id = ''
        for nb_cluster_name in nb_cluster_dict:
            #print(f' vm_cluster_name: {vm_cluster_name} : nb_cluster_name: {nb_cluster_name}')
            if vm_cluster_name == nb_cluster_name:
                vm_cluster_id = nb_cluster_dict[nb_cluster_name]
                #print(f'{vm.name} matched.\nID: {vm_cluster_id}')

        # VM NetBox Platform ID (OS)
        vm_platform_id = 18
        for nb_platform_name in nb_platform_dict:
            #print(f'vm_os_name: {vm_os} : nb_platform_name: {nb_platform_name}')
            if nb_platform_name in vm_os:
                vm_platform_id = nb_platform_dict[nb_platform_name]
                #print(f'{vm.name} matched.\nID: {vm_platform_id}\n')

        # VM NetBox Status
        vm_status = 'active' if vm_power_state == 'poweredon' else 'offline'

        # VM NetBox Prefix, VRF ID, VLAN ID
        vm_prefix_name = ''
        vm_nb_vlan_id = ''
        vm_vrf_id = ''
        vm_cidr_ip = ''
        vm_subnet_ip = ''
        vlan_found_in_netbox = False
        for prefix_detail in prefix_dict:
            if vm_vlan_id == prefix_dict[prefix_detail][5]:  # If netbox vlan was equal to vm vlan
                vm_prefix_name = prefix_dict[prefix_detail][0]  # Name of IP Prefix Range in netbox
                vm_vrf_id = prefix_dict[prefix_detail][2]  # VRF ID of netbox
                vm_nb_vlan_id = prefix_dict[prefix_detail][4]  # vlan ID of netbox
                vm_cidr_ip = (vm_ip + '/' + vm_prefix_name.split('/')[1]).strip()  # CIDR IP
                vm_subnet_info = calculate_subnet_info(vm_cidr_ip)
                vm_subnet_ip = vm_subnet_info['subnet']  # VM Subnet IP
                vlan_found_in_netbox = True
                break

        if not vlan_found_in_netbox:
            print(f'vlan not found in netbox: {vm_name} - {vm_vlan_id}')
            vlans_not_found_in_netbox.append([vm_name, vm_vlan_id])

                # print(f'{15 * '-'}\n{vm_vlan_id} : {prefix_dict[prefix_detail][5]}\n\n{vm_name}\n{vm_ip}\n{vm_cidr_ip}\n{vm_subnet_ip}\n{vm_vrf_id}\n{vm_nb_vlan_id}\n{15 * '-'}\n')

        # Filling VMs Dict
        vms_dict[vm_name] = [vm_name, vm_cluster_id, vm_status, vm_site, vm_platform_id, vm_cpu_core, vm_memory, vm_disk_size_mb, vm_cidr_ip, vm_vrf_id, vm_fqdn, vm_portgroup, vm_vlan_id, vm_subnet_ip, vm_os]
        vm_counter += 1

print(f'vCenter Operations Finished\n\nNetBox Operations Started.\nNumber of VMs: {len(vms_dict)}\n\n')

'''
for k, v in vms_dict.items():
    print(k)
    print(f'    vm_name: {v[0]}')
    print(f'    vm_cluster_id: {v[1]}')
    print(f'    vm_status: {v[2]}')
    print(f'    vm_site: {v[3]}')
    print(f'    vm_platform_id: {v[4]}')
    print(f'    vm_cpu_core: {v[5]}')
    print(f'    vm_memory: {v[6]}')
    print(f'    vm_disk_size_mb: {v[7]}')
    print(f'    vm_cidr_ip: {v[8]}')
    print(f'    vm_vrf_id: {v[9]} Type: {type(v[9])}')
    print(f'    vm_fqdn: {v[10]}')
    print(f'    vm_portgroup: {v[11]}')
    print(f'    vm_vlan_id: {v[12]}')
    print(f'    vm_subnet_ip: {v[13]}')
    print(f'    vm_os: {v[14]}')
    print('\n')

'''
# NetBox VM Creation
for virtual_machine in vms_dict:
    # 1. Create a Virtual Machine
    vm_data = {
        "name": vms_dict[virtual_machine][0],
        "cluster": vms_dict[virtual_machine][1],
        "status": vms_dict[virtual_machine][2], # offline, active
        "site": vms_dict[virtual_machine][3],  # 2 --> ME. 4 --> Vanak
        "platform": vms_dict[virtual_machine][4],  # 12 --> Ubuntu 24.04 LTS
        "vcpus": vms_dict[virtual_machine][5],  # Number of virtual CPUs
        "memory": vms_dict[virtual_machine][6],  # Memory in MB (e.g., 8192 MB = 8 GB)
        "disk": vms_dict[virtual_machine][7],  # Disk size in MB
        "custom_fields": {  # Replace with your actual custom fields
            "Owner": "choice2", # choice2 --> CSB
            "Availability": 0,
            "Confidentiality": 0,
            "Integrity": 0
        },
    }

    try:
        vm = nb.virtualization.virtual_machines.create(vm_data)
        print(f"\n\nCreated VM: {vms_dict[virtual_machine][0]}")

    except pynetbox.RequestError as err:
        error_text = str(err.error)
        if "Virtual machine name must be unique per cluster" in error_text:
            print(f'VM "{vms_dict[virtual_machine][0]}" already created.\n{25 * '-'}\n')
            continue  # go to next vm
        else:
            print(f'\n\n{vms_dict[virtual_machine][0]} : VM Creation Error: {err}\n{vms_dict[virtual_machine]}\n{25 * '-'}\n')


    try:
        # 2. Create an Interface for the VM
        interface_data = {
            "name": "eth0",
            "virtual_machine": vm.id,
            "type": "virtual"
        }

        interface = nb.virtualization.interfaces.create(interface_data)
        print(f"Created Interface: {interface.name}")
    except Exception as err:
        print(f'{vms_dict[virtual_machine][0]} : Interface Creation Error: {err}\n{vms_dict[virtual_machine]}\n{25 * '-'}\n')

    if vms_dict[virtual_machine][2] == 'offline':
        print(f'Skipping IP Assignment: {vm.name} Powered Off')
        print(f'Skipping Primary IP Assignment: {vm.name} Powered Off')
        print(f"{15 * '-'}\n")

    # 3. Assign an IP Address to the Interface
    elif vms_dict[virtual_machine][2] == 'active': #  Create an interface if the vm is on

        try:
            if vms_dict[virtual_machine][9] != 'None': # if vrf id exists
                ip_data = {
                    "address": vms_dict[virtual_machine][8],  # IP address and prefix CIDR
                    "assigned_object_type": "virtualization.vminterface",  # Type of assigned object
                    "assigned_object_id": interface.id,  # ID of the assigned object
                    "status": "active",  # IP address status
                    "vrf": vms_dict[virtual_machine][9],  # Replace with the VRF ID or None if not applicable
                    "dns_name": vms_dict[virtual_machine][10],  # VM FQDN
                }
            else:
                ip_data = {
                    "address": vms_dict[virtual_machine][8],  # IP address and prefix CIDR
                    "assigned_object_type": "virtualization.vminterface",  # Type of assigned object
                    "assigned_object_id": interface.id,  # ID of the assigned object
                    "status": "active",  # IP address status
                    "dns_name": vms_dict[virtual_machine][10],  # VM FQDN
                }

            # vms_dict[virtual_machine][12] == '3695' or vms_dict[virtual_machine][12] == '3684' or vms_dict[virtual_machine][12] == '3699' or vms_dict[virtual_machine][12] == '3685':

            try:
                ip = nb.ipam.ip_addresses.create(ip_data)
                print(f"Assigned IP: {ip.address} to Interface: {interface.name}")

            except pynetbox.RequestError as err:
                error_text = str(err.error)
                if "Duplicate IP address" in error_text:
                    print(f"IP {vms_dict[virtual_machine][8]} already exists. Trying to assign it...")

                    # Find the existing IP
                    existing_ips = nb.ipam.ip_addresses.filter(address=vms_dict[virtual_machine][8])
                    ip = next(iter(existing_ips), None)

                    if ip:
                        # Update the IP assignment
                        ip_update_data = {
                            "assigned_object_type": "virtualization.vminterface",
                            "assigned_object_id": interface.id,
                            "status": "active",
                            "dns_name": vms_dict[virtual_machine][10],
                        }
                        ip.update(ip_update_data)
                        print(f"Reassigned existing IP: {ip.address} to Interface: {interface.name} of {vms_dict[virtual_machine][0]}")
                    else:
                        print(f"ERROR: IP {vms_dict[virtual_machine][8]} not found!")
                        ip = None
                else:
                    print(
                        f'{vms_dict[virtual_machine][0]} : IP Assigning Error: {err}\n{vms_dict[virtual_machine]}\n{25 * "-"}\n')
                    ip = None

        except Exception as err:
            print(f'{vms_dict[virtual_machine][0]} : IP Assigning Error: {err}\n{vms_dict[virtual_machine]}\n{25 * '-'}\n')


        # 4. Set the IP as the VM's Primary IP
        # Reload the VM object to ensure the latest state
        try:
            vm = nb.virtualization.virtual_machines.get(vm.id)
            updated_vm = vm.update({
                "primary_ip4": ip.id,  # Use 'primary_ip6' for an IPv6 address
            })
            print(f"Updated VM: Setting Primary IP\n{25 * '-'}\n")
        except Exception as err:
            print(f'{vms_dict[virtual_machine][0]} : Setting Primary IP Error: {err}\n{vms_dict[virtual_machine]}\n{25 * '-'}\n')


if len(vms_without_ip) > 0:
    print('VMs without IP:')
    for no_ip_vm in vms_without_ip:
        print(f'  {no_ip_vm}')

if len(vlans_not_found_in_netbox) > 0:
    print('\n\nNetBox Missing VLANs:')
    for missing_vlan in vlans_not_found_in_netbox:
        print(f'{missing_vlan[0]} - VLAN ID: {missing_vlan[1]}')
