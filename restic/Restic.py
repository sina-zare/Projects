#!/usr/bin/env python3

import json
import os
import sys
import subprocess
import time

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
        print(f"❌ Command failed: {' '.join(e.cmd) if isinstance(e.cmd, list) else e.cmd}")
        print(e.output)
        sys.exit(1)


def init_restic_repo():
    print("Checking if restic repository exists...")
    try:
        run_command(["restic", "cat", "config"], capture_output=True)
        print("✅ Repository exists. Proceeding...")
    except:
        print("Repository not found. Initializing...")
        run_command(["restic", "init"])
        print("✅ Repository initialized.")


def pgdump_backup_remote(remote_host_name, remote_host_ip):
    print("Starting remote PostgreSQL dump...")
    dump_path = f"{restic_dump_dir}/{remote_host_name}_pg_dump.sql"
    print(f"Connecting to {remote_host_name} to dump...")

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
        print(f"Starting to dump at {dump_path}")
        while ssh_proc.poll() is None:
            try:
                size = os.path.getsize(dump_path)
                print(f"Dumping... Current size: {human_readable_size(size)}")
                time.sleep(20)
            except FileNotFoundError:
                pass

        ssh_proc.wait()
        final_size = os.path.getsize(dump_path)
        print("✅ Dump completed.")
        print(f"Size: {human_readable_size(final_size)}")


def run_backup(remote_host_name):
    # Step 1: Backup
    print("Backing up with restic...")
    dump_path = f"{restic_dump_dir}/{remote_host_name}_pg_dump.sql"
    run_command(["restic", "backup", "--host", remote_host_name, dump_path])
    print("✅ Backup completed successfully!")

    # Step 2: Apply retention policy
    print("Applying retention policy...")
    run_command([
        "restic", "forget", "--prune", "--host", remote_host_name,
        "--keep-daily", "7",
    ])
    print("✅ Retention policy applied!")


def restore_backup(remote_host_name, snapshot_id="latest"):
    if snapshot_id == "":
        snapshot_id = "latest"

    elif len(snapshot_id) != 8:
        print("❌ Wrong snapshot ID, it must be 8 characters.\nTerminating program.")
        sys.exit(1)

    print(f"Restoring with restic for {remote_host_name}...")
    os.makedirs(restic_temp_restore_dir, exist_ok=True)
    run_command([
        "restic", "restore", f"{snapshot_id}", "--host", remote_host_name,
        "--verify", "--target", restic_temp_restore_dir
    ])

    # Moving .sql file to root of restore dir (kill tree)
    os.makedirs(restic_restore_dir, exist_ok=True)
    src_sql_path = f"{restic_temp_restore_dir}{restic_dump_dir}/{remote_host_name}_pg_dump.sql"
    dst_sql_path = f"{restic_restore_dir}/{remote_host_name}_pg_dump.sql"
    run_command(["mv", f"{src_sql_path}", f"{dst_sql_path}"])
    run_command(["rm", "-rf", f"{restic_temp_restore_dir}"])
    print(f"✅ Backup restore completed successfully into: {restic_restore_dir}")


def list_backups(remote_host_name):
    print(f"Listing backups of {remote_host_name}:")
    run_command(["restic", "snapshots"])
    print("\nSnapshot raw size:")
    run_command(["restic", "stats", "--mode", "raw-data"])
    print("\nSnapshot restore size:")
    run_command(["restic", "stats", "--mode", "restore-size"])

def cleanup(remote_host_name):
    print(f"✅ Cleaning up {remote_host_name}'s dump...")
    dump_path = f"{restic_dump_dir}/{remote_host_name}_pg_dump.sql"
    if os.path.exists(dump_path):
        os.remove(dump_path)


def remove_snapshot(remote_host_name, snapshot_id):
    if not snapshot_id:
        snapshot_id = "latest"
    elif len(snapshot_id) < 8:
        print("❌ Snapshot ID too short. Must be at least 8 characters or use 'latest'.")
        sys.exit(1)

    print(f"⚠️ Removing snapshot `{snapshot_id}` for host `{remote_host_name}`...")
    run_command(["restic", "forget", "--prune", snapshot_id])
    print("✅ Snapshot removed and repository pruned.")

