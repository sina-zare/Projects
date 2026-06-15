import sys
import jdatetime
from datetime import datetime, timedelta, timezone
from pyzabbix import ZabbixAPI
from cryptography.fernet import Fernet
import re
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter
import traceback
import time
import os
from git import Repo, GitCommandError


# --- Configuration ---
script_name = 'zabbix_get_active_templates'
total_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-execs.txt'
total_failed_exec_counter_file = f'C://Temp//Script_Metrics//{script_name}-total-failed-execs.txt'
pushgateway_url = 'http://me-prometheus.abramad.com:9091'
job_name = 'python_scripts'
instance = script_name
datacenter = 'miremad_vanak'
target = 'zabbix_server_templates'

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

    # Connect to the Zabbix API
    zabbix_nodes = {
        # Vanak
        'vop-zabbix': ['vop-zabbix', "http://172.29.6.7"],
        'vvop-customerzabbix': ['vop-customerzabbix', "http://172.29.6.15"],

        # Miremad
        'me-zabbix': ['me-zabbix', "http://172.17.234.13/zabbix"],
        'me-customerzabbix': ['me-customerzabbix', "http://172.17.234.23"]
    }

    username = 'sysops-svc'
    password = decryptor('sysops-svc_enc', 'sysops-svc_key')

    for zabbix_node in zabbix_nodes:

        zabbix_node_name = zabbix_nodes[zabbix_node][0]
        zabbix_node_url = zabbix_nodes[zabbix_node][1]

        zapi = ZabbixAPI(zabbix_node_url)
        zapi.login(username, password)



        # Fetch all templates with linked hosts
        templates_with_hosts = zapi.template.get(
            selectHosts="extend",  # Get detailed host information
            output=["templateid", "name"]  # Only fetch template ID and name
        )


        # Find templates that have at least one host attached
        templates_with_at_least_one_host = [
            [template['name'], template['templateid']] for template in templates_with_hosts if template['hosts']
        ]

        #for i in templates_with_at_least_one_host:
        #    print(i)


        # Export templates with at least one host attached
        if templates_with_at_least_one_host:

            print('\n' + 40 * '#' + f'  {zabbix_node_name}  ' + 40 * '#' + '\n')

            for template in templates_with_at_least_one_host:

                template_name = template[0]
                template_id = template[1]

                try:
                    # Export template by ID
                    export_data = zapi.configuration.export(
                        format="json",  # Export format (xml or json)
                        options={
                            "templates": [template_id], # Specify templates to export
                            "hosts": []  # Include the hosts in the export
                        }
                    )

                    # Sanitize the template name to avoid issues with file names
                    safe_template_name = re.sub(r"[^\w\-\.]", "_", template_name)
                    file_name = f"{zabbix_node_name}_{safe_template_name}.json"

                    # Save the exported template to a separate file
                    output_dir = rf'C:\Gitlab\{zabbix_node_name}\templates'
                    os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists

                    with open(os.path.join(output_dir, file_name), "w", encoding="utf-8") as f:
                        f.write(export_data)
                    print(f"Exported template '{template_name}' to '{file_name}'")

                except Exception as e:
                    print(f"Error exporting template {template_name}: {e}")

                    success = False
                    error_string_summary += f" {type(e).__name__}: {e}"

                    # Get the traceback and extract the last traceback frame
                    tb = traceback.extract_tb(e.__traceback__)
                    last_call = tb[-1]  # the last traceback frame, where the exception occurred
                    error_string_detail += f" Error 'exporting template' occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"

            print(100 * '#' + '\n')
        else:
            print("No templates with at least one host attached found.")


        # Logout
        zapi.user.logout()


    '''
    # Gitlab Part
    def git_commit_and_push(repo_path, commit_message, git_url, local_branch="main", remote_branch="main"):
        global error_string_summary
        global error_string_detail
        global success
        try:
            # Ensure repo exists
            if not os.path.exists(repo_path):
                print(f"Initializing new repository at {repo_path}...")
                os.makedirs(repo_path, exist_ok=True)
                repo = Repo.init(repo_path)
                origin = repo.create_remote('origin', git_url)
            else:
                repo = Repo(repo_path)
                if 'origin' not in [r.name for r in repo.remotes]:
                    origin = repo.create_remote('origin', git_url)
                else:
                    origin = repo.remote(name='origin')

            # Disable SSL verification if needed
            repo.git.config("http.sslVerify", "false")

            # Ensure correct branch is checked out
            try:
                repo.git.checkout(local_branch)
            except Exception:
                print(f"Branch '{local_branch}' does not exist locally, creating it...")
                repo.git.checkout('-b', local_branch)

            # Stage ALL changes (tracked + untracked)
            repo.git.add(all=True)  # equivalent to `git add -A`

            # Commit if there are changes
            if repo.is_dirty(untracked_files=True):
                repo.index.commit(commit_message)
                print(f"Committed changes with message: {commit_message}")
            else:
                print("No changes to commit.")

            # Force push (overwrite remote with local repo state)
            origin.push(refspec=f"{local_branch}:{remote_branch}", force=True)
            print(f"Force pushed {local_branch} to remote {remote_branch}")

        except Exception as e:
            print(f"An error occurred: {e}")
            success = False
            error_string_summary += f" {type(e).__name__}: {e}"

            tb = traceback.extract_tb(e.__traceback__)
            last_call = tb[-1]
            error_string_detail += f" Error in {last_call.filename}, line {last_call.lineno}: {last_call.line}"

    '''



    def git_commit_and_push(repo_path, commit_message, git_url, local_branch="main", remote_branch="main"):
        global error_string_summary
        global error_string_detail
        global success

        try:
            # Ensure repo exists
            if not os.path.exists(repo_path):
                print(f"Initializing new repository at {repo_path}...")
                os.makedirs(repo_path, exist_ok=True)
                repo = Repo.init(repo_path)
                origin = repo.create_remote('origin', git_url)
            else:
                repo = Repo(repo_path)
                if 'origin' not in [r.name for r in repo.remotes]:
                    origin = repo.create_remote('origin', git_url)
                else:
                    origin = repo.remote(name='origin')

            # Disable SSL verification if needed
            repo.git.config("http.sslVerify", "false")

            # Ensure correct branch is checked out
            try:
                repo.git.checkout(local_branch)
            except Exception:
                print(f"Branch '{local_branch}' does not exist locally, creating it...")
                repo.git.checkout('-b', local_branch)

            # --- NEW STEP: Pull latest changes before committing/pushing ---
            try:
                print(f"Pulling latest changes from remote '{remote_branch}'...")
                origin.fetch()  # fetch remote updates
                repo.git.pull('origin', remote_branch, '--rebase')  # rebase to avoid merge commits
                print("Pull (rebase) completed successfully.")
            except GitCommandError as ge:
                print(f"Warning: Pull failed ({ge}). Continuing with local changes.")

            # Stage ALL changes (tracked + untracked)
            repo.git.add(all=True)

            # Commit if there are changes
            if repo.is_dirty(untracked_files=True):
                repo.index.commit(commit_message)
                print(f"Committed changes with message: {commit_message}")
            else:
                print("No changes to commit.")

            # Push (force optional)
            origin.push(refspec=f"{local_branch}:{remote_branch}", force=True)
            print(f"Force pushed {local_branch} to remote {remote_branch}")

        except Exception as e:
            print(f"An error occurred: {e}")
            success = False
            error_string_summary += f" {type(e).__name__}: {e}"

            tb = traceback.extract_tb(e.__traceback__)
            last_call = tb[-1]
            error_string_detail += f" Error in {last_call.filename}, line {last_call.lineno}: {last_call.line}"


    # Replace with your GitLab repository URL with access token
    # Use this format: https://<username>:<access-token>@gitlab.com/<namespace>/<repository>.git
    git_url = "https://project_18_bot_d2dc9c6efaac110db0a7e7e1fa3ce133:glpat-XqrFcA9rWY4rbgVreM9EEW86MQp1OjEyCA.01.0y0p14wd7@me-gitlab.abramad.com/operation/sysops/zabbix.git"

    # Path to your local repository
    repo_path = "C:\\Gitlab"

    # Get current time in UTC with timezone-aware object
    now_utc = datetime.now(timezone.utc)
    # Apply the +3:30 timezone offset
    time_with_offset = now_utc + timedelta(hours=3, minutes=30)
    # Convert to Jalali
    jalali_time = jdatetime.datetime.fromgregorian(datetime=time_with_offset)
    # Format to remove milliseconds
    formatted_jalali_time = jalali_time.strftime('%Y-%m-%d %H:%M:%S')


    # Commit message
    commit_message = f"uploaded new files at {formatted_jalali_time}"

    # Call the function
    git_commit_and_push(repo_path, commit_message, git_url, local_branch="main", remote_branch="main")


except Exception as err:
    print(f"Script failed: {err}")
    success = False
    error_string_summary += f" {type(err).__name__}: {err}"

    # Get the traceback and extract the last traceback frame
    tb = traceback.extract_tb(err.__traceback__)
    last_call = tb[-1]  # the last traceback frame, where the exception occurred
    error_string_detail += f" Error occurred in file {last_call.filename}, line {last_call.lineno}: {last_call.line}"



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
        grouping_key={'instance': instance, 'target': target, 'datacenter': datacenter},
        registry=registry
    )

    print('✅ Metrics Sent.')

