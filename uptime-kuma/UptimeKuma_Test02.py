from uptime_kuma_api import UptimeKumaApi, MonitorType

try:
    api = UptimeKumaApi('http://172.29.6.100:80')
    api.login('admin', 'I4=t8K<xn')

    # Fetch all monitors
    monitors = api.get_monitors()

    # Find the monitor by name and get its ID
    monitor_list = []
    for monitor in monitors[:100]:
        monitor_list.append([monitor['id'], monitor['name'], monitor['url'], monitor['description']])

    with open("C:\\Temp\\temp-vip.txt", "w", encoding="utf-8") as file:
        for i in monitor_list:
            file.write(f"{i[0]},{i[1]},{i[2]},{i[3]}\n")

    api.disconnect()

    monitor_list2 = []
    with open("C:\\Temp\\temp-vip.txt", "r", encoding="utf-8") as file:
        for i in file:
            monitor_list2.append(i.replace('\n', '').split(','))

    api02 = UptimeKumaApi('http://172.29.6.102:8080/')
    api02.login('admin', 'I4=t8K<xn')

    for item in monitor_list2:
        monitor_config02 = {
            "type": MonitorType.KEYWORD,
            "name": f"{item[1]}",
            "url": f"{item[2]}",
            "keyword": "ورود کاربران",
            "interval": 90,
            "maxretries": 3,
            "retryInterval": 30,
            "timeout": 72,
            "resendInterval": 480,
            "maxredirects": 10,
            "accepted_statuscodes": ['200-299'],
            "description": f"{item[3]}",
            "notificationIDList": [1]  # Enable Telegram Notification
        }

        try:
            result = api02.add_monitor(**monitor_config02)
            print(result, end=' : ')
            print(item[1])
            # time.sleep(0.5)
        except Exception as err:
            print(err)

    api02.disconnect()



except Exception as err:
    print(f"Error:\n{err}")