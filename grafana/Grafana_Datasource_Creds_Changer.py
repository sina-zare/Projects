import requests
import urllib3
from time import sleep

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
me_grafana_url = 'https://me-grafana.abramad.com'
vnk_grafana_url = 'https://vnk-grafana.abramad.com'

# Organizations with their specific tokens
me_grafana_org_creds = [
    {'id': 1, 'name': 'Main Org.', 'token': 'xyz', 'url': me_grafana_url},
]

vnk_grafana_org_creds = [
    {'id': 1, 'name': 'Main Org.', 'token': 'xyz', 'url': vnk_grafana_url},
]



def get_current_org(session, grafana_url):
    """Get the current organization context"""
    try:
        response = session.get(f"{grafana_url}/api/org")
        if response.status_code == 200:
            return response.json()
        print(f"    🔴 Failed to get current org: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"    🔴 Exception getting current org: {str(e)}")
    return None


def get_org_datasources(session, org_id, org_name, grafana_url):
    """Get data sources for a specific organization"""
    try:
        response = session.get(f"{grafana_url}/api/datasources")
        if response.status_code == 200:
            return response.json()
        print(f"    🔴 Failed to get datasources for org {org_name} (ID: {org_id}): {response.status_code} - {response.text}")
    except Exception as e:
        print(f"    🔴 Exception getting datasources: {str(e)}")
    return None


def update_datasource_creds(datasource, new_username, new_password):

    print(f"    🟢 Updating: {datasource['name']} (ID: {datasource['id']})")

    # Make a full copy of the original datasource
    payload = datasource.copy()

    # Update the username in jsonData
    if 'jsonData' in payload:
        payload['jsonData'] = payload['jsonData'].copy()  # Copy jsonData to avoid modifying original
        payload['jsonData']['username'] = new_username

    # Add secure password (creates new secureJsonData if it doesn't exist)
    payload['secureJsonData'] = {'password': new_password}

    # Remove read-only fields
    read_only_fields = ['id', 'orgId', 'typeLogoUrl', 'readOnly']
    for field in read_only_fields:
        payload.pop(field, None)

    return payload




grafana_org_creds = [me_grafana_org_creds, vnk_grafana_org_creds]


for goc in grafana_org_creds:
    print(f"{goc[0]['url'].split('/')[2]} --> Starting organization check for {len(goc)} organizations\n")

    for org in goc:
    
        # Check a single organization with its specific token
        # Create a new session for this organization
        session = requests.Session()
        session.headers.update({
            'Authorization': f'Bearer {org["token"]}',
            'Content-Type': 'application/json'
        })
        session.verify = False  # Only for testing with self-signed certs
    
        print(f"\nChecking organization: {org['name']} (ID: {org['id']})")
    
        # Verify we can access this org
        current_org = get_current_org(session, org['url'])
        if not current_org or current_org['id'] != org['id']:
            print(f"    🔴 Cannot access organization (might be invalid token or permissions)")
            continue
    
        # Get and display data sources
        datasources = get_org_datasources(session, org['id'], org['name'], org['url'])
    

        # Taking out zabbix data sources
        zabbix_datasources = []
        for ds in datasources:
            if ds['type'] == 'alexanderzobnin-zabbix-datasource':
                zabbix_datasources.append(ds)

        if not zabbix_datasources:
            print("    🔴 No Zabbix datasources found")

        new_username = 'grafana'
        new_password = 'O83Njs!je+z83mLQ'
        for ds in zabbix_datasources:

            updated_payload = update_datasource_creds(ds, new_username, new_password)
            # Send update request
            update_url = f"{org['url']}/api/datasources/{ds['id']}"
            update_response = session.put(update_url, json=updated_payload)

            if update_response.status_code == 200:
                print(f"    🟢 Successfully updated credentials\n")
            else:
                print(f"    🔴 Failed to update: {update_response.status_code} - {update_response.text}\n")


    
    
        print('-' * 60)
    
        sleep(0.5)  #  avoid rate limiting

print("\n\nCompleted checks for all organizations")

