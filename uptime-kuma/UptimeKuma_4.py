import time

from uptime_kuma_api import UptimeKumaApi, MonitorStatus

down_name_list = set()
with open('C://Temp//list2.txt', 'r') as file:
    for node in file:
        down_name_list.add(node.strip('\n'))



api = UptimeKumaApi('http://172.17.255.85:3013')
api.login('admin', 'I4=t8K<xn')
monitors = api.get_monitors()

for down in down_name_list:
    for monitor in monitors:

        if down.lower() == monitor['name'].lower():
            monitor_id = monitor['id']

            try:
                api.delete_monitor(monitor_id)
                print(f"Deleted: {monitor['name']} - {monitor['id']}")
                time.sleep(2)


            except Exception as e:
                # Handle the case where the monitor does not exist or other issues
                print(f"Error while handling {monitor['name']}, Error: {e}")
