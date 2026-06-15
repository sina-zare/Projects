#!/usr/bin/env python3

import subprocess

services = ["zabbix-server", "zabbix-agent2"]

for service in services:
    try:
        print(f"Restarting {service}...")
        subprocess.run(
            ["sudo", "systemctl", "restart", service],
            check=True
        )
        print(f"{service} restarted successfully ✅")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to restart {service}: {e}")
