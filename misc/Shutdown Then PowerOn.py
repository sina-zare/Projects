from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim
import ssl
import time
import os
import csv
from datetime import datetime

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

task_start_time = time.time()

# Open the CSV file
with open('E:/PythonCSV/vm_name_list.csv', newline='') as csvfile:
    # Create a CSV reader
    reader = csv.reader(csvfile)
    # Initialize an empty list to store the rows
    vm_name = []
    # Loop through each row in the CSV file
    for row in reader:
        # Append the row to the list
        vm_name.append(row)

# Use a nested list comprehension to flatten the list and convert all elements to strings
flatten_vm_list = [str(item) for sublist in vm_name for item in sublist]
flag_initial = 0
shutdown_flag_final = 0
poweron_flag_final = 0

#count vms in csv
for j in flatten_vm_list:
    flag_initial += 1

# Create an SSL context with no certificate verification
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
context.verify_mode = ssl.CERT_NONE
# connect to vcenter to Shutdown and Power on servers
me_vc = connect.SmartConnect(host='me-vc01.abramad.com', user=username, pwd= password, port=443, sslContext=context)
me_content = me_vc.RetrieveContent()

for entity in me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True).view:
    for i in flatten_vm_list:
        if entity.name == i:
            entity.ShutdownGuest()
            now = datetime.now()
            print(f"shutdown task for {i} was sent in {now.strftime('%H:%M:%S')}")
            shutdown_flag_final += 1
            time.sleep(20)

if shutdown_flag_final == flag_initial:
    print("All VMs are now shut down.")

for entity in me_content.viewManager.CreateContainerView(me_content.rootFolder, [vim.VirtualMachine], True).view:
    for i in flatten_vm_list:
        if entity.name == i:
            entity.PowerOnVM_Task()
            now = datetime.now()
            print(f"poweron task for {i} was sent in {now.strftime('%H:%M:%S')}")
            time.sleep(5)
            #Wait for the task to complete
            while entity.PowerOnVM_Task().info.state == vim.TaskInfo.State.running:
                continue
            poweron_flag_final += 1



if poweron_flag_final == flag_initial:
    print("All VMs are now powered on.")

# Elapsed time calculation
task_end_time = time.time()
task_elapsed_time = task_end_time - task_start_time
print(f"\nThe proccess took {task_elapsed_time:.2f} seconds.")

Disconnect(me_vc)
