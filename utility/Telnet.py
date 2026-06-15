#!/usr/bin/env python3

import subprocess
import sys

def run_command(command, capture_output=False, check=True, shell=False):
    try:
        result = subprocess.run(
            command,
            shell=shell,
            check=check,
            capture_output=capture_output,
            text=True,
        )
        return result.stdout if capture_output else None
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {' '.join(e.cmd) if isinstance(e.cmd, list) else e.cmd}")
        print(e.output)


telnet_client_file = "./telnet_clients.txt"

telnet_clients = []
with open(telnet_client_file, "r", encoding="utf-8") as file:

    lines = file.readlines()[:]  # Skip the first line
    for line in lines:
        line = line.strip()
        if not line:
            continue  # Skip empty lines

        tmp_list = line.split(':')
        if len(tmp_list) != 2:
            print(f"Skipping malformed line: {line}")
            continue
        hostname = tmp_list[0]
        ip = tmp_list[1]

        telnet_clients.append([hostname, ip])

for host in telnet_clients:
    print(f"\n{host[0]}) ", end="\n\t")
    run_command(["nc", "-zv", f"{host[1]}", "22"])