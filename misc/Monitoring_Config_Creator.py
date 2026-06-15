

import time
from jdatetime import date, datetime
import os
import shutil
from csv import DictReader

# Take Data from CSV File
with open("C:\\Users\\sina.z\\Desktop\\Python-Projects\\Monitoring_Config_Creator.csv") as csv_file:
    data = DictReader(csv_file)

    for datum in data:
        data_dict = datum

customer_name = data_dict["Customer_Name"]
email_addresses = data_dict["Email_Addresses"].lower()


# Getting Backup from main .py files
today_date_jalali = date.today().strftime("%Y-%m-%d")
current_time = (str(datetime.now())[11:19]).replace(":", "-")
backup_path = f"C:\\Users\\sina.z\\Desktop\\Python-Projects\\Backup_Files\\{today_date_jalali}"

# Ensure log directory exists, create if it doesn't
if not os.path.exists(backup_path):
    os.makedirs(backup_path)

# Source file path
me_disk_vip = "C:\\Users\\sina.z\\Desktop\\Python-Projects\\ME_Disk_VIP_Agent.py"
me_resource_vip = "C:\\Users\\sina.z\\Desktop\\Python-Projects\\ME_Resource_VIP_Agent.py"
agent_cache_cleaner = "C:\\Users\\sina.z\\Desktop\\Python-Projects\\Agent_Cache_Cleaner.py"

me_disk_vip_new_name_path = f"{backup_path}\\{current_time}-ME_Disk_VIP_Agent.py"
me_resource_vip_new_name_path = f"{backup_path}\\{current_time}-ME_Resource_VIP_Agent.py"
agent_cache_cleaner_new_name_path = f"{backup_path}\\{current_time}-Agent_Cache_Cleaner.py"

# Copy the backup to the destination folder
shutil.copy(me_disk_vip, me_disk_vip_new_name_path)
shutil.copy(me_resource_vip, me_resource_vip_new_name_path)
shutil.copy(agent_cache_cleaner, agent_cache_cleaner_new_name_path)
print("Backups were taken.")


# Disk Config to append
me_disk_config = f'''

# {customer_name}
low_disk_checker(
    "mail.systemgroup.net",
    username,
    password,
    'SolarwindsMonitoringVIP/ME_Disk/{customer_name}',
    "ME-Disk-VIP-{customer_name}-Duplicate-Check-DB.csv",
    "{email_addresses}",
    "support@abramad.com,alireza.ja@abramad.com")

'''

# Disk Resource to append
me_resource_config = f'''

# {customer_name}
resource_peak_checker('SolarwindsMonitoringVIP/ME_Resource/{customer_name}',
                      "ME-Resource-VIP-{customer_name}-Duplicate-Check-DB.csv",
                      "{email_addresses}",
                      "support@abramad.com,alireza.ja@abramad.com")
                        
'''

# Append Original .py Files
with open(me_disk_vip, 'a') as ME_Disk_VIP:
    # Write the content you want to append
    ME_Disk_VIP.write(me_disk_config)

with open(me_resource_vip, 'a') as ME_Resource_VIP:
    # Write the content you want to append
    ME_Resource_VIP.write(me_resource_config)

print(f"Original Files were Appended for {customer_name}")


# Creating Database Files
with open(f"C:\\Users\\sina.z\\Desktop\\Python-Projects\\EmailsTicketNo\\ME-Disk-VIP\\ME-Disk-VIP-{customer_name}-Duplicate-Check-DB.csv", 'w'):
    pass

with open(f"C:\\Users\\sina.z\\Desktop\\Python-Projects\\EmailsTicketNo\\ME-Resource-VIP\\ME-Resource-VIP-{customer_name}-Duplicate-Check-DB.csv", 'w'):
    pass

print("Database CSV Files Created")


# Appending Agent_Cache_Cleaner
cache_cleaner_config = f"""

#{customer_name}
me_disk_vip_{customer_name.lower()}_check_db_path = "C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/ME-Disk-VIP/ME-Disk-VIP-{customer_name}-Duplicate-Check-DB.csv"
me_resource_vip_{customer_name.lower()}_check_db_path = "C:/Users/sina.z/Desktop/Python-Projects/EmailsTicketNo/ME-Resource-VIP/ME-Resource-VIP-{customer_name}-Duplicate-Check-DB.csv"
empty_csv_file(me_disk_vip_{customer_name.lower()}_check_db_path)
empty_csv_file(me_resource_vip_{customer_name.lower()}_check_db_path)

"""

# Append Original Agent_Cache_Cleaner
with open(agent_cache_cleaner, 'a') as Agent_Cache_Cleaner:
    # Write the content you want to append
    Agent_Cache_Cleaner.write(cache_cleaner_config)

print(f"Agent Cache Cleaner Appended for {customer_name}")



try:
    ########### Folder Creation in Mail Server ############
    import imaplib
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
    #new_folder = 'AAAA'

    create_folder_in_folder(server, username, password, parent_folder_disk, customer_name)
    create_folder_in_folder(server, username, password, parent_folder_resource, customer_name)

    print(f"Folders were created in mail server")
    time.sleep(5)

except Exception as e:
    print(f"Error: \n{e}")
    time.sleep(10)
