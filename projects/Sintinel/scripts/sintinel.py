#!/usr/bin/env python3

import json
import os
import sys
import subprocess
import logging
import time
from logging.handlers import RotatingFileHandler
from colorama import Fore, Style, init
from tabulate import tabulate
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway, Counter

init(autoreset=True)




# ---------- Configurable globals (load from environment) ----------

# --- PushGateway Configuration ---
script_name = 'sintinel'
pushgateway_url = os.getenv("PUSHGATEWAY_URL", "")  # e.g. "https://me-prometheus.abramad.com:9091"
job_name = os.getenv("PUSHGATEWAY_JOB", "docker_containers")
instance = os.getenv("PUSHGATEWAY_INSTANCE", script_name)
pushgw_target = os.getenv("PUSHGATEWAY_TARGET", "sintinel_clients")
pushgw_team_label = os.getenv("LABEL_TEAM", "sysops")

# Backup retention policy
backup_retention = os.getenv("BACKUP_RETENTION_POLICY", "")

# Directories inside container (defaults)
restic_restore_dir = "/opt/sintinel/restore"
restic_cache_dir = "/opt/sintinel/cache"

# Path to SSH user/key to use for remote ssh connections (inside container)
def_ssh_user = "root"
def_ssh_port = "22"
ssh_key_name = os.getenv("SSH_KEY_NAME", "id_ed25519")
ssh_key = f"/home/sintinel/.ssh/{ssh_key_name}"

# Postgres envs
def_postgresql_user = "postgres"
def_postgresql_port = "5432"

# Path to clients file (must be mounted into container)
restic_client_file = "/opt/scripts/sintinel_clients.txt"

# Restic REST server host/port (configured at runtime)
# - If RESTSERVER_HOST == "localhost" the container entrypoint starts a local rest-server.
# - Otherwise the script will connect to the remote server given by RESTSERVER_HOST:RESTSERVER_PORT.
rest_server_host = os.getenv("RESTSERVER_HOST", "")
rest_server_port = os.getenv("RESTSERVER_PORT", "8000")  # used in repo address

# Logging config
log_dir = "/var/log/sintinel"
log_file = os.path.join(log_dir, "sintinel.log")
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
max_log_megabytes = int(os.getenv("LOG_MAX_MEGABYTES", "10")) * 1024 * 1024  # 10MB default
log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", "3"))

# user output
host_restore_display = os.getenv("HOST_RESTORE_DIR", "")

# Set restic cache dir for restic binary
os.environ["RESTIC_CACHE_DIR"] = restic_cache_dir
# -----------------------------------------------------------------

# --- Metric Definition
registry = CollectorRegistry()

# Per-client metrics
backup_success = Gauge(
    'sintinel_backup_success',
    'Backup success status (1=success, 0=failure)',
    ['client','backup_type','backup_dir','team'],
    registry=registry
)
backup_duration = Gauge(
    'sintinel_backup_duration_seconds',
    'Backup duration in seconds',
    ['client','backup_type','backup_dir','team'],
    registry=registry
)


# Ensure log directory exists
os.makedirs(log_dir, exist_ok=True)


# ----- Logging setup -----
logger = logging.getLogger("sintinel")
logger.setLevel(getattr(logging, log_level, logging.INFO))

# Console handler (no colors here)
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)   # <-- IMPORTANT: prevents INFO from being printed by logger
ch_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
ch.setFormatter(ch_fmt)
logger.addHandler(ch)

# Rotating file handler (writes all logs to /var/log/sintinel/sintinel.log)
try:
    fh = RotatingFileHandler(
        log_file,
        maxBytes=max_log_megabytes,
        backupCount=log_backup_count,
        encoding="utf-8",
    )
    fh.setLevel(getattr(logging, log_level, logging.INFO))
    fh_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S")
    fh.setFormatter(fh_fmt)
    logger.addHandler(fh)
except Exception as e:
    print(Fore.LIGHTYELLOW_EX + f"⚠️  Could not create file handler for logging: {e}" + Style.RESET_ALL)


def cprint(level, color, msg, *args, **kwargs):
    text = msg % args if args else msg
    if level == 'info': # info is not printed to console by default
        print(color + text + Style.RESET_ALL)

    if level == "info":
        logger.info(color + text + Style.RESET_ALL)
    elif level == "warning":
        logger.warning(color + text + Style.RESET_ALL)
    elif level == "error":
        logger.error(color + text + Style.RESET_ALL)
    elif level == "debug":
        logger.debug(color + text + Style.RESET_ALL)

