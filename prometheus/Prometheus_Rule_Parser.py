import os
import yaml
import time
import openpyxl
import traceback
import subprocess
from pathlib import Path
from html import escape
from atlassian import Confluence
from cryptography.fernet import Fernet
from urllib.parse import urlparse, urlunparse
from datetime import datetime, timezone, timedelta
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter


# --- Configuration ---
script_name = 'prometheus_rule_parser'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'https://vnk-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
push_datacenter = 'miremad_vanak'
target = 'all_team_alert_rules'

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

def build_authenticated_git_url(repo_url, token):
    """
    Convert:
        https://gitlab.com/group/repo.git

    To:
        https://oauth2:TOKEN@gitlab.com/group/repo.git
    """

    parsed = urlparse(repo_url)

    authenticated_netloc = f"oauth2:{token}@{parsed.netloc}"

    return urlunparse((
        parsed.scheme,
        authenticated_netloc,
        parsed.path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))

def git_clone_or_pull(repo_url, repo_path, branch="main", timeout=300):
    """
    Clone repository if it does not exist.
    Otherwise perform git pull.

    Args:
        repo_url (str): Git repository URL.
        repo_path (str): Local repository path.
        branch (str): Branch name.
        timeout (int): Command timeout in seconds.

    Returns:
        dict
    """
    token = os.getenv("GITLAB_TOKEN")

    if not token:
        return {
            "success": False,
            "stderr": "GITLAB_TOKEN environment variable is not set"
        }

    authenticated_url = build_authenticated_git_url(repo_url, token)

    repo = Path(repo_path)

    try:

        # --------------------------------------------------
        # Clone repository
        # --------------------------------------------------
        if not repo.exists():
            repo.parent.mkdir(parents=True, exist_ok=True)

            clone_cmd = [
                "git",
                "clone",
                "-b",
                branch,
                authenticated_url,
                str(repo)
            ]

            result = subprocess.run(
                clone_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False
            )

            return {
                "action": "clone",
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            }

        # --------------------------------------------------
        # Validate git repository
        # --------------------------------------------------
        if not (repo / ".git").exists():
            return {
                "action": "none",
                "success": False,
                "stderr": f"{repo} exists but is not a git repository",
                "returncode": -1
            }

        # --------------------------------------------------
        # Update remote URL with token
        # --------------------------------------------------
        subprocess.run(
            [
                "git",
                "remote",
                "set-url",
                "origin",
                authenticated_url
            ],
            cwd=repo,
            capture_output=True,
            text=True,
            shell=False
        )

        # --------------------------------------------------
        # Pull latest changes
        # --------------------------------------------------
        pull_cmd = [
            "git",
            "pull",
            "origin",
            branch
        ]

        result = subprocess.run(
            pull_cmd,
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False
        )

        return {
            "action": "pull",
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }

    except subprocess.TimeoutExpired:

        return {
            "action": "timeout",
            "success": False,
            "stderr": f"Operation timed out after {timeout} seconds",
            "returncode": -1
        }

    except Exception as e:

        return {
            "action": "error",
            "success": False,
            "stderr": str(e),
            "returncode": -1
        }

def decryptor(enc_env_var, key_env_var):
    # Load the key
    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = (os.environ.get(enc_env_var)).encode()
    # Decrypt Data
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())

    # print(f"Decryped Text: {decrypted_password}")
    return decrypted_password.decode()

def generate_html(team, rows):
    """
    Generate Confluence-compatible HTML table
    """

    iran_tz = timezone(timedelta(hours=3, minutes=30))
    generated_time = datetime.now(iran_tz).strftime("%Y-%m-%d %H:%M UTC+03:30")

    html = f"""
    <h1>{escape(team.upper())} Team Alert Rules</h1>

    <p>
        Generated automatically from Prometheus rule files.<br/>
        Last update: {generated_time}<br/>
        Total alerts: {len(rows)}
    </p>

    <ac:structured-macro ac:name="expand">
      <ac:parameter ac:name="title">Alert Rules</ac:parameter>

      <ac:rich-text-body>

        <table>
          <tbody>

            <tr>
              <th>Datacenter</th>
              <th>Alert</th>
              <th>Team</th>
              <th>Severity</th>
              <th>Type</th>
              <th>Group</th>
              <th>File</th>
              <th>Expression</th>
            </tr>
    """

    for r in rows:
        html += f"""
            <tr>
              <td>{escape(str(r.get("datacenter", "")))}</td>
              <td>{escape(str(r.get("alert", "")))}</td>
              <td>{escape(str(r.get("team", "")))}</td>
              <td>{escape(str(r.get("severity", "")))}</td>
              <td>{escape(str(r.get("alert_type", "")))}</td>
              <td>{escape(str(r.get("group", "")))}</td>
              <td>{escape(str(r.get("file", "")))}</td>
              <td>
                <code>
                  {escape(str(r.get("expr", "")))}
                </code>
              </td>
            </tr>
        """

    html += """
          </tbody>
        </table>

      </ac:rich-text-body>
    </ac:structured-macro>
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
    Create/update Confluence page and optionally upload attachment
    """

    existing_page = confluence.get_page_by_title(
        space=space,
        title=title
    )

    if existing_page:
        page_id = existing_page["id"]

        print(f"[INFO] Updating existing page: {title}")

        confluence.update_page(
            page_id=page_id,
            title=title,
            body=html,
            representation="storage",
            full_width=True
        )

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


