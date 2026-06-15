function Decrypt-Text {
    param(
        [string]$cipherText,
        [int]$key
    )

    $plainText = ""
    for ($i = 0; $i -lt $cipherText.Length; $i++) {
        $char = $cipherText[$i]
        $plainInt = [int][char]$char - $key
        $plainText += [char]::ConvertFromUtf32($plainInt)
    }
    return $plainText
}

$usercld = Decrypt-Text -cipherText $env:sincloud -key 9999
$userabr = Decrypt-Text -cipherText $env:sin -key 9999
$pass = Decrypt-Text -cipherText $env:spass -key 9999
$pw = ConvertTo-SecureString $pass -AsPlainText -Force

# Credential Object
$credsabr = New-Object System.Management.Automation.PSCredential ($userabr, $pw)
$credscld = New-Object System.Management.Automation.PSCredential ($usercld, $pw)


# Connect to the vCenter server
#Connect-VIServer -Server mra-vc01.abramad.com -Credential $credsabr

# Read the VM names from the text file
$vmNames = Get-Content -Path "E:\Scripts4ChangeRequest\Ghat_Daem.txt"


foreach ($vmName in $vmNames) {

    # Delete each VM
    #$vm = Get-VM -Name $vmName -ErrorAction SilentlyContinue
    #if ($vm) {
        #$vm | Remove-VM -Confirm:$false -DeletePermanently
        #Write-Host "Deleted VM: $vmName"
    #}
    #else {
        #Write-Host "VM not found: $vmName"
    #}


    # Delete Residual backup files from backup server
    Invoke-Command -ComputerName "MRA-Backup.cloud.local" -Credential $credscld -ScriptBlock {
        param($folderName)

        # Check if $folderName is not empty or just whitespace
        if (-not [string]::IsNullOrWhiteSpace($folderName)) {
            $parentPath = "E:\MirrorBackups"

            # Get all folders named $folderName in the parent path
            $foldersToDelete = Get-ChildItem -Path $parentPath -Filter $folderName -Recurse | Where-Object { $_.PSIsContainer }

            # Delete each $folderName folder
            foreach ($folder in $foldersToDelete) {
                Remove-Item -Path $folder.FullName -Recurse -Force
            }
            Write-Host "Backup Data for $folderName Deleted Successfully."
        } else {
            Write-Host "Skipping deletion for empty folder name."
        }
    } -ArgumentList $vmName
}