from cryptography.fernet import Fernet
import subprocess

def encryptor_env(password, env_enc, env_key):
    # Generate a key and store it securely
    key = Fernet.generate_key()

    # Encrypt sensitive data
    encryption_key = Fernet(key)
    encrypted_password = encryption_key.encrypt(password.encode())

    # Saving Enc_Password and key to System Envs
    subprocess.run(['setx', '/M', env_enc, f'{str(encrypted_password)[2:-1]}'], check=True)
    subprocess.run(['setx', '/M', env_key, f'{str(key)[2:-1]}'], check=True)

    print(f"Password Encrypted.")

# Saving Encrypted Password to System Envs
encryptor_env('0nlyGodenough20#', "test-svc_enc", "test-svc_key")
