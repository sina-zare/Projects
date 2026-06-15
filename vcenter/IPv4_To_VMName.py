from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import os
import warnings
import time
import ssl


# Print with delay function
def print_with_delay(text):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(0.03)
    print("\n")

# Decryption function
def decrypt(cipher_text, key):
  plain_text = ""
  for i in range(len(cipher_text)):
    char = cipher_text[i]
    plain_int = ord(char) - key
    plain_text += chr(plain_int)
  return plain_text

# Print with delay function
def print_with_delay_connecting(text):
    for char in text:
        print(f'Connecting, Please Wait {char}      ', end='', flush=True)
        time.sleep(0.009)
        os.system('cls' if os.name == 'nt' else 'clear')

# Print sequence of characters until connection is made
print_with_delay_connecting(["/","--","\\","|","/","--","\\","|","/","--","\\","|"])

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

try:
    # Connectiong to vCenter
    ME_VC = connect.SmartConnect(host='me-vc01.abramad.com',user= username,pwd= password,port=443,sslContext=context)
    me_content = ME_VC.RetrieveContent()
    me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
    me_vms = [vm for vm in me_vm_view.view if (vm.name.startswith("MER-") or vm.name.startswith("MEF-") or vm.name.startswith("MES-") or vm.name.startswith("MEA-") or vm.name.startswith("MEB-") or vm.name.startswith("MEM-") or vm.name.startswith("MEI-") or vm.name.startswith("MESA-"))]


    while True:

        input_vm_ip = input("Enter target IP: \n").lower().strip()

        for vm in me_vms:
            if (vm.runtime.powerState == "poweredOn"):
                # retrieve vm IP address
                vm_ip = ""
                if vm.guest is not None:
                    for nic in vm.guest.net:
                        if nic.ipConfig is not None:
                            for ip in nic.ipConfig.ipAddress:
                                if not ip.ipAddress.startswith('169.254') and not ip.ipAddress.startswith(
                                        'fe80'):
                                    vm_ip = ip.ipAddress

                if vm_ip == input_vm_ip:
                    print(vm.name)


        input("\n\n\n\n\n\n\n\nPress Enter to continue: ")
        # Clear CMD screen
        os.system('cls' if os.name == 'nt' else 'clear')

    Disconnect(ME_VC)

except:
    print_with_delay("Run the app again.")
    time.sleep(1.5)