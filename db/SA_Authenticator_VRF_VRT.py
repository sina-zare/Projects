try: # Module Importing
    from ldap3 import Server, Connection, SUBTREE, ALL_ATTRIBUTES
    from stdiomask import getpass
    import os
    import win32net
    import win32security
    from cryptography.fernet import Fernet
    import time
    import sys

except Exception as e:
    print("Error in Importing Modules.")
    input(e)


# Function Definition
def get_ad_user_groups(username, password, domain_controller, base_dn):
    try:
        checked_username = ""
        if "@" in username:
            checked_username = username
        else:
            checked_username = username + "@cloud.local"


        # Set up LDAP connection
        server = Server(domain_controller)
        conn = Connection(server, user=checked_username, password=password, auto_bind=True)

        # Define LDAP search parameters
        search_filter = f'(&(objectClass=user)(UserPrincipalName={checked_username}))'
        conn.search(search_base=base_dn,
                    search_filter=search_filter,
                    search_scope=SUBTREE,
                    attributes=[ALL_ATTRIBUTES])

        if len(conn.entries) == 0:
            print("No Groups found for user:", checked_username)
            print("Probably your user is not created in Customers OU.")
            time.sleep(10)
            sys.exit()
            return []

        # Extract and return groups from the 'memberOf' attribute
        user_entry = conn.entries[0]
        groups_dn = user_entry['memberOf'].values

        # Pruning Distinguished Names
        groups = []
        for group_dn in groups_dn:
            gp_holder = group_dn.split(",")
            groups.append(gp_holder[0][3:])

        return groups

    except Exception as e:
        print("Error in get_user_groups Function.")
        print("An error occurred:", e)
        time.sleep(10)
        sys.exit()
        return []



def is_group(sid):
    """
    Check if the SID belongs to a group.
    """
    try:
        _, _, account_type = win32security.LookupAccountSid(None, sid)
        return account_type == win32security.SidTypeGroup
    except:
        return False

def get_local_administrators():
    # Get the SID (Security Identifier) of the Administrators group
    admins_sid = win32security.ConvertStringSidToSid("S-1-5-32-544")

    # Query members of the Administrators group
    members, _, _ = win32net.NetLocalGroupGetMembers(None, "Administrators", 2)

    # Filter out user accounts
    admin_members = []
    for member in members:
        if is_group(member['sid']):
            name, _, _ = win32security.LookupAccountSid(None, member['sid'])
            admin_members.append(name)

    return admin_members

def decryptor(enc_env_var, key_env_var):
    try:
        # Check if Env Variables are Null
        if os.environ.get(enc_env_var) == None or os.environ.get(key_env_var) == None:
            print("Run the app as Administrator.")
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


try: # Main App
    # Credentials
    username = input("Username: ")
    password = getpass("Password: ")
    domain_controller = 'ldap://VRA-DC01.cloud.local'
    #base_dn = 'OU=RahkaranAbri,DC=cloud,DC=local'
    base_dn = 'DC=cloud,DC=local'
    os.system('cls' if os.name == 'nt' else 'clear')

    #if username.lower() == "sina.z" or username.lower() == "sina.z@cloud.local" or username.lower() == "ma" or username.lower() == "ma@cloud.local" or username.lower() == "soheila.s" or username.lower() == "soheila.s@cloud.local" or username.lower() == "rayehe.r" or username.lower() == "rayehe.r@cloud.local" or username.lower() == "mohammad.bar" or username.lower() == "mohammad.bar@cloud.local" or username.lower() == "amir.rz" or username.lower() == "amir.rz@cloud.local" or username.lower() == "parisa.j" or username.lower() == "parisa.j@cloud.local" or username.lower() == "ali.af" or username.lower() == "ali.af@cloud.local":
    #    base_dn = 'DC=cloud,DC=local'

    ad_groups = get_ad_user_groups(username, password, domain_controller, base_dn)
    local_admins = get_local_administrators()

    #print(f"Groups that {username} is a Member Of: ", ad_groups)
    #print(f"Local Administrators: ", local_admins)
    #print("\n\n")

    ad_groups_len = len(ad_groups)
    flag = 0
    pass_seen = False
    for ad_grp in ad_groups:
        if ad_grp in local_admins:
            if not pass_seen:
                print(f"Access Granted:  {username} ~~> {ad_grp}")
                password = decryptor("sgsp", "sgsk")
                print(f"Copy the password within 30 seconds:\n\n{password}")
                pass_seen = True
        else:
            flag += 1

        if ad_groups_len == flag:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("You Don't have Permission to use SA Password.\ncontact 'support@abramad.com'")
            time.sleep(10)
            sys.exit()



    time.sleep(30)



except Exception as e:
    print("An error occurred:", e)
    time.sleep(10)
    sys.exit()