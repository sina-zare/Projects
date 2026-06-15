from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter
from urllib3.exceptions import InsecureRequestWarning
from cryptography.fernet import Fernet
from pyzabbix import ZabbixAPI
from itertools import chain
from pyvim.connect import Disconnect
from pyvim import connect
from pyVmomi import vim
import traceback
import warnings
import time
import ssl
import os

# --- Configuration ---
script_name = 'zabbix_divergence_detector'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'https://me-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
datacenter = 'vanak_&_miremad'
target = 'zabbix_&_vcenters'

# Create a registry for our custom metrics
registry = CollectorRegistry()

# Define metrics
duration_gauge = Gauge('script_exec_duration_seconds', 'Duration of my script', registry=registry)
status_gauge = Gauge('script_success', 'Whether script succeeded (1) or failed (0)', registry=registry)
total_execution_counter = Counter('script_total_execs', 'Total number of times the script has run',
                                  registry=registry)
total_failed_execution_counter = Counter('script_total_failed_execs',
                                         'Total number of times the script has failed to finish gracefully',
                                         registry=registry)
last_error_message = Gauge('script_last_error_message',
                           'The last error message encountered during script execution',
                           ['error_summary', 'error_detail'], registry=registry)

# Simulate your script logic
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
    # Load the key
    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = (os.environ.get(enc_env_var)).encode()
    # Decrypt Data
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())

    # print(f"Decryped Text: {decrypted_password}")
    return decrypted_password.decode()


# Function to check if a VM is under vcenter folder
def is_in_vc_folder(vm, folder_list):
    parent = vm.parent
    allowed = set(folder_list)  # Faster lookups

    while parent:
        if isinstance(parent, vim.Folder):
            if parent.name in allowed:
                return True
        parent = parent.parent

    return False


# Function to check if a VM is not under vcenter folder
def is_not_in_vc_folder(vm, folder_list):
    parent = vm.parent
    denied = set(folder_list)  # Faster lookups

    while parent:
        if isinstance(parent, vim.Folder):
            if parent.name in denied:
                return False
        parent = parent.parent

    return True

