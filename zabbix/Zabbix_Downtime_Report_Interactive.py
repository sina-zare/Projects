try:
    import os
    import sys
    import time
    from stdiomask import getpass
    import openpyxl
    from pyzabbix import ZabbixAPI
    from cryptography.fernet import Fernet
    from datetime import datetime, timedelta, timezone

    def subtract_time(x, y):
        # Parse the main time (x) as a datetime object not string
        x_time = datetime.strptime(x, '%H:%M:%S')

        # Parse the subtraction time (y)
        y_hours = int(y.split('h')[0].split()[-1]) if 'h' in y else 0
        y_minutes = int(y.split('m')[0].split()[-1]) if 'm' in y else 0
        y_seconds = int(y.split('s')[0].split()[-1]) if 's' in y else 0

        # Create a timedelta for the time to subtract
        y_delta = timedelta(hours=y_hours, minutes=y_minutes, seconds=y_seconds)
        # Subtract the timedelta
        result_time = x_time - y_delta

        # Format the result as 'HH:MM:SS'
        return result_time.strftime('%H:%M:%S')

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


    def parse_duration(text):
        days = hours = minutes = seconds = 0

        for part in text.split():
            if part.endswith("d"):
                days = int(part[:-1])
            elif part.endswith("h"):
                hours = int(part[:-1])
            elif part.endswith("m"):
                minutes = int(part[:-1])
            elif part.endswith("s"):
                seconds = int(part[:-1])

        return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

    # Zabbix API connection
    zabbix_selection = input('Select Server:\n1) ME-CustomerZabbix\n2) VNK-CustomerZabbix\n> ')
    if zabbix_selection == '1':
        zabbix_url = 'https://me-customerzabbix.abramad.com'
    elif zabbix_selection == '2':
        zabbix_url = 'https://vnk-customerzabbix.abramad.com'
    else:
        'Wrong Selection\nTerminating Script'
        time.sleep(2)
        sys.exit()

    os.system('cls' if os.name == 'nt' else 'clear')

    username = input("Username: ")
    password = getpass("Password: ")

    zapi = ZabbixAPI(zabbix_url)
    zapi.login(username, password)
    print(f'Connected to {zabbix_url}\n\n')
    # Define filters
    media_type = 'Mattermost'
    search_string = 'URL is Down'
    resolved_identifier = 'Problem has been resolved'
    date_from = input('Enter Start Date: (Format: 2024/10/03)\n: ')
    time_from = input('\nEnter Start Time: (Format: 23:00:00) (Default Value: 00:00:00)\n: ')
    if time_from == '':
        time_from = '00:00:00'
    os.system('cls' if os.name == 'nt' else 'clear')
    date_to = input('Enter End Date: (Format: 2024/10/09)\n: ')
    time_to = input('\nEnter End Time: (Format: 06:30:00)(Default Value: 00:00:00)\n: ')
    if time_to == '':
        time_to = '00:00:00'

    datetime_from = int(datetime.strptime(f'{date_from} {time_from}', '%Y/%m/%d %H:%M:%S').timestamp())
    datetime_to = int(datetime.strptime(f'{date_to} {time_to}', '%Y/%m/%d %H:%M:%S').timestamp())

    # Get media type ID for 'Telegram'
    media_types = zapi.mediatype.get(output='extend')
    media_type_id = next((mt['mediatypeid'] for mt in media_types if mt['name'] == media_type), None)

    if media_type_id is None:
        print(f"\nMedia type '{media_type}' not found.")
    else:
        # Fetch alerts sent via 'Telegram' within the time frame
        print('\nGathering Alerts')
        alerts = zapi.alert.get(
            output='extend',
            time_from=datetime_from,
            time_till=datetime_to,
            mediatypeids=media_type_id
        )

        print('Calculating Data')
        downtime = []
        for alert in alerts:
            if search_string in alert['subject'] and resolved_identifier in alert['message']:

                data = {}
                #print(alert['message'].strip().split("\n"))
                for line in alert['message'].strip().split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        data[key.strip()] = value.strip()

                    # Handle special lines like first line (resolved time)
                    if line.startswith("Problem has been resolved at"):
                        parts = line.split()
                        r_time = parts[5]
                        r_date = parts[7]
                        data["Resolved time"] = f"{r_date} {r_time}"
                #print(data)

                # Parse resolved time
                resolved_time = datetime.strptime(data["Resolved time"], "%Y.%m.%d %H:%M:%S")
                # Convert "Problem duration" into timedelta
                duration = parse_duration(data["Problem duration"])
                # Incident time = resolved time - duration
                incident_time = resolved_time - duration
                data["Incident time"] = incident_time

                downtime.append([data["Host"], data["Incident time"], data["Resolved time"], data["Problem duration"]])



    # Saving the Data in an Excel file
    # Load the Excel file
    print('Converting Data to Excel Format')
    workbook = openpyxl.Workbook()
    worksheet = workbook.active

    header = ["Server Name", "Incident time", "Resolved time", "Problem duration"]
    worksheet.append(header)

    time.sleep(2)
    counter = 0
    for data in downtime:
        worksheet.append(data)
        counter += 1
        print(f'Failed URLs: {counter}')
        os.system('cls' if os.name == 'nt' else 'clear')

    # Save the changes to the Excel file
    excel_file_path = f'C:/Temp/{zabbix_url.replace('https://', '').split('.')[0]}-servers-downtime-({str(date_from).replace('/','-')}_{str(date_to).replace('/','-')}).xlsx'
    print(f'Saving Excel file: {excel_file_path}')
    workbook.save(excel_file_path)

    time.sleep(5)

except Exception as err:
    print(f'Error: {err}')
    time.sleep(5)