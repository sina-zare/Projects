import imaplib
import os
from cryptography.fernet import Fernet


def create_folder_in_folder(server, username, password, parent_folder, new_folder):
    # Connect to the IMAP server
    mail = imaplib.IMAP4_SSL(server)
    # Login
    mail.login(username, password)
    #print(mail.list())  # Print the list of available folders
    # Select the parent folder
    mail.select(parent_folder)
    # Create the new folder
    mail.create(parent_folder + '/' + new_folder)
    # Logout
    mail.logout()

def decryptor(enc_env_var, key_env_var):

    # Load the key
    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = (os.environ.get(enc_env_var)).encode()
    # Decrypt Data
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())

    #print(f"Decryped Text: {decrypted_password}")
    return decrypted_password.decode()




# Usage example
server = "mail.systemgroup.net"
username = decryptor("enc_sinaz_abramad","key_sinaz_abramad")
password = decryptor("enc_sinaz_pass","key_sinaz_pass")
parent_folder_disk = 'SolarwindsMonitoringVIP/ME_Disk'
parent_folder_resource = 'SolarwindsMonitoringVIP/ME_Resource'
new_folder = 'AAAA'#input('Folder Name: ')

#create_folder_in_folder(server, username, password, parent_folder_disk, new_folder)
#create_folder_in_folder(server, username, password, parent_folder_resource, new_folder)


