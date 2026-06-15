#!/usr/bin/env python3

import json
import os
import sys
import subprocess
import time
from colorama import Fore, Style, init
from tabulate import tabulate

init(autoreset=True)

def run_command(command, capture_output=False, check=True, shell=False):
    try:
        result = subprocess.run(
            command,
            shell=shell,
            check=check,
            capture_output=capture_output,
            text=True,
        )
        return result.stdout if capture_output else None
    except subprocess.CalledProcessError as e:
        print(Fore.LIGHTRED_EX + f"❌ Command failed: {' '.join(e.cmd) if isinstance(e.cmd, list) else e.cmd}")
        print(e.output)
        sys.exit(1)


def init_restic_repo():
    print(Fore.LIGHTWHITE_EX + "Checking if restic repository exists...")
    try:
        run_command(["restic", "cat", "config"], capture_output=True)
        print(Fore.LIGHTGREEN_EX + "✅ Repository exists. Proceeding...")
    except:
        print(Fore.LIGHTYELLOW_EX + "Repository not found. Initializing...")
        run_command(["restic", "init"])
        print(Fore.LIGHTGREEN_EX + "✅ Repository initialized.")


def pgdump_backup_remote(remote_host_name, remote_host_ip):
    print(Fore.LIGHTWHITE_EX + "Starting remote PostgreSQL dump...")
    dump_path = f"{restic_dump_dir}/{remote_host_name}_pg_dump.sql"
    print(Fore.LIGHTWHITE_EX + f"Connecting to {remote_host_name} to dump...")

    def human_readable_size(size_bytes):
        if size_bytes >= 1024 ** 3:
            return f"{size_bytes / (1024 ** 3):.2f} GB"
        elif size_bytes >= 1024 ** 2:
            return f"{size_bytes / (1024 ** 2):.2f} MB"
        else:
            return f"{size_bytes / 1024:.2f} KB"

    with open(dump_path, "wb") as out_file:
        ssh_proc = subprocess.Popen(
            ["ssh", "-i", ssh_key, f"sysops@{remote_host_ip}", "pg_dumpall -U postgres -h localhost"],
            stdout=out_file
        )
        print(Fore.LIGHTWHITE_EX + f"Starting to dump at {dump_path}")
        while ssh_proc.poll() is None:
            try:
                size = os.path.getsize(dump_path)
                print(Fore.LIGHTWHITE_EX + f"Dumping... Current size: {human_readable_size(size)}")
                time.sleep(20)
            except FileNotFoundError:
                pass

        ssh_proc.wait()
        final_size = os.path.getsize(dump_path)
        print(Fore.LIGHTGREEN_EX + "✅ Dump completed.")
        print(Fore.CYAN + f"Size: {human_readable_size(final_size)}")


def pgdump_backup_remote_streamed(remote_host_name, remote_host_ip):
    print(Fore.LIGHTWHITE_EX + f"📡 Starting streamed backup from {remote_host_name}...")

    ssh_cmd = [
        "ssh", "-i", ssh_key,
        f"sysops@{remote_host_ip}",
        "pg_dumpall -U postgres -h localhost"
    ]

    # `pv` will show progress for the incoming data stream from pg_dumpall
    pv_cmd = ["pv", "--progress", "--rate", "--timer", "--bytes"]

    restic_cmd = [
        "restic", "backup", "--stdin",
        "--stdin-filename", f"{remote_host_name}_pg_dump.sql",
        "--host", remote_host_name
    ]

    # Start the pg_dump SSH process
    p1 = subprocess.Popen(ssh_cmd, stdout=subprocess.PIPE)

    # Pipe it through pv
    p2 = subprocess.Popen(pv_cmd, stdin=p1.stdout, stdout=subprocess.PIPE)

    # Pipe that into restic
    p3 = subprocess.Popen(restic_cmd, stdin=p2.stdout)

    # Properly close unused pipe ends
    p1.stdout.close()
    p2.stdout.close()

    # Wait for processes to complete
    p3_ret = p3.wait()
    if p3_ret != 0:
        print(Fore.LIGHTRED_EX + "❌ Restic failed to back up the stream.")
        sys.exit(1)
    print(Fore.LIGHTGREEN_EX + "✅ Streamed backup completed.")


