Get-NetIPConfiguration

New-NetIPAddress -InterfaceIndex “26” -IPAddress 172.26.76.30 -PrefixLength 24 -DefaultGateway 172.26.76.11
Set-DnsClientServerAddress -InterfaceIndex "26" -ServerAddresses "172.26.76.11 , 8.8.8.8"
ipconfig /all
Start-Sleep -s 7
ping google.com -t