#Copy-Item -Path "C:\Temp\AgentConfig.xml" -Destination "\\MER-REFAHKY-DB1.cloud.local\C$\Temp\" -Confirm:$False -Force

[STRING]$ServerName = HostName

$AgentConfigSecTeam = [XML](Get-Content -Path "C:\Temp\AgentConfig.xml")
$NameXMLSecTeam = $AgentConfigSecTeam.WinCollectConfiguration.AgentCore.Name
$IdentifierXMLSecTeam = $AgentConfigSecTeam.WinCollectConfiguration.AgentCore.Identifier
$VersionXMLSecTeam = $AgentConfigSecTeam.WinCollectConfiguration.version

$AgentConfigInstalled = [XML](Get-Content -Path "C:\Program Files\IBM\WinCollect\config\AgentConfig.xml")
$NameXMLInstalled = $AgentConfigInstalled.WinCollectConfiguration.AgentCore.Name
$IdentifierXMLInstalled = $AgentConfigInstalled.WinCollectConfiguration.AgentCore.Identifier
$VersionXMLInstalled = $AgentConfigInstalled.WinCollectConfiguration.version

IF (($NameXMLInstalled -NE $ServerName) -AND ($IdentifierXMLInstalled -NE $ServerName)) {
    
    $AgentConfigSecTeam.WinCollectConfiguration.version = $VersionXMLInstalled
    $AgentConfigSecTeam.WinCollectConfiguration.AgentCore.Name  = $ServerName
    $AgentConfigSecTeam.WinCollectConfiguration.AgentCore.Identifier= $ServerName
    $AgentConfigSecTeam.Save("C:\Temp\AgentConfigNewVersion.xml")
    Start-Sleep -Seconds 5

    Copy-Item -Path "C:\Temp\AgentConfigNewVersion.xml" -Destination 'C:\Program Files\IBM\WinCollect\config\AgentConfig.xml' -Confirm:$False -Force
    Restart-Service -Name WinCollect -Confirm:$False -Force
    Start-Sleep -Seconds 5
    
    Remove-Item -Path "C:\Temp\AgentConfig.xml" -Force -Confirm:$False
    Remove-Item -Path "C:\Temp\AgentConfigNewVersion.xml" -Force -Confirm:$False
}
ELSEIF ('SecTeam' -NOTIN $AgentConfigInstalled.WinCollectConfiguration.LocalSources.Name) {
    $AgentConfigSecTeam.WinCollectConfiguration.version = $VersionXMLInstalled
    $AgentConfigSecTeam.WinCollectConfiguration.AgentCore.Name  = $ServerName
    $AgentConfigSecTeam.WinCollectConfiguration.AgentCore.Identifier= $ServerName
    $AgentConfigSecTeam.Save("C:\Temp\AgentConfigNewVersion.xml")
    Start-Sleep -Seconds 5

    Copy-Item -Path "C:\Temp\AgentConfigNewVersion.xml" -Destination 'C:\Program Files\IBM\WinCollect\config\AgentConfig.xml' -Confirm:$False -Force
    Restart-Service -Name WinCollect -Confirm:$False -Force
    Start-Sleep -Seconds 5
    
    Remove-Item -Path "C:\Temp\AgentConfig.xml" -Force -Confirm:$False
    Remove-Item -Path "C:\Temp\AgentConfigNewVersion.xml" -Force -Confirm:$False
    
}
ELSE {
    Remove-Item -Path "C:\Temp\AgentConfig.xml" -Force -Confirm:$False
}