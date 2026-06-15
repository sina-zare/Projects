#!/usr/bin/env python3

import requests


def is_iran_ip(ip):
    try:
        response = requests.get(
            f"https://api.country.is/{ip}",
            timeout=5
        )
        response.raise_for_status()

        data = response.json()
        return data.get("country") #== "IR"

    except requests.RequestException as e:
        print(f"Error checking IP {ip}: {e}")
        return False


if __name__ == "__main__":
    ip = input("Enter IP address: ").strip()

    if is_iran_ip(ip):
        print(f"{ip} belongs to Iran (IR)")
    else:
        print(f"{ip} does NOT belong to Iran")