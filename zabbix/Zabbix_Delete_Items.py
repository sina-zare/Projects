from pyzabbix import ZabbixAPI
from cryptography.fernet import Fernet
import os
import sys

def decryptor(enc_env_var, key_env_var):
    """Decrypt env var `enc_env_var` using Fernet key in `key_env_var`.
       Returns decrypted string or raises ValueError on failure."""
    key = os.environ.get(key_env_var)
    enc = os.environ.get(enc_env_var)

    if not key or not enc:
        raise ValueError(f"Missing environment variable(s): {key_env_var} or {enc_env_var}")

    # Fernet expects bytes
    key_bytes = key.encode()
    enc_bytes = enc.encode()

    f = Fernet(key_bytes)
    decrypted_bytes = f.decrypt(enc_bytes)
    return decrypted_bytes.decode()



# ----- Config -----
zabbix_url = "https://vnk-zabbix.abramad.com"
zabbix_user = "sysops-svc"
# decrypt password from your env as you previously used
zabbix_password = decryptor('sysops-svc_enc', 'sysops-svc_key')

# Hosts to process (exact hostnames as in Zabbix UI)
host_names = [
 'VAB-DMGT-E7U26',
 'VAB-DMGT-F7U26',
 'VOS-AMGT-A6U33',
 'VOS-AMGT-B6U33',
 'VRA-AMGT-G5U33',
 'VRA-AMGT-G6U33',
 'VRA-AMGT-H5U33',
 'VRA-AMGT-H6U33',
 'VTS-AMGT-C1U33',
 'VTS-AMGT-C6U33',
 'VAB-AMGT-E5U33',
 'VAB-AMGT-F5U33',
 'VDC-CMGT',
 'VDC-CMGT-M2U26',
 'VR4-AMGT-G3U33',
 'VR4-AMGT-H3U33',
 'VR4-Leaf-G7U22',
 'VR4-Leaf-H7U22',
 'VRA-DMGT-G7U26',
 'VRA-AMGT-H6U33',
 'VTS-Leaf-D7U24'
]


# Match prefix (case-insensitive)
item_prefix = "Interface Vlan"

# Safe-by-default
dry_run = False
# -------------------


try:
    zapi = ZabbixAPI(zabbix_url, timeout=30)
    zapi.login(zabbix_user, zabbix_password)
except Exception as e:
    print("Failed to connect/login to Zabbix API:", e)
    sys.exit(1)

print("Connected to Zabbix API")

# Get host objects
hosts = zapi.host.get(output=["hostid", "host"], filter={"host": host_names})
if not hosts:
    print("No matching hosts found for the list provided.")
    sys.exit(1)

prefix_lower = item_prefix.lower()

for host in hosts:
    hostid = host["hostid"]
    hostname = host["host"]
    print(f"\nProcessing host: {hostname} (id: {hostid})")

    # Retrieve items for the host. If your hosts have many items you can add a 'limit' or
    # narrow fields; here we get name and itemid for reliable local filtering.
    try:
        items = zapi.item.get(output=["itemid", "name", "status", "templateid"], hostids=hostid, limit=10000)
    except Exception as e:
        print(f"  Failed to fetch items for host {hostname}: {e}")
        continue

    # Case-insensitive prefix match
    matching = [i for i in items if i.get("name") and i["name"].lower().startswith(prefix_lower)]

    if not matching:
        print("  No matching items found")
        continue

    for it in matching:
        tpl = it.get("templateid") or "0"
        print(f"  Found: {it['name']} (itemid: {it['itemid']}, templateid: {tpl}, status: {it.get('status')})")

    item_ids = [it["itemid"] for it in matching]

    if dry_run:
        print(f"  DRY-RUN: {len(item_ids)} items would be deleted (set dry_run=False to perform deletion)")
    else:
        try:
            # pyzabbix accepts a list of ids
            result = zapi.item.delete(*item_ids)
            # result usually returns deleted IDs
            print(f"  Deleted {len(item_ids)} items: {result}")
        except Exception as e:
            print(f"  Deletion failed for host {hostname}: {e}")
            # common reason: items inherited from templates; see notes below

print("\nDone.")
