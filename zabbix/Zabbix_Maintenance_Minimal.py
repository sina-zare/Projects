try:
    import csv
    from datetime import datetime, timedelta
    from pyzabbix import ZabbixAPI
    from stdiomask import getpass
    import os
    import traceback
    #from cryptography.fernet import Fernet
    import warnings
    from urllib3.exceptions import InsecureRequestWarning
    from colorama import init, Fore, Back, Style

    init(autoreset=True)

    '''
    def decryptor(enc_env_var, key_env_var):
        # Load the key
        key = os.environ.get(key_env_var)
        encryption_key = Fernet(key)
        encrypted_password = (os.environ.get(enc_env_var)).encode()
        # Decrypt Data
        decrypted_password = encryption_key.decrypt(encrypted_password.decode())
    
        # print(f"Decryped Text: {decrypted_password}")
        return decrypted_password.decode()
    '''

    # Suppress only the single InsecureRequestWarning from urllib3
    warnings.simplefilter("ignore", InsecureRequestWarning)

    zabbix_url_list = {
        '1': 'https://me-customerzabbix.abramad.com',
        '2': 'https://vnk-customerzabbix.abramad.com'
    }

    server_prompt = (
            Fore.RED + Style.BRIGHT + "╔══════════════════════════════╗\n" +  # Red border top
            Fore.WHITE + Style.BRIGHT + "║       Choose Server ID       ║\n" +
            Fore.RED + Style.BRIGHT + "╠══════════════════════════════╣\n" +  # Red separator
            Fore.WHITE + Style.BRIGHT + "║ 1) ME-CustomerZabbix         ║\n" +  # White option
            Fore.WHITE + Style.BRIGHT + "║ 2) VNK-CustomerZabbix        ║\n" +  # White option
            Fore.RED + Style.BRIGHT + "╚══════════════════════════════╝\n" +  # Red border bottom
            Fore.WHITE + Style.BRIGHT + ": "
    )
    user_input = input(server_prompt)

    if user_input == '1' or user_input == '2':
        zabbix_url = user_input
    else:
        raise ValueError(f"⚠️ Wrong ID")

    #username = 'sysops-svc'
    #password = decryptor('sysops-svc_enc', 'sysops-svc_key')

    username = input("\nUsername: ")
    password = getpass("Password: ")

    # Connect to Zabbix
    zapi = ZabbixAPI(zabbix_url_list[zabbix_url.strip()])
    zapi.session.verify = False
    # zapi.session.headers.update({"User-Agent": "PyZabbix"})
    zapi.login(username.strip(), password)

    print(f"\nConnected to Zabbix API Version {zapi.api_version()}\n")


    # Ask for duration (hours or minutes)
    duration_hours = input('Duration (Hours, press Enter to skip): ')
    duration_minutes = input('Duration (Minutes, press Enter to skip): ')

    # Convert input to integers (default 0 if empty)
    duration_hours = int(duration_hours) if duration_hours.strip() else 0
    duration_minutes = int(duration_minutes) if duration_minutes.strip() else 0

    if duration_hours == 0 and duration_minutes == 0:
        raise ValueError("Duration must be greater than 0!")

    csv_file_path = "C://Temp//maintenance_nodes.csv"

    # Read hosts from CSV
    print('\nChecking CSV.')
    hosts = []
    with open(csv_file_path, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                if 'Node Name' not in row[0]:  # skip header
                    hostname = row[0].strip().lower()
                    if hostname:  # skip empty or blank lines
                        hosts.append(hostname)

    if hosts:
        print(f'    ✅ OK')
    else:
        raise ValueError("    ⚠️ No hosts found in CSV file!")

    # Get ALL hosts from Zabbix (once)
    print('\nFetching Zabbix hosts...')
    all_hosts = zapi.host.get(output=["host", "hostid"])
    zabbix_host_map = {h["host"].lower(): h for h in all_hosts}  # lowercased dict

    # Match hosts case-insensitively
    print('\nSearching Zabbix.')
    host_ids = []
    for hostname in hosts:
        if not hostname:
            continue
        if hostname in zabbix_host_map:
            match = zabbix_host_map[hostname]
            print(f'    ✅ {match["host"]} found in Zabbix')
            host_ids.append(match["hostid"])
        else:
            print(f"    ⚠️ '{hostname}' not found in Zabbix!")

    if not host_ids:
        raise ValueError("    ⚠️ No valid hosts found in Zabbix!")


    # Base maintenance prefix
    base_name = "Automated-Maintenance"
    # Get existing maintenances with that prefix
    existing_maintenances = zapi.maintenance.get(output=["name"])

    # calculating number suffix for maintenance name
    max_suffix = 0
    for m in existing_maintenances:
        name = m.get("name", "")
        if name.startswith(base_name):
            parts = name.split("-")
            if parts[-1].isdigit():
                num = int(parts[-1])
                if num > max_suffix:
                    max_suffix = num

    # New maintenance name with increment
    maintenance_name = f"{base_name}-{max_suffix + 1:02d}"

    # Calculate total duration in seconds
    duration_seconds = duration_hours * 3600 + duration_minutes * 60

    # Define maintenance time window
    now = int(datetime.now().timestamp())
    end = now + duration_seconds
    now_readable = datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S")
    end_readable = datetime.fromtimestamp(end).strftime("%Y-%m-%d %H:%M:%S")

    # Build description text
    duration_text = []
    if duration_hours > 0:
        duration_text.append(f"{duration_hours} hours")
    if duration_minutes > 0:
        duration_text.append(f"{duration_minutes} minutes")
    duration_text = " | ".join(duration_text)


    print("🆕 Creating new maintenance...")

    maintenance = zapi.maintenance.create({
        "name": maintenance_name,
        "maintenance_type": 0,   # 1 = No data collection, 0 = With data collection
        "active_since": now,
        "active_till": end,
        "hostids": host_ids,
        "description": f"Maintenance window since {now_readable} till {end_readable} | {duration_text} | {username}",
        "timeperiods": [{
            "timeperiod_type": 0,   # one-time maintenance
            "start_date": now,
            "period": duration_seconds
        }]
    })

    print(f"\n✅ Done.")
    input('\n\nPress enter to close.')


except Exception as err:
    tb = traceback.extract_tb(err.__traceback__)
    last_call = tb[-1]  # the last traceback frame, where the exception occurred
    print(f'''\n🚫 Error:
    {type(err).__name__}: {err}
    file: {last_call.filename}, line: {last_call.lineno}: {last_call.line}
    ''')
    input('\n\nPress enter to close.')

