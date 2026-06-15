import os
from jira import JIRA

# JIRA instance URL
jira_url = 'https://jira.abramad.com'  # Replace with your Jira server URL

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

# JIRA credentials
jira_username = decryptor("enc_sinaz_abramad","key_sinaz_abramad")
jira_password = decryptor("enc_sinaz_pass","key_sinaz_pass")

# Connect to JIRA with SSL verification disabled
options = {
    'server': jira_url,
    'verify': False  # Disable SSL verification
}

# Create a JIRA client
jira = JIRA(options=options, basic_auth=(jira_username.split('@')[0], jira_password))

# Issue details
issue_dict = {
    'project': {'key': 'SERVICDESK'},
    'issuetype': {'name': 'Customer Incident'},
    'summary': 'Sarv Sina',
    'description': f'{10 * '~'}',
    'customfield_11223': '0058231341',
    'assignee': {'name': 'jira.portal'}
}

# Create the issue
new_issue = jira.create_issue(fields=issue_dict)

# Now update the reporter field separately
#jira.issue(new_issue.key).update(fields={'reporter': {'name': 'jira.portal'}})

print(f"Issue created: {new_issue.key}")


"""
'customfield_11717': 'this is Sarv Summary',
    'customfield_11716': 'my description',
    'customfield_11718': '0058231341',
"""