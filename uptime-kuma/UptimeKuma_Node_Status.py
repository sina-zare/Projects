from uptime_kuma_api import UptimeKumaApi, MonitorStatus

# Initialize the API
api = UptimeKumaApi('http://172.17.255.85:3013')

# Log in to the API
api.login('admin', 'I4=t8K<xn')

# Fetch all monitors
monitors = api.get_monitors()

# Iterate through each monitor and fetch its status using the get_monitor_status function
for monitor in monitors:
    monitor_id = monitor['id']

    try:
        # Get the monitor status
        monitor_status = api.get_monitor_status(monitor_id)

        # Convert the monitor status to a readable string
        if monitor_status == MonitorStatus.UP:
            status_str = "Up"
        elif monitor_status == MonitorStatus.DOWN:
            status_str = "Down"
        elif monitor_status == MonitorStatus.PENDING:
            status_str = "Pending"
        else:
            status_str = "Unknown"

        # Print monitor name and status
        print(f"Monitor Name: {monitor['name']}, Status: {status_str}")

    except Exception as e:
        # Handle the case where the monitor does not exist or other issues
        print(f"Monitor Name: {monitor['name']}, Status: Error - {e}")