def run_backup_streamed(remote_host_name, remote_host_ip):
    # 1) Stream the pg_dump directly into Restic
    pgdump_backup_remote_streamed(remote_host_name, remote_host_ip)

    # 2) Apply retention policy
    print(Fore.LIGHTWHITE_EX + "Applying retention policy…")
    run_command([
        "restic", "forget", "--prune",
        "--host", remote_host_name,
        "--keep-daily", backup_retention_days,
    ])
    print(Fore.LIGHTGREEN_EX + "✅ Retention policy applied!")

def run_backup(remote_host_name):
    # Step 1: Backup
    print(Fore.LIGHTWHITE_EX + "Backing up with restic...")
    dump_path = f"{restic_dump_dir}/{remote_host_name}_pg_dump.sql"
    run_command(["restic", "backup", "--host", remote_host_name, dump_path])
    print(Fore.LIGHTGREEN_EX + "✅ Backup completed successfully!")

    # Step 2: Apply retention policy
    print(Fore.LIGHTWHITE_EX + "Applying retention policy...")
    run_command([
        "restic", "forget", "--prune", "--host", remote_host_name,
        "--keep-daily", backup_retention_days,
    ])
    print(Fore.LIGHTGREEN_EX + "✅ Retention policy applied!")

def run_backup_dir(remote_host_name, remote_host_ip, remote_dir):
    """
    SSH into a remote host and back up a directory (and all its contents)
    directly into Restic using streaming over SSH.
    """
    print(Fore.LIGHTWHITE_EX + f"📁 Starting directory backup from {remote_host_name}:{remote_dir}...")

    # Step 1: tar the remote directory and stream it
    ssh_cmd = [
        "ssh", "-i", ssh_key,
        f"sysops@{remote_host_ip}",
        f"sudo tar -cf - -C {remote_dir} ."
    ]

    # Step 2: show progress with pv


    pv_cmd = ["pv", "--progress", "--rate", "--timer", "--bytes"]

    # Step 3: pipe tar output into Restic
    restic_cmd = [
        "restic", "backup", "--stdin",
        "--stdin-filename", f"{remote_host_name}_{remote_dir.strip('/').replace('/', '_')}.tar",
        "--host", remote_host_name
    ]

    # Start the remote tar command via SSH
    p1 = subprocess.Popen(ssh_cmd, stdout=subprocess.PIPE)

    # Pipe it through pv
    p2 = subprocess.Popen(pv_cmd, stdin=p1.stdout, stdout=subprocess.PIPE)

    # Pipe that into restic
    p3 = subprocess.Popen(restic_cmd, stdin=p2.stdout)

    # Close unused pipe ends
    p1.stdout.close()
    p2.stdout.close()

    # Wait for restic to finish
    p3_ret = p3.wait()
    if p3_ret != 0:
        print(Fore.LIGHTRED_EX + "❌ Restic failed to back up the remote directory.")
        sys.exit(1)

    print(Fore.LIGHTGREEN_EX + f"✅ Directory backup of {remote_dir} from {remote_host_name} completed successfully.")

    # Step 4: Apply retention policy
    print(Fore.LIGHTWHITE_EX + "Applying retention policy…")
    run_command([
        "restic", "forget", "--prune",
        "--host", remote_host_name,
        "--keep-daily", backup_retention_days,
    ])
    print(Fore.LIGHTGREEN_EX + "✅ Retention policy applied!")

def restore_backup(remote_host_name, snapshot_id="latest"):
    if snapshot_id == "":
        snapshot_id = "latest"

    elif len(snapshot_id) != 8:
        print(Fore.LIGHTRED_EX + "❌ Wrong snapshot ID, it must be 8 characters.\nTerminating program.")
        sys.exit(1)

    print(Fore.LIGHTWHITE_EX + f"Restoring with restic for {remote_host_name}...")
    os.makedirs(restic_restore_dir, exist_ok=True)
    run_command([
        "restic", "restore", f"{snapshot_id}", "--host", remote_host_name,
        "--verify", "--target", restic_restore_dir
    ])

    print(Fore.LIGHTGREEN_EX + f"✅ Backup restore completed successfully into: {restic_restore_dir}")

def list_backups(remote_host_name):
    print(Fore.LIGHTWHITE_EX + f"Listing backups of {remote_host_name}:")
    run_command(["restic", "snapshots"])
    print(Fore.LIGHTWHITE_EX + "\nSnapshot raw size:")
    run_command(["restic", "stats", "--mode", "raw-data"])
    print(Fore.LIGHTWHITE_EX + "\nSnapshot restore size:")
    run_command(["restic", "stats", "--mode", "restore-size"])

