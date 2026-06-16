Param(
  [int]$IntervalSeconds = 1,
  [int]$TopN = 5
)

# Get running services that have a ProcessId
$services = Get-CimInstance -ClassName Win32_Service |
            Where-Object { $_.State -eq 'Running' -and $_.ProcessId -ne 0 } |
            Select-Object Name, DisplayName, ProcessId

# Map PID -> list of services
$map = @{}
foreach ($s in $services) {
    $procId = $s.ProcessId
    if (-not $map.ContainsKey($procId)) { $map[$procId] = @() }
    $map[$procId] += $s.Name
}

# Initial snapshot of CPU and WorkingSet
$initial = @{}
foreach ($procId in $map.Keys) {
    try {
        $p = Get-Process -Id $procId -ErrorAction Stop
        $initial[$procId] = [PSCustomObject]@{
            CPU  = if ($p.CPU) { [double]$p.CPU } else { 0.0 }
            WS   = if ($p.WorkingSet64) { [double]$p.WorkingSet64 } else { 0.0 }
            Name = $p.ProcessName
        }
    } catch {
        # process may exit between service enumeration and Get-Process
    }
}

# Sleep to measure CPU delta
Start-Sleep -Seconds $IntervalSeconds

# Prepare totals and results
$results   = @()
$procCount = [Environment]::ProcessorCount
$totalMem  = try { [double](Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory } catch { 0 }

foreach ($procId in $initial.Keys) {
    try {
        $p2 = Get-Process -Id $procId -ErrorAction Stop
        $cpu2 = if ($p2.CPU) { [double]$p2.CPU } else { 0.0 }
        $ws2  = if ($p2.WorkingSet64) { [double]$p2.WorkingSet64 } else { 0.0 }

        $cpuDelta = $cpu2 - $initial[$procId].CPU
        $cpuPercent = 0.0
        if ($IntervalSeconds -gt 0 -and $cpuDelta -gt 0) {
            # percent across all logical processors
            $cpuPercent = ($cpuDelta / $IntervalSeconds) / $procCount * 100.0
        }

        $memPercent = 0.0
        if ($totalMem -gt 0) {
            $memPercent = ($ws2 / $totalMem) * 100.0
        }

        $results += [PSCustomObject]@{
            "{#SVCNAME}"     = ($map[$procId] -join ",")
            "{#PID}"         = $procId
            "{#PROCNAME}"    = $initial[$procId].Name
            CPU              = [math]::Round($cpuPercent, 2)
            MemoryMB         = [math]::Round($ws2 / 1MB, 2)
            MemoryPercent    = [math]::Round($memPercent, 2)
        }
    } catch {
        # process gone — ignore
    }
}

# Select top N by CPU then Memory
$top = @()
if ($results.Count -gt 0) {
    $top = $results |
           Sort-Object -Property @{Expression='CPU';Descending=$true}, @{Expression='MemoryMB';Descending=$true} |
           Select-Object -First $TopN
}

# Emit JSON for Zabbix LLD; always output valid JSON (empty array if no results)
#if ($top -eq $null -or $top.Count -eq 0) {
#    Write-Output "[]"
#} else {
#    $top | ConvertTo-Json -Depth 4 -Compress
#}

# Emit JSON for Zabbix LLD: always produce {"data":[ ... ]}
$lld = @{ data = $top }
# Increase depth if needed; -Compress to make output compact
$lld | ConvertTo-Json -Depth 6 -Compress
