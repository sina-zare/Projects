from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import csv
import os
import time
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
username = decryptor("enc_sinaz_abramad","key_sinaz_abramad")
password = decryptor("enc_sinaz_pass","key_sinaz_pass")

# *** Connecting to ME-VC01.Abramad.Com to get the Report ***

# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

ME_VC = connect.SmartConnect(host='me-vc01.abramad.com',user= username,pwd= password,port=443,sslContext=context)
me_content = ME_VC.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if (vm.name.startswith("MER-") or vm.name.startswith("MEF-") or vm.name.startswith("MES-") or vm.name.startswith("MEA-") or vm.name.startswith("MEB-") or vm.name.startswith("MEM-") or vm.name.startswith("MEI-") )]
for vm in me_vms:
    if (vm.name == "MEA-ShoyaSaz-A1"):
        note = vm.config.annotation
        print(note)


