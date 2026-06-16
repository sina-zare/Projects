Param(
  [int]$TopN = 5
)

# Total physical memory in bytes
$totalMem = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory
$results  = @()

# Collect per-PID memory usage
Get-Process | ForEach-Object {
    try {
        $memMB = [math]::Round($_.WorkingSet64 / 1MB, 2)
        $results += [PSCustomObject]@{
            "{#PROCNAME}"   = $_.ProcessName
            "{#PID}"        = $_.Id
            MemoryMB        = $memMB
        }
    } catch {}
}

# Aggregate by process name (case-insensitive)
$aggregated = $results |
    Group-Object -Property @{ Expression = { $_."{#PROCNAME}".ToLowerInvariant() } } |
    ForEach-Object {
        $group = $_.Group
        $displayName = $group[0]."{#PROCNAME}"
        $memSum = ($group | Measure-Object -Property MemoryMB -Sum).Sum
        $memSumRounded = [math]::Round([double]$memSum, 2)

        # compute percent from summed MB -> convert back to bytes
        $memPercent = 0.0
        if ($totalMem -gt 0) {
            $memPercent = [math]::Round((($memSumRounded * 1MB) / $totalMem) * 100.0, 2)
        }

        [PSCustomObject]@{
            "{#PROCNAME}"   = $displayName
            MemoryMB        = $memSumRounded
            MemoryPercent   = $memPercent
        }
    }

# Top N by summed MemoryMB
$top = $aggregated | Sort-Object -Property MemoryMB -Descending | Select-Object -First $TopN
@{ data = $top } | ConvertTo-Json -Depth 5 -Compress
