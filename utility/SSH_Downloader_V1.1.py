import paramiko
from scp import SCPClient
import os
import logging
import time
import socket
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_ssh_client(server, port, user, password, timeout=30):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password, timeout=timeout)
    return client


def find_remote_paths(ssh_client, remote_prefix, regex_pattern):
    # Use find to list all files in the directory
    remote_dir = os.path.dirname(remote_prefix)
    find_command = f"find {remote_dir} -type f"

    stdin, stdout, stderr = ssh_client.exec_command(find_command)
    paths = stdout.read().decode().splitlines()

    # Filter paths using the provided regex pattern
    matching_paths = [path for path in paths if re.search(regex_pattern, path)]
    return matching_paths


def download_files(ssh_client, remote_paths, local_base_path, batch_size=100, retries=3, timeout=30):
    with SCPClient(ssh_client.get_transport(), socket_timeout=timeout) as scp:
        for i in range(0, len(remote_paths), batch_size):
            batch = remote_paths[i:i+batch_size]
            for remote_path in batch:
                filename = os.path.basename(remote_path)
                local_path = os.path.join(local_base_path, filename)
                for attempt in range(retries):
                    try:
                        scp.get(remote_path, local_path, recursive=False)
                        logging.info(f"Successfully downloaded {remote_path} to {local_path}")
                        break
                    except (paramiko.SSHException, scp.SCPException, socket.timeout) as e:
                        logging.error(f"Error downloading {remote_path}: {e}")
                        if attempt < retries - 1:
                            logging.info(f"Retrying {remote_path} (attempt {attempt + 1}/{retries})...")
                            time.sleep(2 ** attempt)  # Exponential backoff
                        else:
                            logging.error(f"Failed to download {remote_path} after {retries} attempts")

server = '192.168.42.82'
port = 22
user = 'tohid.zare'
password = 'Tohid.zare@12345'
date = input("Enter Date in following format: --> /06/17: ")
phone_id = input("Enter Phone ID: ")
date_path = date.replace("/", "-")
print("\n\n")
regex_pattern = fr'out-[-.\d]+-{phone_id}-[-.\d]+\.wav'
remote_prefix = f'/var/spool/asterisk/monitor/2024/{date}/'
local_base_path = f'C:/Temp/Out/{date_path}-ID-{phone_id}'

ssh_client = create_ssh_client(server, port, user, password)
try:
    if not os.path.exists(local_base_path):
        os.makedirs(local_base_path)
    remote_paths = find_remote_paths(ssh_client, remote_prefix, regex_pattern)
    if not remote_paths:
        print(f"No files or directories found with prefix {remote_prefix}")
    else:
        download_files(ssh_client, remote_paths, local_base_path)
        print(f"Files with prefix {remote_prefix} downloaded successfully to {local_base_path}")
finally:
    ssh_client.close()
