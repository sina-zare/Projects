from stdiomask import getpass
import winrm

def run_powershell_command(host, username, password):
    # Create a WinRM session
    session = winrm.Session(
        target=host,
        auth=(username, password),
        transport='ntlm',  # Use NTLM authentication
        server_cert_validation='ignore'  # Ignore SSL certificate validation (only use if you trust the target)
    )

    # PowerShell command to be executed remotely
    command = """
    Get-Disk | Where-Object -FilterScript {$_.PartitionStyle -EQ 'raw'} | 
        Initialize-Disk -PartitionStyle GPT -PassThru | 
            New-Partition -AssignDriveLetter -UseMaximumSize | 
                Format-Volume -FileSystem NTFS
    Start-Sleep -Seconds 7
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
    """

    # Execute the PowerShell command remotely
    result = session.run_ps(command)

    # Output the result
    print("Status code:", result.status_code)
    print("Standard Output:", result.std_out.decode('utf-8'))
    print("Standard Error:", result.std_err.decode('utf-8'))

try:
    target_host = input("Target Host: ").strip()
    target_username = input("Username: ").strip()
    target_password = password = getpass("Password: ")

    run_powershell_command(target_host, target_username, target_password)
    print('\n\nAll disks for {target_host} have been initialized and extended successfully.')
    input("\n\nPress anything to exit...")

except Exception as err:
    print(f"Error: {err}")
