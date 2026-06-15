
netsh interface set interface name="Wi-Fi" admin=DISABLED
netsh interface ipv4 set address name="Wi-Fi" source=dhcp
netsh interface set interface name="Wi-Fi" admin=ENABLED
ipconfig /all
Start-Sleep -s 4
ping google.com -t