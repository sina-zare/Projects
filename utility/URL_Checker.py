import requests
import socket
import time
import re
import os

def rahkaran_status(ip):

    if ip == "185.187.84.180":
        print("Attar P8 DataCenter\nRestricted")
    elif ip == "185.187.84.181":
        print("Attar P8 DataCenter\nOpen to All")
    elif ip == "185.187.85.5" or ip == "185.187.85.6":
        print("Attar P8 DataCenter\nIran Access")
    elif ip == "92.61.182.10":
        print("MirEmad DataCenter\nOpen to All")
    elif ip == "92.61.182.12":
        print("MirEmad DataCenter\nRestricted")

def fqdn_to_ip(fqdn):
    try:
        # Attempt to resolve the FQDN to an IP address
        ip_address = socket.gethostbyname(fqdn)
        print(f'\nPublic IP: {ip_address}')
        rahkaran_status(ip_address)
        return ip_address
    except socket.gaierror as e:
        # Handle the error if the FQDN cannot be resolved
        print(f'Error in "fqdn_to_ip" function:\n{e}\n')
        #return f'Error in "fqdn_to_ip" function:\n{e}'

def check_website(url):
    try:
        # Make a GET request to the website
        response = requests.get(url)
        # Check if the HTTP status code is between 200 and 299
        if (200 <= response.status_code <= 299) and re.search("ورود کاربر", response.text):
            print(f"{url}:  <OK>  ")
            return '<OK>'
        else:
            print(f"{url}:  <Not OK>  : {response.status_code}")
            return '<Not OK>'

    except requests.RequestException as e:
        print(f"An error occurred while trying to access the website: {e}")
        return 'Error'


def check_url_with_retry(url, fqdn, retries=5, delay=60):
    for attempt in range(retries):

        test_connection = check_website(url)
        ip = fqdn_to_ip(fqdn)
        if test_connection == '<OK>':
            input("\n\n\nPress Enter to Continue.")
            break
        else:

            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...\n")
                time.sleep(delay)
            else:
                input("Failed to fetch website after several attempts\n\n\nPress Enter to Continue.")




while 1:
    os.system('cls' if os.name == 'nt' else 'clear')
    vm_name = input("VRA/VPS/RA VM Name: ").strip().lower().split('-')
    customer_url = f'https://{vm_name[1]}.rahkaran.ir'
    customer_fqdn = f'{vm_name[1]}.rahkaran.ir'

    print(f"\n{3 * '#'} {customer_url} {3 * '#'}\n")
    check_url_with_retry(customer_url, customer_fqdn)


