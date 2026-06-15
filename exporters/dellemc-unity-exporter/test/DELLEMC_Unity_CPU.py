import requests
from requests.auth import HTTPBasicAuth
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

UNITY_IP = "unity480.company.com"
username = "xyz"
password = "xyz"

url = (
    f"https://{UNITY_IP}/api/types/metricValue/instances"
    f'?filter=path EQ "sp.*.cpu.summary.utilization"&per_page=1'
)


headers = {
    "X-EMC-REST-CLIENT": "true",
    "Accept": "application/json"
}

r = requests.get(
    url,
    auth=HTTPBasicAuth(username, password),
    verify=False,
    headers=headers,
)

if r.status_code != 200:
    print("Error:", r.status_code)
    print(r.text)  # Optional: see what the server returned
    exit(1)

# Only parse JSON if status code is 200
#content_json = r.json()
#print(json.dumps(content_json, indent=4, sort_keys=True, ensure_ascii=False))

entries = r.json().get("entries", [])

if not entries:
    print("No metric entries returned.")
    exit(0)

latest = entries[0]["content"]
values = latest.get("values", {})

cpu_spa = values.get("spa")
cpu_spb = values.get("spb")

if cpu_spa is not None:
    print(f"CPU SPA: {float(cpu_spa):.2f}%")

if cpu_spb is not None:
    print(f"CPU SPB: {float(cpu_spb):.2f}%")
