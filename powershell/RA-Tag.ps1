# Connect to vCenter and retrieve VMs matching the criteria
Connect-VIServer -Server mra-vc01.abramad.com –User cloud\sina.z –Password “S@Bw00fer20936742”
$vms = Get-VM -Name 'RA-*' 

# Set the path to the folder where you want to find the latest folder created
$FolderPath = "C:\Users\sina.z\Desktop\RahkaranAbriReport"


# Get the latest folder created in the specified path
$LatestFolder = Get-ChildItem -Path $FolderPath | Sort-Object -Property CreationTime -Descending | Select-Object -First 1

# Set the static part of the filename
$StaticPart = "RA-Tag"

# Set the dynamic part of the filename to be the name of the latest folder created
$DynamicPart = $LatestFolder.Name

# Combine the static and dynamic parts of the filename to create the full filename
$FileName = $StaticPart + "-" + $DynamicPart + ".csv"

#create file path
$FilePath = $FolderPath + '\' + $LatestFolder + '\' + $FileName

# Create empty hashtables to hold the tag data
$farsi_tag_data = @{}
$mou_tag_data = @{}

# Iterate through each VM and retrieve the FarsiName and MoU tag values
foreach ($vm in $vms) {
    $farsi_tag = Get-TagAssignment -Entity $vm -Category 'FarsiName'
    $mou_tag = Get-TagAssignment -Entity $vm -Category 'MoU'
    if ($farsi_tag) {
        $farsi_tag_data[$vm.Name] = $farsi_tag.Tag.Name
    }
    if ($mou_tag) {
        $mou_tag_data[$vm.Name] = $mou_tag.Tag.Name
    }
}

# Create a PSCustomObject with the tag data and export it to a CSV file
$vm_data = foreach ($vm in $vms) {
    [PSCustomObject] @{
        Name = $vm.Name
        MoU = $mou_tag_data[$vm.Name]
        FarsiName = $farsi_tag_data[$vm.Name]
        
    }
}

# Export the VM data to a CSV file that supports Unicode
$vm_data | Export-Csv -Path $FilePath -Encoding Unicode -NoTypeInformation
