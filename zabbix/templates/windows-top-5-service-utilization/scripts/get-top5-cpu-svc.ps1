Param(
  [int]$IntervalSeconds = 1,
  [int]$TopN = 5
)

# Initial snapshot
$initial = @{}
foreach ($p in Get-Process) {
    try {
        $initial[$p.Id] = $p.CPU
    } catch {}
}

Start-Sleep -Seconds $IntervalSeconds

$procCount = [Environment]::ProcessorCount
$results = @()

foreach ($p in Get-Process) {
    try {
        $cpu1 = if ($initial.ContainsKey($p.Id)) { $initial[$p.Id] } else { 0.0 }
        $cpu2 = if ($p.CPU) { [double]$p.CPU } else { 0.0 }
        $cpuDelta = $cpu2 - $cpu1

        $cpuPercent = 0.0
        if ($IntervalSeconds -gt 0 -and $cpuDelta -gt 0) {
            $cpuPercent = ($cpuDelta / $IntervalSeconds) / $procCount * 100.0
        }

        $results += [PSCustomObject]@{
            "{#PROCNAME}" = $p.ProcessName
            "{#PID}"      = $p.Id
            CPU           = [math]::Round($cpuPercent, 2)
        }
    } catch {}
}

# Aggregate CPU by process name (case-insensitive grouping)
$aggregated = $results |
    Group-Object -Property @{ Expression = { $_."{#PROCNAME}".ToLowerInvariant() } } |
    ForEach-Object {
        $group = $_.Group
        $displayName = $group[0]."{#PROCNAME}"
        $cpuSum = ($group | Measure-Object -Property CPU -Sum).Sum
        [PSCustomObject]@{
            "{#PROCNAME}" = $displayName
            CPU           = [math]::Round([double]$cpuSum, 2)
        }
    }

$top = $aggregated | Sort-Object -Property CPU -Descending | Select-Object -First $TopN
@{ data = $top } | ConvertTo-Json -Depth 5 -Compress
