from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import time
import os
import csv

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
username = decryptor("enc_sinaz_abramad","key_sinaz_abramad")
password = decryptor("enc_sinaz_pass","key_sinaz_pass")

# *** Connecting to vc.sgcloud.local to get the Report ***

# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE

sgc_vc = connect.SmartConnect(
    host='vc.sgcloud.local',
    user='sina.z@sgcloud.local',
    pwd= password,
    port=443,
    sslContext=context
)

print("Start connecting to 'vc.sgcloud.local' vCenter...")
# MRA Process Time Calculation
ram_increase_start_time = time.time()

sgc_content = sgc_vc.RetrieveContent()
print("Connected to 'vc.sgcloud.local successfully'")

sgc_vm_view = sgc_content.viewManager.CreateContainerView(sgc_content.rootFolder, [vim.VirtualMachine], True)
'''
sgc_vms = [vm for vm in sgc_vm_view.view if (vm.name.lower().startswith("VPS-") and not vm.name.lower().startswith(
        "VPS-AutoUpTest1") and not vm.name.lower().startswith("VPS-AutoUpTest2") and not vm.name.lower().startswith(
        "VPS-bkptest") and not vm.name.lower().startswith("VPS-Inferatest") and not vm.name.lower().startswith(
        "VPS-NSXTest1") and not vm.name.lower().startswith("VPS-NSXTest2") and not vm.name.lower().startswith(
        "VPS-SolarTest") and not vm.name.lower().startswith("VPS-AutoUpTest2") and not vm.name.lower().startswith(
        "VPS-BKPTSTDB") and not vm.name.lower().startswith("VPS-FanoosTst") and not vm.name.lower().startswith(
        "VPS-FanoosTst2") and not vm.name.lower().startswith("VPS-Penet") and not vm.name.lower().startswith("VPS-Penetration")) ]
'''

sgc_vms = [vm for vm in sgc_vm_view.view if (vm.name.lower().startswith("vps-fanoostst")) or (vm.name.lower().startswith("test-fanoos")) ]


# create directory(if doesn't exist) and raw log file
log_folder_path = 'C:/Users/sina.z/Desktop/'
if not os.path.exists(log_folder_path):
    os.makedirs(log_folder_path)
log_file_name =  f'RAM_Increase_Log.csv'
log_file_path = os.path.join(log_folder_path, log_file_name,)

# Open log CSV file in write mode
with open(log_file_path, mode='w', newline='') as file:
    # Create a CSV writer object
    writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    # Write the header row to the CSV file
    writer.writerow(['VM Name', 'VM ESXi Host', 'VM Compute CLuster', 'Former RAM Amount(GB)', 'Present RAM Amount(GB)', 'Increased RAM Amount(GB)', 'Cluster "HighPerf-6254" Total Increased RAM', 'Cluster "HighPerf-6154" Total Increased RAM', 'Errors'])

    # cl1: "HQ-HighPerformance-CascadeLake-6254",    cl2: "HQ-HighPerformance-SkyLake-6154"
    sum_of_cl1_required_ram = 0
    sum_of_cl2_required_ram = 0
    vms_under_8gb = []

    for vm in sgc_vms:
    #if vm is powered on
        if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
            vm_name = vm.name
            vm_host = vm.runtime.host.name
            vm_cluster = vm.runtime.host.parent.name
            #vm_cluster_total_memory_in_terabytes = (vm.runtime.host.parent.resourcePool.parent.summary.totalMemory)/(1024*1024*1024*1024)
            #vm_cluster_free_memory_in_terabytes = (vm.runtime.host.parent.resourcePool.parent.summary.effectiveMemory)/(1024*1024*1024*1024)
            vm_ram = int(vm.config.hardware.memoryMB / 1024)
            vm_required_ram = 0
            vm_error = ""

            # check if vm memory is less than 8 GB
            if (8 - vm_ram) > 0:
                vm_required_ram = 8 - vm_ram
                vms_under_8gb.append(vm_name)
                # find total required RAM to be increased per cluster
                if vm_cluster == "HQ-HighPerformance-CascadeLake-6254":
                    sum_of_cl1_required_ram += vm_required_ram
                elif vm_cluster == "HQ-HighPerformance-SkyLake-6154":
                    sum_of_cl2_required_ram += vm_required_ram
                try:
                    # Set the memory to 8GB
                    vm.ReconfigVM_Task(spec=vim.vm.ConfigSpec(memoryMB=8192))
                    print(f"Memory of {vm_name} increased successfully")
                    #time.sleep(120)

                except Exception as e:
                    # Handle the error
                    vm_error = e


        # create a row of data for each vm
        row = [vm_name, vm_host, vm_cluster, vm_ram, "",vm_required_ram, "", "", vm_error]
        # Write the data to the CSV file
        writer.writerow(row)

Disconnect(sgc_vc)



# connect to vcenter to fetch RAM amount after increase
sgc_vc_next_attempt = connect.SmartConnect(host='vc.sgcloud.local', user='sina.z@sgcloud.local', pwd= password, port=443, sslContext=context)
sgc_content_next_attempt = sgc_vc_next_attempt.RetrieveContent()


# save data in rows for later use
updated_rows = []

# Open the CSV file in read mode
with open(log_file_path, 'r') as csvfile:
    # Use the csv module to read the file
    reader = csv.reader(csvfile)


    for entity in sgc_content_next_attempt.viewManager.CreateContainerView(sgc_content_next_attempt.rootFolder, [vim.VirtualMachine], True).view:
        # Create a list to hold the updated rows

        for i in vms_under_8gb:
            if entity.name == i:
                vm_ram_next_attempt = int(entity.config.hardware.memoryMB / 1024)

                # Reset the file pointer to the beginning of the file
                csvfile.seek(0)
                # Loop through each row in the file
                for row in reader:
                    # Check if the first column matches vm name
                    if row[0] == entity.name:
                        # Update the 5th column with new RAM amount
                        row[4] = vm_ram_next_attempt
                        # Add the row (updated or not) to the list
                        updated_rows.append(row)

# Open the CSV file in write mode
with open(log_file_path, 'w', newline='') as csvfile:


    # Use the csv module to write the updated rows to the file
    writer = csv.writer(csvfile)
    # Write the header row to the CSV file
    writer.writerow(
        ['VM Name', 'VM ESXi Host', 'VM Compute CLuster', 'Former RAM Amount(GB)', 'Present RAM Amount(GB)',
         'Increased RAM Amount(GB)', 'Cluster "HighPerf-6254" Total Increased RAM',
         'Cluster "HighPerf-6154" Total Increased RAM', 'Errors'])
    writer.writerows(updated_rows)


# Open the CSV file for reading and writing cluster total increased memory
with open(log_file_path, 'r+', newline='') as file:
    reader = csv.reader(file)
    writer = csv.writer(file)
    # Read the existing data and write it back to the file
    rows = list(reader)
    if len(rows) >= 2:
        # write to 2nd row 6th column then 2nd row 7th column
        rows[1][6] = sum_of_cl1_required_ram
        rows[1][7] = sum_of_cl2_required_ram
        # move pointer to beginning of file
        file.seek(0)
        writer.writerows(rows)

Disconnect(sgc_vc_next_attempt)

# Elapsed time calculation
ram_increase_end_time = time.time()
ram_increase_elapsed_time = ram_increase_end_time - ram_increase_start_time
print(f"\nThe proccess took {ram_increase_elapsed_time:.2f} seconds.")