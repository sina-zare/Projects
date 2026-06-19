import subprocess
import time
from datetime import datetime


WIFI_1 = "ABR-WiFi"
WIFI_2 = "SG-WLAN"

INTERVAL = 300  # 5 minutes


# def connect_wifi(ssid):
#     print(f"[{datetime.now()}] Connecting to {ssid}...")
#
#     result = subprocess.run(
#         ["netsh", "wlan", "connect", f"name={ssid}"],
#         capture_output=True,
#         text=True
#     )
#
#     if result.returncode == 0:
#         print(f"Connected to {ssid}")
#     else:
#         print(f"Failed to connect to {ssid}")
#         print(result.stderr)

def connect_wifi(ssid):
    print(f"Connecting to {ssid}...")

    result = subprocess.run(
        ["netsh", "wlan", "connect", f"name={ssid}"],
        capture_output=True,
        text=True
    )

    print("Return code:", result.returncode)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

while True:
    connect_wifi(WIFI_1)
    time.sleep(INTERVAL)

    connect_wifi(WIFI_2)
    time.sleep(INTERVAL)