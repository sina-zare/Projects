import os
import time
import smtplib
import openpyxl
import pyzipper
import warnings
import traceback
from pyzabbix import ZabbixAPI
from email.header import Header
from cryptography.fernet import Fernet
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from urllib3.exceptions import InsecureRequestWarning
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter


# --- Configuration ---
script_name = 'zabbix_maintenance_reports'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'https://vnk-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
datacenter = 'vanak_&_miremad'
target = 'zabbix_servers'

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


# read script run counter from file
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


# write updated count to file
def write_value_to_file(file_path, value):
    with open(file_path, 'w') as f:
        f.write(str(value))


def send_anonymous_email(from_email,
                         to_email,
                         cc_email,
                         subject,
                         html_message,
                         direction,
                         mail_server='mail.abramad.com',
                         attachments=None
                          ):
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


# zipper
def make_zip(files, zip_name, password):
    with pyzipper.AESZipFile(zip_name, 'w', compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES) as zf:
        zf.setpassword(password.encode())

        for file_path in files:
            file_name = os.path.basename(file_path)  # <- keeps only filename
            zf.write(file_path, arcname=file_name)  # <- overrides path inside ZIP


def decryptor(enc_env_var, key_env_var):
    # Load the key
    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = (os.environ.get(enc_env_var)).encode()
    # Decrypt Data
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())
    # print(f"Decrypted Text: {decrypted_password}")
    return decrypted_password.decode()

try:
    warnings.simplefilter("ignore", InsecureRequestWarning)
    zabbix_url_dict = {
        'ME-CustomerZabbix': 'https://me-customerzabbix.abramad.com',
        'VNK-CustomerZabbix': 'https://vnk-customerzabbix.abramad.com',
        'ME-Zabbix': 'https://me-zabbix.abramad.com/zabbix',
        'VNK-Zabbix': 'https://vnk-zabbix.abramad.com'
    }

    # Connect to Zabbix
    username = 'sysops-svc'
    password = decryptor('sysops-svc_enc', 'sysops-svc_key')
    zip_file_path = 'C://Temp//zabbix_maintenance_report.zip'
    zip_file_pass = "uS8#N@H2k(2M)8&nL]'Z;"
    receiver_email = 'admin@abramad.com'
    cc_email = 'sysops@abramad.com'
    files = []

    try:
        for key, url in zabbix_url_dict.items():

            excel_file_path = f'C://Temp//{key.lower()}_maintenance_report.xlsx'
            zapi = ZabbixAPI(url.strip())
            zapi.session.verify = False
            # zapi.session.headers.update({"User-Agent": "PyZabbix"})
            zapi.login(username.strip(), password)

            print(f"\n✅ Connected to {key}\nVersion {zapi.api_version()}")
            maintenances = zapi.maintenance.get(
                selectHosts=["hostid", "host"],
                selectGroups=["groupid", "name"]
            )
            # Excel export part
            workbook = openpyxl.Workbook()
            worksheet = workbook.active
            # Write the dictionary data to the worksheet
            header = ["Maintenance Name", "Start", "End", "Duration", "Initiator", "Nodes"]
            worksheet.append(header)

            if maintenances:
                for m in maintenances:
                    # print(f"Maintenance: {m['name']}")
                    # print(f"Description: {m['description']}")
                    # print("Hosts:")
                    # for h in m.get("hosts", []):
                    #     print(f"  - {h['host']}")
                    # print("-" * 50)

                    maintenance_id = m['maintenanceid']
                    maintenance_name = m['name']
                    parsed_desc = m['description'].replace('Maintenance window since ', '').replace(' till ', ',').replace(' | ', ',').split(',')
                    start_dt = parsed_desc[0]
                    end_dt = parsed_desc[1]
                    initiator = parsed_desc[-1]
                    # creating duration
                    tmp = parsed_desc
                    tmp.pop()
                    tmp.pop(0)
                    tmp.pop(0)
                    duration = ''.join(tmp).replace(' days', 'd').replace(' hours', 'h').replace(' minutes', 'm')
                    #print(f'{start_dt} | {end_dt} | {duration} | {initiator}')

                    nodes = []
                    for h in m.get("hosts", []):
                        nodes.append(h['host'])

                    worksheet.append([maintenance_name, start_dt, end_dt, duration, initiator, ', '.join(nodes)])

                    # delete maintenance
                    try:
                        zapi.maintenance.delete(maintenance_id)
                        print(f"✅ Deleted maintenance: {maintenance_name} (ID: {maintenance_id})")
                    except Exception as e:
                        print(f"❌ Failed to delete maintenance {maintenance_name} (ID: {maintenance_id}): {e}")

                # Save the changes to the Excel file
                workbook.save(excel_file_path)
                files.append(excel_file_path)
            else:
                print('    No Maintenance Found.')

    except Exception as err:
        print(f"Zabbix task failed: {err}")
        success = False
        error_string_summary = f"{type(err).__name__}: {err}"

        # Get the traceback and extract the last traceback frame
        tb = traceback.extract_tb(err.__traceback__)
        last_call = tb[-1]  # the last traceback frame, where the exception occurred
        error_string_detail = f"Error occurred in line {last_call.lineno}: {last_call.line}"

    if files:
        make_zip(files, zip_file_path, zip_file_pass)

        email_body = 'You can find "Zabbix Maintenance Report" in attachment section.<br>Password of the zip file is shared with you in PasswordManager<br>Disclaimer: If you received this email it means that the original "Maintenance Objects" are purged in Zabbix.'
        send_anonymous_email(
            from_email="AbramadReport@abramad.com",
            to_email=receiver_email,
            cc_email=cc_email,
            subject=f'Zabbix Maintenance Report',
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
    # finalizing Metrics
    # script duration
    duration = time.time() - start_time
    duration_gauge.set(duration)

    # script success Status
    status_gauge.set(1 if success else 0)

    # script total Executions
    total_exec_counts = read_value_from_file(total_exec_counter_file) + 1
    write_value_to_file(total_exec_counter_file, total_exec_counts)
    total_execution_counter.inc(total_exec_counts)

    if not success:
        # script total failed executions
        total_failed_exec_counts = read_value_from_file(total_failed_exec_counter_file) + 1
        write_value_to_file(total_failed_exec_counter_file, total_failed_exec_counts)
        total_failed_execution_counter.inc(total_failed_exec_counts)

        # script Last error message
        last_error_message.labels(error_summary=error_string_summary, error_detail=error_string_detail).set(1)

    elif success:
        # script total failed executions
        total_failed_exec_counts = read_value_from_file(total_failed_exec_counter_file)
        total_failed_execution_counter.inc(total_failed_exec_counts)

        # script last error message
        last_error_message.labels(error_summary="None", error_detail="None").set(0)

    # push metrics to pushgateway
    push_to_gateway(
        gateway=pushgateway_url,
        job=job_name,
        grouping_key={'instance': instance, 'target': target, 'datacenter': datacenter},
        registry=registry
    )
    print(f'✅ Metrics sent to {pushgateway_url}')