def cleanup(remote_host_name):
    print(Fore.LIGHTWHITE_EX + f"✅ Cleaning up {remote_host_name}'s dump...")
    dump_path = f"{restic_dump_dir}/{remote_host_name}_pg_dump.sql"
    if os.path.exists(dump_path):
        os.remove(dump_path)

def remove_snapshot(remote_host_name, snapshot_id):
    if not snapshot_id:
        snapshot_id = "latest"
    elif len(snapshot_id) < 8:
        print(Fore.LIGHTRED_EX + "❌ Snapshot ID too short. Must be at least 8 characters or use 'latest'.")
        sys.exit(1)

    print(Fore.LIGHTYELLOW_EX + f"⚠️ Removing snapshot `{snapshot_id}` for host `{remote_host_name}`...")
    run_command(["restic", "forget", "--prune", snapshot_id])
    print(Fore.LIGHTWHITE_EX + "✅ Snapshot removed and repository pruned.")

def remove_all_snapshots(remote_host_name):
    print(Fore.LIGHTWHITE_EX + f"📋 Listing all snapshots for host `{remote_host_name}`...")

    result = subprocess.run(["restic", "snapshots", "--json"], capture_output=True, text=True)
    snapshots = json.loads(result.stdout)

    snapshot_ids = [snap['short_id'] for snap in snapshots if snap['hostname'] == remote_host_name]

    if not snapshot_ids:
        print(Fore.LIGHTYELLOW_EX + "ℹ️ No snapshots found.")
        return

    print(Fore.LIGHTYELLOW_EX + f"⚠️ Removing {len(snapshot_ids)} snapshots...")
    for snap_id in snapshot_ids:
        run_command(["restic", "forget", snap_id])

    print(Fore.LIGHTYELLOW_EX + "🧹 Pruning unreferenced data...")
    run_command(["restic", "prune"])
    print(Fore.LIGHTWHITE_EX + "✅ All snapshots removed and repo pruned.")




# Main
if len(sys.argv) < 2:
    print(Fore.LIGHTRED_EX + "❌ Expecting at least one argument:" + Fore.LIGHTWHITE_EX + "[backup|restore|remove|list]")
    sys.exit(1)

action = sys.argv[1]
target = None

if len(sys.argv) >= 3:
    target = sys.argv[2] # postic list all --> target = all

# Global Variables
backup_retention_days = "5"
restic_restore_dir = "/opt/restic-restore"
#restic_temp_restore_dir = "/opt/s3-mount/restic-backup-restore/cache/temp-restore"
#restic_dump_dir = "/opt/s3-mount/restic-backup-restore/dump" # not used in pipe stdouting
ssh_key = "/home/sysops/.ssh/id_ed25519_pgbackup"
restic_client_file = "/opt/scripts/restic/restic_clients.txt"
os.environ["RESTIC_CACHE_DIR"] = "/opt/s3-mount/restic-backup-restore/cache" # "/var/cache/restic"

# Restic Clients Data Gathering From File
if not os.path.exists(restic_client_file):
    print(Fore.LIGHTRED_EX + f"❌ Input file {restic_client_file} not found.")
    sys.exit(1)

restic_clients = {}
with open(restic_client_file, "r", encoding="utf-8") as file:
    counter = 0
    lines = file.readlines()[1:]  # Skip the first line
    for line in lines:
        line = line.strip()
        if not line:
            continue  # Skip empty lines

        tmp_list = line.split(':')
        if len(tmp_list) < 6:
            print(Fore.LIGHTMAGENTA_EX + f"Skipping malformed line: {line}\nRegard the correct format: _Hostname_:_Host_IP_:_Restic_User_:_Restic_Password_:_Repo_Password_:_Backup_Type_:_Backup_Dir_")
            continue  # Skip lines with the wrong number of fields

        counter += 1
        if tmp_list[5] == 'psql':
            tmp_dict = {
                'id': counter,
                'host_name': tmp_list[0],
                'host_ip': tmp_list[1],
                'restic_user': tmp_list[2],
                'restic_pass': tmp_list[3],
                'repo_pass': tmp_list[4],
                'backup_type': tmp_list[5],
            }
            #              _Hostname_
            restic_clients[tmp_list[0]] = tmp_dict
        elif tmp_list[5] == 'dir':
            tmp_dict = {
                'id': counter,
                'host_name': tmp_list[0],
                'host_ip': tmp_list[1],
                'restic_user': tmp_list[2],
                'restic_pass': tmp_list[3],
                'repo_pass': tmp_list[4],
                'backup_type': tmp_list[5],
                'backup_dir': tmp_list[6],
            }
            #              _Hostname_
            restic_clients[tmp_list[0]] = tmp_dict


