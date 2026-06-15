from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter
from pyvim.connect import SmartConnect, Disconnect
from cryptography.fernet import Fernet
from pyVmomi import vim
import traceback
import time
import ssl
import sys
import os


# --- Configuration ---
script_name = 'product_line_resources'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'https://me-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
datacenter = 'vanak_miremad'
target = 'all_vms'


# Create a registry for our custom metrics
registry = CollectorRegistry()

# Define metrics
duration_gauge = Gauge('script_exec_duration_seconds', 'Duration of my script', registry=registry)
status_gauge = Gauge('script_success', 'Whether script succeeded (1) or failed (0)', registry=registry)
total_execution_counter = Counter('script_total_execs', 'Total number of times the script has run', registry=registry)
total_failed_execution_counter = Counter('script_total_failed_execs', 'Total number of times the script has failed to finish gracefully', registry=registry)
last_error_message = Gauge('script_last_error_message','The last error message encountered during script execution',['error_summary', 'error_detail'], registry=registry)

# Service Specific Metrics
product_members_total = Gauge(
    'product_members_total',
    'Total number of clients per product line',
    ['product', 'total_on', 'total_off'],
    registry=registry
)

product_used_memory_total = Gauge(
    'product_used_memory_total',
    'Total amount of used memory per product line',
    ['product', 'used_memory_on', 'used_memory_off'],
    registry=registry
)

product_used_cpu_total = Gauge(
    'product_used_cpu_total',
    'Total amount of used cpu per product line',
    ['product', 'used_cpu_on', 'used_cpu_off'],
    registry=registry
)

product_used_disk_total = Gauge(
    'product_used_disk_total',
    'Total amount of used disk per product line',
    ['product', 'used_disk_on', 'used_disk_off'],
    registry=registry
)


start_time = time.time()
success = True
error_string_summary = ""
error_string_detail = ""

# --- Read script run counter from file ---
def read_value_from_file(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)  # Create the directory if it doesn't exist

    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.write('0')
        return 0

    try:
        with open(file_path, 'r') as f:
            return int(f.read().strip())
    except ValueError:
        # In case of a corrupt or non-integer value
        return 0

# --- Write updated count to file ---
def write_value_to_file(file_path, value):
    with open(file_path, 'w') as f:
        f.write(str(value))

def decryptor(enc_env_var, key_env_var):
    try:
        # Check if Env Variables are Null
        if os.environ.get(enc_env_var) == None or os.environ.get(key_env_var) == None:
            print("No Env Found or You need to Run the script as Administrator")
            time.sleep(10)
            sys.exit()

        # Load the key
        key = os.environ.get(key_env_var)
        encryption_key = Fernet(key)
        encrypted_password = (os.environ.get(enc_env_var)).encode()
        # Decrypt Data
        decrypted_password = encryption_key.decrypt(encrypted_password.decode())

        #print(f"Decryped Text: {decrypted_password}")
        return decrypted_password.decode()

    except Exception as e:
        print("Error in decryptor Function.")
        print("An error occurred:", e)
        time.sleep(10)

def vm_resource_getter(vm):

    # Extract basic VM information
    vm_info = {
        'name': vm.name,
        'status': 'on' if vm.runtime.powerState.lower() == 'poweredon' else 'off',
        'cluster': vm.runtime.host.parent.name.lower(),
        'cpu': vm.config.hardware.numCPU,
        'memory': int((vm.config.hardware.memoryMB / 1024)),
        'disk': 0
    }

    # Calculate disk space
    for device in vm.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualDisk):
            vm_info['disk'] += round((device.capacityInBytes / 1073741824))


    return vm_info

