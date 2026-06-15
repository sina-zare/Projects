import openpyxl
from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
from email.header import Header
import ssl
import warnings
from cryptography.fernet import Fernet
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter
import traceback
import time
import os
import pyzipper

# --- Configuration ---
script_name = 'all_vms_info_unified'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'https://vnk-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
target = 'all_vcenter_customer_vms'

# Create a registry for our custom metrics
registry = CollectorRegistry()

# Define metrics
duration_gauge = Gauge('script_exec_duration_seconds', 'Duration of my script', registry=registry)
status_gauge = Gauge('script_success', 'Whether script succeeded (1) or failed (0)', registry=registry)
total_execution_counter = Counter('script_total_execs', 'Total number of times the script has run', registry=registry)
total_failed_execution_counter = Counter('script_total_failed_execs',
                                         'Total number of times the script has failed to finish gracefully',
                                         registry=registry)
last_error_message = Gauge('script_last_error_message', 'The last error message encountered during script execution',
                           ['error_summary', 'error_detail'], registry=registry)

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


    def send_anonymous_email(from_email, to_email, cc_email, subject, html_message, direction,
                             mail_server='mail.abramad.com', attachments=None):

        ##############################################
        ######### HTML Body Begin For Email ##########
        html_line_break = '''
                                <p><br></p>
                            '''
        html_msg_1 = f'''
                            <html dir={direction}>
                              <body>
                            '''
        html_msg_2 = f'''
                                <p  style="font-family: DiodrumArabic-Regular">{html_message}</p>
                            '''
        html_msg_3 = f'''
                                '''
        html_msg_4 = '''
                              </body>
                            </html>
                            '''
        ######### HTML Body End For Email ##########
        ############################################

        email_body = html_msg_1 + html_msg_2 + html_line_break + html_line_break + html_msg_3 + html_msg_4

        # Split email addresses into lists
        to_email_list = to_email.split(",") if to_email else []
        cc_email_list = cc_email.split(",") if cc_email else []
        all_recipients = to_email_list + cc_email_list

        # Create the email message
        msg = MIMEMultipart()
        msg["From"] = Header(from_email, "utf-8")
        msg["To"] = Header(", ".join(to_email_list), "utf-8")  # For display purposes
        msg["CC"] = Header(", ".join(cc_email_list), "utf-8")  # For display purposes
        msg["Subject"] = Header(subject, "utf-8")

        # Attach HTML body
        msg.attach(MIMEText(email_body, "html", "utf-8"))

        # Attach files if any
        if attachments:
            for attachment in attachments:
                if os.path.exists(attachment):
                    with open(attachment, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(attachment))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment)}"'
                        msg.attach(part)
                else:
                    print(f"Warning: Attachment {attachment} not found.")

        # Connect to the mail server and send the email
        with smtplib.SMTP(mail_server, 25) as server:
            server.sendmail(from_email, all_recipients, msg.as_string())
            print("Email sent successfully.")


    def decryptor(enc_env_var, key_env_var):
        # Load the key
        key = os.environ.get(key_env_var)
        encryption_key = Fernet(key)
        encrypted_password = (os.environ.get(enc_env_var)).encode()
        # Decrypt Data
        decrypted_password = encryption_key.decrypt(encrypted_password.decode())
        # print(f"Decrypted Text: {decrypted_password}")
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


    # Zipper function
    def make_zip(files, zip_name, password):
        with pyzipper.AESZipFile(zip_name, 'w', compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES) as zf:
            zf.setpassword(password.encode())

            for file_path in files:
                file_name = os.path.basename(file_path)  # <- keeps only filename
                zf.write(file_path, arcname=file_name)  # <- overrides path inside ZIP


    # Service Specific Metrics
    # Disk
    vm_storage_hdd_total_bytes = Gauge(
        'vm_storage_hdd_total',
        'The total amount of hdd disk on a vm in bytes',
        ['vm_name', 'national_id', 'storage_cluster', 'vm_storage_total_gibibytes', 'datacenter'],
        registry=registry
    )
    vm_storage_ssd_total_bytes = Gauge(
        'vm_storage_ssd_total',
        'The total amount of ssd disk on a vm in bytes',
        ['vm_name', 'national_id', 'storage_cluster', 'vm_storage_total_gibibytes', 'datacenter'],
        registry=registry
    )
    vm_storage_arch_total_bytes = Gauge(
        'vm_storage_arch_total',
        'The total amount of archive disk on a vm in bytes',
        ['vm_name', 'national_id', 'storage_cluster', 'vm_storage_total_gibibytes', 'datacenter'],
        registry=registry
    )
    vm_storage_hyb_total_bytes = Gauge(
        'vm_storage_hyb_total',
        'The total amount of hybrid disk on a vm in bytes',
        ['vm_name', 'national_id', 'storage_cluster', 'vm_storage_total_gibibytes', 'datacenter'],
        registry=registry
    )
    vm_storage_nvme_total_bytes = Gauge(
        'vm_storage_nvme_total',
        'The total amount of nvme disk on a vm in bytes',
        ['vm_name', 'national_id', 'storage_cluster', 'vm_storage_total_gibibytes', 'datacenter'],
        registry=registry
    )

    # Compute
    vm_cpu_spec = Gauge(
        'vm_cpu_spec',
        'vm allocated cpu in core',
        ['vm_name', 'national_id', 'compute_cluster', 'cpu_type', 'datacenter'],
        registry=registry
    )
    vm_memory_spec = Gauge(
        'vm_memory_spec',
        'vm allocated memory in GB',
        ['vm_name', 'national_id', 'compute_cluster', 'datacenter'],
        registry=registry
    )

    # General
    vm_general_spec = Gauge(
        'vm_general_spec',
        'vm general information',
        ['vm_name',
         'hostname',
         'dns_suffix',
         'os',
         'product_line',
         'company_name',
         'national_id',
         'power',
         'compute_cluster',
         'creation_ticket_id',
         'shutdown_ticket_id',
         'disconnect_ticket_id',
         'creation_date',
         'shutdown_date',
         'disconnect_date',
         'url',
         'dongle',
         'sts_vpn',
         'ids_ips',
         'waf',
         'vip',
         'agent_name',
         'agent_no',
         'agent_email',
         'nic',
         'confidentiality',
         'integrity',
         'availability',
         'datacenter',
         ],
        registry=registry
    )
    vm_network_spec = Gauge(
        'vm_network_spec',
        'vm network information',
        ['vm_name', 'national_id', 'private_ip', 'public_ip', 'vlan_id', 'portgroup_id', 'datacenter'],
        registry=registry
    )

    # Evaluative
    vm_name_and_hostname_matches = Gauge(
        'vm_name_and_hostname_matches',
        'returns 1 if vm_name matches vm_hostname',
        ['product_line', 'vm_name', 'vm_hostname', 'national_id', 'datacenter'],
        registry=registry
    )
    # end of metric prototype

    vcenters = {
        "vab-vc": "vab-vc01.abramad.com",
        "me-vc": "me-vc01.abramad.com",
    }
    username = 'sysops-svc@abramad.com'
    password = decryptor('sysops-svc_enc', 'sysops-svc_key')
    excel_file_path = 'C://Temp//vm_report.xlsx'
    zip_file_path = 'C://Temp//vm_report.zip'
    zip_file_pass = 'S9x#ndW3o@zOMl0z'
    receiver_email = 'sales@abramad.com,accounting@abramad.com'
    # receiver_email = 'abramadsysops@abramad.com'
    cc_email = 'admin@abramad.com,abramadsysops@abramad.com'
    # cc_email = ''

    vab_prefixes = ("vr1-", "vr2-", "vr3-", "vrd-", "vat-", "vbi-", "vmi-", "vsp-", "vsf-", "via-")
    me_prefixes = ("mer-", "merd-", "mea-", "meb-", "mem-", "mes-", "mef-", "mei-")

    pfx_rahkaran = ("vr1-", "vr2-", "vr3-", "vrd-", "mer-", "merd-")
    pfx_automation = ("vat-", "mea-")
    pfx_bi = ("vbi-", "meb-")
    pfx_miaas = ("vmi-", "mem-")
    pfx_sepidar = ("vsp-", "mes-")
    pfx_sahamfasl = ("vsf-", "mef-")
    pfx_iaas = ("via-", "mei-")

    vab_allowed_folders = ["Rahkaran", "BI", "IaaS", "ManagedIaaS", "AutomationEdari", "Sepidar", "Sepidar-DaaS"]
    vab_denied_folders = []

    me_allowed_folders = ["Customers"]
    me_denied_folders = []

    vab_key_map = {
        301: "vm_creation_date",
        311: "vm_shutdown_date",
        767676: "vm_disconnect_date", # Update key
        620: "vm_company_name",
        302: "vm_public_ip",
        402: "vm_creation_ticket_no",
        501: "vm_shutdown_ticket_no",
        7676767: "vm_disconnect_ticket_no", # Update key
        306: "vm_national_no",
        101: "vm_tafsil_no",
        102: "vm_backup_status",
        303: "vm_url",
        304: "vm_ipsids_status",
        305: "vm_in_dept_status",
        307: "vm_not_monitored_status",
        308: "vm_owner",
        309: "vm_dongle_status",
        312: "vm_site_to_site_status",
        313: "vm_usage",
        314: "vm_vip_status",
        315: "vm_waf_status",
        316: "vm_zabbix_vip_status",
        602: "vm_rep_name",
        603: "vm_rep_no",
        604: "vm_rep_email",
        608: "vm_confidentiality_weight",
        609: "vm_integrity_weight",
        610: "vm_availability_weight",
        611: "vm_product_line",
    }

    me_key_map = {
        104: "vm_creation_date",
        401: "vm_shutdown_date",
        767676: "vm_disconnect_date", # Update key
        1202: "vm_company_name",
        603: "vm_public_ip",
        1405: "vm_creation_ticket_no",
        1406: "vm_shutdown_ticket_no",
        1206: "vm_disconnect_ticket_no",
        611: "vm_national_no",
        1201: "vm_tafsil_no",
        102: "vm_backup_status",
        604: "vm_url",
        703: "vm_ipsids_status",
        903: "vm_in_dept_status",
        76767676: "vm_not_monitored_status", # Update key
        1001: "vm_owner",
        701: "vm_dongle_status",
        702: "vm_site_to_site_status",
        1002: "vm_usage",
        705: "vm_vip_status",
        704: "vm_waf_status",
        7676767676: "vm_zabbix_vip_status", # Update key
        1203: "vm_rep_name",
        1204: "vm_rep_no",
        1205: "vm_rep_email",
        1301: "vm_confidentiality_weight",
        1302: "vm_integrity_weight",
        1303: "vm_availability_weight",
        1304: "vm_product_line",
    }

    # Ignore the warning/# Create an SSL context with no certificate verification
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.verify_mode = ssl.CERT_NONE
    vm_dict = {}

    for vcenter_name, vcenter_addr in vcenters.items():
        # Connecting to vCenter
        print(f'connecting to {vcenter_name}')
        vc = connect.SmartConnect(host=vcenter_addr, user=username, pwd=password, port=443, sslContext=context)
        content = vc.RetrieveContent()
        vm_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
        print('gathering vms')
        if vcenter_name.startswith('vab'):
            vms = [vm for vm in vm_view.view if (is_in_vc_folder(vm, vab_allowed_folders) and vm.name.lower().startswith(vab_prefixes))]
        elif vcenter_name.startswith('me'):
            vms = [vm for vm in vm_view.view if (is_in_vc_folder(vm, me_allowed_folders) and vm.name.lower().startswith(me_prefixes))]

        # Sort the vms list based on their names
        print('sorting vms')
        sorted_vms = sorted(vms, key=lambda vm: vm.name.lower())

        for vm in sorted_vms:

            # === Calculating VM Specs ===

            # initializing variables
            vm_sum_ssd = 0
            vm_sum_ssd_in_bytes = 0
            vm_sum_hdd = 0
            vm_sum_hdd_in_bytes = 0
            vm_sum_arch = 0
            vm_sum_arch_in_bytes = 0
            vm_sum_nvme = 0
            vm_sum_nvme_in_bytes = 0
            vm_sum_hyb = 0
            vm_sum_hyb_in_bytes = 0
            vm_storage_cluster_ssd = 'N/A'
            vm_storage_cluster_hdd = 'N/A'
            vm_storage_cluster_arch = 'N/A'
            vm_storage_cluster_hyb = 'N/A'
            vm_storage_cluster_nvme = 'N/A'
            vm_vlan_id = 'N/A'
            vm_portgroup = 'N/A'
            vm_nic_status = 0

            # name
            vm_name = vm.name

            # hostname and dns suffix
            if vm.summary.guest.hostName and '.' in vm.summary.guest.hostName:
                tmp_nm = vm.summary.guest.hostName.split('.')
                vm_hostname = tmp_nm[0]
                vm_dns_suffix = tmp_nm[-2] + '.' + tmp_nm[-1]
            else:
                if vm.summary.guest.hostName:
                    vm_hostname = vm.summary.guest.hostName
                else:
                    vm_hostname = 'N/A'
                vm_dns_suffix = 'N/A'

            # VM Guest OS
            if vm.config.guestFullName:
                vm_os = vm.config.guestFullName
            else:
                vm_os = 'N/A'

            # compute cluster
            vm_compute_cluster = vm.runtime.host.parent.name

            # power state
            power_state = vm.runtime.powerState.lower()
            if power_state == "poweredon":
                vm_power = "on"
            else:
                vm_power = "off"

            # get vm custom attributes
            vm_attrs = {}
            for attr in vm.summary.customValue:
                # Attribute key value check
                # if vm_name == 'VSP-YektaSabz':
                #    print(f'{attr.key}: {attr.value}')
                if vcenter_name.startswith('vab'):
                    if attr.key in vab_key_map:
                        vm_attrs[vab_key_map[attr.key]] = attr.value
                elif vcenter_name.startswith('me'):
                    if attr.key in me_key_map:
                        vm_attrs[me_key_map[attr.key]] = attr.value

            # set vm custom attributes
            vm_company_name =               vm_attrs.get('vm_company_name', 'N/A')
            vm_national_id =                vm_attrs.get('vm_national_no', 'N/A')
            vm_creation_ticket_id =         vm_attrs.get('vm_creation_ticket_no', 'N/A')
            vm_shutdown_ticket_id =         vm_attrs.get('vm_shutdown_ticket_no', 'N/A')
            vm_disconnect_ticket_id =       vm_attrs.get('vm_disconnect_ticket_no', 'N/A')
            vm_creation_date =              vm_attrs.get('vm_creation_date', 'N/A')
            vm_shutdown_date =              vm_attrs.get('vm_shutdown_date', 'N/A')
            vm_disconnect_date =            vm_attrs.get('vm_disconnect_date', 'N/A')
            vm_public_ip =                  vm_attrs.get('vm_public_ip', 'N/A')
            vm_url =                        vm_attrs.get('vm_url', 'N/A')
            vm_agent_name =                 vm_attrs.get('vm_rep_name', 'N/A')
            vm_agent_no =                   vm_attrs.get('vm_rep_no', 'N/A')
            vm_agent_email =                vm_attrs.get('vm_rep_email', 'N/A')
            vm_confidentiality =            vm_attrs.get('vm_confidentiality_weight', 'N/A')
            vm_integrity =                  vm_attrs.get('vm_integrity_weight', 'N/A')
            vm_availability =               vm_attrs.get('vm_availability_weight', 'N/A')
            vm_dongle =                     'True' if (vm_attrs.get('vm_dongle_status', 'N/A')).strip() == '1' else 'False'
            vm_sts_vpn =                    'True' if (vm_attrs.get('vm_site_to_site_status', 'N/A')).strip() == '1' else 'False'
            vm_ids_ips =                    'True' if (vm_attrs.get('vm_ipsids_status', 'N/A')).strip() == '1' else 'False'
            vm_waf =                        'True' if (vm_attrs.get('vm_waf_status', 'N/A')).strip() == '1' else 'False'
            vm_vip =                        'True' if (vm_attrs.get('vm_vip_status', 'N/A')).strip() == '1' else 'False'


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
            else:
                vm_product_line = 'N/A'

            # datacenter
            if vcenter_name.startswith('vab'):
                vm_datacenter = 'Vanak-P73'
            elif vcenter_name.startswith('me'):
                vm_datacenter = 'Miremad-Asiatech'

            # Take vm disk's origin and capacity
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualDisk):
                    if "-pro-" in str(device.backing.fileName).lower():
                        vm_storage_cluster_ssd = device.backing.fileName.split()[0].strip('[]').rsplit('-', 1)[0]
                        vm_sum_ssd += (device.capacityInBytes / 1024 / 1024 / 1024)
                        vm_sum_ssd_in_bytes += device.capacityInBytes
                    elif "-std-" in str(device.backing.fileName).lower():
                        vm_storage_cluster_hdd = device.backing.fileName.split()[0].strip('[]').rsplit('-', 1)[0]
                        vm_sum_hdd += (device.capacityInBytes / 1024 / 1024 / 1024)
                        vm_sum_hdd_in_bytes += device.capacityInBytes
                    elif "-archive-" in str(device.backing.fileName).lower():
                        vm_storage_cluster_arch = device.backing.fileName.split()[0].strip('[]').rsplit('-', 1)[0]
                        vm_sum_arch += (device.capacityInBytes / 1024 / 1024 / 1024)
                        vm_sum_arch_in_bytes += device.capacityInBytes
                    elif "-ultra-" in str(device.backing.fileName).lower():
                        vm_storage_cluster_nvme = device.backing.fileName.split()[0].strip('[]').rsplit('-', 1)[0]
                        vm_sum_nvme += (device.capacityInBytes / 1024 / 1024 / 1024)
                        vm_sum_nvme_in_bytes += device.capacityInBytes
                    elif "-adv-" in str(device.backing.fileName).lower():
                        vm_storage_cluster_hyb = device.backing.fileName.split()[0].strip('[]').rsplit('-', 1)[0]
                        vm_sum_hyb += (device.capacityInBytes / 1024 / 1024 / 1024)
                        vm_sum_hyb_in_bytes += device.capacityInBytes

            # get cpu type
            if "-highperformance-" in vm_compute_cluster.lower():
                vm_cpu_type = "HighPerformance"
            elif "-normal-" in vm_compute_cluster.lower():
                vm_cpu_type = "NormalPerformance"
            else:
                vm_cpu_type = "N/A"

            # get cpu core
            vm_cpu_core = vm.config.hardware.numCPU

            # get memory
            vm_memory = int(vm.config.hardware.memoryMB / 1024)

            # Get PortGroup and Vlan ID and NIC connection status
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):

                    # VM NIC Status
                    nic_connected = device.connectable.connected
                    vm_nic_status = 1 if nic_connected else 0

                    network = device.backing
                    if isinstance(network, vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo):
                        dvs_portgroup_key = network.port.portgroupKey
                        dvs_uuid = network.port.switchUuid

                        # Retrieve the Distributed Virtual Switch
                        dvs = content.dvSwitchManager.QueryDvsByUuid(dvs_uuid)

                        # Find the port group by key
                        for portgroup in dvs.portgroup:
                            if portgroup.key == dvs_portgroup_key:
                                vlan_config = portgroup.config.defaultPortConfig.vlan

                                # VM VLAN ID
                                if isinstance(vlan_config, vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec):
                                    vm_vlan_id = vlan_config.vlanId
                                else:
                                    vm_vlan_id = "N/A"

                                # VM PortGroup Name
                                vm_portgroup = portgroup.name if portgroup.name else "N/A"
                                break
                    else:
                        print(f"  {vm.name}: Network: Non-distributed virtual port group or no backing info")

            # retrieve vm ip address
            vm_private_ip = "N/A"
            if vm.guest is not None:
                candidate_ips = []
                for nic in vm.guest.net:
                    if nic.ipConfig is not None:
                        for ip in nic.ipConfig.ipAddress:
                            candidate_ips.append(ip.ipAddress)

                for ip in candidate_ips:
                    if not ip.startswith(('169.254', 'fe80')):
                        vm_private_ip = ip
                        break

            vm_nic_status_label = 'Connected' if vm_nic_status == 1 else 'Disconnected'

            # Metric initialization
            vm_general_spec.labels(vm_name=vm_name,
                                   hostname=vm_hostname,
                                   dns_suffix=vm_dns_suffix,
                                   os=vm_os,
                                   product_line=vm_product_line,
                                   company_name=vm_company_name,
                                   national_id=vm_national_id,
                                   power=vm_power,
                                   compute_cluster=vm_compute_cluster,
                                   creation_ticket_id=vm_creation_ticket_id,
                                   shutdown_ticket_id=vm_shutdown_ticket_id,
                                   disconnect_ticket_id=vm_disconnect_ticket_id,
                                   creation_date=vm_creation_date,
                                   shutdown_date=vm_shutdown_date,
                                   disconnect_date=vm_disconnect_date,
                                   url=vm_url,
                                   dongle=vm_dongle,
                                   sts_vpn=vm_sts_vpn,
                                   ids_ips=vm_ids_ips,
                                   waf=vm_waf,
                                   vip=vm_vip,
                                   agent_name=vm_agent_name,
                                   agent_no=vm_agent_no,
                                   agent_email=vm_agent_email,
                                   nic=vm_nic_status_label,
                                   confidentiality=vm_confidentiality,
                                   integrity=vm_integrity,
                                   availability=vm_availability,
                                   datacenter=vm_datacenter,
                                   ).set(1)

            vm_cpu_spec.labels(vm_name=vm_name,
                               national_id=vm_national_id,
                               compute_cluster=vm_compute_cluster,
                               cpu_type=vm_cpu_type,
                               datacenter=vm_datacenter,
                               ).set(vm_cpu_core)

            vm_memory_spec.labels(vm_name=vm_name,
                                  national_id=vm_national_id,
                                  compute_cluster=vm_compute_cluster,
                                  datacenter=vm_datacenter,
                                  ).set(vm_memory)

            vm_network_spec.labels(vm_name=vm_name,
                                   national_id=vm_national_id,
                                   private_ip=vm_private_ip,
                                   public_ip=vm_public_ip,
                                   vlan_id=vm_vlan_id,
                                   portgroup_id=vm_portgroup,
                                   datacenter = vm_datacenter,
                                   ).set(vm_nic_status)

            vm_storage_ssd_total_bytes.labels(vm_name=vm_name,
                                              national_id=vm_national_id,
                                              storage_cluster=vm_storage_cluster_ssd,
                                              vm_storage_total_gibibytes=vm_sum_ssd,
                                              datacenter = vm_datacenter,
                                              ).set(vm_sum_ssd_in_bytes)

            vm_storage_hdd_total_bytes.labels(vm_name=vm_name,
                                              national_id=vm_national_id,
                                              storage_cluster=vm_storage_cluster_hdd,
                                              vm_storage_total_gibibytes=vm_sum_hdd,
                                              datacenter=vm_datacenter,
                                              ).set(vm_sum_hdd_in_bytes)

            vm_storage_arch_total_bytes.labels(vm_name=vm_name,
                                               national_id=vm_national_id,
                                               storage_cluster=vm_storage_cluster_arch,
                                               vm_storage_total_gibibytes=vm_sum_arch,
                                               datacenter=vm_datacenter,
                                               ).set(vm_sum_arch_in_bytes)

            vm_storage_hyb_total_bytes.labels(vm_name=vm_name,
                                              national_id=vm_national_id,
                                              storage_cluster=vm_storage_cluster_hyb,
                                              vm_storage_total_gibibytes=vm_sum_hyb,
                                              datacenter=vm_datacenter,
                                              ).set(vm_sum_hyb_in_bytes)

            vm_storage_nvme_total_bytes.labels(vm_name=vm_name,
                                               national_id=vm_national_id,
                                               storage_cluster=vm_storage_cluster_nvme,
                                               vm_storage_total_gibibytes=vm_sum_nvme,
                                               datacenter=vm_datacenter,
                                               ).set(vm_sum_nvme_in_bytes)

            if vm_name and vm_hostname and vm_name.lower() != vm_hostname.lower():
                vm_name_and_hostname_matches.labels(product_line=vm_product_line,
                                                    vm_name=vm_name,
                                                    vm_hostname=vm_hostname,
                                                    national_id=vm_national_id,
                                                    datacenter=vm_datacenter,
                                                    ).set(0)
            else:
                vm_name_and_hostname_matches.labels(product_line=vm_product_line,
                                                    vm_name=vm_name,
                                                    vm_hostname=vm_hostname,
                                                    national_id=vm_national_id,
                                                    datacenter=vm_datacenter,
                                                    ).set(1)

            print(f'''
            Info:
            Name:               {vm_name}
            Hostname:           {vm_hostname}
            DNS Suffix:         {vm_dns_suffix}
            OS:                 {vm_os}
            Product Line:       {vm_product_line}
            Power State:        {vm_power}
            Compute Cluster:    {vm_compute_cluster}
            Company Name:       {vm_company_name}
            National ID:        {vm_national_id}
            Ticket ID:          {vm_creation_ticket_id}
            Creation Date:      {vm_creation_date}
            Shutdown Date:      {vm_shutdown_date}
            URL:                {vm_url}
            Dongle:             {vm_dongle}
            SiteToSite VPN:     {vm_sts_vpn}
            IDSIPS:             {vm_ids_ips}
            WAF:                {vm_waf}
            VIP:                {vm_vip}
    
            ============================
            Agent:
            Name:               {vm_agent_name}
            Number:             {vm_agent_no}
            Email:              {vm_agent_email}
    
            ============================
            Compute:
            CPU Type:           {vm_cpu_type}
            CPU Core:           {vm_cpu_core}
            Memory:             {vm_memory}
    
            ============================
            Network:
            NIC Connected:      {vm_nic_status}
            VLAN ID:            {vm_vlan_id}
            Portgroup ID:       {vm_portgroup}
            Private IP:         {vm_private_ip}
            Public IP:          {vm_public_ip}
    
            ============================
            Storage:
            SSD:                {vm_sum_ssd}
            SSD Bytes:          {vm_sum_ssd_in_bytes}
            SSD S Cluster:      {vm_storage_cluster_ssd}
    
            HDD:                {vm_sum_hdd}
            HDD Bytes:          {vm_sum_hdd_in_bytes}
            HDD S Cluster:      {vm_storage_cluster_hdd}
    
            Hybrid:             {vm_sum_hyb}
            Hybrid Bytes:       {vm_sum_hyb_in_bytes}
            Hybrid S Cluster:   {vm_storage_cluster_hyb}
    
            NVMe:               {vm_sum_nvme}
            NVMe Bytes:         {vm_sum_nvme_in_bytes}
            NVMe S Cluster:     {vm_storage_cluster_nvme}
    
            Archive:            {vm_sum_arch}
            Archive Bytes:      {vm_sum_arch_in_bytes}
            Archive S Cluster:  {vm_storage_cluster_arch}
    
            ============================
                        ''')

            vm_dict[f'{vm_name}'] = [vm_name, vm_power, vm_national_id, vm_creation_date, vm_creation_ticket_id,
                                     str(vm_memory), str(vm_cpu_core), str(vm_cpu_type), str(int(vm_sum_hdd)),
                                     str(int(vm_sum_ssd)), str(int(vm_sum_arch)), str(int(vm_sum_hyb)),
                                     str(int(vm_sum_nvme)), vm_private_ip, vm_public_ip, vm_url,
                                     vm_dongle, vm_sts_vpn, vm_ids_ips, vm_waf, vm_company_name]

        Disconnect(vc)

    # Excel export part
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    # Write the dictionary data to the worksheet
    header = ["Server Name", "State", "National ID", "Creation Date", "Ticket No", "RAM (GB)", "CPU Core",
              "CPU Type", "HDD Disk (GB)", "SSD Disk (GB)", "Capacity Disk (GB)", "Hybrid Disk (GB)",
              "NVMe Disk (GB)", "Private IP", "Public IP", "URL", "Physical Dongle", "Site-to-Site VPN",
              "IDS/IPS", "WAF Service", "Company Name"]
    worksheet.append(header)

    for vm_data in vm_dict:
        worksheet.append(vm_dict[vm_data])

    # Save the changes to the Excel file
    workbook.save(excel_file_path)

    files = [excel_file_path]
    make_zip(files, zip_file_path, zip_file_pass)

    email_body = 'Dear colleagues<br>You can find "Unified Customer VM Report" in attachment section.<br>Password of the zip file is shared with you in PasswordManager'
    send_anonymous_email(
        from_email="AbramadReport@abramad.com",
        to_email=receiver_email,
        cc_email=cc_email,
        subject=f'Abramad Customers VM Report',
        html_message=f"{email_body}<br><br>Agent: {script_name}",
        direction="ltr",
        attachments=[zip_file_path]
    )



except Exception as err:
    print(f"Script failed: {err}")
    success = False
    error_string_summary = f"{type(err).__name__}: {err}"

    # Get the traceback and extract the last traceback frame
    tb = traceback.extract_tb(err.__traceback__)
    last_call = tb[-1]  # the last traceback frame, where the exception occurred
    error_string_detail = f"Error occurred in line {last_call.lineno}: {last_call.line}"


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
