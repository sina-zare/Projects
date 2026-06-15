import subprocess
import os

# Decryption function
def decrypt(cipher_text, key):
    plain_text = ""
    for i in range(len(cipher_text)):
        char = cipher_text[i]
        plain_int = ord(char) - key
        plain_text += chr(plain_int)
    return plain_text



# Credentials
cloud_username = decrypt(os.environ.get('sincloud'), 9999)
username = decrypt(os.environ.get('sin'), 9999)
password = decrypt(os.environ.get('spass'), 9999)
server_name = "mer-morvaridsh.cloud.local"
"""
# Define the PowerShell script for reading and modifying the file
ps_script = f'''
$user = "{cloud_username}" 
$pw = ConvertTo-SecureString "{password}" -AsPlainText -Force
$creds = New-Object System.Management.Automation.PSCredential ($user, $pw)
Invoke-Command -ComputerName "mer-morvaridsh.cloud.local" '''
ps_script += '-Credential $creds -ScriptBlock {'
ps_script += '''
$filePath = "C:\Temp\web.config"
$content = (Get-Content -Path $filePath)
$content
}
'''

# Execute the PowerShell script on the remote server
result = subprocess.run(["powershell.exe", "-Command", ps_script], stdout=subprocess.PIPE)

unprocessd = str(result.stdout.decode()).split("\n")
print(unprocessd)
"""