if action == "backup":
    if target == 'all':

        for hostname, hostdata in restic_clients.items():
            # --- Set environment variables ---
            os.environ["RESTIC_REPOSITORY"] = f"rest:http://{hostdata['restic_user']}:{hostdata['restic_pass']}@localhost:8010/{hostdata['restic_user']}"
            os.environ["RESTIC_PASSWORD"] = hostdata['repo_pass']

            # Backup Procedure
            if hostdata['backup_type'] == 'psql':
                print(Fore.LIGHTWHITE_EX + f"Starting backup from {hostdata['host_name']}:{hostdata['backup_type']}\n")
                init_restic_repo()
                run_backup_streamed(hostdata['host_name'], hostdata['host_ip'])
                print(Fore.LIGHTYELLOW_EX + (121 * '#') + '\n')
            elif hostdata['backup_type'] == 'dir':
                print(Fore.LIGHTWHITE_EX + f"Starting backup from {hostdata['host_name']}:{hostdata['backup_dir']}\n")
                init_restic_repo()
                run_backup_dir(hostdata['host_name'], hostdata['host_ip'], hostdata['backup_dir'])
                print(Fore.LIGHTYELLOW_EX + (121 * '#') + '\n')


    else:
        # Build the dynamic prompt for table data
        table_data = []
        for i, host in enumerate(restic_clients.values(), 1):
            hostname = Fore.LIGHTYELLOW_EX + host['host_name'] + Style.RESET_ALL
            # Color the backup type
            if host['backup_type'] == 'dir':
                backup_type = Fore.YELLOW + host['backup_type'] + Style.RESET_ALL
            else:  # psql
                backup_type = Fore.GREEN + host['backup_type'] + Style.RESET_ALL

            # Color and label the backup directory or file
            if host['backup_type'] == 'psql':
                backup_dir = Fore.MAGENTA + "PostgreSQL dump" + Style.RESET_ALL
            else:
                backup_dir = Fore.MAGENTA + host['backup_dir'] + Style.RESET_ALL

            table_data.append([i, hostname, backup_type, backup_dir])

        # Print the prompt with the table
        print(Fore.LIGHTWHITE_EX + "Select one host ID to backup:\n")
        print(tabulate(table_data, headers=["ID", "Hostname", "Backup Type", "Backup Dir/File"],tablefmt="rounded_outline"))
        user_input = input(Fore.LIGHTWHITE_EX + "\nEnter your choice: ")

        # Find the selected host
        selected_host = None
        for host_data in restic_clients.values():
            if host_data['id'] == int(user_input):
                selected_host = host_data
                break

        if selected_host:

            # --- Set environment variables ---
            os.environ["RESTIC_REPOSITORY"] = f"rest:http://{selected_host['restic_user']}:{selected_host['restic_pass']}@localhost:8010/{selected_host['restic_user']}"
            os.environ["RESTIC_PASSWORD"] = selected_host['repo_pass']

            # Backup Procedure
            if selected_host['backup_type'] == 'psql':
                print(Fore.LIGHTWHITE_EX + f"Starting backup from {selected_host['host_name']}:{selected_host['backup_type']}\n")
                init_restic_repo()
                run_backup_streamed(selected_host['host_name'], selected_host['host_ip'])
                print(Fore.LIGHTYELLOW_EX + (121 * '#') + '\n')
            elif selected_host['backup_type'] == 'dir':
                print(Fore.LIGHTWHITE_EX + f"Starting backup from {selected_host['host_name']}:{selected_host['backup_dir']}\n")
                init_restic_repo()
                run_backup_dir(selected_host['host_name'], selected_host['host_ip'], selected_host['backup_dir'])
                print(Fore.LIGHTYELLOW_EX + (121 * '#') + '\n')

        else:
            print(Fore.LIGHTRED_EX + f"❌ Invalid ID")
            sys.exit(1)



