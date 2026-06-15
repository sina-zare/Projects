from cryptography.fernet import Fernet
import time
import sys
import os

def decryptor(enc_env_var, key_env_var):
    try:
        # Check if Env Variables are Null
        enc_value = os.environ.get(enc_env_var)
        key_value = os.environ.get(key_env_var)

        if enc_value is None or key_value is None:
            print("No Env Found or You need to Run the script as Administrator")
            time.sleep(10)
            sys.exit()

        # Convert key and encrypted password to bytes
        key = key_value.encode()
        encrypted_password = enc_value.encode()

        # Load the key into Fernet
        encryption_key = Fernet(key)

        # Decrypt Data
        decrypted_password = encryption_key.decrypt(encrypted_password)

        return decrypted_password.decode()

    except Exception as e:
        print("Error in decryptor Function.")
        print("An error occurred:", e)
        time.sleep(10)

print(decryptor('sysops_svc_enc', 'sysops_svc_key'))
password = decryptor('sysops_svc_enc', 'sysops_svc_key')