def categorize_vms(vm_data):
    # Categorizes VMs into predefined groups based on name prefixes.
    categories = {
        # ME OnPrem
        'MER': {},
        'MES': {},
        'MEF': {},
        'MEA': {},
        'MEB': {},
        'MESA': {},
        'MEM': {},
        'MEI': {},

        # DaaS
        'MEV': {},

        # VNK OnPrem
        'VAT': {},
        'VBI': {},
        'VIA': {},
        'VMI': {},
        'VR': {},  # Parent category for VR series
        'VR1': {},
        'VR2': {},
        'VR3': {},
        'VRD': {},
        'VSF': {},
        'VSP': {},

        # Rahkaran Abri
        'VRA': {},
        'VRF': {},
        'VRT': {}
    }

    for vm_name, data in vm_data.items():
        vm_upper = vm_name.upper()

        # Special handling for VR series
        if vm_upper.startswith(('VR1-', 'VR2-', 'VR3-', 'VRD-')):
            prefix = vm_upper[:3]
            categories['VR'][vm_name] = data
            categories[prefix][vm_name] = data
            continue

        # General case for other prefixes
        for prefix in categories:
            if vm_upper.startswith(f"{prefix}-"):
                categories[prefix][vm_name] = data
                break

    return categories

def metric_setter(categories_dict):
    # ['product', 'used_memory_on', 'used_memory_off'],
    for product, vms in categories_dict.items():
        print(f'\n{product}: ')

        # Initialize counters for this product
        members_total = len(vms)
        members_on = 0
        members_off = 0

        used_mem_total = 0
        used_mem_on = 0
        used_mem_off = 0

        used_cpu_total = 0
        used_cpu_on = 0
        used_cpu_off = 0

        used_disk_total = 0
        used_disk_on = 0
        used_disk_off = 0

        # Calculating metrics
        for vm_name, vm_data in vms.items():
            print(f'\t{vm_name}')
            used_mem_total += vm_data['memory']
            used_cpu_total += vm_data['cpu']
            used_disk_total += vm_data['disk']

            if vm_data['status'] == 'on':
                members_on += 1
                used_mem_on += vm_data['memory']
                used_cpu_on += vm_data['cpu']
                used_disk_on += vm_data['disk']
            else:
                members_off += 1
                used_mem_off += vm_data['memory']
                used_cpu_off += vm_data['cpu']
                used_disk_off += vm_data['disk']

            # Print VM details
            for vm_key, vm_val in vm_data.items():
                print(f'\t\t{vm_key}: {vm_val}')


        # Setting metric
        product_members_total.labels(
            product=product,
            total_on=members_on,
            total_off=members_off
        ).set(members_total)

        product_used_memory_total.labels(
            product=product,
            used_memory_on=used_mem_on,
            used_memory_off=used_mem_off
        ).set(used_mem_total)

        product_used_cpu_total.labels(
            product=product,
            used_cpu_on=used_cpu_on,
            used_cpu_off=used_cpu_off
        ).set(used_cpu_total)

        product_used_disk_total.labels(
            product=product,
            used_disk_on=used_disk_on,
            used_disk_off=used_disk_off
        ).set(used_disk_total)



try:
    username = 'sysops-svc@abramad.com'
    password = decryptor('sysops-svc_enc', 'sysops-svc_key')

    # SSL context for vCenter connections
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    vcenter_list = ['vab-vc01.abramad.com', 'vra-vc01.abramad.com', 'mev-vc01.abramad.com', 'me-vc01.abramad.com']
    #vcenter_list = ['vab-vc01.abramad.com']


    all_vms_dict = {}
    vm_counter = 0
    for vcenter in vcenter_list:

        vc_login_info = SmartConnect(host=vcenter, user=username, pwd=password, sslContext=context)
        content = vc_login_info.RetrieveContent()
        container = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
        vms = container.view
        container.Destroy()

        for vm in vms[:]:

            vm_data = vm_resource_getter(vm)
            all_vms_dict[vm_data['name']] = vm_data
            vm_counter += 1

            print(f'Processed: {vm_data['name']} - {vm_counter}')

        Disconnect(vc_login_info)

    # Categorize VMs
    vm_categories = categorize_vms(all_vms_dict)

    metric_setter(vm_categories)

    '''
    for categ_key, categ_val in vm_categories.items():
        print(f'\n{categ_key}: ')
        for vm_name, vm_data in categ_val.items():
            print(f'\t{vm_name}')
            for vm_key, vm_val in vm_data.items():
                print(f'\t\t{vm_key}: {vm_val}')

    '''


except Exception as err:
    print(f"Script failed: {err}")
    success = False
    error_string_summary = f"{type(err).__name__}: {err}"

    # Get the traceback and extract the last traceback frame
    tb = traceback.extract_tb(err.__traceback__)
    last_call = tb[-1]  # the last traceback frame, where the exception occurred
    error_string_detail = f"Error occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"



