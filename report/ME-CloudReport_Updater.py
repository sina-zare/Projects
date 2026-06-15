import sys
import time
import pyodbc
import os

# Credentials
from cryptography.fernet import Fernet
def decryptor(enc_env_var, key_env_var):

    # Load the key
    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = (os.environ.get(enc_env_var)).encode()
    # Decrypt Data
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())

    return decrypted_password.decode()

password = decryptor("pyodbc_enc","pyodbc_key")

def record_disabler(local_url):

    # Connection parameters
    server = 'ME-CloudReport.cloud.local'
    database = 'Monitoring'
    # Establish connection
    connection = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+'pyodbc'+';PWD='+password)
    # Create a cursor
    cursor = connection.cursor()
    # Execute SQL query
    sql_query = f"UPDATE dbo.App SET CheckStatus = 'False' WHERE URL LIKE '{local_url}'"
    cursor.execute(sql_query)
    # Commit the transaction
    connection.commit()
    # Close connection
    connection.close()
    print("Disabled successfully.")


def record_changer(new_url, old_url):

    # Connection parameters
    server = 'ME-CloudReport.cloud.local'
    database = 'Monitoring'
    # Establish connection
    connection = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+'pyodbc'+';PWD='+password)
    # Create a cursor
    cursor = connection.cursor()
    # Execute SQL query
    sql_query = f"UPDATE dbo.App SET URL = '{new_url}' WHERE URL LIKE '{old_url}'"
    cursor.execute(sql_query)
    # Commit the transaction
    connection.commit()
    # Close connection
    connection.close()
    print("Updated successfully.")


while True:
    choise = input("1) Disable Record\n2) Change Record\n3) Exit\n\n: ")

    if choise == "1":
        os.system('cls' if os.name == 'nt' else 'clear')
        record_disabler(input("Enter Full URL on 'CloudReport' to Disable: "))
        input("\nPress Enter to Continue")
        os.system('cls' if os.name == 'nt' else 'clear')

    elif choise == "2":
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Enter New URL then Old URL to Replace.")
        record_changer(input("New URL: "), input("Old URL: "))
        input("\nPress Enter to Continue")
        os.system('cls' if os.name == 'nt' else 'clear')

    elif choise == "3":
        print("Adius ;)")
        time.sleep(2)
        sys.exit()

    else:
        print("Wrong Selection")
        time.sleep(2)
