import win32net
import win32security

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

if __name__ == "__main__":
    administrators = get_local_administrators()
    print("Members of the Administrators group:")
    for admin in administrators:
        print(admin)
