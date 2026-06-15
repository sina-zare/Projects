from cryptography.fernet import Fernet
import os


def encryptor(password, key_name):

    # Generate a key and store it securely
    key = Fernet.generate_key()
    with open(f"{key_name}.key", "wb") as key_file:
        key_file.write(key)

    # Encrypt sensitive data
    encryption_key = Fernet(key)
    encrypted_password = encryption_key.encrypt(password.encode())

    print(f"Encryped Text: {encrypted_password}")
    return encrypted_password


def decryptor(enc_env_var, key_env_var):

    # Load the key

    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = (os.environ.get(enc_env_var)).encode()
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())

    #print(f"Decryped Text: {decrypted_password}")
    return decrypted_password.decode()

#encryptor("sina.z@sgcloud.local", "sina_password_secret")
passwd = decryptor("enc_sinaz_cloud","key_sinaz_cloud")
print(passwd)