def sintinel_logo():
    sintinel_ascii = '''
  _________.__        __  .__              .__   
 /   _____/|__| _____/  |_|__| ____   ____ |  |  
 \_____  \ |  |/    \   __\  |/    \_/ __ \|  |  
 /        \|  |   |  \  | |  |   |  \  ___/|  |__
/_______  /|__|___|  /__| |__|___|  /\___  >____/
        \/         \/             \/     \/      
    '''

    print(Fore.LIGHTMAGENTA_EX + sintinel_ascii + Style.RESET_ALL)
    time.sleep(1.5)
    os.system('cls' if os.name == 'nt' else 'clear')


def build_retention_flags(policy_string):
    """
    Converts 'last:5,daily:7,weekly:4' into:
    ['--keep-last', '5', '--keep-daily', '7', '--keep-weekly', '4']
    """
    flags = []
    if not policy_string:
        msg = '''
Backup Retention Policy not set, defaulting to '--keep-last 5'

Retention Policy Env:
    BACKUP_RETENTION_POLICY="last:5,daily:7,weekly:4,monthly:1"
    → keep 5 last snapshots, 7 daily, 4 weekly, 1 monthly
        '''
        cprint("warning", Fore.LIGHTYELLOW_EX, msg)
        return ["--keep-last", "5"]  # Default fallback

    parts = [p.strip() for p in policy_string.split(",") if p.strip()]
    for part in parts:
        try:
            k, v = part.split(":")
            flags.extend([f"--keep-{k.strip()}", v.strip()])
        except ValueError:
            print(f"⚠️ Invalid retention policy part: {part}")
    return flags


# ----- Command runner -----
def run_command(command, capture_output=False, check=True, shell=False):
    logger.debug("run_command: %s (shell=%s)", command, shell)
    try:
        result = subprocess.run(
            command,
            shell=shell,
            check=check,
            capture_output=capture_output,
            text=True,
        )
        if capture_output:
            logger.debug("Command output: %s", result.stdout[:1000])
            return result.stdout
        return None
    except subprocess.CalledProcessError as e:
        # Log error context and outputs
        cmd_repr = " ".join(e.cmd) if isinstance(e.cmd, (list, tuple)) else str(e.cmd)
        logger.error("Command failed: %s", cmd_repr)
        if e.stdout:
            logger.error("Stdout: %s", e.stdout)
        if e.stderr:
            logger.error("Stderr: %s", e.stderr)
        cprint("error", Fore.LIGHTRED_EX, f"❌ Command failed: {cmd_repr}")
        # Exit with the same returncode
        sys.exit(e.returncode)


# ----- Core operations -----
def init_restic_repo():
    cprint("info", Fore.LIGHTWHITE_EX, "Checking if restic repository exists...")
    try:
        run_command(["restic", "cat", "config"], capture_output=True)
        cprint("info", Fore.LIGHTGREEN_EX, "✅ Repository exists. Proceeding...")
    except:
        cprint("warning", Fore.LIGHTYELLOW_EX, "Repository not found. Initializing...")
        run_command(["restic", "init"])
        cprint("info", Fore.LIGHTGREEN_EX, "✅ Repository initialized.")