'''
def remove_all_snapshot(remote_host_name):
    print(f"✅ Removing {remote_host_name}'s all snapshot")
    print(f"Omitting every snapshots but latest")
    run_command(["restic", "forget", "--keep-last", "1"])
    print(f"Omitting latest snapshot")
    run_command(["restic", "forget", "latest"])
    print("Pruning unreferenced snapshots.")
    run_command(["restic", "prune"])
'''

def remove_all_snapshots(remote_host_name):
    print(f"📋 Listing all snapshots for host `{remote_host_name}`...")

    result = subprocess.run(["restic", "snapshots", "--json"], capture_output=True, text=True)
    snapshots = json.loads(result.stdout)

    snapshot_ids = [snap['short_id'] for snap in snapshots if snap['hostname'] == remote_host_name]

    if not snapshot_ids:
        print("ℹ️ No snapshots found.")
        return

    print(f"⚠️ Removing {len(snapshot_ids)} snapshots...")
    for snap_id in snapshot_ids:
        run_command(["restic", "forget", snap_id])

    print("🧹 Pruning unreferenced data...")
    run_command(["restic", "prune"])
    print("✅ All snapshots removed and repo pruned.")




# Main
if len(sys.argv) < 2:
    print("❌ Expecting at least one argument: [backup|restore|remove|list]")
    sys.exit(1)

action = sys.argv[1]
target = None

if len(sys.argv) >= 3:
    target = sys.argv[2]

# Global Variables
restic_restore_dir = "/opt/restic-backup-restore/restore"
restic_temp_restore_dir = "/opt/restic-backup-restore/cache/temp-restore"
restic_dump_dir = "/opt/restic-backup-restore/dump"
ssh_key = "/home/sysops/.ssh/id_ed25519_pgbackup"
restic_client_file = "/opt/scripts/restic/restic_clients.txt"
os.environ["RESTIC_CACHE_DIR"] = "/opt/restic-backup-restore/cache" # "/var/cache/restic"

# Restic Clients Data Gathering From File
if not os.path.exists(restic_client_file):
    print(f"❌ Input file {restic_client_file} not found.")
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
        if len(tmp_list) != 5:
            print(f"Skipping malformed line: {line}")
            continue  # Skip lines with the wrong number of fields

        counter += 1
        tmp_dict = {
            'id': counter,
            'host_name': tmp_list[0],
            'host_ip': tmp_list[1],
            'restic_user': tmp_list[2],
            'restic_pass': tmp_list[3],
            'repo_pass': tmp_list[4],
        }

        restic_clients[tmp_list[0]] = tmp_dict

if action == "backup":
    if target == 'all':

        for hostname, hostdata in restic_clients.items():
            # --- Set environment variables ---
            os.environ["RESTIC_REPOSITORY"] = f"rest:http://{hostdata['restic_user']}:{hostdata['restic_pass']}@localhost:8010/{hostdata['restic_user']}"
            os.environ["RESTIC_PASSWORD"] = hostdata['repo_pass']

            # Backup Procedure
            print("Starting backup...\n")
            init_restic_repo()
            pgdump_backup_remote(hostdata['host_name'], hostdata['host_ip'])
            run_backup(hostdata['host_name'])
            cleanup(hostdata['host_name'])
            print((121 * '#') + '\n')

    else:
        # Build the dynamic prompt
        prompt_lines = ["Select one host ID to backup:"]
        for i, host in enumerate(restic_clients, 1):
            prompt_lines.append(f"{i}) {host}")
        prompt_lines.append("\nEnter your choice: ")

        # Join with newlines and pass to input()
        user_input = input('\n'.join(prompt_lines))

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
            print("Starting backup...\n")
            init_restic_repo()
            pgdump_backup_remote(selected_host['host_name'], selected_host['host_ip'])
            run_backup(selected_host['host_name'])
            cleanup(selected_host['host_name'])
            print((121 * '#') + '\n')

        else:
            print(f"❌ Invalid ID")
            sys.exit(1)



