import time

from jira import JIRA
import os
from jira.resources import PropertyHolder

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
jira_username = 'support'
jira_password = decryptor('enc_jira_automation_user','key_jira_automation_user')

# Connect to JIRA with SSL verification disabled
options = {
    'server': jira_url,
    'verify': False  # Disable SSL verification
}


# Connect to Jira
jira = JIRA(options=options, basic_auth=(jira_username, jira_password))




for i in range(3276,17500):
    # Issue key to be updated
    issue_key = f'SERVICDESK-{str(i)}'

    issue = jira.issue(issue_key)

    sarv_ticket_no = ((issue.fields.__dict__['summary']).split('-'))[3][13:]

    update_payload1 = {

    "customfield_11726": f"test"

    }

    update_payload2 = {

        "customfield_11726": f"{sarv_ticket_no}"

    }

    # Update the issue
    try:
        issue = jira.issue(issue_key)
        issue.update(fields=update_payload1)
        time.sleep(1)
        issue.update(fields=update_payload2)
        print(f'Successfully updated {issue_key} to Archive-Customer-Ticket.')
        #time.sleep(2)
    except Exception as e:
        print(f'Failed to update {issue_key}: {str(e)}')
