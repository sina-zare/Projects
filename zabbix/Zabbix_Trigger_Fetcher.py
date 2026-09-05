import os
import json
import time
import openpyxl
import traceback
from html import escape
from pyzabbix import ZabbixAPI
from atlassian import Confluence
from cryptography.fernet import Fernet
from urllib.parse import urlparse, urlunparse
from datetime import datetime, timezone, timedelta
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter

# --- Configuration ---
script_name = 'zabbix_trigger_fetcher'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'https://vnk-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
push_datacenter = 'miremad_vanak'
target = 'zabbix_template_triggers'

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

    # print(f"Decrypted Text: {decrypted_password}")
    return decrypted_password.decode()


def generate_html(zbx_name, template_name, rows):
    """
    Generate Confluence-compatible HTML table for a single template's rows.
    """

    html = f"""
    <h2>{escape(template_name)}</h2>

    <p>
    <b>Zabbix Server:</b> {escape(zbx_name)}<br/>
    <b>Triggers:</b> {len(rows)}
    </p>

    <table>
    <tbody>
    <tr>
    <th>Alert</th>
    <th>Severity</th>
    <th>Status</th>
    <th>Expression</th>
    </tr>
    """

    row_colors = {
        "enabled": "#d9ead3",   # light green
        "disabled": "#f4cccc",  # light red
    }

    for r in rows:
        row_bg = row_colors.get(r["status"], "")
        row_style = f' style="background-color: {row_bg};"' if row_bg else ""
        html += f"""
        <tr{row_style}>
            <td>{escape(r["trigger"])}</td>
            <td>{escape(r["severity"])}</td>
            <td>{escape(r["status"])}</td>
            <td><code>{escape(r["expression"])}</code></td>
        </tr>
        """

    html += """
      </tbody>
    </table>
    """

    return html


def publish_page(
        confluence,
        space,
        title,
        html,
        excel_file_path=None,
        parent_id=None
):
    """
    Create or update a Confluence page and optionally upload an Excel attachment.

    Parameters:
        confluence      : Atlassian Confluence object
        space           : Confluence space key (e.g. "ManSer")
        title           : Page title
        html            : Page body (storage format)
        excel_file_path : Optional path to XLSX file to attach
        parent_id       : Optional parent page ID
    """

    existing_page = confluence.get_page_by_title(
        space_key=space,
        title=title
    )

    # Page exists
    if existing_page.get("size", 0) > 0:
        page_id = existing_page["results"][0]["id"]

        print(f"[INFO] Updating existing page: {title}")

        confluence.update_page(
            page_id=page_id,
            title=title,
            body=html,
            representation="storage",
            full_width=True
        )

    # Page does not exist
    else:
        print(f"[INFO] Creating new page: {title}")

        result = confluence.create_page(
            space=space,
            title=title,
            body=html,
            parent_id=parent_id,
            representation="storage",
            full_width=True
        )

        page_id = result["id"]

    # Upload Excel attachment
    if excel_file_path and os.path.exists(excel_file_path):
        attachment_name = os.path.basename(excel_file_path)

        print(f"[INFO] Uploading attachment: {attachment_name}")

        confluence.attach_file(
            filename=excel_file_path,
            name=attachment_name,
            page_id=page_id,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    print(f"[SUCCESS] Published page: {title}")

    return page_id


severity_map = {
    "0": "Not classified",
    "1": "Information",
    "2": "Warning",
    "3": "Average",
    "4": "High",
    "5": "Disaster"
}

zabbix_nodes = {
    # Vanak
    'VNK-Zabbix': "https://vnk-zabbix.abramad.com",
    'VNK-CustomerZabbix': "https://vnk-customerzabbix.abramad.com",

    # Miremad
    'ME-Zabbix': "https://me-zabbix.abramad.com/zabbix",
    'ME-CustomerZabbix': "https://me-customerzabbix.abramad.com"
}

username = 'sysops-svc'
password = decryptor('sysops-svc_enc', 'sysops-svc_key')

iran_tz = timezone(timedelta(hours=3, minutes=30))

for zbx_name, abx_addr in zabbix_nodes.items():
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    header = ["Zabbix Server", "Template", "Alert", "Severity", "Status", "Expression"]
    worksheet.append(header)

    generated_time = datetime.now(iran_tz).strftime("%Y-%m-%d %H:%M UTC+03:30")

    html = f"""
    <h1>{escape(zbx_name.upper())} Zabbix Template Triggers</h1>

    <p>
        Generated automatically from Zabbix active templates.<br/>
        Last update: {generated_time}<br/>
    </p>"""

    zapi = ZabbixAPI(abx_addr)
    zapi.login(username, password)

    # Get all active templates
    # Fetch all templates with linked hosts
    templates_with_hosts = zapi.template.get(
        selectHosts="extend",  # Get detailed host information
        output=["templateid", "name"]  # Only fetch template ID and name
    )

    # Find templates that have at least one host attached
    templates_with_at_least_one_host = [
        template
        for template in templates_with_hosts
        if template['hosts']
    ]

    if templates_with_at_least_one_host:
        print(f"Templates found: {len(templates_with_at_least_one_host)}")

    for template in templates_with_at_least_one_host:
        print(f"Checking template: {template['name']}")

        triggers = zapi.trigger.get(
            output=[
                "description",
                "expression",
                "priority",
                "status"
            ],
            templateids=template["templateid"],
            expandExpression=True
        )

        print(f"Triggers found: {len(triggers)}")

        trigger_prototypes = zapi.triggerprototype.get(
            output=[
                "description",
                "expression",
                "priority",
                "status"
            ],
            templateids=template["templateid"],
            expandExpression=True
        )

        print(f"Trigger prototypes found: {len(trigger_prototypes)}")

        template_rows = []

        for trigger in triggers:
            row = {
                "zabbix_server": zbx_name,
                "template": template["name"],
                "trigger": trigger["description"],
                "expression": trigger["expression"],
                "severity": severity_map[trigger["priority"]],
                "status": "enabled" if trigger["status"] == "0" else "disabled"
            }
            template_rows.append(row)

        for trigger in trigger_prototypes:
            row = {
                "zabbix_server": zbx_name,
                "template": template["name"],
                "trigger": trigger["description"],
                "expression": trigger["expression"],
                "severity": severity_map[trigger["priority"]],
                "status": "enabled" if trigger["status"] == "0" else "disabled",
            }
            template_rows.append(row)

        for r in template_rows:
            worksheet.append([
                r["zabbix_server"],
                r["template"],
                r["trigger"],
                r["severity"],
                r["status"],
                r["expression"],
            ])

        html += generate_html(
            zbx_name,
            template["name"],
            template_rows
        )

    iran_date = datetime.now(iran_tz).strftime("%Y_%m_%d")
    excel_dir = f"C:/Temp/{script_name}/reports"
    os.makedirs(excel_dir, exist_ok=True)
    excel_path = f"{excel_dir}/{zbx_name}_triggers_{iran_date}.xlsx"
    workbook.save(excel_path)

    confluence = Confluence(
        url='https://confluence.abramad.com',
        username=username,
        password=password,
        verify_ssl=False
    )

    publish_page(
        confluence=confluence,
        space="ManSer",
        title=zbx_name,
        html=html,
        excel_file_path=excel_path
    )