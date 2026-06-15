Get-NetFirewallProfile | Set-NetFirewallProfile -Enabled False -Confirm:$False
cscript c:\windows\system32\slmgr.vbs /skms kms.abramad.com
Start-Sleep -Seconds 5
cscript c:\windows\system32\slmgr.vbs /ato
   
   
Get-Disk | Where-Object -FilterScript {$_.PartitionStyle -EQ 'raw'} | 
    Initialize-Disk -PartitionStyle GPT -PassThru | 
        New-Partition -AssignDriveLetter -UseMaximumSize | 
            Format-Volume -FileSystem NTFS
 
Start-Sleep -Seconds 5

$Disks = Get-Disk

ForEach ($Disk IN $Disks) {
    $DiskPartitions = Get-Partition -DiskNumber $($Disk.Number)
    ForEach ($DiskPartition IN $DiskPartitions) {
        IF ($DiskPartition.DriveLetter) {
            $MaxSize = (Get-PartitionSupportedSize -DriveLetter $($DiskPartition.DriveLetter)).SizeMax
            Resize-Partition -DriveLetter $DiskPartition.DriveLetter -Size $MaxSize -ErrorAction SilentlyContinue
        }
    }
}
