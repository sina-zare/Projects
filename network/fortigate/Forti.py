try:
    from netmiko import Netmiko
    import time
    import os
    import getpass

except Exception as e:
    print(e)
    time.sleep(2)

def connect_to_fg(address, port, username, password):

    def decrypt(cipher_text, key):
        plain_text = ""
        for i in range(len(cipher_text)):
            char = cipher_text[i]
            plain_int = ord(char) - key
            plain_text += chr(plain_int)
        return plain_text

    def print_with_delay(text):
        for char in text:
            print(char, end='', flush=True)
            time.sleep(0.03)
        print("\n")

    # Credentials
    #username = "sina.z"
    #password = decrypt(os.environ.get('spass'), 9999)
    #username = str(input("Username: ").strip())
    #password = getpass("Password: ")
    #os.system('cls' if os.name == 'nt' else 'clear')


    fortigate_fw = {
        'device_type': 'fortinet',
        'host': address,
        'username': username,
        'password': password,
        'port': port
    }

    print_with_delay(f"{'#' * 10} Connecting to the Device {'#' * 10}")
    global ssh_to_fg
    ssh_to_fg = Netmiko(**fortigate_fw)

    print(ssh_to_fg.find_prompt())
    print_with_delay(f"{'#' * 10} Connected {'#' * 10}")
    time.sleep(2)
    os.system('cls' if os.name == 'nt' else 'clear')



def new_fw_policy(policy_no, policy_name, src_int, dst_int, src_addr_list, dst_addr_list, service_list, username, ticket_no):

    source_addresses = ''
    for address in src_addr_list:
        source_addresses += f"{address} "

    destination_addresses = ''
    for address in dst_addr_list:
        destination_addresses += f"{address} "

    services = ''
    for service in service_list:
        services += f"{service} "

    commands = [
        'config firewall policy',
        f'edit {policy_no}',
        #f'set name "{policy_name}"',
        f'set srcintf "{src_int}"',
        #f'set dstintf "{dst_int}"',
        #'set action accept',
        #f'set srcaddr {source_addresses}',
        #f'set dstaddr {destination_addresses}',
        #'set schedule "always"',
        #f'set service {services}',
        #'set logtraffic all',
        f'set comments "Test"',
        'next',
        'end'
    ]

    return commands

try:
    usr = 'x'
    pwd = getpass.getpass("Password: ")
    connect_to_fg('172.17.242.254', 2345, 'tst', 'tst')

except Exception as e:
    print(e)
    time.sleep(2)