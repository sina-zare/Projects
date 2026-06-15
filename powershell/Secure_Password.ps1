# Exporting Password

# Prompt for the password
$password = Read-Host "Enter Password" -AsSecureString

# Convert the secure string to an encrypted standard string and save to a file
$password | ConvertFrom-SecureString | Set-Content "C:\Users\sina.z\Desktop\Python\FinanceTeamReport.txt"


################################

# Importing Password

# Read the encoded password from the file
$securePassword = Get-Content "C:\Users\sina.z\Desktop\Python\FinanceTeamReport.txt" | ConvertTo-SecureString

# If the command you're using accepts a SecureString, you can use it directly
# Example: Using the secure password with `Get-Credential`
$credential = New-Object System.Management.Automation.PSCredential("username", $securePassword)

# If you need the plain text password (less secure), convert it to plain text
$plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
)

# Example usage of the plain text password
Write-Host "The password is: $plainPassword"
