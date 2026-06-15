
from pyvim.connect import Disconnect
from pyvim import connect
from pyVmomi import vim
import jdatetime
import warnings
import ssl
import os


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

username = 'sina.z@abramad.com'
password = decryptor("enc_sinaz_pass","key_sinaz_pass")


# Ignore the warning
warnings.filterwarnings("ignore", category=DeprecationWarning)
# *** Connecting to ME-VC01.Abramad.Com to get the Report ***
# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

# Connecting to vCenter
ME_VC = connect.SmartConnect(host='me-vc01.abramad.com', user=username, pwd=password, port=443, sslContext=context)
me_content = ME_VC.RetrieveContent()
me_vm_view = me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True)
me_vms = [vm for vm in me_vm_view.view if (vm.name.lower().startswith("me"))]
sorted_vms = sorted(me_vms, key=lambda vm: vm.name.lower())


mer = 0
mea = 0
mea_os = []
mea_lin = 0
mea_win = 0
mef = 0
mes = 0
meb = 0
mesa = 0
mesa_os = []
mem = 0
me = 0
me_os = []
me_lin = 0
me_win = 0
med = 0
med_os = []
med_lin = 0
med_win = 0
mep = 0
mep_os = []
mep_lin = 0
mep_win = 0
meo = 0
meo_os = []
meo_lin = 0
meo_win = 0

for vm in sorted_vms:

    if vm.name.lower().startswith('mer-') or vm.name.lower().startswith('merd-'):
        mer += 1

    if vm.name.lower().startswith('mea-'):
        mea_gos = vm.summary.config.guestFullName
        mea_os.append(mea_gos)
        mea += 1

    if vm.name.lower().startswith('mef-'):
        mef += 1

    if vm.name.lower().startswith('mes-'):
        mes += 1

    if vm.name.lower().startswith('meb-'):
        meb += 1

    if vm.name.lower().startswith('mesa-'):
        mesa_gos = vm.summary.config.guestFullName
        mesa_os.append(mesa_gos)
        mesa += 1

    if vm.name.lower().startswith('mem-'):
        mem += 1

    if vm.name.lower().startswith('me-'):
        me_gos = vm.summary.config.guestFullName
        me_os.append(me_gos)
        me += 1

    if vm.name.lower().startswith('med-'):
        med_gos = vm.summary.config.guestFullName
        med_os.append(med_gos)
        med += 1

    if vm.name.lower().startswith('mep-'):
        mep_gos = vm.summary.config.guestFullName
        mep_os.append(mep_gos)
        mep += 1

    if vm.name.lower().startswith('meo-'):
        meo_gos = vm.summary.config.guestFullName
        meo_os.append(meo_gos)
        meo += 1


for i in me_os:
    if 'Linux' in i or 'CentOS' in i:
        me_lin += 1
    elif 'Windows' in i:
        me_win += 1

for i in med_os:
    if 'Linux' in i or 'CentOS' in i:
        med_lin += 1
    elif 'Windows' in i:
        med_win += 1

for i in mep_os:
    if 'Linux' in i or 'CentOS' in i:
        mep_lin += 1
    elif 'Windows' in i:
        mep_win += 1

for i in meo_os:
    if 'Linux' in i or 'CentOS' in i:
        meo_lin += 1
    elif 'Windows' in i:
        meo_win += 1

for i in mea_os:
    if 'Linux' in i or 'CentOS' in i:
        mea_lin += 1
    elif 'Windows' in i:
        mea_win += 1

print(f'Operation Total: {me}')
print(f'  ME Linux: {me_lin}')
print(f'  ME Windows: {me_win}')
print('\n')
print(f'Development Total: {med}')
print(f'  MED Linux: {med_lin}')
print(f'  MED Windows: {med_win}')
print('\n')
print(f'OpenStack Total: {meo}')
print(f'  MEO Linux: {meo_lin}')
print(f'  MEO Windows: {meo_win}')
print('\n')
print(f'Platform Total: {mep}')
print(f'  MEP Linux: {mep_lin}')
print(f'  MEP Windows: {mep_win}')
print('\n')
print(f'Managed Customers: {mer + mea + meb + mef + mes + mem + mesa}')
print(f'  Rahkaran: {mer}')
print(f'  Automation: {mea}')
print(f'    Automation Linux: {mea_lin}')
print(f'    Automation Windows: {mea_win}')
print(f'  Saham Fasl: {mef}')
print(f'  Saham Abri: {mesa}')
print(f'  Sepidar: {mes}')
print(f'  BI: {meb}')
print(f'  MEM: {mem}')
print('\n')

