from uptime_kuma_api import UptimeKumaApi, MonitorType

api = UptimeKumaApi('http://172.17.255.85:3014/')
api.login('admin', 'I4=t8K<xn')

ping_list = [['name', 'host.name', 'description'], ['name2', 'host.name2', 'description2']]

for node in ping_list:
    monitor_config = {
        "type": MonitorType.PING,
        "name": f"{node[0]}",
        "hostname": f"{node[1]}",
        "interval": 90,
        "maxretries": 3,
        "retryInterval": 30,
        "resendInterval": 480,
        "description": f"{node[2]}",
        "notificationIDList": [1]  # Enable Telegram Notification

    }

    result = api.add_monitor(**monitor_config)
    print(f'{result}\n')

api.disconnect()

#
