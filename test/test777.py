from pyzabbix import ZabbixAPI

# Zabbix server details
zabbix_url = "http://vnk-zabbix.abramad.com/"
zabbix_user = "sina.z"
zabbix_password = "S@Bw00fer20936744"



# Connect to the Zabbix API
zapi = ZabbixAPI(zabbix_url)
zapi.login(zabbix_user, zabbix_password)
print(f"Connected to Zabbix API at {zabbix_url}")

host_id = "12755"


try:
    zapi.hostinterface.create({
        'hostid': host_id,
        'type': 2,  # SNMP
        'main': 1,
        'useip': 1,
        'ip': "192.168.2.25",
        'dns': '',
        'port': '161',
        'details': {
            'version': 3,
            'bulk': 1,
            'securityname': 'your_security_name',
            'securitylevel': 3,
            'authprotocol': 0,
            'authpassphrase': 'your_auth_passphrase',
            'privprotocol': 0,
            'privpassphrase': 'your_priv_passphrase',
            'contextname': ''
        }
    })
    print("SNMPv3 interface added successfully.")
except Exception as e:
    print(f"Failed to add SNMPv3 interface: {e}")