try:
    REPO_PATH = f"C:/Temp/{script_name}"  # local working copy of the git repo
    GITLAB_URL = "https://gitlab.abramad.com/abramad/sysops/prometheus.git"
    PROJECT = GITLAB_URL.split("/")[-1].split(".")[0]
    BRANCH = "sysops-automation"


    response = git_clone_or_pull(repo_url=GITLAB_URL, repo_path=REPO_PATH, branch=BRANCH)
    print(response)

    username = 'sysops-svc'
    password = decryptor('sysops-svc_enc', 'sysops-svc_key')


    rules_path = {
        "Miremad": f"C:/Temp/{script_name}/me-prometheus/config/prometheus_config/rules",
        "Vanak": f"C:/Temp/{script_name}/vnk-prometheus/prometheus_config/rules"
    }
    team_alerts = {}
    for datacenter, rule_dir in rules_path.items():
        for root, dirs, files in os.walk(rule_dir):
            for file in files:
                if file.endswith((".yml", ".yaml")):
                    file_path = os.path.join(root, file)

                    with open(file_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)

                        if not data:
                            continue

                        for group in data.get("groups", []):
                            group_name = group.get("name")

                            for rule in group.get("rules", []):

                                alert = rule.get("alert", "Recording_Rule")
                                expr = rule.get("expr")
                                team = rule.get("labels", {}).get("team", "no_name")
                                alert_type = rule.get("labels", {}).get("type")
                                severity = rule.get("labels", {}).get("severity")

                                if team not in team_alerts:
                                    team_alerts[team] = {}
                                if datacenter not in team_alerts[team]:
                                    team_alerts[team][datacenter] = []

                                team_alerts[team][datacenter].append( {
                                    "alert": alert,
                                    "expr": expr,
                                    "severity": severity,
                                    "type": alert_type,
                                    "team": team,
                                    "group": group_name,
                                    "file": file
                                })

    confluence = Confluence(
        url='https://confluence.abramad.com',
        username=username,
        password=password,
        verify_ssl=False
    )

    team_pages = {
        "caas": {
            "space": "ManSer",
            "title": "CaaS"
        },
        "ceph": {
            "space": "ManSer",
            "title": "Ceph"
        },
        "csb": {
            "space": "ManSer",
            "title": "CSB"
        },
        "kubernetes": {
            "space": "ManSer",
            "title": "K8S"
        },
        "mlp": {
            "space": "ManSer",
            "title": "MLP"
        },
        "iaas": {
            "space": "ManSer",
            "title": "Openstack"
        },
        "security": {
            "space": "ManSer",
            "title": "Security"
        },
        "support": {
            "space": "ManSer",
            "title": "Support"
        },
        "sysops": {
            "space": "ManSer",
            "title": "SysOps"
        },
    }


    for team, datacenter in team_alerts.items():
        print(f"{team}")
        rows = []
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        header = ["Datacenter", "Alert", "Team", "Severity", "Type", "Group", "File", "Expression"]
        worksheet.append(header)

        for datacenter_name, alert_list  in datacenter.items():
            print(f"\t{datacenter_name}")
            for alert_data in alert_list:
                print(f"\t\t{alert_data['alert']}")
                for key, value in alert_data.items():
                    print(f"\t\t\t{key}: {value}")

                rows.append({
                    "datacenter": datacenter_name,
                    "alert": alert_data["alert"],
                    "team": alert_data["team"],
                    "severity": alert_data["severity"],
                    "type": alert_data["type"],
                    "group": alert_data["group"],
                    "file": alert_data["file"],
                    "expr": alert_data["expr"]
                })

        html = generate_html(team, rows)


        for r in rows:
            worksheet.append([
                r["datacenter"],
                r["alert"],
                r["team"],
                r["severity"],
                r["type"],
                r["group"],
                r["file"],
                r["expr"]
            ])

        iran_tz = timezone(timedelta(hours=3, minutes=30))
        iran_date = datetime.now(iran_tz).strftime("%Y_%m_%d")

        excel_path = f"C:/Temp/{script_name}/reports/{team}_prometheus_rules_{iran_date}.xlsx"
        workbook.save(excel_path)
        print(f"\n{team} total alerts parsed: {len(rows)}")

        if team not in team_pages:
            print(f"Skipping unknown team: {team}")
            continue

        config = team_pages[team]

        publish_page(
            confluence=confluence,
            space=config["space"],
            title=config["title"],
            html=html,
            excel_file_path=excel_path
        )


except Exception as e:
    success = False
    error_string_summary += f"{type(e).__name__}: {e}"

    # Get the traceback and extract the last traceback frame
    tb = traceback.extract_tb(e.__traceback__)
    last_call = tb[-1]  # the last traceback frame, where the exception occurred
    error_string_detail += f"Error occurred in line {last_call.lineno}: {last_call.line}"
    print(f"Script failed: {error_string_summary}\n{error_string_detail}")


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
        grouping_key={'instance': instance, 'target': target, 'datacenter': push_datacenter },
        registry=registry
    )

    print('Metrics Sent.')

