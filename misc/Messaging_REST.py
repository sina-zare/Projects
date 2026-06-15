import requests
import json

# Set the service URL and endpoint
service_url = "https://messaging.abramad.com/webapi"
endpoint = "/api/services/app/PublicApi/CreateBatchSend"

# Define the full URL
url = f"{service_url}{endpoint}"

# Set the headers, including the access token
headers = {
    "X-Application-AccessToken": "afd6dd1a84d949e8a9a3a543c66a25c3",
    "Content-Type": "application/x-www-form-urlencoded"
}

# Define the request payload (JSON body)
data = {
    "onBehalfOfApplicationName": "CustomersPortal",
    "smsChannelName": "Magfa",
    "emailChannelName": "CustomersPortal",
    "scheduleSendTime": None,  # ISO 8601 format
    "expireMessagesAfterHours": 12,
    "messages": [
        {
            "smsBody": "Test SMS Body",
            "emailCaption": "Test Email Caption",
            "emailBody": "Test Email Body",
            "externalEntityName": "CustomerEntity",
            "externalEntityId": "Entity123",
            "externalDescription": "This is a test description",
            "externalGroupName": "CustomerNationalId",
            "externalGroupValue": "0058231341",


            "externalTrackingNumber": "Tracking123",
            "smsRecipients": [
                {"to": "09031360327"},
                {"to": "09379690139"}
            ],
            "emailRecipients": [
                {
                    "to": "ehsan.h@abramad.com",
                    "cc": "sina.z@abramad.com",
                    "bcc": ""
                }
            ]
        }
    ]
}

# Convert the data to JSON and wrap it in a model field
form_data = {
    "model": json.dumps(data)
}

# Send the POST request
response = requests.post(url, headers=headers, data=form_data, verify=True)

# Print the response from the server
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")


#"externalSubGroupName": "SubGroupA",
#"externalSubGroupValue": "SubValueA",