finally:
    # Finalizing Metrics
    # Script Duration
    duration = time.time() - start_time
    duration_gauge.set(duration)

    #Script Success Status
    status_gauge.set(1 if success else 0)

    # Script Total Executions
    total_exec_counts = read_value_from_file(total_exec_counter_file) + 1
    write_value_to_file(total_exec_counter_file, total_exec_counts)
    total_execution_counter.inc(total_exec_counts)

    if not success:
        # Script Total Failed Executions
        total_failed_exec_counts = read_value_from_file(total_failed_exec_counter_file) + 1
        write_value_to_file(total_failed_exec_counter_file, total_failed_exec_counts)
        total_failed_execution_counter.inc(total_failed_exec_counts)

        # Script Last Error Message
        last_error_message.labels(error_summary=error_string_summary, error_detail=error_string_detail).set(1)

    elif success:
        # Script Total Failed Executions
        total_failed_exec_counts = read_value_from_file(total_failed_exec_counter_file)
        total_failed_execution_counter.inc(total_failed_exec_counts)

        # Script Last Error Message
        last_error_message.labels(error_summary="None", error_detail="None").set(0)


    # Push metrics to Pushgateway

    push_to_gateway(
        gateway=pushgateway_url,
        job=job_name,
        grouping_key={'instance': instance, 'target': target, 'datacenter': datacenter},
        registry=registry
    )

    print('\n\n✅ Metrics Sent.')





"""
for vm_name, vm_data in all_vms_dict.items():

    # Categorizing
    # ME OnPrem
    if vm_name.lower().startswith('mer-'):
        mer_dict[vm_name] = vm_data
        continue

    if vm_name.lower().startswith('mes-'):
        mes_dict[vm_name] = vm_data
        continue

    if vm_name.lower().startswith('mef-'):
        mef_dict[vm_name] = vm_data
        continue

    if vm_name.lower().startswith('mea-'):
        mea_dict[vm_name] = vm_data
        continue

    if vm_name.lower().startswith('meb-'):
        meb_dict[vm_name] = vm_data
        continue

    if vm_name.lower().startswith('mesa-'):
        mesa_dict[vm_name] = vm_data
        continue

    if vm_name.lower().startswith('mem-'):
        mem_dict[vm_name] = vm_data
        continue

    if vm_name.lower().startswith('mei-'):
        mei_dict[vm_name] = vm_data
        continue

    # DaaS
    if vm_name.lower().startswith('mev-'):
        mev_dict[vm_name] = vm_data
        continue

    # VNK OnPrem
    if vm_name.lower().startswith('vat-'):
        vat_dict[vm_name] = vm_data
        continue

    if vm_name.lower().startswith('vbi-'):
        vbi_dict[vm_name] = vm_data
        continue

    if vm_name.lower().startswith('via-'):
        via_dict[vm_name] = vm_data
        continue

    if vm_name.lower().startswith('vmi-'):
        vmi_dict[vm_name] = vm_data
        continue

    if vm_name.lower().startswith('vr1-') or vm_name.lower().startswith('vr2-') or vm_name.lower().startswith('vr3-'):
        vr_dict[vm_name] = vm_data

        if vm_name.lower().startswith('vr1-'):
            vr1_dict[vm_name] = vm_data
        elif vm_name.lower().startswith('vr2-'):
            vr2_dict[vm_name] = vm_data
        elif vm_name.lower().startswith('vr3-'):
            vr3_dict[vm_name] = vm_data

        continue

    if vm_name.lower().startswith('vsf-'):
        vsf_dict[vm_name] = vm_data
        continue

    if vm_name.lower().startswith('vsp-'):
        vsp_dict[vm_name] = vm_data
        continue

    # Rahkaran Abri Product
    if vm_name.lower().startswith('vra-'):
        vra_dict[vm_name] = vm_data
        continue

    if vm_name.lower().startswith('vrf-'):
        vrf_dict[vm_name] = vm_data
        continue

    if vm_name.lower().startswith('vrt-'):
        vrt_dict[vm_name] = vm_data
        continue



    #for k, v in vm_data.items():
    #    print(f'    {k}: {v}')
"""
