Param(
  [int]$TopN = 5
)

$totalMem = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory
$results = @()

# Collect per-PID memory usage (use PrivateMemorySize64)
Get-Process | ForEach-Object {
    try {
        $results += [PSCustomObject]@{
            "{#PROCNAME}" = $_.ProcessName
            "{#PID}"      = $_.Id
            MemoryBytes   = $_.PrivateMemorySize64
        }
    } catch {}
}

# Aggregate by process name (case-insensitive)
$aggregated = $results |
    Group-Object -Property @{ Expression = { $_."{#PROCNAME}".ToLowerInvariant() } } |
    ForEach-Object {
        $group = $_.Group
        $displayName = $group[0]."{#PROCNAME}"
        $memSumBytes = ($group | Measure-Object -Property MemoryBytes -Sum).Sum
        $memMB = [math]::Round($memSumBytes / 1MB, 2)
        $memPercent = [math]::Round(($memSumBytes / $totalMem) * 100, 2)

        [PSCustomObject]@{
            "{#PROCNAME}"   = $displayName
            MemoryMB        = $memMB
            MemoryPercent   = $memPercent
        }
    }

# Top N by summed MemoryMB
$top = $aggregated | Sort-Object -Property MemoryMB -Descending | Select-Object -First $TopN
@{ data = $top } | ConvertTo-Json -Depth 5 -Compress
