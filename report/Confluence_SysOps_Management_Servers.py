from atlassian import Confluence
from cryptography.fernet import Fernet
from pyvim import connect
from pyVmomi import vim
import warnings
import ssl
import os
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter
import traceback
import time

# --- Configuration ---
script_name = 'confluence_sysops_management_servers'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'https://me-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
datacenter = 'miremad_vanak'
target = 'sysops_management_servers'

# Create a registry for our custom metrics
registry = CollectorRegistry()

# Define metrics
duration_gauge = Gauge('script_exec_duration_seconds', 'Duration of my script', registry=registry)
status_gauge = Gauge('script_success', 'Whether script succeeded (1) or failed (0)', registry=registry)
total_execution_counter = Counter('script_total_execs', 'Total number of times the script has run', registry=registry)
total_failed_execution_counter = Counter('script_total_failed_execs', 'Total number of times the script has failed to finish gracefully', registry=registry)
last_error_message = Gauge('script_last_error_message','The last error message encountered during script execution',['error_summary', 'error_detail'], registry=registry)


# Simulate your script logic
start_time = time.time()
success = True
error_string_summary = ""
error_string_detail = ""


try:
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

        #print(f"Decryped Text: {decrypted_password}")
        return decrypted_password.decode()


    # Function to check if a VM is under the 'SYSOPS' folder
    def is_in_sysops_folder(vm):
        parent = vm.parent
        while parent:
            if isinstance(parent, vim.Folder) and parent.name == "SysOpsTeam":
                return True
            parent = parent.parent
        return False

    # ================================================================================ #

    username = 'sysops-svc@abramad.com'
    password = decryptor('sysops-svc_enc', 'sysops-svc_key')

    con_username = username.split('@')[0]
    con_password = password

    # Ignore the warning
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    # *** Connecting to ME-VC01.Abramad.Com to get the Report ***
    # Create an SSL context with no certificate verification
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.verify_mode = ssl.CERT_NONE

    vcenters = ['me-vc01.abramad.com', 'vab-vc01.abramad.com']


    me_table_body = """
    <h2>MirEmad</h2>
    <table>
      <tbody>
        <tr>
          <th>Server Name</th>
          <th>IP Address</th>
          <th>Status</th>
        </tr>
    """

    vnk_table_body = """
    <h2>Vanak</h2>
    <table>
      <tbody>
        <tr>
          <th>Server Name</th>
          <th>IP Address</th>
          <th>Status</th>
        </tr>
    """


    for vcenter in vcenters:
        print(f'Processing {vcenter}.')

        # Connecting to vCenter
        vc = connect.SmartConnect(host=vcenter,user= username,pwd= password,port=443,sslContext=context)
        vc_content = vc.RetrieveContent()
        vc_vm_view = vc_content.viewManager.CreateContainerView(vc_content.rootFolder, [vim.VirtualMachine], True)

        # Filtering VMs in the 'SYSOPS' folder
        sysops_vms = [vm for vm in vc_vm_view.view if is_in_sysops_folder(vm)]
        sorted_vms = sorted(sysops_vms, key=lambda vm: vm.name)

        for vm in sorted_vms:

            # VM Name
            vm_name = vm.name

            # retrieve vm IP address
            vm_ip = "0.0.0.0"
            if vm.guest is not None:
                for nic in vm.guest.net:
                    if nic.ipConfig is not None:
                        for ip in nic.ipConfig.ipAddress:
                            if ip.ipAddress.startswith('172.17') or ip.ipAddress.startswith('172.21') or ip.ipAddress.startswith('172.29'):
                                vm_ip = ip.ipAddress


            vm_status = 'Powered On' if vm.runtime.powerState.lower() == 'poweredon' else 'Powered Off'

            if vcenter.lower().startswith('me-vc01'):
                me_table_body += f'''
                <tr>
                  <td>{vm_name}</td>
                  <td>{vm_ip}</td>
                  <td>{vm_status}</td>
                </tr>
                '''
            if vcenter.lower().startswith('vab-vc01'):
                vnk_table_body += f'''
                <tr>
                  <td>{vm_name}</td>
                  <td>{vm_ip}</td>
                  <td>{vm_status}</td>
                </tr>
                '''
        print(f'Finished Operating {vcenter}.\n')

    me_table_body += '''
      </tbody>
    </table>
    <br/><br/>
    '''

    vnk_table_body += '''
      </tbody>
    </table>
    <br/><br/>
    '''

    full_table_body = me_table_body + vnk_table_body

    # Step 1: Connect to Confluence
    confluence = Confluence(
        url='https://confluence.abramad.com',
        username=con_username,
        password=con_password,
        verify_ssl=False
    )

    # Step 2: Get the Page ID
    page_title = 'Management Servers List'
    space_key = 'ManSer'

    page = confluence.get_page_by_title(space=space_key, title=page_title)
    if not page:
        raise Exception("Page not found.")
    page_id = page['id']


    # Step 4: Publish Changes
    confluence.update_page(
        page_id=page_id,
        title=page_title,
        body=full_table_body,
        representation='storage'
    )
    print("Page updated successfully.")


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

    print('✅ Metrics Sent.')


