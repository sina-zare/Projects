import csv
import openpyxl
from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
from email.header import Header
import ssl
import warnings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter
import traceback
import random
import time
import os

# --- Configuration ---
script_name = 'all_vms_info'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'https://me-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
datacenter = 'miremad'
target = 'me-vc01_customer_vms'

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




    def send_anonymous_email(from_email, to_email, cc_email, subject, html_message, direction,
                             mail_server='mail.abramad.com', attachments=None):
        try:
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

        except Exception as err:
            print(f"email_sender Function Error: {err}")
            send_anonymous_email('ScriptErrors@abramad.com', 'abramadsysops@abramad.com', 'sina.z@abramad.com',
                                 f"email_sender Function Error in running All_VMs_Info.py",
                                 f"Error Occurred:<br><b>{err}<br></b> Agent: All_VMs_Info.py",
                                 'ltr')


    # Append Dict B to Dict A
    def append_dict(target_dict, source_dict):
        for key, value in source_dict.items():
            if key in target_dict:
                target_dict[key].extend(value)
            else:
                # target_dict[key] = [value]
                continue


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

    username = 'support@abramad.com'
    username = 'sysops-svc@abramad.com'

    password = decryptor('sysops-svc_enc', 'sysops-svc_key')


    commvault_reports_path = "C:/Users/sina.z/Desktop/Commvault Reports/"
    # Get a list of all files in the folder
    files = os.listdir(commvault_reports_path)
    # Sort the files based on their creation time
    sorted_files = sorted(files, key=lambda x: os.path.getctime(os.path.join(commvault_reports_path, x)), reverse=True)
    # Get the latest file (first element in the sorted list)
    latest_commvault_report = sorted_files[0]

    full_path_to_latest_commvault_report = commvault_reports_path + latest_commvault_report

    vm_backup_info = {}

    with open(full_path_to_latest_commvault_report, "r") as file:
        csv_reader = csv.reader(file)

        # Skip the first 21 lines
        for _ in range(21):
            next(csv_reader)

        # Read from row 22 onwards
        for row in csv_reader:
            try:
                # Initializing
                bk_type_incr = 0
                bk_type_full = 0

                # take backup size
                bk_size_in_gb = (int(row[5]) / (1024 ** 3))

                if row[1].lower() == "incremental":
                    bk_type_incr += 1
                elif row[1].lower() == "full":
                    bk_type_full += 1

                if int(row[2][-7:-6]) >= 0 and int(row[2][-7:-6]) <= 4:
                    bk_schedule = row[2][-11:-7] + "0:00" + row[2][-3:]
                else:
                    bk_schedule = row[2][-11:-7] + "5:00" + row[2][-3:]

                # import backup data for each VM in a dictionary
                vm_name = row[0].lower()
                if vm_name in vm_backup_info:
                    # Backup size
                    vm_backup_info[vm_name][0] += round(bk_size_in_gb, 1)
                    # Backup Incremental Jobs
                    vm_backup_info[vm_name][1] += bk_type_incr
                    # Backup Full Jobs
                    vm_backup_info[vm_name][2] += bk_type_full


                else:
                    # Backup Size 19[0]
                    vm_backup_info[vm_name] = [round(bk_size_in_gb, 1)]

                    # Backup Incremental Jobs 19[1]
                    vm_backup_info[vm_name].append(bk_type_incr)

                    # Backup Full Jobs 19[1]
                    vm_backup_info[vm_name].append(bk_type_full)

                    # Backup Schedule 19[2]
                    vm_backup_info[vm_name].append(bk_schedule)


            except:
                continue

    print(f"Selected Commvault Report: {latest_commvault_report}\n\n")

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
    me_vms = [vm for vm in me_vm_view.view if (
                vm.name.startswith("MER-") or vm.name.startswith("MERD-") or vm.name.startswith(
            "MEF-") or vm.name.startswith("MES-") or vm.name.startswith("MEA-") or vm.name.startswith(
            "MEB-") or vm.name.startswith("MEM-") or vm.name.startswith("MEI-") or vm.name.startswith("MESA-"))]

    vm_specs = {}
    vm_error = []

    for vm in me_vms:

        # === Calculating VM Specs ===

        # initializing variables
        vm_sum_ssd = 0
        vm_sum_hdd = 0
        vm_sum_capacity = 0
        vm_sum_nvme = 0
        vm_sum_hyb = 0
        vm_is_found = 1
        vm_cluster = vm.runtime.host.parent.name

        # Get VM Creation Date
        vm_creation_date = ""
        custom_value_d = vm.summary.customValue
        for i in custom_value_d:
            if i.key == 104:
                vm_creation_date = (i.value)

        # VM Power State
        vm_power_state = "خاموش"
        power_state = vm.runtime.powerState.lower()
        if power_state == "poweredon":
            vm_power_state = "روشن"

        # Take vm disk's origin and capacity
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualDisk):
                if "-pro-" in str(device.backing.fileName).lower():
                    vm_sum_ssd += (device.capacityInBytes / 1024 / 1024 / 1024)
                    #vm_sum_ssd_in_bytes += device.capacityInBytes
                elif "-std-" in str(device.backing.fileName).lower():
                    vm_sum_hdd += (device.capacityInBytes / 1024 / 1024 / 1024)
                    #vm_sum_hdd_in_bytes += device.capacityInBytes
                elif "-archive-" in str(device.backing.fileName).lower():
                    vm_sum_capacity += (device.capacityInBytes / 1024 / 1024 / 1024)
                    #vm_sum_cap_in_bytes += device.capacityInBytes
                elif "-ultra-" in str(device.backing.fileName).lower():
                    vm_sum_nvme += (device.capacityInBytes / 1024 / 1024 / 1024)
                    #vm_sum_nvme_in_bytes += device.capacityInBytes
                elif "-adv-" in str(device.backing.fileName).lower():
                    vm_sum_hyb += (device.capacityInBytes / 1024 / 1024 / 1024)
                    #vm_sum_hyb_in_bytes += device.capacityInBytes

        '''for device in vm.config.hardware.device:

            if isinstance(device, vim.vm.device.VirtualDisk):

                if "-ultraperfssd-" in str(device.backing.fileName).lower() or "-ultraperformance-ssd" in str(device.backing.fileName).lower() or "-ultraperf-" in str(device.backing.fileName).lower():
                    vm_sum_ssd += (device.capacityInBytes / 1024 / 1024 / 1024)
                elif "-perf-" in str(device.backing.fileName).lower() or "-performance" in str(device.backing.fileName).lower() or "-highperf-" in str(device.backing.fileName).lower():
                    vm_sum_hdd += (device.capacityInBytes / 1024 / 1024 / 1024)
                elif "-capacity-" in str(device.backing.fileName).lower():
                    vm_sum_capacity += (device.capacityInBytes / 1024 / 1024 / 1024)'''

        # Find CPU Type
        if "-highperformance-" in vm_cluster.lower():
            vm_cpu_type = "High Performance"
        elif "-normal-" in vm_cluster.lower():
            vm_cpu_type = "Normal Performance"
        else:
            vm_cpu_type = "N/A"

        # Get VM CPU Core
        vm_cpu_core = vm.config.hardware.numCPU

        # Find if vm has public IP
        vm_has_public_ip = "ندارد"
        vm_custom_attr = vm.summary.customValue
        for i in vm_custom_attr:
            if i.key == 603 and i.value != "":
                vm_has_public_ip = "دارد"

        # Get VM Persian Name
        vm_persian_name = ""
        custom_value_n = vm.summary.customValue
        for i in custom_value_n:
            if i.key == 103:
                vm_persian_name = i.value

        # retrieve vm IP address
        vm_ip = ""
        if vm.guest is not None:
            for nic in vm.guest.net:
                if nic.ipConfig is not None:
                    for ip in nic.ipConfig.ipAddress:
                        if not ip.ipAddress.startswith('169.254') and not ip.ipAddress.startswith(
                                'fe80'):
                            vm_ip = ip.ipAddress

        # Get VM RAM
        vm_ram = int(vm.config.hardware.memoryMB / 1024)

        # Get VM Public IP
        vm_public_ip = ""
        vm_custom_attr = vm.summary.customValue
        for i in vm_custom_attr:
            if i.key == 603:
                vm_public_ip = i.value

        # Get VM URL
        vm_url = ""
        vm_custom_attr = vm.summary.customValue
        for i in vm_custom_attr:
            if i.key == 604:
                vm_url = i.value

        # Get Physical Dongle Status
        vm_physical_dongle = "ندارد"
        custom_value_n = vm.summary.customValue
        for i in custom_value_n:
            if i.key == 701 and i.value == "1":
                vm_physical_dongle = "دارد"

        # Get Site-to-Site VPN Status
        vm_site2site_vpn = "ندارد"
        custom_value_n = vm.summary.customValue
        for i in custom_value_n:
            if i.key == 702 and i.value == "1":
                vm_site2site_vpn = "دارد"

        # Get IDS/IPS Status
        vm_ids_ips = "ندارد"
        custom_value_n = vm.summary.customValue
        for i in custom_value_n:
            if i.key == 703 and i.value == "1":
                vm_ids_ips = "دارد"

        # Get WAF Status
        vm_waf = "ندارد"
        custom_value_n = vm.summary.customValue
        for i in custom_value_n:
            if i.key == 704 and i.value == "1":
                vm_waf = "دارد"

        # Get National ID Status
        vm_national_id = "ندارد"
        custom_value_n = vm.summary.customValue
        for i in custom_value_n:
            if i.key == 611:
                vm_national_id = i.value

        # Get VM Ticket No
        vm_ticket_no = "0"
        vm_note = vm.config.annotation.split("\n")
        vm_ticket_no = (vm_note[0][10:]).replace(":", "").strip()

        #                                      0           1               2                3                 4         5           6               7               8                   9               10       11          12           13               14             15        16         17         18         19
        vm_specs[f'{(vm.name).lower()}'] = [vm.name, vm_power_state, vm_national_id, vm_creation_date, vm_ticket_no,
                                            str(vm_ram), str(vm_cpu_core), str(vm_cpu_type),
                                            str(int(vm_sum_hdd)), str(int(vm_sum_ssd)), str(int(vm_sum_capacity)), str(int(vm_sum_hyb)), str(int(vm_sum_nvme)), vm_ip,
                                            vm_public_ip, vm_url, vm_physical_dongle, vm_site2site_vpn, vm_ids_ips, vm_waf,
                                            vm_persian_name]

    append_dict(vm_specs, vm_backup_info)

    # Check and fill with N/A if
    for key in vm_specs:
        if len(vm_specs[key]) < 20:
            vm_specs[key].extend([0, "N/A", "N/A", "N/A"])

    """
    count = 0
    for vm in vm_specs:
        try:
            print(f'''\n=======================
    
            Persian Name: {vm_specs[vm][13]}
            National ID: {vm_specs[vm][18]}
            Server Name: {vm_specs[vm][0]}
            is: {vm_specs[vm][1]}
            Create Date: {vm_specs[vm][2]}
            Private IP: {vm_specs[vm][3]}
            RAM: {vm_specs[vm][4]} GB
            CPU: {vm_specs[vm][5]} Core - {vm_specs[vm][6]}
            HDD Disk: {vm_specs[vm][7]}
            SSD Disk: {vm_specs[vm][8]}
            Capacity Disk: {vm_specs[vm][9]}
            Public IP: {vm_specs[vm][10]}
            Public IP: {vm_specs[vm][11]}
            URL: {vm_specs[vm][12]}
            Physical Dongle: {vm_specs[vm][14]}
            Site-to-Site VPN: {vm_specs[vm][15]}
            IDS/IPS: {vm_specs[vm][16]}
            WAF Service: {vm_specs[vm][17]}
    
            Backup Info
            Backup Size: {round(vm_specs[vm][19][0], 1)} GB
            Backup Jobs: {vm_specs[vm][19][1]} Incremental, {vm_specs[vm][19][2]} Full
            Backup Schedule: {vm_specs[vm][19][3]}
    
            \n=======================''')
    
    
    
        except:
            print(f"{vm_specs[vm][0]} threw an error!\n")
            vm_error.append(f"{vm_specs[vm][0]}")
    
    
    print("error throwing servers:")
    for i in vm_error:
        print(i)
    """

    # Load the Excel file
    workbook = openpyxl.Workbook()

    # Select the worksheet where you want to add data
    worksheet = workbook.active

    # Write the dictionary data to the worksheet
    # Write the dictionary data to the worksheet
    header = ["Server Name", "State", "National ID", "Creation Date", "Ticket No", "RAM (GB)", "CPU Core", "CPU Type", "HDD Disk (GB)",
              "SSD DIsk (GB)", "Capacity Disk (GB)", "Hybrid Disk (GB)", "NVMe Disk (GB)", "Private IP", "Public IP", "URL", "Physical Dongle",
              "Site-to-Site VPN", "IDS/IPS", "WAF Service", "Persian Name", "Backup Size (GB)", "Incremental Backup Jobs",
              "Full Backup Jobs", "Backup Schedule"]
    worksheet.append(header)

    for vm in vm_specs:
        worksheet.append(vm_specs[vm])

    # Save the changes to the Excel file
    workbook.save('C:/Users/sina.z/Desktop/Automation_Reports/All_VMs_Info/Servers-Full-Report.xlsx')

    Disconnect(ME_VC)

    # Date Processes

    from datetime import date
    from persiantools.jdatetime import JalaliDate
    import datetime

    month_dict = {
        "01": "Far",
        "02": "Ord",
        "03": "Khor",
        "04": "Tir",
        "05": "Mor",
        "06": "Shah",
        "07": "Mehr",
        "08": "Aban",
        "09": "Azar",
        "10": "Dey",
        "11": "Bah",
        "12": "Esf"
    }

    month_dict_persian = {
        "Dey": "دی",
        "Bah": "بهمن",
        "Esf": "اسفند",
        "Far": "فروردین",
        "Ord": "اردیبهشت",
        "Khor": "خرداد",
        "Tir": "تیر",
        "Mor": "مرداد",
        "Shah": "شهریور",
        "Mehr": "مهر",
        "Aban": "آبان",
        "Azar": "آذر"
    }

    # Get today's date
    today = date.today()
    # Convert to Persian date
    persian_date = JalaliDate.to_jalali(today.year, today.month, today.day)
    # Format the Persian date as "YYYY/MM/DD"
    today_persian_date = persian_date.strftime("%Y/%m/%d")

    current_month = f'{month_dict[str(today_persian_date[5:7])]}'
    persian_current_month = month_dict_persian[current_month]
    current_day = today_persian_date[8:11]
    current_year = today_persian_date[0:4]
    # Get the current date and time
    current_date = datetime.datetime.now()
    # Get the abbreviated name of the current day
    day_name = current_date.strftime('%a')



    if True:
        # Send Email to King

        import imaplib
        import email
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication

        #sender_email = 'sina.z@abramad.com'
        receiver_email = 'sales@abramad.com, accounting@abramad.com'
        cc_email = 'admin@abramad.com, sysops@abramad.com'

        attachment = 'C:/Users/sina.z/Desktop/Automation_Reports/All_VMs_Info/Servers-Full-Report.xlsx'



        ##############################################
        ######### HTML Body Begin For Email ##########
        html_line_break = '''
                    <p><br></p>
                '''
        html_msg_1 = '''
                <html dir="rtl">
                  <body>
                '''
        html_msg_2 = '''
                    <p  style="font-family: DiodrumArabic-Regular">با سلام و احترام</p>
                '''
        html_msg_3 = f'''
                    <p  style="font-family: DiodrumArabic-Regular">گزارش اطلاعات کامل سرور های مشترکین ابرآمد تا تاریخ {current_day} {persian_current_month} {current_year} به پیوست قرار گرفت.</p>
                '''
        #html_msg_4 = f'''
                    #<p  style="font-family: DiodrumArabic-Regular">لازم به ذکر است، این گزارش به صورت روزانه در confluence برزرسانی میگردد که از طریق لینک زیر میتوانید به صفحه ی مربوطه مراجعه نمایید. در نظر داشته باشید که این گزارش بصورت هفتگی نیز برای شما ارسال میشود.</p>
                #'''
        #html_msg_5 = f'''
                        #<p  style="font-family: DiodrumArabic-Regular">https://confluence.abramad.com/x/_dFY</p>
                    #'''
        #html_msg_7 = f'''
                    #<p style="font-family: DiodrumArabic-Regular"><em><b>سینا زارع<br>سرپرست تیم پشتیبانی ابرآمد<br>واحد عملیات</b></em></p>
                #'''
        html_msg_8 = '''
                  </body>
                </html>
                '''
        ######### HTML Body End For Email ##########
        ############################################

        email_body = html_msg_1 + html_msg_2 + html_msg_3 + html_line_break + html_msg_8 #html_msg_4 + html_msg_5 + html_line_break + html_msg_7

        send_anonymous_email(
            from_email="AbramadReport@abramad.com",
            to_email=receiver_email,
            cc_email=cc_email,
            subject=f'گزارش اطلاعات کامل مشترکین میرعماد | {current_day} {persian_current_month} {current_year}',
            html_message=f"{email_body}<br><br>Agent: All_VMs_Info.py",
            direction="rtl",
            attachments=[attachment]
        )



    '''
    # Confluence file upload part
    # https://confluence.abramad.com/x/_dFY
    import requests
    
    auth = ('user', f'{password}')
    
    headers = {'X-Atlassian-Token': 'nocheck'}
    
    # Define the Confluence base URL and the necessary headers for authentication:
    base_url = 'https://confluence.abramad.com'
    
    page_id = '5820921'  # or 'your-page-title'
    
    # Define the file path and name of the file to upload:
    file_path = "C:/Users/sina.z/Desktop/Automation_Reports/All_VMs_Info/Servers-Full-Report.xlsx"
    file_name = f"Servers-Full-Report-{current_day}-{current_month}-{current_year}.xlsx"
    
    # Read the file content and prepare the request data:
    with open(file_path, 'rb') as file:
        file_content = file.read()
    data = {
        'file': (file_name, file_content),
        'comment': f'Uploaded by S.Z via Magic on {current_day}-{current_month}-{current_year}'
    }
    
    # Send the request to upload the file to the Confluence page:
    upload_url = f'{base_url}/rest/api/content/{page_id}/child/attachment'
    response = requests.post(upload_url, auth=auth, headers=headers, files=data, verify=False)
    
    # Check the response status and handle any errors
    if response.status_code == 200:
        print('File uploaded successfully.')
    else:
        print(f'Error uploading file: {response.status_code} - {response.text}')
    
    
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

    print('✅ Metrics Sent.')

