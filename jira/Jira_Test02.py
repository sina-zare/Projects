import os
from jira import JIRA

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

# JIRA instance URL
jira_url = 'https://pmtest.abramad.com'

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
    'issuetype': {'name': 'Sarv-Customer-Ticket'},
    'summary': 'Ehsan',
    'customfield_11716': 'Subject',
    'customfield_11328': 'FarsiName',
    'description': 'Description',
    'customfield_11223': 'National_ID',
    'reporter': {'name': 'jira.portal'},
    'assignee': {'name': 'jira.portal'}

}
# 'customfield_11488': 'AllAbramadTeamMembers'
"""# Get the available transitions for the new issue
transitions = jira.transitions('SERVICDESK-2415')

# Print the available transitions to identify the correct transition ID
for transition in transitions:
    print(f"ID: {transition['id']}, Name: {transition['name']}")
"""



# Create the issue
new_issue = jira.create_issue(fields=issue_dict)
# Perform the transition to change the issue state to Resolved
jira.transition_issue(new_issue, '11')

print(f"Issue created: {new_issue.key}")

# Add a comment to the created issue
#comment = jira.add_comment(new_issue, 'This is a comment #1.')

#comment = jira.add_comment('SERVICDESK-2413', 'This is a comment #3.')
#print(f"Issue {new_issue.key} created and comment added.")
