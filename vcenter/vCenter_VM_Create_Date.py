from pyvim import connect
from pyVmomi import vim
import ssl
from persiantools.jdatetime import JalaliDate
import os
import warnings

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
username = "sina.z@abramad.com"
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
me_vms = [vm for vm in me_vm_view.view if (vm.name.startswith("vts-mrs-minio"))]

for vm in me_vms:

    real_vm_creation_date = str(JalaliDate(vm.config.createDate)).replace("-", "/")
    print(f"{vm.name}: {real_vm_creation_date}")