elif action == "restore":
    if target == 'all':

        for hostname, hostdata in restic_clients.items():
            # --- Set environment variables ---
            os.environ["RESTIC_REPOSITORY"] = f"rest:http://{hostdata['restic_user']}:{hostdata['restic_pass']}@localhost:8010/{hostdata['restic_user']}"
            os.environ["RESTIC_PASSWORD"] = hostdata['repo_pass']

            # Restore Procedure
            print("Starting restore...\n")
            restore_backup(hostdata['host_name'], "latest")
            print((121 * '#') + '\n')

    else:
        # Build the dynamic prompt
        prompt_lines = ["Select one host ID to restore its backup:"]
        for i, host in enumerate(restic_clients, 1):
            prompt_lines.append(f"{i}) {host}")
        prompt_lines.append("\nEnter your choice: ")

        # Join with newlines and pass to input()
        user_input = input('\n'.join(prompt_lines))

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

            input_snapshot = (input('Enter snapshot ID to restore:(latest) ')).strip()
            # Restore Procedure
            print("Starting restore...\n")
            restore_backup(selected_host['host_name'], input_snapshot)
            print((121 * '#') + '\n')
        else:
            print(f"❌ Invalid ID")
            sys.exit(1)



elif action == "list":
    if target == 'all':

        for hostname, hostdata in restic_clients.items():
            # --- Set environment variables ---
            os.environ["RESTIC_REPOSITORY"] = f"rest:http://{hostdata['restic_user']}:{hostdata['restic_pass']}@localhost:8010/{hostdata['restic_user']}"
            os.environ["RESTIC_PASSWORD"] = hostdata['repo_pass']

            # Listing Backups Procedure
            print("Listing...\n")
            list_backups(hostdata['host_name'])
            print((121 * '#') + '\n')

    else:
        # Build the dynamic prompt
        prompt_lines = ["Select one host ID to list its backups:"]
        for i, host in enumerate(restic_clients, 1):
            prompt_lines.append(f"{i}) {host}")
        prompt_lines.append("\nEnter your choice: ")

        # Join with newlines and pass to input()
        user_input = input('\n'.join(prompt_lines))

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
            print("Listing...\n")
            list_backups(selected_host['host_name'])
            print((121 * '#') + '\n')
        else:
            print(f"❌ Invalid ID")
            sys.exit(1)

elif action == "remove":
    if target == 'all':

        for hostname, hostdata in restic_clients.items():
            # --- Set environment variables ---
            os.environ["RESTIC_REPOSITORY"] = f"rest:http://{hostdata['restic_user']}:{hostdata['restic_pass']}@localhost:8010/{hostdata['restic_user']}"
            os.environ["RESTIC_PASSWORD"] = hostdata['repo_pass']

            # Removing snapshots procedure
            print("Removing snapshots...\n")
            remove_all_snapshots(hostdata['host_name'])
            print((121 * '#') + '\n')

    else:
        # Build the dynamic prompt
        prompt_lines = ["Select one host ID to remove its backups:"]
        for i, host in enumerate(restic_clients, 1):
            prompt_lines.append(f"{i}) {host}")
        prompt_lines.append("\nEnter your choice: ")

        # Join with newlines and pass to input()
        user_input = input('\n'.join(prompt_lines))

        # Find the selected host
        selected_host = None
        for host_data in restic_clients.values():
            if host_data['id'] == int(user_input):
                selected_host = host_data
                break

        if selected_host:
            input_snapshot = (input('Enter snapshot ID to remove[ID|latest|all]:(latest) ')).strip()

            # --- Set environment variables ---
            os.environ["RESTIC_REPOSITORY"] = f"rest:http://{selected_host['restic_user']}:{selected_host['restic_pass']}@localhost:8010/{selected_host['restic_user']}"
            os.environ["RESTIC_PASSWORD"] = selected_host['repo_pass']

            # Listing Backups Procedure
            print("Removing snapshot...\n")
            if input_snapshot.lower() == "all":
                remove_all_snapshots(selected_host['host_name'])
            else:
                remove_snapshot(selected_host['host_name'], input_snapshot)
            print((121 * '#') + '\n')
        else:
            print(f"❌ Invalid ID")
            sys.exit(1)

else:
    print(f"❌ Invalid argument: {action}")
    print("Usage: script.py [backup|restore|remove|list]")
    sys.exit(1)


