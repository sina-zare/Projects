$AAA = Import-Csv -Path "C:\Temp\newCustomers-National-Code.csv"

$ZZZ = @()
ForEach ($AA IN $AAA) {
    TRY {
        # Get-VM -Name $($AA.VMName).Trim().Replace(' ','') -ErrorAction Stop
        Get-VM -Name $($AA.VMName).Trim().Replace(' ','') -ErrorAction Stop | 
            Set-Annotation -CustomAttribute 'National ID' -Value $($AA.NationalID).Trim()
    }
    CATCH {
        $ZZZ += $AA
    }
}

$ZZZ | Export-Csv -Path C:\Temp\Customers-National-Code-ZZZ.CSV -NoTypeInformation -Encoding UTF8 -Force -Confirm:$False
