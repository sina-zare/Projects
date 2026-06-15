import os
import csv
from jira import JIRA
from cryptography.fernet import Fernet


def append_to_csv(file_path, data):
    with open(file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([data])

def decryptor(enc_env_var, key_env_var):

    # Load the key
    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = (os.environ.get(enc_env_var)).encode()
    # Decrypt Data
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())

    #print(f"Decryped Text: {decrypted_password}")
    return decrypted_password.decode()

# Gathering Data from CSV file.
issues_to_ticket = []
with open("C:\\Temp\\jira_ticket.csv", "r", encoding="utf-8") as file:
    csv_reader = csv.reader(file)
    # Skip the first line
    for _ in range(1):
        next(csv_reader)

    for row in csv_reader:
        source_ips = row[0]
        destination_ips = row[1]
        source_vms = row[2]
        destination_vms = row[3]
        description = row[4]

        issues_to_ticket.append([description, source_ips, destination_ips, source_vms, destination_vms])


# JIRA instance URL
jira_url = 'https://jira.abramad.com'  # Replace with your Jira server URL

# JIRA credentials
jira_username = "sina.z"
jira_password = decryptor("sina.z_enc","sina.z_key")

# Connect to JIRA with SSL verification disabled
options = {
    'server': jira_url,
    'verify': False  # Disable SSL verification
}

jira = JIRA(options=options, basic_auth=(jira_username, jira_password))

counter = 0
for issue in issues_to_ticket:
    counter += 1

    # Define the issue details
    issue_data = {
        'project': {'key': 'SERVICDESK'},  # Project Key
        'issuetype': {'name': 'Network Team Request'},  # Issue Type
        'summary': f'Network Access Needed for SysOps No {counter}',  # Summary of the issue
        'description': f'{issue[0]}',  # Description
        'customfield_11441': {'value': 'Network Access'},  # Network Team Internal Request
        'customfield_11262': f'{issue[1]}',  # Source IP
        'customfield_11336': f'{issue[2]}',  # Destination IP
        'customfield_11702': f'{issue[3]}',  # VM Name(Source)
        'customfield_11703': f'{issue[4]}',  # VM Name(Destination)
        'customfield_11613': {'name': 'SysOPSTeamMembers'},
    }

    # Create the issue
    new_issue = jira.create_issue(fields=issue_data)

    print(f"Issue created successfully: {new_issue.key}")

    # Save Ticket Numbers to follow
    append_to_csv("C:\\Temp\\Created_tickets.csv", new_issue.key)