elif action == "restore":
    if target == 'all':

        for hostname, hostdata in restic_clients.items():
            # --- Set environment variables ---
            os.environ["RESTIC_REPOSITORY"] = f"rest:http://{hostdata['restic_user']}:{hostdata['restic_pass']}@localhost:8010/{hostdata['restic_user']}"
            os.environ["RESTIC_PASSWORD"] = hostdata['repo_pass']

            # Restore Procedure
            print(Fore.LIGHTWHITE_EX + "Starting restore...\n")
            restore_backup(hostdata['host_name'], "latest")
            print(Fore.LIGHTYELLOW_EX + (121 * '#') + '\n')

    else:
        # Build the dynamic prompt for table data
        table_data = []
        for i, host in enumerate(restic_clients.values(), 1):
            hostname = Fore.LIGHTYELLOW_EX + host['host_name'] + Style.RESET_ALL
            # Color the backup type
            if host['backup_type'] == 'dir':
                backup_type = Fore.YELLOW + host['backup_type'] + Style.RESET_ALL
            else:  # psql
                backup_type = Fore.GREEN + host['backup_type'] + Style.RESET_ALL

            # Color and label the backup directory or file
            if host['backup_type'] == 'psql':
                backup_dir = Fore.MAGENTA + "PostgreSQL dump" + Style.RESET_ALL
            else:
                backup_dir = Fore.MAGENTA + host['backup_dir'] + Style.RESET_ALL

            table_data.append([i, hostname, backup_type, backup_dir])

        # Print the prompt with the table
        print(Fore.LIGHTWHITE_EX + "Select one host ID to restore:\n")
        print(tabulate(table_data, headers=["ID", "Hostname", "Backup Type", "Backup Dir/File"],tablefmt="rounded_outline"))
        user_input = input(Fore.LIGHTWHITE_EX + "\nEnter your choice: ")

        # Find the selected host
        selected_host = None
        for host_data in restic_clients.values():
            if host_data['id'] == int(user_input):
                selected_host = host_data
                break

        if selected_host:

            # --- Set environment variables ---
            os.environ["RESTIC_REPOSITORY"] = f"rest:http://{selected_host['restic_user']}:{selected_host['restic_pass']}@localhost:8010/{selected_host['restic_user']}"
            os.environ["RESTIC_PASSWORD"] = selected_host['repo_pass']

            input_snapshot = (input(Fore.LIGHTWHITE_EX + 'Enter snapshot ID to restore:(latest) ')).strip()
            # Restore Procedure
            print(Fore.LIGHTWHITE_EX + "Starting restore...\n")
            restore_backup(selected_host['host_name'], input_snapshot)
            print(Fore.LIGHTYELLOW_EX + (121 * '#') + '\n')
        else:
            print(Fore.LIGHTRED_EX + f"❌ Invalid ID")
            sys.exit(1)



elif action == "list":
    if target == 'all':

        for hostname, hostdata in restic_clients.items():
            # --- Set environment variables ---
            os.environ["RESTIC_REPOSITORY"] = f"rest:http://{hostdata['restic_user']}:{hostdata['restic_pass']}@localhost:8010/{hostdata['restic_user']}"
            os.environ["RESTIC_PASSWORD"] = hostdata['repo_pass']

            # Listing Backups Procedure
            print(Fore.LIGHTWHITE_EX + "Listing...\n")
            list_backups(hostdata['host_name'])
            print(Fore.LIGHTYELLOW_EX + (121 * '#') + '\n')

    else:
        # Build the dynamic prompt for table data
        table_data = []
        for i, host in enumerate(restic_clients.values(), 1):
            hostname = Fore.LIGHTYELLOW_EX + host['host_name'] + Style.RESET_ALL
            # Color the backup type
            if host['backup_type'] == 'dir':
                backup_type = Fore.YELLOW + host['backup_type'] + Style.RESET_ALL
            else:  # psql
                backup_type = Fore.GREEN + host['backup_type'] + Style.RESET_ALL

            # Color and label the backup directory or file
            if host['backup_type'] == 'psql':
                backup_dir = Fore.MAGENTA + "PostgreSQL dump" + Style.RESET_ALL
            else:
                backup_dir = Fore.MAGENTA + host['backup_dir'] + Style.RESET_ALL

            table_data.append([i, hostname, backup_type, backup_dir])

        # Print the prompt with the table
        print(Fore.LIGHTWHITE_EX + "Select one host ID to list its backups:\n")
        print(tabulate(table_data, headers=["ID", "Hostname", "Backup Type", "Backup Dir/File"], tablefmt="rounded_outline"))
        user_input = input(Fore.LIGHTWHITE_EX + "\nEnter your choice: ")

        # Find the selected host
        selected_host = None
        for host_data in restic_clients.values():
            if host_data['id'] == int(user_input):
                selected_host = host_data
                break

        if selected_host:

            # --- Set environment variables ---
            os.environ["RESTIC_REPOSITORY"] = f"rest:http://{selected_host['restic_user']}:{selected_host['restic_pass']}@localhost:8010/{selected_host['restic_user']}"
            os.environ["RESTIC_PASSWORD"] = selected_host['repo_pass']

            # Listing Backups Procedure
            print(Fore.LIGHTWHITE_EX + "Listing...\n")
            list_backups(selected_host['host_name'])
            print(Fore.LIGHTYELLOW_EX + (121 * '#') + '\n')
        else:
            print(Fore.LIGHTRED_EX + f"❌ Invalid ID")
            sys.exit(1)

