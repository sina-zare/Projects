from uptime_kuma_api import UptimeKumaApi

api = UptimeKumaApi('http://172.17.255.85:3013/')
api.login('admin', 'I4=t8K<xn')

# Fetch all monitors
monitors = api.get_monitors()

# Find the monitor by name and get its ID
monitor_name = "soheila"
monitor_id = None
for monitor in monitors:
    if monitor['name'].lower() == monitor_name.lower():
        monitor_id = monitor['id']
        break

# If the monitor exists, delete it
if monitor_id:
    api.delete_monitor(monitor_id)
    print(f"Monitor '{monitor_name}' deleted successfully.")
else:
    print(f"Monitor '{monitor_name}' not found.")

api.disconnect()
