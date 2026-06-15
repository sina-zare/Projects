import requests

# Replace with your UptimeRobot API key
API_KEY = "u1760387-a5f78e005ffd60fb94c4320c"

# API endpoint to get alert contacts
URL = "https://api.uptimerobot.com/v2/getAlertContacts"

# Data for the request
data = {
    "api_key": API_KEY,
    "format": "json"  # Response format
}

try:
    # Make the POST request to the API
    response = requests.post(URL, data=data)
    response.raise_for_status()  # Raise an error for bad status codes

    # Parse the JSON response
    alert_contacts = response.json()

    # Check if the request was successful
    if alert_contacts.get("stat") == "ok":
        print("Alert Contacts:")
        for contact in alert_contacts.get("alert_contacts", []):
            print(f"ID: {contact['id']}, Friendly Name: {contact['friendly_name']}, Type: {contact['type']}")
    else:
        print("Failed to fetch alert contacts:", alert_contacts.get("error", "Unknown error"))

except requests.exceptions.RequestException as e:
    print("An error occurred:", e)
