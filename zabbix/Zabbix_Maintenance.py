# pyinstaller --onefile --icon=zabbix.ico --hidden-import=csv --hidden-import=datetime --hidden-import=pyzabbix --hidden-import=stdiomask --hidden-import=os --hidden-import=traceback --hidden-import=warnings --hidden-import=urllib3 --hidden-import=colorama Zabbix_Maintenance.py

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

    def get_valid_input(prompt, fmt, example):
        """Loop until valid input is entered or empty string is returned."""
        while True:
            user_input = input(f"{prompt}\nFormat: {fmt} (e.g., {example}): ").strip()
            if not user_input:  # allow empty input
                return ""
            try:
                # Just try to parse, not storing result here
                datetime.strptime(user_input, fmt)
                return user_input
            except ValueError:
                print(Fore.RED + f"\nInvalid input! Please use the format {fmt}" + Fore.RESET)

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
        '2': 'https://vnk-customerzabbix.abramad.com',
        '3': 'https://me-zabbix.abramad.com/zabbix',
        '4': 'https://vnk-zabbix.abramad.com'
    }

    print(Fore.YELLOW + "{ Zabbix Maintenance creation tool }\n")
    server_prompt_0 = (
            Fore.RED + Style.BRIGHT   + "╔══════════════════════════════╗\n" +  # Red border top
            Fore.WHITE + Style.BRIGHT + "║ 1) ME-CustomerZabbix         ║\n" +  # White option
            Fore.WHITE + Style.BRIGHT + "║ 2) VNK-CustomerZabbix        ║\n" +
            Fore.WHITE + Style.BRIGHT + "║ 3) ME-Zabbix                 ║\n" +
            Fore.WHITE + Style.BRIGHT + "║ 4) VNK-Zabbix                ║\n" +
            Fore.RED + Style.BRIGHT   + "╚══════════════════════════════╝\n" +  # Red border bottom
            Fore.WHITE + Style.BRIGHT + "Choose server ID: "
    )

    while True:
        user_input = input(server_prompt_0)
        if user_input in ("1", "2", "3", "4"):
            zabbix_url = user_input
            break
        else:
            print(Fore.RED + "⚠️ Invalid choice! Please enter 1 to 4.\n" + Fore.RESET)

    #username = 'sysops-svc'
    #password = decryptor('sysops-svc_enc', 'sysops-svc_key')

    username = input("\nUsername: ")
    password = getpass("Password: ")

    # Connect to Zabbix
    zapi = ZabbixAPI(zabbix_url_list[zabbix_url.strip()])
    zapi.session.verify = False
    # zapi.session.headers.update({"User-Agent": "PyZabbix"})
    zapi.login(username.strip(), password)

    print(Fore.LIGHTGREEN_EX + f"\n✅ Connected to Zabbix API Version {zapi.api_version()}\n" + Fore.RESET)

    # Ask for start date/time from user
    print("\n" + Fore.YELLOW + "Getting maintenance details.")
    print("\n" + Fore.YELLOW + "Enter start date (leave empty for current date)")
    date_input = get_valid_input("Start Date", "%Y-%m-%d", "2024-01-15")
    print("\n" + Fore.YELLOW + "Enter start time (leave empty for now)")
    time_input = get_valid_input("Start Time", "%H:%M:%S", "14:30:00")



    # Convert input to integers (default 0 if empty)
    while True:
        # Ask for duration (hours or minutes)
        duration_hours = input("\n" + Fore.YELLOW + 'Duration (Hours, press Enter to skip):' + Fore.WHITE + " ")
        duration_minutes = input("\n" + Fore.YELLOW + 'Duration (Minutes, press Enter to skip):' + Fore.WHITE + " ")

        duration_hours = int(duration_hours) if duration_hours.strip() else 0
        duration_minutes = int(duration_minutes) if duration_minutes.strip() else 0

        if duration_hours == 0 and duration_minutes == 0:
            print(Fore.RED + "⚠️ Duration must be greater than 0!\n" + Fore.RESET)
        else:
            break




    if date_input and time_input:
        # Case 1: Both provided
        start_datetime = datetime.strptime(f"{date_input} {time_input}", "%Y-%m-%d %H:%M:%S")
    elif date_input and not time_input:
        # Case 2: Date only (default now)
        clock_now = datetime.now().strftime("%H:%M:%S")
        start_datetime = datetime.strptime(f"{date_input} {clock_now}", "%Y-%m-%d %H:%M:%S")
    elif time_input and not date_input:
        # Case 3: Time only (use today's date)
        today_str = datetime.now().strftime("%Y-%m-%d")
        start_datetime = datetime.strptime(f"{today_str} {time_input}", "%Y-%m-%d %H:%M:%S")
    else:
        # Case 4: Neither → current time
        start_datetime = datetime.now()

    now = int(start_datetime.timestamp())
    print("\n" + Fore.LIGHTGREEN_EX + f"Using start time: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")


    csv_file_path = "C://Temp//maintenance_nodes.csv"
    # Read hosts from CSV
    print("\n" + Fore.YELLOW + 'Checking CSV.')
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
        print(Fore.LIGHTGREEN_EX + f'    ✅ OK')
    else:
        raise ValueError("    ⚠️ No hosts found in CSV file!")

    # Get ALL hosts from Zabbix (once)
    print("\n" + Fore.YELLOW + 'Fetching Zabbix hosts...')
    all_hosts = zapi.host.get(output=["host", "hostid"])
    zabbix_host_map = {h["host"].lower(): h for h in all_hosts}  # lowercased dict

    # Match hosts case-insensitively
    print(Fore.YELLOW + 'Searching Zabbix.')
    host_ids = []
    for hostname in hosts:
        if not hostname:
            continue
        if hostname in zabbix_host_map:
            match = zabbix_host_map[hostname]
            print(Fore.LIGHTGREEN_EX + f'    ✅ {match["host"]} found in Zabbix')
            host_ids.append(match["hostid"])
        else:
            print(Fore.LIGHTRED_EX + f"    ⚠️ '{hostname}' not found in Zabbix!")

    if not host_ids:
        raise ValueError("    ⚠️ No valid hosts found in Zabbix!")


    # Get existing maintenances with that prefix
    existing_maintenances = zapi.maintenance.get(output=["name"])

    # calculating number suffix for maintenance name
    max_suffix = 0
    for m in existing_maintenances:
        name = m.get("name", "")
        if name.startswith("Automated-Maintenance"):
            parts = name.split("-")
            if parts[-1].isdigit():
                num = int(parts[-1])
                if num > max_suffix:
                    max_suffix = num

    # New maintenance name with increment
    maintenance_name = f"Automated-Maintenance-{max_suffix + 1:02d}"

    # Calculate total duration in seconds
    duration_seconds = duration_hours * 3600 + duration_minutes * 60

    # Define maintenance time window
    end = now + duration_seconds
    now_readable = datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S")
    end_readable = datetime.fromtimestamp(end).strftime("%Y-%m-%d %H:%M:%S")
    current_datetime = datetime.fromtimestamp(int(datetime.now().timestamp())).strftime("%Y-%m-%d %H:%M:%S")

    # Build description text
    duration_text = []
    if duration_hours > 0:
        duration_text.append(f"{duration_hours} hours")
    if duration_minutes > 0:
        duration_text.append(f"{duration_minutes} minutes")
    duration_text = " | ".join(duration_text)


    server_prompt_1 = (
            Fore.RED + Style.BRIGHT + "\n\n╔══════════════════════════════╗\n" +  # Red border top
            Fore.WHITE + Style.BRIGHT + "║ 1) Create New Maintenance    ║\n" +  # White option
            Fore.WHITE + Style.BRIGHT + "║ 2) Edit Existing Maintenance ║\n" +  # White option
            Fore.RED + Style.BRIGHT + "╚══════════════════════════════╝\n" +  # Red border bottom
            Fore.WHITE + Style.BRIGHT + "Choose an option (Default 1, press Enter to skip): "
    )

    # Ask for maintenance option
    maintenance_option = input(server_prompt_1)
    maintenance_option = int(maintenance_option) if maintenance_option.strip() else 1

    if maintenance_option == 2:
        while True:
            input_maintenance_name = input("\n" + Fore.YELLOW + 'Enter maintenance name to edit: ').strip()

            if not input_maintenance_name:
                print(Fore.RED + "⚠️ Maintenance name cannot be empty!" + Fore.RESET)
                continue

            # Check if maintenance with this name already exists
            existing = zapi.maintenance.get(
                filter={"name": input_maintenance_name},
                output=["maintenanceid", "description"]
            )

            if not existing:
                print(Fore.RED + f"⚠️ Maintenance name '{input_maintenance_name}' not found in Zabbix! Try again." + Fore.RESET)
                continue  # prompt again

            # If found → break loop
            maint_id = existing[0]["maintenanceid"]
            old_desc = existing[0].get("description", "")
            print(f"🔄 Updating existing maintenance (ID: {maint_id})...")

            new_desc = ""
            if old_desc.strip():
                new_desc = old_desc + "\n"
            new_desc += f"Maintenance window since {now_readable} till {end_readable} | {duration_text} | {username} | modified {current_datetime}"

            maintenance = zapi.maintenance.update({
                "maintenanceid": maint_id,
                "name": input_maintenance_name,
                "maintenance_type": 0,  # 1 = No data collection, 0 = With data collection
                "active_since": now,
                "active_till": end,
                "hostids": host_ids,
                "description": new_desc,
                "timeperiods": [{
                    "timeperiod_type": 0,  # one-time maintenance
                    "start_date": now,
                    "period": duration_seconds
                }]
            })

            print("\n" + Fore.LIGHTGREEN_EX + "✅ Done.")
            input('\n\nPress enter to close.')
            break  # exit loop after success


    elif maintenance_option == 1:
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

        print("\n" + Fore.LIGHTGREEN_EX + "✅ Done.")
        input('\n\nPress enter to close.')

    else:
        raise ValueError(f"⚠️ Wrong Option")

except Exception as err:
    tb = traceback.extract_tb(err.__traceback__)
    last_call = tb[-1]  # the last traceback frame, where the exception occurred
    print(Fore.RED + f'''\n🚫 Error:
    {type(err).__name__}: {err}
    ''' + Fore.RESET)
    input('\n\nPress enter to close.')