try:
    # metric definition
    zabbix_monitoring_divergence = Gauge(
            'zabbix_monitoring_divergence',
            'returns 1 if vm_name is not found in zabbix or is not monitored with agent related templates',
            ['product_line', 'vm_name', 'vm_hostname', 'zabbix_server', 'zabbix_state', 'component', 'datacenter'],
            registry=registry
        )


    vcenters = {
            "vab-vc": "vab-vc01.abramad.com",
            "me-vc": "me-vc01.abramad.com",
            "vra-vc": "vra-vc01.abramad.com",
        }
    username = 'sysops-svc@abramad.com'
    password = decryptor('sysops-svc_enc', 'sysops-svc_key')

    vab_prefixes = ("vr1-", "vr2-", "vr3-", "vrd-", "vat-", "vbi-", "vmi-", "vsp-", "vsf-", "via-")
    me_prefixes = ("mer-", "merd-", "mea-", "meb-", "mem-", "mes-", "mef-", "mei-")
    vra_prefixes = ("vra-", "vrf-", "vrt-")

    pfx_rahkaran = ("vr1-", "vr2-", "vr3-", "vrd-", "mer-", "merd-")
    pfx_automation = ("vat-", "mea-")
    pfx_bi = ("vbi-", "meb-")
    pfx_miaas = ("vmi-", "mem-")
    pfx_sepidar = ("vsp-", "mes-")
    pfx_sahamfasl = ("vsf-", "mef-")
    pfx_iaas = ("via-", "mei-")
    pfx_rahkaran_abri = ("vra-", "vrf-", "vrt-")

    vab_allowed_folders = ["Rahkaran", "BI", "IaaS", "ManagedIaaS", "AutomationEdari", "Sepidar", "Sepidar-DaaS"]
    vab_denied_folders = []

    me_allowed_folders = ["Customers"]
    me_denied_folders = []

    vra_allowed_folders = ["VRACustomers", "VRFCustomers", "VRTCustomers"]
    vra_denied_folders = []


    zabbix_url_dict = {
        'ME-CustomerZabbix': 'https://me-customerzabbix.abramad.com',
        'VNK-CustomerZabbix': 'https://vnk-customerzabbix.abramad.com',
        #'ME-Zabbix': 'https://me-zabbix.abramad.com/zabbix',
        #'VNK-Zabbix': 'https://vnk-zabbix.abramad.com'
    }
    zabbix_user = username.split('@')[0]

    os_tmpl_names = ("Linux by Zabbix agent active",
                     "Windows by Zabbix agent active",
                     "Windows by Zabbix agent active OnPrem",
                     "Windows by Zabbix agent active Rahkaran Abri",
                     "Windows by Zabbix agent active Rahkaran OnPrem",
                     "Windows by Zabbix agent active Rahkaran OnPrem Nord",
                     "Windows by Zabbix agent active Rahkaran OnPrem Ramak",
                     "Windows by Zabbix agent active Rahkaran Tose OnPrem",
                     )

    url_tmpl_names = ("Automation-OnPrem-Tpl",
                      "Rahkaran-OnPrem-Tpl-Far",
                      "Rahkaran-OnPrem-Tpl-Eng",
                      "Rahkaran-OnPrem-Tpl-Arb",
                      "Rahkaran-Abri-Tpl",
                      "Rahkaran-Abri-Tpl-Arb",
                      "Rahkaran-Abri-Tpl-Eng",
                      "Web-Service-Tpl",
                      )

    #############################################################################
    # Ignore the warning/# Create an SSL context with no certificate verification
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.verify_mode = ssl.CERT_NONE

    vab_vm_dict = {}
    vra_vm_dict = {}
    me_vm_dict = {}

    for vcenter_name, vcenter_url in vcenters.items():
        # Connecting to vCenter
        print(f'connecting to {vcenter_name}')
        vc = connect.SmartConnect(host=vcenter_url, user=username, pwd=password, port=443, sslContext=context)
        content = vc.RetrieveContent()
        vm_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
        print('gathering vms')
        vms = []
        if vcenter_name.startswith('vab'):
            vms = [vm for vm in vm_view.view if (is_in_vc_folder(vm, vab_allowed_folders) and vm.name.lower().startswith(vab_prefixes))]
        elif vcenter_name.startswith('me'):
            vms = [vm for vm in vm_view.view if (is_in_vc_folder(vm, me_allowed_folders) and vm.name.lower().startswith(me_prefixes))]
        elif vcenter_name.startswith('vra'):
            vms = [vm for vm in vm_view.view if (is_in_vc_folder(vm, vra_allowed_folders) and vm.name.lower().startswith(vra_prefixes))]

        # Sort the vms list based on their names
        print('sorting vms')
        sorted_vms = sorted(vms, key=lambda vm: vm.name.lower())

        for vm in sorted_vms:
            # power state
            power_state = vm.runtime.powerState.lower()
            if power_state == "poweredon":
                # name
                vm_name = vm.name

                # hostname
                if vm.summary.guest.hostName and '.' in vm.summary.guest.hostName:
                    tmp_nm = vm.summary.guest.hostName.split('.')
                    vm_hostname = tmp_nm[0]
                else:
                    if vm.summary.guest.hostName:
                        vm_hostname = vm.summary.guest.hostName
                    else:
                        vm_hostname = 'N/A'
                # product line
                if vm_name.lower().startswith(pfx_rahkaran):
                    vm_product_line = 'Rahkaran_OnPrem'
                elif vm_name.lower().startswith(pfx_automation):
                    vm_product_line = 'Automation'
                elif vm_name.lower().startswith(pfx_bi):
                    vm_product_line = 'BI'
                elif vm_name.lower().startswith(pfx_miaas):
                    vm_product_line = 'Managed_IaaS'
                elif vm_name.lower().startswith(pfx_sepidar):
                    vm_product_line = 'Sepidar'
                elif vm_name.lower().startswith(pfx_sahamfasl):
                    vm_product_line = 'Saham_Fasl'
                elif vm_name.lower().startswith(pfx_iaas):
                    vm_product_line = 'IaaS'
                elif vm_name.lower().startswith(pfx_rahkaran_abri):
                    vm_product_line = 'Rahkaran_Abri'
                else:
                    vm_product_line = 'N/A'

                # categorizing
                if vm_name.lower().startswith(vab_prefixes):
                    vm_datacenter = 'Vanak'
                    vab_vm_dict[vm_name] = {
                        'vm_name': vm_name,
                        'vm_hostname': vm_hostname,
                        'vm_product_line': vm_product_line,
                        'vm_datacenter': vm_datacenter,
                    }
                elif vm_name.lower().startswith(vra_prefixes):
                    vm_datacenter = 'Vanak'
                    vra_vm_dict[vm_name] = {
                        'vm_name': vm_name,
                        'vm_hostname': vm_hostname,
                        'vm_product_line': vm_product_line,
                        'vm_datacenter': vm_datacenter,
                    }
                elif vm_name.lower().startswith(me_prefixes):
                    vm_datacenter = 'Miremad'
                    me_vm_dict[vm_name] = {
                        'vm_name': vm_name,
                        'vm_hostname': vm_hostname,
                        'vm_product_line': vm_product_line,
                        'vm_datacenter': vm_datacenter,
                    }

    #  Gathering Data from Zabbix
    os_tmpl_dict = {}
    url_tmpl_dict = {}

    warnings.simplefilter("ignore", InsecureRequestWarning)
    try:
        for zbx_name, zbx_url in zabbix_url_dict.items():
            zapi = ZabbixAPI(zbx_url)
            zapi.session.verify = False
            # zapi.session.headers.update({"User-Agent": "PyZabbix"})
            zapi.login(zabbix_user, password)
            print(f"\n✅ Connected to {zbx_name}\nVersion {zapi.api_version()}")

            templates_with_hosts = zapi.template.get(
                selectHosts=["hostid", "host", "status"],  # Get host information
                output=["templateid", "name"]  # Get template ID and name
            )


            for template in templates_with_hosts:
                tmpl_name = template.get('name', 'N/A')
                tmpl_hosts = template.get('hosts', [])

                #print(tmpl_name)
                for host in tmpl_hosts:
                    host_name = host.get('host', 'N/A')
                    host_status = host.get('status', 'N/A')
                    #print(f"    {host_status} | {host_name}")

                    if tmpl_name in os_tmpl_names:
                        os_tmpl_dict.setdefault(tmpl_name, []).append({
                            'host': host_name,
                            'status': host_status,
                            'zbx_srv': zbx_name
                        })
                    elif tmpl_name in url_tmpl_names:
                        url_tmpl_dict.setdefault(tmpl_name, []).append({
                            'host': host_name,
                            'status': host_status,
                            'zbx_srv': zbx_name
                        })

    except Exception as err:
        print(f"❌ Error connecting to {zbx_name}: {err}")
        success = False
        error_string_summary += f"{type(err).__name__}: {err}"

        # Get the traceback and extract the last traceback frame
        tb = traceback.extract_tb(err.__traceback__)
        last_call = tb[-1]  # the last traceback frame, where the exception occurred
        error_string_detail += f"Error occurred in line {last_call.lineno}: {last_call.line}"
        print(f"Script failed: {error_string_summary}\n{error_string_detail}")

    # import pprint as pp
    # pp.pp(os_tmpl_dict)
    # print(50 * '#')
    # pp.pp(url_tmpl_dict)


    # Checking if agent and url monitoring misses a host
    # Create a lowercased set of keys for os_tmpl_dict
    zbx_os_hosts_dict_lower = {
        host_entry['host'].lower(): {
                            'host': host_entry['host'].lower(),
                            'status': host_entry['status'],
                            'zbx_srv': host_entry['zbx_srv']
                        }
        for tmpl_hosts in os_tmpl_dict.values()
        for host_entry in tmpl_hosts
    }

    zbx_url_hosts_dict_lower = {
        host_entry['host'].lower(): {
                            'host': host_entry['host'].lower(),
                            'status': host_entry['status'],
                            'zbx_srv': host_entry['zbx_srv']
                        }
        for tmpl_hosts in url_tmpl_dict.values()
        for host_entry in tmpl_hosts
    }

    #os_hosts_lower_keys = {k.lower() for k in zbx_os_hosts_dict_lower.keys()}
    agent_excluded = ('mei-', 'via-')
    url_included = ('mer-', 'merd-', 'mea-', 'vr1-', 'vr2-', 'vr3-', 'vat-', 'vra-')
    url_excluded = ('-t', '-db', '-db1', '-db2', 'drdb', 'drdb1', 'drdb2', '-rds1', '-lock', '-a2', '-a3', '-a4', '-a5', '-a6', '-a7', '-a8')

    for vm_name, vm_dict in chain(vab_vm_dict.items(), vra_vm_dict.items(), me_vm_dict.items()):
        # Agents
        if not vm_name.lower().startswith(agent_excluded):
            if vm_name.lower() not in set(zbx_os_hosts_dict_lower.keys()):
                zabbix_monitoring_divergence.labels(
                    product_line=vm_dict.get('vm_product_line', 'N/A'),
                    vm_name=vm_dict.get('vm_name', 'N/A'),
                    vm_hostname=vm_dict.get('vm_hostname', 'N/A'),
                    zabbix_server='N/A',
                    zabbix_state='N/A',
                    component='Agent',
                    datacenter=vm_dict.get('vm_datacenter', 'N/A'),
                    ).set(1)

                print(f"❌ {vm_name} not found in agent templates")

            elif vm_name.lower() in set(zbx_os_hosts_dict_lower.keys()) and zbx_os_hosts_dict_lower[vm_name.lower()]['status'] == '1':
                zabbix_monitoring_divergence.labels(
                    product_line=vm_dict.get('vm_product_line', 'N/A'),
                    vm_name=vm_dict.get('vm_name', 'N/A'),
                    vm_hostname=vm_dict.get('vm_hostname', 'N/A'),
                    zabbix_server=zbx_os_hosts_dict_lower[vm_name.lower()]['zbx_srv'],
                    zabbix_state='disabled',
                    component='Agent',
                    datacenter=vm_dict.get('vm_datacenter', 'N/A'),
                ).set(1)

                print(f"❌ {vm_name} found in agent templates but was disabled")

            elif vm_name.lower() in set(zbx_os_hosts_dict_lower.keys()) and zbx_os_hosts_dict_lower[vm_name.lower()]['status'] == '0':
                zabbix_monitoring_divergence.labels(
                    product_line=vm_dict.get('vm_product_line', 'N/A'),
                    vm_name=vm_dict.get('vm_name', 'N/A'),
                    vm_hostname=vm_dict.get('vm_hostname', 'N/A'),
                    zabbix_server=zbx_os_hosts_dict_lower[vm_name.lower()]['zbx_srv'],
                    zabbix_state='enabled',
                    component='Agent',
                    datacenter=vm_dict.get('vm_datacenter', 'N/A'),
                ).set(0)

        # URL
        if vm_name.lower().startswith(url_included) and not vm_name.lower().endswith(url_excluded):
            if vm_name.lower() not in set(zbx_url_hosts_dict_lower.keys()):
                zabbix_monitoring_divergence.labels(
                    product_line=vm_dict.get('vm_product_line', 'N/A'),
                    vm_name=vm_dict.get('vm_name', 'N/A'),
                    vm_hostname=vm_dict.get('vm_hostname', 'N/A'),
                    zabbix_server='N/A',
                    zabbix_state='N/A',
                    component='URL',
                    datacenter=vm_dict.get('vm_datacenter', 'N/A'),
                    ).set(1)

                print(f"❌ {vm_name} not found in URL templates")

            elif vm_name.lower() in set(zbx_url_hosts_dict_lower.keys()) and zbx_url_hosts_dict_lower[vm_name.lower()]['status'] == '1':
                zabbix_monitoring_divergence.labels(
                    product_line=vm_dict.get('vm_product_line', 'N/A'),
                    vm_name=vm_dict.get('vm_name', 'N/A'),
                    vm_hostname=vm_dict.get('vm_hostname', 'N/A'),
                    zabbix_server=zbx_url_hosts_dict_lower[vm_name.lower()]['zbx_srv'],
                    zabbix_state='disabled',
                    component='URL',
                    datacenter=vm_dict.get('vm_datacenter', 'N/A'),
                ).set(1)

                print(f"❌ {vm_name} found in URL templates but was disabled")

            elif vm_name.lower() in set(zbx_url_hosts_dict_lower.keys()) and zbx_url_hosts_dict_lower[vm_name.lower()]['status'] == '0':
                zabbix_monitoring_divergence.labels(
                    product_line=vm_dict.get('vm_product_line', 'N/A'),
                    vm_name=vm_dict.get('vm_name', 'N/A'),
                    vm_hostname=vm_dict.get('vm_hostname', 'N/A'),
                    zabbix_server=zbx_url_hosts_dict_lower[vm_name.lower()]['zbx_srv'],
                    zabbix_state='enabled',
                    component='URL',
                    datacenter=vm_dict.get('vm_datacenter', 'N/A'),
                ).set(0)


except Exception as err:
    success = False
    error_string_summary += f"{type(err).__name__}: {err}"

    # Get the traceback and extract the last traceback frame
    tb = traceback.extract_tb(err.__traceback__)
    last_call = tb[-1]  # the last traceback frame, where the exception occurred
    error_string_detail += f"Error occurred in line {last_call.lineno}: {last_call.line}"
    print(f"Script failed: {error_string_summary}\n{error_string_detail}")


finally:
    # Finalizing Metrics
    # Script Duration
    duration = time.time() - start_time
    duration_gauge.set(duration)

    # Script Success Status
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
        grouping_key={'instance': instance, 'target': target},
        registry=registry
    )
    print(f'✅ Metrics sent to {pushgateway_url}')
