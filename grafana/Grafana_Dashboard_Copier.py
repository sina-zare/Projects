import requests
import urllib3
urllib3.disable_warnings()

# Each organization has its own:
## datasource
## service account
## folders
## dashboards

mep_sregrafana_organizations = [
    {'id': 1, 'name': 'Main Org.', 'token': 'xyz'},
]

vop_grafana_organizations = [
    {'id': 1, 'name': 'Main Org.', 'token': 'xyz'},
]


## Datasource UID to be replaced in destination dashboards.
## you can get it from datasource url in grafana.
destination_ds_uid = 'fe8h5wm7rp8u8e'

# Source Grafana instance configuration
## a service account with read access suffices for source.
source_url = "https://grafana.abramad.com"
source_api_key = "xyz"

# Destination Grafana instance configuration
## you need to create a service account with admin access to create dashboards.
destination_url = "https://vnk-grafana.abramad.com"
destination_api_key = "xyz"

# Headers for API requests
source_headers = {
    "Authorization": f"Bearer {source_api_key}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

destination_headers = {
    "Authorization": f"Bearer {destination_api_key}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}




# Get all folders from the source Grafana instance
source_folders_url = f"{source_url}/api/folders"
source_folders_response = requests.get(source_folders_url, headers=source_headers, verify=False)
print("Get Folders Response:", source_folders_response.json())
print("    ------------------           ")
source_folders = source_folders_response.json()

# Create folders in the destination Grafana instance
for folder in source_folders:
    destination_folders_url = f"{destination_url}/api/folders"
    folder_data = {
        "uid": folder["uid"],
        "title": folder["title"],
    }
    print("folder_data: ", folder_data)
    folder_create_response = requests.post(destination_folders_url, headers=destination_headers, json=folder_data,
                                           verify=False)
    print("folder_create_response: ", folder_create_response)

# Get all dashboards from the source Grafana instance
source_dashboards_url = f"{source_url}/api/search?type=dash-db"
source_dashboards_response = requests.get(source_dashboards_url, headers=source_headers, verify=False)
source_dashboards = source_dashboards_response.json()
print("Dashboards:", len(source_dashboards))


## replace datasource uid for all prometheus datasources
## changeit if you need other datasources replaced.
def replace_uid(data, new_uid):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "datasource" and isinstance(value, dict) and "type" in value and value['type'] == "prometheus":
                data[key]["uid"] = new_uid
            else:
                replace_uid(value, new_uid)
    elif isinstance(data, list):
        for item in data:
            replace_uid(item, new_uid)


# Create dashboards in the destination Grafana instance
for dashboard in source_dashboards:
    destination_dashboards_url = f"{destination_url}/api/dashboards/db"
    dash = \
    requests.get(f"{source_url}/api/dashboards/uid/{dashboard['uid']}", headers=source_headers, verify=False).json()[
        'dashboard']
    print("Dashboard: ", dashboard)
    dash['id'] = None

    replace_uid(dash, destination_ds_uid)
    if "folderUid" in dashboard:
        dashboard_data = {
            "dashboard": dash,
            "folderUid": dashboard["folderUid"],
            "overwrite": True,
            "message": "by python migration"
        }
    else:
        dashboard_data = {
            "dashboard": dash,
            "overwrite": True,
            "message": "by python migration"
        }
    dash_create_response = requests.post(destination_dashboards_url, headers=destination_headers, json=dashboard_data,
                                         verify=False)
    print("Dashboard create response: ", dash_create_response)
    if dash_create_response.status_code != 200: exit()

print("Dashboards and folders have been migrated.")

