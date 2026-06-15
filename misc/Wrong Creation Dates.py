from pyvim import connect
from pyVmomi import vim
import ssl
from persiantools.jdatetime import JalaliDate
import os
import warnings

'''
from persiantools.jdatetime import JalaliDate

# Persian date to check
date_to_check = JalaliDate(1402, 1, 1)

# Boundary Persian dates
lower_boundary = JalaliDate(1402, 1, 1)
upper_boundary = JalaliDate(1402, 12, 29)

# Check if the Persian date falls between the boundary dates
if lower_boundary <= date_to_check <= upper_boundary:
    print("The Persian date falls between the boundary dates.")
else:
    print("The Persian date does not fall between the boundary dates.")
'''


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

#print_with_delay("VMs Between Dates, made with love by S.Z")
#time.sleep(1)
# *** Connecting to ME-VC01.Abramad.Com to get the Report ***
# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

# Connecting to vCenter
ME_VC = connect.SmartConnect(host='me-vc01.abramad.com',user= username,pwd= password,port=443,sslContext=context)
me_content = ME_VC.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if (vm.name.startswith("MER-") or vm.name.lower().startswith("MERD-") or vm.name.startswith("MEF-") or vm.name.startswith("MES-") or vm.name.startswith("MEA-") or vm.name.startswith("MEB-") or vm.name.startswith("MEM-") or vm.name.startswith("MEI-") or vm.name.startswith("MESA-") )]


count = 0
# Start Calculation of falling in dates VMs
for vm in me_vms:



    real_vm_creation_date = str(JalaliDate(vm.config.createDate)).replace("-", "/")
    # Get VM Creation Date
    vm_creation_date = ""

    custom_value_d = vm.summary.customValue
    for i in custom_value_d:
        if i.key == 104:
            vm_creation_date = i.value

    #print(vm.name)
    #print(vm_creation_date)
    #print(real_vm_creation_date, "\n")

    if vm_creation_date.strip() != real_vm_creation_date.strip():

        count += 1
        print("VM Name:", vm.name)
        print("Filled With:", vm_creation_date)
        print("Must Be Filled With:", real_vm_creation_date, "\n")

print("Count:", count)
