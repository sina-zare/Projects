'''
# https://requests.readthedocs.io/en/master/
import requests

# credentials
username = "abramad_41307"
password = "EMGTOmKSNELnpFKD"

domain = "domain"

# call
contents = requests.get("https://sms.magfa.com/api/http/sms/v1?service=getcredit&username=" + username + "&password=" + password + "&domain=""")
print(contents.text)

import requests

url = "https://sms.magfa.com/api/http/sms/v1?service=getcredit"

payload = {}
headers = {
  'Authorization': 'Basic YWJyYW1hZF80MTMwNzpFTUdUT21LU05FTG5wRktE'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)

import requests

url = "https://sms.magfa.com/api/http/sms/v1?service=enqueue"

payload = {'username': 'abramad_41307',
'password': 'EMGTOmKSNELnpFKD',
'from': '300041307',
'to': '09379690139',
'text': 'سلام'}
files=[

]
headers = {
  'Authorization': 'Basic YWJyYW1hZF80MTMwNzpFTUdUT21LU05FTG5wRktE'
}

response = requests.request("GET", url, headers=headers, data=payload, files=files)

print(response.text)



import requests

url = "https://sms.magfa.com/api/http/sms/v2/send"
headers = {'accept': "application/json", 'cache-control': "no-cache"}

# credentials
username = "abramad_41307"
password = "EMGTOmKSNELnpFKD"
domain = ""


# or json data
payload = {'senders': '300041307', 'messages':'سلام', 'recipients':['09379690139', '09118762732']}
# call json
response = requests.post(url, headers=headers, auth=(username + '/' + domain, password), json=payload)
print(response.json())


import requests

url = "https://sms.magfa.com/api/http/sms/v2/send"

payload = {'senders': '300041307', 'messages':'سلام', 'recipients':'09379690139'}
headers = {
  'Authorization': 'Basic YWJyYW1hZF80MTMwNzpFTUdUT21LU05FTG5wRktE'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
'''

import requests
import json
import base64

# ByLKAUIpMNBEP5OH

url = "https://sms.magfa.com/api/http/sms/v2/send"

payload = {
    'senders': ['300041307'],
    'messages': ['Text'],
    'recipients': ['09379690139', '09129056738']
}

# bAW64("USERNAME:PASSWORD") -> base64("magfausername/magfadomain:password")
magfa_username = "abramad_41307"
magfa_domain = "abramad"
magfa_password = "ByLKAUIpMNBEP5OH"
magfa_auth = base64.b64encode(f"{magfa_username}/{magfa_domain}:{magfa_password}".encode("ascii")).decode("ascii")

headers = {
  'Authorization': f"Basic {magfa_auth}",
  'Content-Type': 'application/json'
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
#print(magfa_auth)
print(response.text)

