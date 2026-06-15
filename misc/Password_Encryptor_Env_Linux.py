from cryptography.fernet import Fernet
import os

def encryptor_env(password, env_enc, env_key):
    # Generate a key and store it securely
    key = Fernet.generate_key()

    # Encrypt sensitive data
    encryption_key = Fernet(key)
    encrypted_password = encryption_key.encrypt(password.encode())

    # Define the line format for /etc/environment
    env_lines = [
        f'{env_enc}="{encrypted_password.decode()}"\n',
        f'{env_key}="{key.decode()}"\n'
    ]

    # Append the variables to /etc/environment
    with open("/etc/environment", "a") as env_file:
        env_file.writelines(env_lines)

    print(f"Password Encrypted and saved to /etc/environment.")

# Run the function
encryptor_env('xxx', "sina.z_enc", "sina.z_key")
