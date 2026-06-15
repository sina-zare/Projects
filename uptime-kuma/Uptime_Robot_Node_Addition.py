import requests

# Replace with your UptimeRobot API key
API_KEY = "u1760387-a5f78e005ffd60fb94c4320c"

# API endpoint
URL = "https://api.uptimerobot.com/v2/newMonitor"


# Data for the new monitor
data = {
    "api_key": API_KEY,
    "format": "json",  # Response format
    "type": 2,         # Monitor type (1 = HTTP(s))
    "url": "https://HoldingGroup.abramad.cloud/sg",  # URL to monitor
    "friendly_name": "Example Node amin",  # Monitor name
    "keyword_type": 2,  # trigger when keyword does not exist
    "keyword_case_type": 1,
    "keyword_value": "ورود کاربران",
    "timeout": "30",
    "monitor_interval": 1,
    "alert_contacts": "3497520"
}

try:
    # Make the POST request to the API
    response = requests.post(URL, data=data)
    response.raise_for_status()  # Raise an error for bad status codes

    # Parse the JSON response
    result = response.json()

    # Check if the monitor was added successfully
    if result.get("stat") == "ok":
        print("Monitor added successfully:", result)
    else:
        print("Failed to add monitor:", result.get("error", "Unknown error"))

except requests.exceptions.RequestException as e:
    print("An error occurred:", e)
