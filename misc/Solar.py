import requests
import json
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

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Disable SSL certificate verification warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# SolarWinds server details
swis_server = 'me-sworion1.abramad.com'
swis_username = 'sina.z@abramad.com'
swis_password = password

# SolarWinds API endpoint
api_endpoint = f'https://{swis_server}/SolarWinds/InformationService/v3/Json/Query'

# SolarWinds query to retrieve alerts
query = '''
SELECT AlertDefID, AlertName, AlertMessage
FROM Orion.AlertActive
WHERE DateTime > GETUTCDATE() - 7
ORDER BY DateTime DESC
'''

# Create the request headers
headers = {
    'Content-Type': 'application/json',
}

# Create the request payload
payload = {
    'query': query
}

# Perform the API request
response = requests.post(api_endpoint, auth=(swis_username, swis_password), headers=headers, json=payload, verify=False)

# Check if the request was successful
if response.status_code == 200:
    try:
        data = response.json()

        # Extract the alerts from the response
        alerts = data.get('results', [])

        # Process the alerts
        for alert in alerts:
            alert_id = alert.get('AlertDefID')
            alert_name = alert.get('AlertName')
            alert_message = alert.get('AlertMessage')

            # Do something with the alert data
            print(f"Alert ID: {alert_id}")
            print(f"Alert Name: {alert_name}")
            print(f"Alert Message: {alert_message}")

    except requests.exceptions.JSONDecodeError as e:
        print(f"Failed to decode JSON response: {e}")
        print(f"Response Content: {response.content}")

else:
    print(f"Failed to retrieve alerts. Status code: {response.status_code}")
    print(f"Response Content: {response.content}")