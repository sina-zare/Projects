import pynetbox

# Configuration
netbox_url = "https://netbox.abramad.com"
netbox_token = "57b72dfc7c90922839fbd9dc8b7e2a244fc0c4c2"

# Connect to NetBox
nb = pynetbox.api(netbox_url, token=netbox_token)


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
