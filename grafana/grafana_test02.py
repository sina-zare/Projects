import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
GRAFANA_URL = 'https://me-grafana.abramad.com'
API_TOKEN = 'xyz'  # Replace with your actual API token


def get_current_org(session):
    """Get the current organization context"""
    try:
        response = session.get(f"{GRAFANA_URL}/api/org")
        if response.status_code == 200:
            return response.json()
        print(f"Failed to get current org: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception getting current org: {str(e)}")
    return None


def try_get_orgs(session):
    """Attempt to get organizations with graceful failure"""
    try:
        response = session.get(f"{GRAFANA_URL}/api/orgs")
        if response.status_code == 200:
            return response.json()
        print(f"Note: Cannot list all organizations (need orgs:read permission). Status: {response.status_code}")
    except Exception as e:
        print(f"Exception getting organizations: {str(e)}")
    return []


def get_org_datasources(session, org_id, org_name):
    """Get data sources for a specific organization"""
    try:
        response = session.get(f"{GRAFANA_URL}/api/datasources")
        if response.status_code == 200:
            return response.json()
        print(f"Failed to get datasources for org {org_name} (ID: {org_id}): {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception getting datasources: {str(e)}")
    return None


def main():
    # Create a session with API token
    session = requests.Session()
    session.headers.update({
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json'
    })
    session.verify = False  # Only for testing with self-signed certs

    # Get current org context
    current_org = get_current_org(session)
    if not current_org:
        print("Unable to determine current organization. Check API token permissions.")
        return

    print(f"\nCurrent org at start: {current_org['name']} (ID: {current_org['id']})\n")

    # Try to get all organizations (may fail due to permissions)
    orgs = try_get_orgs(session)

    # If we can't get orgs list, just work with the current org
    if not orgs:
        print("Will only check current organization since we can't list all orgs")
        orgs = [current_org]

    # Process each organization
    for org in orgs:
        org_id = org['id']
        org_name = org['name']

        # Skip if already in this org
        if org_id == current_org['id']:
            print(f"\nChecking current organization: {org_name} (ID: {org_id})")
        else:
            print(f"\nAttempting to switch to org: {org_name} (ID: {org_id})")

            # Switch organization context
            try:
                switch_response = session.post(f"{GRAFANA_URL}/api/user/using/{org_id}")
                if switch_response.status_code != 200:
                    print(f"  [!] Failed to switch: {switch_response.status_code} - {switch_response.text}")
                    continue
            except Exception as e:
                print(f"  [!] Exception during switch: {str(e)}")
                continue

            # Verify the switch worked
            current_org = get_current_org(session)
            if not current_org or current_org['id'] != org_id:
                print(f"  [!] Still in org {current_org['id'] if current_org else 'unknown'}")
                continue

            print(f"  Successfully switched to {org_name}")

        # Get and display data sources
        datasources = get_org_datasources(session, org_id, org_name)
        if datasources is not None:
            print(f"\n  Data sources in {org_name}:")
            if not datasources:
                print("    No data sources found")
            else:
                for ds in datasources:
                    print(f"    - {ds['name']} ({ds['type']})")
        print('-' * 60)

    # Switch back to original org at the end if we changed
    if current_org['id'] != orgs[0]['id']:
        session.post(f"{GRAFANA_URL}/api/user/using/{orgs[0]['id']}")


if __name__ == '__main__':
    main()