elif action == "remove":
    if target == 'all':

        for hostname, hostdata in restic_clients.items():
            # --- Set environment variables ---
            os.environ["RESTIC_REPOSITORY"] = f"rest:http://{hostdata['restic_user']}:{hostdata['restic_pass']}@localhost:8010/{hostdata['restic_user']}"
            os.environ["RESTIC_PASSWORD"] = hostdata['repo_pass']

            # Removing snapshots procedure
            print(Fore.LIGHTYELLOW_EX + "Removing snapshots...\n")
            remove_all_snapshots(hostdata['host_name'])
            print(Fore.LIGHTYELLOW_EX + (121 * '#') + '\n')

    else:
        # Build the dynamic prompt for table data
        table_data = []
        for i, host in enumerate(restic_clients.values(), 1):
            hostname = Fore.LIGHTYELLOW_EX + host['host_name'] + Style.RESET_ALL
            # Color the backup type
            if host['backup_type'] == 'dir':
                backup_type = Fore.YELLOW + host['backup_type'] + Style.RESET_ALL
            else:  # psql
                backup_type = Fore.GREEN + host['backup_type'] + Style.RESET_ALL

            # Color and label the backup directory or file
            if host['backup_type'] == 'psql':
                backup_dir = Fore.MAGENTA + "PostgreSQL dump" + Style.RESET_ALL
            else:
                backup_dir = Fore.MAGENTA + host['backup_dir'] + Style.RESET_ALL

            table_data.append([i, hostname, backup_type, backup_dir])

        # Print the prompt with the table
        print(Fore.LIGHTWHITE_EX + "Select one host ID to remove its snapshot:\n")
        print(tabulate(table_data, headers=["ID", "Hostname", "Backup Type", "Backup Dir/File"],tablefmt="rounded_outline"))
        user_input = input(Fore.LIGHTWHITE_EX + "\nEnter your choice: ")

        # Find the selected host
        selected_host = None
        for host_data in restic_clients.values():
            if host_data['id'] == int(user_input):
                selected_host = host_data
                break

        if selected_host:
            input_snapshot = (input(Fore.LIGHTWHITE_EX + 'Enter snapshot ID to remove[ID|latest|all]:(latest) ')).strip()

            # --- Set environment variables ---
            os.environ["RESTIC_REPOSITORY"] = f"rest:http://{selected_host['restic_user']}:{selected_host['restic_pass']}@localhost:8010/{selected_host['restic_user']}"
            os.environ["RESTIC_PASSWORD"] = selected_host['repo_pass']

            # Listing Backups Procedure
            print(Fore.LIGHTYELLOW_EX + "Removing snapshot...\n")
            if input_snapshot.lower() == "all":
                remove_all_snapshots(selected_host['host_name'])
            else:
                remove_snapshot(selected_host['host_name'], input_snapshot)
            print(Fore.LIGHTYELLOW_EX + (121 * '#') + '\n')
        else:
            print(Fore.LIGHTRED_EX + f"❌ Invalid ID")
            sys.exit(1)

else:
    print(Fore.LIGHTRED_EX + f"❌ Invalid argument: {action}")
    print(Fore.LIGHTWHITE_EX + "Usage: script.py [backup|restore|remove|list]")
    sys.exit(1)

