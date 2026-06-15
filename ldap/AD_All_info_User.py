try:
    from ldap3 import Server, Connection, SUBTREE, ALL_ATTRIBUTES
    from stdiomask import getpass
except Exception as e:
    print("Error in Importing Modules.")
    input(e)

def get_user_groups(username, password, domain_controller, base_dn):
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
            print("No entries found for user:", checked_username)
            return []

        # Extract and return groups from the 'memberOf' attribute
        user_entry = conn.entries[0]
        return conn.entries

    except Exception as e:
        print("Error in Function.")
        print("An error occurred:", e)
        input()
        return []

try:
    # Example usage
    username = input("Username: ")
    password = getpass("Password: ")
    domain_controller = 'ldap://ME-DC1.cloud.local'
    base_dn = 'DC=cloud,DC=local'

    print("\n")
    groups = get_user_groups(username, password, domain_controller, base_dn)
    for i in groups:
        print("Groups for user:", i)
    input()

except Exception as e:
    print("Error in Body.")
    input(e)