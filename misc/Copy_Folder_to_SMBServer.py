from smb.SMBConnection import SMBConnection
import os

def copy_folder_to_smb(server, share, remote_folder, local_folder, username, password):
    try:
        # Connect to the SMB server
        conn = SMBConnection(username, password, "local_machine", server, use_ntlm_v2=True, is_direct_tcp=True)
        assert conn.connect(server, 445)

        # Walk through the local folder and upload files
        for root, dirs, files in os.walk(local_folder):
            for dir_name in dirs:
                # Create directories on the remote share
                remote_path = os.path.join(remote_folder, os.path.relpath(os.path.join(root, dir_name), local_folder))
                remote_path = remote_path.replace("\\", "/")
                conn.createDirectory(share, remote_path)

            for file_name in files:
                local_file_path = os.path.join(root, file_name)
                remote_file_path = os.path.join(remote_folder, os.path.relpath(local_file_path, local_folder))
                remote_file_path = remote_file_path.replace("\\", "/")

                # Upload the file
                with open(local_file_path, "rb") as file_obj:
                    conn.storeFile(share, remote_file_path, file_obj)

        print("Folder copied successfully.")
        conn.close()

    except Exception as e:
        print(f"An error occurred: {e}")

# Parameters
server = "vra-pad.cloud.local"
share = "c$"
remote_folder = "Temp/zabbixagent"  # Remote destination path
local_folder = r"D:\OneDrive\Abramad\SysOps\Zabbix\Windows"  # Local folder path to copy
username = "cloud\\sina.z"
password = "S@Bw00fer20936744"

# Copy the folder
#copy_folder_to_smb(server, share, remote_folder, local_folder, username, password)

import logging
logging.basicConfig(level=logging.DEBUG)

conn = SMBConnection(username, password, "local_machine", "vra-pad.cloud.local", use_ntlm_v2=True)
conn.connect("vra-pad.cloud.local", 445)