def pgdump_backup_remote_streamed(remote_host_name, remote_host_ip, ssh_user, ssh_port, postgresql_user, postgresql_port):
    cprint("info", Fore.LIGHTWHITE_EX, f"📡 Starting streamed backup from {remote_host_name}...")

    if not ssh_user:
        ssh_user = def_ssh_user
    if not ssh_port:
        ssh_port = def_ssh_port
    if not postgresql_user:
        postgresql_user = def_postgresql_user
    if not postgresql_port:
        postgresql_port = def_postgresql_port

    ssh_cmd = [
        "ssh", "-i", ssh_key,
        "-o", "IdentitiesOnly=yes",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        f"-p {ssh_port}",
        f"{ssh_user}@{remote_host_ip}",
        f"pg_dumpall -U {postgresql_user} -h localhost -p {postgresql_port}"
    ]

    pv_cmd = ["pv", "--progress", "--rate", "--timer", "--bytes"]

    restic_cmd = [
        "restic", "backup", "--stdin",
        "--stdin-filename", f"{remote_host_name}_pg_dump.sql",
        "--host", remote_host_name
    ]

    logger.debug("SSH cmd: %s", ssh_cmd)
    p1 = subprocess.Popen(ssh_cmd, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(pv_cmd, stdin=p1.stdout, stdout=subprocess.PIPE)
    p3 = subprocess.Popen(restic_cmd, stdin=p2.stdout)
    p1.stdout.close()
    p2.stdout.close()
    p3_ret = p3.wait()
    if p3_ret != 0:
        cprint("error", Fore.LIGHTRED_EX, "❌ Restic failed to back up the stream.")
        raise SystemExit(1)
    cprint("info", Fore.LIGHTGREEN_EX, "✅ Streamed backup completed.")


def run_backup_streamed(remote_host_name, remote_host_ip, ssh_user, ssh_port, postgresql_user, postgresql_port):
    pgdump_backup_remote_streamed(remote_host_name, remote_host_ip, ssh_user, ssh_port, postgresql_user, postgresql_port)
    cprint("info", Fore.LIGHTWHITE_EX, f"Applying retention policy")
    retention_flags = build_retention_flags(backup_retention)
    run_command([
        "restic", "forget", "--prune",
        "--host", remote_host_name,
        *retention_flags
    ])
    cprint("info", Fore.LIGHTGREEN_EX, f"✅ Retention policy applied. {retention_flags}")


def run_backup_dir(remote_host_name, remote_host_ip, remote_dir, ssh_user, ssh_port):
    cprint("info", Fore.LIGHTWHITE_EX, f"📁 Starting directory backup from {remote_host_name}:{remote_dir}...")

    ssh_cmd = [
        "ssh", "-i", ssh_key,
        "-o", "IdentitiesOnly=yes",
        "-o", "StrictHostKeyChecking=no",  # optional: disable hostkey checking (see security note)
        "-o", "UserKnownHostsFile=/dev/null",  # optional: don't write to known_hosts
        f"-p {ssh_port}",
        f"{ssh_user}@{remote_host_ip}",
        f"sudo tar -cf - -C {remote_dir} ."
    ]

    pv_cmd = ["pv", "--progress", "--rate", "--timer", "--bytes"]

    restic_cmd = [
        "restic", "backup", "--stdin",
        "--stdin-filename", f"{remote_host_name}_{remote_dir.strip('/').replace('/', '_')}.tar",
        "--host", remote_host_name
    ]

    logger.debug("SSH tar cmd: %s", ssh_cmd)
    p1 = subprocess.Popen(ssh_cmd, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(pv_cmd, stdin=p1.stdout, stdout=subprocess.PIPE)
    p3 = subprocess.Popen(restic_cmd, stdin=p2.stdout)
    p1.stdout.close()
    p2.stdout.close()
    p3_ret = p3.wait()
    if p3_ret != 0:
        cprint("error", Fore.LIGHTRED_EX, "❌ Restic failed to back up the remote directory.")
        raise SystemExit(1)

    cprint("info", Fore.LIGHTGREEN_EX, f"✅ Directory backup of {remote_dir} from {remote_host_name} completed successfully.")
    cprint("info", Fore.LIGHTWHITE_EX, "Applying retention policy…")
    retention_flags = build_retention_flags(backup_retention)
    run_command([
        "restic", "forget", "--prune",
        "--host", remote_host_name,
        *retention_flags
    ])
    cprint("info", Fore.LIGHTGREEN_EX, f"✅ Retention policy applied. {retention_flags}")


def restore_backup(remote_host_name, snapshot_id="latest"):
    if snapshot_id == "":
        snapshot_id = "latest"
    elif snapshot_id != "latest" and len(snapshot_id) != 8:
        cprint("error", Fore.LIGHTRED_EX, "❌ Wrong snapshot ID, it must be 8 characters.\nTerminating program.")
        raise SystemExit(1)

    cprint("info", Fore.LIGHTWHITE_EX, f"Restoring with restic for {remote_host_name}...")
    os.makedirs(restic_restore_dir, exist_ok=True)
    run_command([
        "restic", "restore", f"{snapshot_id}", "--host", remote_host_name,
        "--verify", "--target", restic_restore_dir
    ])
    if host_restore_display:
        cprint("info", Fore.LIGHTGREEN_EX,f"✅ Backup restore completed into: {restic_restore_dir} (host: {host_restore_display})")
    else:
        cprint("info", Fore.LIGHTGREEN_EX, f"✅ Backup restore completed into: {restic_restore_dir}")


def list_backups(remote_host_name):
    cprint("info", Fore.LIGHTWHITE_EX, f"Listing backups of {remote_host_name}:")
    run_command(["restic", "snapshots"])
    cprint("info", Fore.LIGHTWHITE_EX, "\nSnapshot raw size:")
    run_command(["restic", "stats", "--mode", "raw-data"])
    cprint("info", Fore.LIGHTWHITE_EX, "\nSnapshot restore size:")
    run_command(["restic", "stats", "--mode", "restore-size"])


def remove_snapshot(remote_host_name, snapshot_id):
    if not snapshot_id:
        snapshot_id = "latest"
    elif snapshot_id != "latest" and len(snapshot_id) < 8:
        cprint("error", Fore.LIGHTRED_EX, "❌ Snapshot ID too short. Must be at least 8 characters or use 'latest'.")
        raise SystemExit(1)

    cprint("warning", Fore.LIGHTYELLOW_EX, f"⚠️ Removing snapshot `{snapshot_id}` for host `{remote_host_name}`...")
    run_command(["restic", "forget", "--prune", snapshot_id])
    cprint("info", Fore.LIGHTWHITE_EX, "✅ Snapshot removed and repository pruned.")


def remove_all_snapshots(remote_host_name):
    cprint("info", Fore.LIGHTWHITE_EX, f"📋 Listing all snapshots for host `{remote_host_name}`...")
    result = subprocess.run(["restic", "snapshots", "--json"], capture_output=True, text=True)
    snapshots = json.loads(result.stdout)
    snapshot_ids = [snap['short_id'] for snap in snapshots if snap.get('hostname') == remote_host_name]
    if not snapshot_ids:
        cprint("warning", Fore.LIGHTYELLOW_EX, "ℹ️ No snapshots found.")
        return
    cprint("warning", Fore.LIGHTYELLOW_EX, f"⚠️ Removing {len(snapshot_ids)} snapshots...")
    for snap_id in snapshot_ids:
        run_command(["restic", "forget", snap_id])
    cprint("warning", Fore.LIGHTYELLOW_EX, "🧹 Pruning unreferenced data...")
    run_command(["restic", "prune"])
    cprint("info", Fore.LIGHTWHITE_EX, "✅ All snapshots removed and repo pruned.")




# ########################### #
# ----- Main Application -----
# ########################### #

sintinel_logo()

if len(sys.argv) < 2:
    cprint("error", Fore.LIGHTRED_EX, "❌ Expecting at least one argument:" + Fore.LIGHTWHITE_EX + "[backup|restore|remove|list]")
    raise SystemExit(1)

action = sys.argv[1]
target = None

if len(sys.argv) >= 3:
    target = sys.argv[2]


# Restic Clients Data Gathering From File
if not os.path.exists(restic_client_file):
    cprint("error", Fore.LIGHTRED_EX, f"❌ Input file {restic_client_file} not found.")
    raise SystemExit(1)

restic_clients = {}
with open(restic_client_file, "r", encoding="utf-8") as file:
    sintinel_clients = []
    counter = 0
    lines = file.readlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue # Skip empty/comment lines if present
        tmp_list = line.split(':')
        if len(tmp_list) < 9:
            cprint("warning", Fore.LIGHTMAGENTA_EX, f"Skipping malformed line: {line}\nRegard the correct format of sintinel_clients.txt:\n PSQL --> Hostname:SSH_User:Host_IP:SSH_Port:Restic_User:Restic_Password:Repo_Password:Backup_Type:Postgres_Port:Postgres_User\nExample  my-db:my-user:192.0.2.10:22:restic-user:RESTIC_USER_PASSWORD:REPO_PASSWORD:psql:5432:postgres\n\nDIR  --> Hostname:SSH_User:Host_IP:SSH_Port:Restic_User:Restic_Password:Repo_Password:Backup_Type:Backup_Dir\nExample  my-fileserver:my-user:192.0.2.11:22:restic-user:RESTIC_USER_PASSWORD:REPO_PASSWORD:dir:/var/www")
            continue
        counter += 1
        if tmp_list[7] == 'psql':
            tmp_dict = {
                'id': counter,
                'host_name': tmp_list[0],
                'ssh_user': tmp_list[1],
                'host_ip': tmp_list[2],
                'ssh_port': tmp_list[3],
                'restic_user': tmp_list[4],
                'restic_pass': tmp_list[5],
                'repo_pass': tmp_list[6],
                'backup_type': tmp_list[7],
                'postgres_port': tmp_list[8],
                'postgres_user': tmp_list[9],
            }
            restic_clients[tmp_list[0]] = tmp_dict
        elif tmp_list[7] == 'dir':
            tmp_dict = {
                'id': counter,
                'host_name': tmp_list[0],
                'ssh_user': tmp_list[1],
                'host_ip': tmp_list[2],
                'ssh_port': tmp_list[3],
                'restic_user': tmp_list[4],
                'restic_pass': tmp_list[5],
                'repo_pass': tmp_list[6],
                'backup_type': tmp_list[7],
                'backup_dir': tmp_list[8],
            }
            restic_clients[tmp_list[0]] = tmp_dict

        sintinel_clients.append(tmp_list[0]) # gathering hostnames



# Action handling
if action == "backup": # we set metric values here
    if target == 'all':
        for hostname, hostdata in restic_clients.items():
            # handling metrics
            start_time = time.time()
            success = False

            try:
                restic_repo = f"rest:http://{hostdata['restic_user']}:{hostdata['restic_pass']}@{rest_server_host}:{rest_server_port}/{hostdata['restic_user']}"
                os.environ["RESTIC_REPOSITORY"] = restic_repo
                os.environ["RESTIC_PASSWORD"] = hostdata['repo_pass']

                if hostdata['backup_type'] == 'psql':
                    backup_success.labels(client=hostdata['host_name'], backup_type=hostdata['backup_type'], backup_dir='PostgreSQL dump',team=pushgw_team_label).set(0)
                    backup_duration.labels(client=hostdata['host_name'], backup_type=hostdata['backup_type'], backup_dir='PostgreSQL dump',team=pushgw_team_label).set(0.0)

                    cprint("info", Fore.LIGHTWHITE_EX, f"Starting backup from {hostdata['host_name']}:{hostdata['backup_type']}\n")
                    init_restic_repo()
                    run_backup_streamed(hostdata['host_name'], hostdata['host_ip'], hostdata['ssh_user'], hostdata['ssh_port'], hostdata['postgres_user'], hostdata['postgres_port'])
                    cprint("info", Fore.LIGHTYELLOW_EX, (121 * '#') + '\n')

                elif hostdata['backup_type'] == 'dir':
                    backup_success.labels(client=hostdata['host_name'], backup_type=hostdata['backup_type'], backup_dir=hostdata['backup_dir'],team=pushgw_team_label).set(0)
                    backup_duration.labels(client=hostdata['host_name'], backup_type=hostdata['backup_type'], backup_dir=hostdata['backup_dir'],team=pushgw_team_label).set(0.0)

                    cprint("info", Fore.LIGHTWHITE_EX, f"Starting backup from {hostdata['host_name']}:{hostdata['backup_dir']}\n")
                    init_restic_repo()
                    run_backup_dir(hostdata['host_name'], hostdata['host_ip'], hostdata['backup_dir'], hostdata['ssh_user'], hostdata['ssh_port'])
                    cprint("info", Fore.LIGHTYELLOW_EX, (121 * '#') + '\n')

                success = True

            except Exception as exc:
                # capture failure and log
                success = False
                cprint("error", Fore.LIGHTRED_EX, f"Backup failed for {hostdata['host_name']}: {exc}")

            finally:
                duration = time.time() - start_time
                if hostdata['backup_type'] == 'psql':
                    backup_success.labels(client=hostdata['host_name'],backup_type=hostdata['backup_type'],backup_dir='PostgreSQL dump',team=pushgw_team_label).set(1 if success else 0)
                    backup_duration.labels(client=hostdata['host_name'],backup_type=hostdata['backup_type'],backup_dir='PostgreSQL dump',team=pushgw_team_label).set(duration)
                elif hostdata['backup_type'] == 'dir':
                    backup_success.labels(client=hostdata['host_name'], backup_type=hostdata['backup_type'], backup_dir=hostdata['backup_dir'],team=pushgw_team_label).set(1 if success else 0)
                    backup_duration.labels(client=hostdata['host_name'], backup_type=hostdata['backup_type'], backup_dir=hostdata['backup_dir'],team=pushgw_team_label).set(duration)
        try:
            # Push metrics to Pushgateway
            if pushgateway_url:
                push_to_gateway(
                    gateway=pushgateway_url,
                    job=job_name,
                    grouping_key={'instance': instance, 'target': pushgw_target},
                    registry=registry
                )
                cprint("info", Fore.LIGHTWHITE_EX, f"Metrics pushed to {pushgateway_url}")
                cprint("info", Fore.LIGHTYELLOW_EX, (121 * '#') + '\n')
            else:
                cprint("warning", Fore.LIGHTYELLOW_EX,f"No pushgateway env provided in .env to push metrics (PUSHGATEWAY_URL='{pushgateway_url}')")
                cprint("info", Fore.LIGHTYELLOW_EX, (121 * '#') + '\n')

        except Exception as err:
            cprint("error", Fore.LIGHTRED_EX,
                   f"Error sending metrics to {pushgateway_url} - {err}")

    else:
        # interactive single host selection
        table_data = []
        for i, host in enumerate(restic_clients.values(), 1):
            hostname = Fore.LIGHTYELLOW_EX + host['host_name'] + Style.RESET_ALL
            backup_type = Fore.YELLOW + host['backup_type'] + Style.RESET_ALL if host['backup_type']=='dir' else Fore.GREEN + host['backup_type'] + Style.RESET_ALL
            backup_dir = Fore.MAGENTA + ("PostgreSQL dump" if host['backup_type']=='psql' else host['backup_dir']) + Style.RESET_ALL
            table_data.append([i, hostname, backup_type, backup_dir])

        cprint("info", Fore.LIGHTWHITE_EX, "Select one host ID to backup:\n")
        print(tabulate(table_data, headers=["ID", "Hostname", "Backup Type", "Backup Dir/File"], tablefmt="rounded_outline"))
        user_input = input(Fore.LIGHTWHITE_EX + "\nEnter your choice: ")
        try:
            sel_id = int(user_input)
        except ValueError:
            cprint("error", Fore.LIGHTRED_EX, "❌ Invalid ID")
            raise SystemExit(1)

        selected_host = None
        for host_data in restic_clients.values():
            if host_data['id'] == sel_id:
                selected_host = host_data
                break

        if selected_host:
            # handling metrics
            start_time = time.time()
            success = False

            try:
                restic_repo = f"rest:http://{selected_host['restic_user']}:{selected_host['restic_pass']}@{rest_server_host}:{rest_server_port}/{selected_host['restic_user']}"
                os.environ["RESTIC_REPOSITORY"] = restic_repo
                os.environ["RESTIC_PASSWORD"] = selected_host['repo_pass']

                if selected_host['backup_type'] == 'psql':
                    backup_success.labels(client=selected_host['host_name'], backup_type=selected_host['backup_type'], backup_dir='PostgreSQL dump',team=pushgw_team_label).set(0)
                    backup_duration.labels(client=selected_host['host_name'], backup_type=selected_host['backup_type'], backup_dir='PostgreSQL dump',team=pushgw_team_label).set(0.0)

                    cprint("info", Fore.LIGHTWHITE_EX, f"Starting backup from {selected_host['host_name']}:{selected_host['backup_type']}\n")
                    init_restic_repo()
                    run_backup_streamed(selected_host['host_name'], selected_host['host_ip'], selected_host['ssh_user'], selected_host['ssh_port'], selected_host['postgres_user'], selected_host['postgres_port'])

                elif selected_host['backup_type'] == 'dir':
                    backup_success.labels(client=selected_host['host_name'], backup_type=selected_host['backup_type'], backup_dir=selected_host['backup_dir'],team=pushgw_team_label).set(0)
                    backup_duration.labels(client=selected_host['host_name'], backup_type=selected_host['backup_type'], backup_dir=selected_host['backup_dir'],team=pushgw_team_label).set(0.0)

                    cprint("info", Fore.LIGHTWHITE_EX, f"Starting backup from {selected_host['host_name']}:{selected_host['backup_dir']}\n")
                    init_restic_repo()
                    run_backup_dir(selected_host['host_name'], selected_host['host_ip'], selected_host['backup_dir'], selected_host['ssh_user'], selected_host['ssh_port'])

                success = True

            except Exception as exc:
                # capture failure and log
                success = False
                cprint("error", Fore.LIGHTRED_EX, f"Backup failed for {selected_host['host_name']}: {exc}")

            finally:
                duration = time.time() - start_time
                if selected_host['backup_type'] == 'psql':
                    backup_success.labels(client=selected_host['host_name'],backup_type=selected_host['backup_type'],backup_dir='PostgreSQL dump',team=pushgw_team_label).set(1 if success else 0)
                    backup_duration.labels(client=selected_host['host_name'],backup_type=selected_host['backup_type'],backup_dir='PostgreSQL dump',team=pushgw_team_label).set(duration)
                elif selected_host['backup_type'] == 'dir':
                    backup_success.labels(client=selected_host['host_name'], backup_type=selected_host['backup_type'], backup_dir=selected_host['backup_dir'],team=pushgw_team_label).set(1 if success else 0)
                    backup_duration.labels(client=selected_host['host_name'], backup_type=selected_host['backup_type'], backup_dir=selected_host['backup_dir'],team=pushgw_team_label).set(duration)



                try:
                    # Push metrics to Pushgateway
                    if pushgateway_url:
                        push_to_gateway(
                            gateway=pushgateway_url,
                            job=job_name,
                            grouping_key={'instance': instance, 'target': pushgw_target},
                            registry=registry
                        )
                        cprint("info", Fore.LIGHTWHITE_EX, f"metrics pushed to {pushgateway_url}")
                        cprint("info", Fore.LIGHTYELLOW_EX, (121 * '#') + '\n')
                    else:
                        cprint("warning", Fore.LIGHTYELLOW_EX, f"no pushgateway env provided in .env to push metrics (PUSHGATEWAY_URL='{pushgateway_url}')")
                        cprint("info", Fore.LIGHTYELLOW_EX, (121 * '#') + '\n')

                except Exception as err:
                    cprint("error", Fore.LIGHTRED_EX,
                           f"Error sending metrics to {pushgateway_url} - {err}")

        else:
            cprint("error", Fore.LIGHTRED_EX, "❌ Invalid ID")
            raise SystemExit(1)


elif action == "restore":
    if target == 'all':
        for hostname, hostdata in restic_clients.items():
            restic_repo = f"rest:http://{hostdata['restic_user']}:{hostdata['restic_pass']}@{rest_server_host}:{rest_server_port}/{hostdata['restic_user']}"
            os.environ["RESTIC_REPOSITORY"] = restic_repo
            os.environ["RESTIC_PASSWORD"] = hostdata.get('repo_pass', '')
            cprint("info", Fore.LIGHTWHITE_EX, "Starting restore...\n")
            restore_backup(hostdata['host_name'], "latest")
            cprint("info", Fore.LIGHTYELLOW_EX, (121 * '#') + '\n')
    else:
        table_data = []
        for i, host in enumerate(restic_clients.values(), 1):
            hostname = Fore.LIGHTYELLOW_EX + host['host_name'] + Style.RESET_ALL
            backup_type = Fore.YELLOW + host['backup_type'] + Style.RESET_ALL if host['backup_type']=='dir' else Fore.GREEN + host['backup_type'] + Style.RESET_ALL
            backup_dir = Fore.MAGENTA + ("PostgreSQL dump" if host['backup_type']=='psql' else host['backup_dir']) + Style.RESET_ALL
            table_data.append([i, hostname, backup_type, backup_dir])
        cprint("info", Fore.LIGHTWHITE_EX, "Select one host ID to restore:\n")
        print(tabulate(table_data, headers=["ID", "Hostname", "Backup Type", "Backup Dir/File"], tablefmt="rounded_outline"))
        user_input = input(Fore.LIGHTWHITE_EX + "\nEnter your choice: ")
        try:
            sel_id = int(user_input)
        except ValueError:
            cprint("error", Fore.LIGHTRED_EX, "❌ Invalid ID")
            raise SystemExit(1)
        selected_host = None
        for host_data in restic_clients.values():
            if host_data['id'] == sel_id:
                selected_host = host_data
                break
        if selected_host:
            restic_repo = f"rest:http://{selected_host['restic_user']}:{selected_host['restic_pass']}@{rest_server_host}:{rest_server_port}/{selected_host['restic_user']}"
            os.environ["RESTIC_REPOSITORY"] = restic_repo
            os.environ["RESTIC_PASSWORD"] = selected_host.get('repo_pass', '')
            input_snapshot = (input(Fore.LIGHTWHITE_EX + 'Enter snapshot ID to restore:(latest) ')).strip()
            cprint("info", Fore.LIGHTWHITE_EX, "Starting restore...\n")
            restore_backup(selected_host['host_name'], input_snapshot)
            cprint("info", Fore.LIGHTYELLOW_EX, (121 * '#') + '\n')
        else:
            cprint("error", Fore.LIGHTRED_EX, "❌ Invalid ID")
            raise SystemExit(1)


elif action == "list":
    if target == 'all':
        for hostname, hostdata in restic_clients.items():
            restic_repo = f"rest:http://{hostdata['restic_user']}:{hostdata['restic_pass']}@{rest_server_host}:{rest_server_port}/{hostdata['restic_user']}"
            os.environ["RESTIC_REPOSITORY"] = restic_repo
            os.environ["RESTIC_PASSWORD"] = hostdata.get('repo_pass', '')
            cprint("info", Fore.LIGHTWHITE_EX, "Listing...\n")
            list_backups(hostdata['host_name'])
            cprint("info", Fore.LIGHTYELLOW_EX, (121 * '#') + '\n')
    else:
        table_data = []
        for i, host in enumerate(restic_clients.values(), 1):
            hostname = Fore.LIGHTYELLOW_EX + host['host_name'] + Style.RESET_ALL
            backup_type = Fore.YELLOW + host['backup_type'] + Style.RESET_ALL if host['backup_type']=='dir' else Fore.GREEN + host['backup_type'] + Style.RESET_ALL
            backup_dir = Fore.MAGENTA + ("PostgreSQL dump" if host['backup_type']=='psql' else host['backup_dir']) + Style.RESET_ALL
            table_data.append([i, hostname, backup_type, backup_dir])
        cprint("info", Fore.LIGHTWHITE_EX, "Select one host ID to list its backups:\n")
        print(tabulate(table_data, headers=["ID", "Hostname", "Backup Type", "Backup Dir/File"], tablefmt="rounded_outline"))
        user_input = input(Fore.LIGHTWHITE_EX + "\nEnter your choice: ")
        try:
            sel_id = int(user_input)
        except ValueError:
            cprint("error", Fore.LIGHTRED_EX, "❌ Invalid ID")
            raise SystemExit(1)
        selected_host = None
        for host_data in restic_clients.values():
            if host_data['id'] == sel_id:
                selected_host = host_data
                break
        if selected_host:
            restic_repo = f"rest:http://{selected_host['restic_user']}:{selected_host['restic_pass']}@{rest_server_host}:{rest_server_port}/{selected_host['restic_user']}"
            os.environ["RESTIC_REPOSITORY"] = restic_repo
            os.environ["RESTIC_PASSWORD"] = selected_host.get('repo_pass', '')
            cprint("info", Fore.LIGHTWHITE_EX, "Listing...\n")
            list_backups(selected_host['host_name'])
            cprint("info", Fore.LIGHTYELLOW_EX, (121 * '#') + '\n')
        else:
            cprint("error", Fore.LIGHTRED_EX, "❌ Invalid ID")
            raise SystemExit(1)


elif action == "remove":
    if target == 'all':
        for hostname, hostdata in restic_clients.items():
            restic_repo = f"rest:http://{hostdata['restic_user']}:{hostdata['restic_pass']}@{rest_server_host}:{rest_server_port}/{hostdata['restic_user']}"
            os.environ["RESTIC_REPOSITORY"] = restic_repo
            os.environ["RESTIC_PASSWORD"] = hostdata.get('repo_pass', '')
            cprint("warning", Fore.LIGHTYELLOW_EX, "Removing snapshots...\n")
            remove_all_snapshots(hostdata['host_name'])
            cprint("info", Fore.LIGHTYELLOW_EX, (121 * '#') + '\n')
    else:
        table_data = []
        for i, host in enumerate(restic_clients.values(), 1):
            hostname = Fore.LIGHTYELLOW_EX + host['host_name'] + Style.RESET_ALL
            backup_type = Fore.YELLOW + host['backup_type'] + Style.RESET_ALL if host['backup_type']=='dir' else Fore.GREEN + host['backup_type'] + Style.RESET_ALL
            backup_dir = Fore.MAGENTA + ("PostgreSQL dump" if host['backup_type']=='psql' else host['backup_dir']) + Style.RESET_ALL
            table_data.append([i, hostname, backup_type, backup_dir])
        cprint("info", Fore.LIGHTWHITE_EX, "Select one host ID to remove its snapshot:\n")
        print(tabulate(table_data, headers=["ID", "Hostname", "Backup Type", "Backup Dir/File"], tablefmt="rounded_outline"))
        user_input = input(Fore.LIGHTWHITE_EX + "\nEnter your choice: ")
        try:
            sel_id = int(user_input)
        except ValueError:
            cprint("error", Fore.LIGHTRED_EX, "❌ Invalid ID")
            raise SystemExit(1)
        selected_host = None
        for host_data in restic_clients.values():
            if host_data['id'] == sel_id:
                selected_host = host_data
                break
        if selected_host:
            input_snapshot = (input(Fore.LIGHTWHITE_EX + 'Enter snapshot ID to remove[ID|latest|all]:(latest) ')).strip()
            restic_repo = f"rest:http://{selected_host['restic_user']}:{selected_host['restic_pass']}@{rest_server_host}:{rest_server_port}/{selected_host['restic_user']}"
            os.environ["RESTIC_REPOSITORY"] = restic_repo
            os.environ["RESTIC_PASSWORD"] = selected_host.get('repo_pass', '')
            cprint("warning", Fore.LIGHTYELLOW_EX, "Removing snapshot...\n")
            if input_snapshot.lower() == "all":
                remove_all_snapshots(selected_host['host_name'])
            else:
                remove_snapshot(selected_host['host_name'], input_snapshot)
            cprint("info", Fore.LIGHTYELLOW_EX, (121 * '#') + '\n')
        else:
            cprint("error", Fore.LIGHTRED_EX, "❌ Invalid ID")
            raise SystemExit(1)
else:
    cprint("error", Fore.LIGHTRED_EX, f"❌ Invalid argument: {action}")
    cprint("info", Fore.LIGHTWHITE_EX, "Usage: sintinel [backup|restore|remove|list]")
    raise SystemExit(1)
