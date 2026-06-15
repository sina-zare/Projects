import csv
import openpyxl
from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import warnings
import os


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



# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)
# *** Connecting to ME-VC01.Abramad.Com to get the Report ***
# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

# Connecting to vCenter
ME_VC = connect.SmartConnect(host='me-vc01.abramad.com',user= username,pwd= password,port=443,sslContext=context)
me_content = ME_VC.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if (vm.name.startswith("MER-") or vm.name.startswith("MERD-") or vm.name.startswith("MEF-") or vm.name.startswith("MES-") or vm.name.startswith("MEA-") or vm.name.startswith("MEB-") or vm.name.startswith("MEM-") or vm.name.startswith("MEI-") )]

counter = 0
for vm in me_vms:
    if (vm.name.lower().startswith("mer-refah") and vm.name.lower().endswith("a1")) or (vm.name.lower().startswith("mer-refah") and vm.name.lower().endswith("a2")) or (vm.name.lower().startswith("mer-refah") and vm.name.lower().endswith("a3")):
        counter += 1
        # Get National ID Status
        vm_national_id = "Null"
        custom_value_n = vm.summary.customValue
        for i in custom_value_n:
            if i.key == 611:
                vm_national_id = i.value

        # Get VM Persian Name
        vm_persian_name = "Null"
        custom_value_n = vm.summary.customValue
        for i in custom_value_n:
            if i.key == 103:
                vm_persian_name = i.value

        # Get VM RAM
        vm_ram = int(vm.config.hardware.memoryMB / 1024)

        # OS Version
        guest_os = vm.guest.guestFullName

        print(f"Name: {vm.name}\nRAM: {vm_ram}\n")