import pynetbox
import ipaddress

# IP Calculator
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


# Configuration
netbox_url = "https://netbox.abramad.com"
netbox_token = "57b72dfc7c90922839fbd9dc8b7e2a244fc0c4c2"

# Connect to NetBox
nb = pynetbox.api(netbox_url, token=netbox_token)

'''
# List all clusters
clusters = nb.virtualization.clusters.all()
print("Clusters:")
for cluster in clusters:
    print(f"ID: {cluster.id}, Name: {cluster.name}")

# List all VM roles
roles = nb.tenancy.tenant_groups.all()  # Alternatively, nb.virtualization.roles if using roles for VMs
print("\nRoles:")
for role in roles:
    print(f"ID: {role.id}, Name: {role.name}")

# List all Sites
sites = nb.dcim.sites.all()
print("Sites:")
for site in sites:
    print(f"ID: {site.id}, Name: {site.name}")

# Fetch and list all platforms
platforms = nb.dcim.platforms.all()
print("\nPlatforms:")
for platform in platforms:
    print(f"ID: {platform.id}, Name: {platform.name}")

# Fetch and list all VMs with custom attributes
vms = nb.virtualization.virtual_machines.all()
print("Virtual Machines and their Custom Attributes:")
for vm in vms:
    print(f"VM Name: {vm.name}")
    print("Custom Attributes:")
    for field, value in vm.custom_fields.items():
        print(f"  {field}: {value}")
    print("-" * 40)


# Fetch all custom fields
custom_fields = nb.extras.custom_fields.all()
# Print custom fields and their details

print("Custom Fields in NetBox:")
for field in custom_fields:
    print(f"Name: {field.name}")
    print(f"  Label: {field.label}")
    print(f"  Type: {field.type}")
    #print(f"  Object Types: {field.obj_type}")
    print(f"  Required: {field.required}")
    print(f"  Default: {field.default}")
    print(f"  Choices: {field.choices if field.type == 'select' else 'N/A'}")
    print("-" * 40)
    
# Fetch all prefixes
prefixes = nb.ipam.prefixes.all()

# Print prefixes and their VRFs
print("All Prefixes and Their Associated VRFs:")
for prefix in prefixes:
    vrf_name = prefix.vrf.name if prefix.vrf else "None"
    vrf_id = prefix.vrf.id if prefix.vrf else "None"
    print(f"Prefix: {prefix.prefix}, VRF Name: {vrf_name}, VRF ID: {vrf_id}")

'''

# Fetch all prefixes
prefixes = nb.ipam.prefixes.all()
prefix_dict = {}
# Print prefixes and their VRFs
print("All Prefixes and Their Associated VRFs:")
for prefix in prefixes:
    vrf_name = prefix.vrf.name if prefix.vrf else "None"
    vrf_id = prefix.vrf.id if prefix.vrf else "None"
    prefix_dict[prefix.prefix.split('/')[0]] = [prefix.prefix, vrf_name, vrf_id]  # Prefix: 10.255.240.28/30, VRF Name: AbramadOPS-Monitoring, VRF ID: 2


# 1. Create a Virtual Machine
vm_data = {
    "name": "VOP-CustomerZabbix-A1",
    "cluster": 4,  # Replace with your cluster ID
    #"role": 1,     # Replace with your VM role ID
    "status": "active", # offline
    "site": 4,  # 2 --> ME. 4 --> Vanak
    "platform": 12,  # 12 --> Ubuntu 24.04 LTS
    "vcpus": 6,  # Number of virtual CPUs
    "memory": 8000,  # Memory in MB (e.g., 8192 MB = 8 GB)
    "disk": 100000,  # Disk size in MB
    "custom_fields": {  # Replace with your actual custom fields
        "Owner": "choice2", # choice2 --> CSB
        "Availability": 3,
        "Confidentiality": 2,
        "Integrity": 1
    },
}
vm = nb.virtualization.virtual_machines.create(vm_data)
print(f"Created VM: {vm.name}")

# 2. Create an Interface for the VM
interface_data = {
    "name": "eth0",
    "virtual_machine": vm.id,
    "type": "virtual",  # or other types like 'bridge', 'bonded'
}
interface = nb.virtualization.interfaces.create(interface_data)
print(f"Created Interface: {interface.name}")

# 3. Assign an IP Address to the Interface
subnet_info = calculate_subnet_info('172.29.6.10/24')
subnet_ip = subnet_info['subnet']
ip_data = {
    "address": "172.29.6.10/24",  # Replace with your IP address and prefix
    "assigned_object_type": "virtualization.vminterface",  # Type of assigned object
    "assigned_object_id": interface.id,  # ID of the assigned object
    "status": "active",  # IP address status
    "vrf": prefix_dict[subnet_ip][2],  # Replace with the VRF ID or None if not applicable
    "dns_name": "example-vm.local",  # Replace with the desired DNS name
}

ip = nb.ipam.ip_addresses.create(ip_data)
print(f"Assigned IP: {ip.address} to Interface: {interface.name}")


# 4. Set the IP as the VM's Primary IP
# Reload the VM object to ensure the latest state
vm = nb.virtualization.virtual_machines.get(vm.id)
updated_vm = vm.update({
    "primary_ip4": ip.id,  # Use 'primary_ip6' for an IPv6 address
})
print(f"Updated VM: Setting Primary IP")
