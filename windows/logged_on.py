from stdiomask import getpass
import subprocess
import os


# Decryption function
def decrypt(cipher_text, key):
    plain_text = ""
    for i in range(len(cipher_text)):
        char = cipher_text[i]
        plain_int = ord(char) - key
        plain_text += chr(plain_int)
    return plain_text


# Credentials
from cryptography.fernet import Fernet
def decryptor(enc_env_var, key_env_var):

    # Load the key
    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = (os.environ.get(enc_env_var)).encode()
    # Decrypt Data
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())

    #print(f"Decryped Text: {decrypted_password}")
    return decrypted_password.decode()

username = 'support@cloud.local'
password = decryptor('support-svc_enc', 'support-svc_key')

while True:

    server_name = input("Enter FQDN of server: ")

    powershell_script = f'''
  $user = "{username}" 
  $pw = ConvertTo-SecureString "{password}" -AsPlainText -Force
  $creds = New-Object System.Management.Automation.PSCredential ($user, $pw)

  '''
    # Take user info
    powershell_script += f'''Invoke-Command -ComputerName {server_name} '''
    powershell_script += '''-Credential $creds -ScriptBlock {QUERY USER}'''

    result = subprocess.run(["powershell.exe", "-Command", powershell_script], stdout=subprocess.PIPE)

    unprocessd = str(result.stdout.decode()).split("\n")
    del unprocessd[0]

    userpass = []
    active_logged_on_users = []

    for i in unprocessd:
        userpass.append(i.split(" "))

    for i in userpass:
        if "Active" in i:
            active_logged_on_users.append(i[1])

    if len(active_logged_on_users) == 0:
        print("No Active Users Found!")

    # store display names in a list
    display_name_unprocessed = []
    display_name_active_users = []

    for display in active_logged_on_users:
        give_info_display_name = f'''
    Import-Module ActiveDirectory
    Get-ADUser -Server me-dc1.cloud.local -Identity {display} -Properties * | Select-Object DisplayName
  '''
        user_display_name_info = subprocess.run(["powershell.exe", "-Command", give_info_display_name],
                                                stdout=subprocess.PIPE)
        display_name_unprocessed.append(str((user_display_name_info.stdout.decode())).split("\n"))

    for i in display_name_unprocessed:
        display_name_active_users.append((i[3][0:-1]).strip())

    # store group names in a list
    group_name_unprocessed = []
    group_name_active_users = []

    for groupname in active_logged_on_users:
        give_info_group_name = f'''
    Import-Module ActiveDirectory
    Get-ADPrincipalGroupMembership -Server me-dc1.cloud.local -Identity {groupname} | select Name
  '''
        user_group_name_info = subprocess.run(["powershell.exe", "-Command", give_info_group_name],
                                              stdout=subprocess.PIPE)
        group_name_unprocessed.append(str((user_group_name_info.stdout.decode())).split("\n"))

    for i in group_name_unprocessed:
        group_name_active_users.append(i[3:-3])

    # how you can remove all spaces and "\r" from each item in the nested lists:
    for nested_list in group_name_active_users:
        for i, item in enumerate(nested_list):
            nested_list[i] = item.strip().replace("\r", "")

    active_logged_on_users_info_dict = dict(zip(display_name_active_users, group_name_active_users))

    print("\nActive Users: ")
    for key, value in active_logged_on_users_info_dict.items():
        print(f"Username: {key}\nMember of: {value}\n\n")

    quit = input("\n\n\nPress Enter to continue.")
    os.system('cls' if os.name == 'nt' else 'clear')