$wifiAdapter = Get-NetAdapter -Name "Wi-Fi"
Set-DnsClientServerAddress -InterfaceIndex $wifiAdapter.ifIndex -ServerAddresses ("1.0.0.1", "1.1.1.1")
New-NetIPAddress -InterfaceIndex $wifiAdapter.ifIndex -IPAddress "172.26.76.113" -PrefixLength 24 -DefaultGateway "172.26.76.11"