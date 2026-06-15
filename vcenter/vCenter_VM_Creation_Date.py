import os
import ssl
import csv
import pytz
import jdatetime
import warnings
from cryptography.fernet import Fernet
from pyvim import connect
from pyVmomi import vim
import colorlog

# --- Setup Color Logger ---
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'bold_red',
    }
))

logger = colorlog.getLogger()
logger.addHandler(handler)
logger.setLevel("INFO")

# --- Disable SSL Warnings ---
warnings.filterwarnings("ignore", category=DeprecationWarning)

# --- Decryption Function ---
def decryptor(enc_env_var, key_env_var):
    key = os.environ.get(key_env_var)
    if not key:
        raise EnvironmentError(f"Missing environment variable for key: {key_env_var}")

    encrypted_password = os.environ.get(enc_env_var)
    if not encrypted_password:
        raise EnvironmentError(f"Missing environment variable for encrypted password: {enc_env_var}")

    fernet = Fernet(key)
    decrypted_password = fernet.decrypt(encrypted_password.encode())
    return decrypted_password.decode()

# --- Read VM Names from CSV ---
def read_vm_list(csv_path):
    vm_list = []
    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            if row:
                vm_list.append(row[0].strip().lower())
    return vm_list

# --- Connect to vCenter ---
def get_vcenter_connection(host, username, password, context):
    return connect.SmartConnect(host=host, user=username, pwd=password, port=443, sslContext=context)

# --- Retrieve VMs from vCenter ---
def get_all_vms(si):
    content = si.RetrieveContent()
    vm_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    vms = vm_view.view
    vm_view.Destroy()
    return vms

# --- Convert to Jalali ---
def convert_to_jalali(dt):
    tehran_tz = pytz.timezone("Asia/Tehran")
    dt_tehran = dt.astimezone(tehran_tz)
    jalali_date = jdatetime.datetime.fromgregorian(datetime=dt_tehran)
    return jalali_date.strftime("%Y/%m/%d %H:%M:%S")


username = 'sysops-svc@abramad.com'
password = decryptor('sysops-svc_enc', 'sysops-svc_key')

context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

vcenter_list = [
    'vts-vc01.abramad.com',
    'vab-vc01.abramad.com',
    'vra-vc01.abramad.com',
    'me-vc01.abramad.com'
]

vm_list_path = "C:\\Temp\\vm_names.csv"
target_vm_list = read_vm_list(vm_list_path)

for target_vm in target_vm_list:
    print('\n')
    logger.info(f"Searching for VM: {target_vm}")
    found = False

    for vc in vcenter_list:
        try:
            si = get_vcenter_connection(vc, username, password, context)
            vms = get_all_vms(si)

            for vm in vms:
                vm_name = vm.name.lower() if vm.name else ""
                vm_hostname = vm.summary.guest.hostName.lower() if vm.summary.guest and vm.summary.guest.hostName else ""

                if target_vm == vm_name or target_vm == vm_hostname:
                    logger.info(f"\t* Found in {vc}: {vm.name} ({vm_hostname})")

                    try:
                        creation_date = vm.config.createDate
                        jalali_str = convert_to_jalali(creation_date)
                        logger.info(f"\t* Creation Date (Tehran +3:30): {jalali_str}")
                    except Exception as e:
                        logger.warning(f"\t! Could not get creation date: {e}")

                    found = True
                    break

        except Exception as conn_err:
            logger.error(f"Failed to connect to {vc}: {conn_err}")

        finally:
            try:
                connect.Disconnect(si)
            except:
                pass

        if found:
            break

    if not found:
        logger.warning(f"\t! VM '{target_vm}' not found in any vCenter.")


