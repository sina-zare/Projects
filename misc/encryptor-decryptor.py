# Encryption function
def encrypt(plain_text, key):
  cipher_text = ""
  for i in range(len(plain_text)):
    char = plain_text[i]
    cipher_int = ord(char) + key
    cipher_text += chr(cipher_int)
  return cipher_text

# Decryption function
def decrypt(cipher_text, key):
  plain_text = ""
  for i in range(len(cipher_text)):
    char = cipher_text[i]
    plain_int = ord(char) - key
    plain_text += chr(plain_int)
  return plain_text



password = "XXX"
key = 11

# Encrypt
cipher = encrypt(password, key)
#print(cipher) # n}pCvvtrneb

# Decrypt
plain = decrypt(cipher, key)
#print(plain) # mypassword


###############################################################################
###############################################################################
import os
from cryptography.fernet import Fernet

# Generate a key and store it securely
#key = Fernet.generate_key()
#with open("secret.key", "wb") as key_file:
#    key_file.write(key)
#
# # Load the key
# with open("sina_password_secret.key", "rb") as key_file:
#     key = key_file.read()
#
# # Encrypt sensitive data
# encryption_key = Fernet(key)
#
# encrypted_password = encryption_key.encrypt("XXX".encode())
# print(f"Encrypted Password: {encrypted_password}")
# #env_var = b'gAAAAABmFRdvWEtA5gw07n5b7tm3F958hBs5hTZfVAqjMsuGV0sZk-7jH3otB_TE3gs8MRfo0csWANXri7jN0de7VXIcdiTqqg=='
#
# decrypted_password = encryption_key.decrypt(env_var.decode())
# print(decrypted_password)
# print(f"key: {key}\nencryption_key: {encryption_key}\nencrypted_password: {encrypted_password}\ndecrypted_password: {decrypted_password.decode()}")

