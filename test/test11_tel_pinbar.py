from cryptography.fernet import Fernet

def encryptor(password, key_name):
    # Generate a key and store it securely
    key = Fernet.generate_key()
    with open(f"{key_name}.key", "wb") as key_file:
        key_file.write(key)

    # Encrypt sensitive data
    encryption_key = Fernet(key)
    encrypted_password = encryption_key.encrypt(password.encode())

    print(f"Encryped Text: {encrypted_password}")
    print(f'Key: {key}')
    return encrypted_password


encryptor('PassW0rd', 'key')