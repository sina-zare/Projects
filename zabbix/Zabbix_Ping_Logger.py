import subprocess
import time
from pyzabbix import ZabbixAPI

# Zabbix API Credentials
ZABBIX_URL = "http://vnk-zabbix.abramad.com"
ZABBIX_USER = "sysops-svc"
ZABBIX_PASSWORD = "N&jG@pZ21V&dP@PAxh5F"
HOSTNAME = "VDC-Bleaf-M4U24"
ITEM_KEYS = {
    "sent": "Interface port-channel2(SG): Bits sent",
    "received": "Interface port-channel2(SG): Bits recieved"
}
THRESHOLD = 9999999999
PING_IP = "192.168.255.4"


def get_zabbix_data(retries=3, delay=5):
    try:
        zapi = ZabbixAPI(ZABBIX_URL)
        zapi.login(ZABBIX_USER, ZABBIX_PASSWORD)

        # Get host ID
        host = zapi.host.get(filter={"host": HOSTNAME})
        if not host:
            print("Host not found")
            return None, None
        host_id = host[0]["hostid"]

        # Get item IDs
        items = zapi.item.get(hostids=host_id, filter={"name": list(ITEM_KEYS.values())})
        item_map = {item["name"]: item["itemid"] for item in items}

        # Fetch latest values
        values = {}
        for key, name in ITEM_KEYS.items():
            item_id = item_map.get(name)
            if item_id:
                history = zapi.history.get(itemids=item_id, sortfield="clock", sortorder="DESC", limit=1)
                if history:
                    values[key] = int(history[0]["value"])

        return values.get("sent"), values.get("received")

    except Exception as err:
        print(f"Error: {err}. Retrying in {delay} seconds...")
        if retries > 0:
            time.sleep(delay)
            return get_zabbix_data(retries=retries - 1, delay=delay)  # Recursive retry with a limit
        else:
            print("Max retries reached. Exiting.")
            return None, None

def ping_logger():
    process = subprocess.Popen(["ping", PING_IP], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)

    for line in iter(process.stdout.readline, ""):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"{timestamp} {line.strip()}"
        print(log_line)

        # Check Zabbix values
        sent, received = get_zabbix_data()
        if sent is not None and (sent > THRESHOLD):
            with open("alert_log.txt", "a") as log_file:
                log_file.write(f"Bits sent ALERT: Zabbix Value= {sent} Ping Value= {log_line}\n")
        if received is not None and (received > THRESHOLD):
            with open("alert_log.txt", "a") as log_file:
                log_file.write(f"Bits Received ALERT: Zabbix Value= {received} Ping Value= {log_line}\n")

ping_logger()
