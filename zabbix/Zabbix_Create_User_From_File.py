from pyzabbix import ZabbixAPI
from cryptography.fernet import Fernet
import csv
import os

def decryptor(enc_env_var, key_env_var):

    # Load the key
    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = (os.environ.get(enc_env_var)).encode()
    # Decrypt Data
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())

    #print(f"Decrypted Text: {decrypted_password}")
    return decrypted_password.decode()

# Gathering Data from CSV file.
user_list = []
with open("C:\\Temp\\zabbix_users.csv", "r", encoding="utf-8") as file:
    csv_reader = csv.reader(file)
    # Skip the first line
    for _ in range(1):
        next(csv_reader)

    for row in csv_reader:
        username = row[0]
        f_name = row[1]
        l_name = row[2]
        grp_name = row[3]
        email_addr = row[4]
        phone = row[5]

        user_list.append({
            "username": username,
            "f_name": f_name,
            "l_name": l_name,
            "grp_name": grp_name,
            "email_addr": email_addr,
            "phone": phone
        })

zabbix_urls = {
        'VNK-Zabbix': "https://vnk-zabbix.abramad.com",
        'VNK-CustomerZabbix': 'http://172.29.6.15',
        'ME-Zabbix': 'http://172.17.234.13/zabbix/',
        'ME-CustomerZabbix': 'http://172.17.234.23'
    }
# Zabbix connection details
user_role = "User role"
#user_role = "Super admin role"

zabbix_username = 'sysops-svc'
zabbix_password = decryptor('sysops-svc_enc', 'sysops-svc_key')

for z_url in zabbix_urls:
    for user in user_list:
        try:
            # New user details
            username = user['username']
            name = user['f_name']
            surname = user['l_name']
            user_group_name = user['grp_name']
            email = user['email_addr']
            phone = user['phone']

            # Connect to Zabbix API
            zapi = ZabbixAPI(zabbix_urls[z_url])
            zapi.login(zabbix_username, zabbix_password)

            #all_media_types = zapi.mediatype.get(output=["name"])
            #print("Available media types:", all_media_types)

            # Get user group ID
            user_groups = zapi.usergroup.get(filter={"name": user_group_name})
            if not user_groups:
                raise Exception(f"User group '{user_group_name}' not found.")
            group_id = user_groups[0]["usrgrpid"]

            # (Optional) Get role ID (if you're on Zabbix 6.0+ with custom roles)
            roles = zapi.role.get(filter={"name": user_role})   # "User role"
            if not roles:
                raise Exception("User role not found.")
            role_id = roles[0]["roleid"]

            # Media type IDs
            email_mediatype_id = zapi.mediatype.get(filter={"name": "Email"})[0]["mediatypeid"]
            sms_mediatype_id = zapi.mediatype.get(filter={"name": "SMS via Magfa"})[0]["mediatypeid"]

            # Create the user
            user = zapi.user.create(
                username=username,  # Changed from 'alias' to 'username'
                name=name,
                surname=surname,
                #passwd="StrongPassword123",
                usrgrps=[{"usrgrpid": group_id}],
                roleid=role_id,  # Only for Zabbix 6.0+
                medias=[
                    {
                        "mediatypeid": email_mediatype_id,
                        "sendto": [email],
                        "active": 0,
                        "severity": 63,
                        "period": "1-7,00:00-24:00"
                    },
                    {
                        "mediatypeid": sms_mediatype_id,
                        "sendto": [phone],
                        "active": 0,
                        "severity": 63,
                        "period": "1-7,00:00-24:00"
                    }
                ]
            )


            print(f"{z_url}: User '{username}' created with ID {user['userids'][0]}")

        except Exception as err:
            print(f'{z_url}: Error: {err}')
