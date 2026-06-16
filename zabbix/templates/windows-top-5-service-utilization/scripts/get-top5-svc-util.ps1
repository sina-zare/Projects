Param(
  [int]$IntervalSeconds = 1,
  [int]$TopN = 5
)

# Get running services that have a ProcessId
$services = Get-CimInstance -ClassName Win32_Service |
            Where-Object { $_.State -eq 'Running' -and $_.ProcessId -ne 0 } |
            Select-Object Name, DisplayName, ProcessId

# Map PID -> list of services
$map = @{ }
foreach ($s in $services) {
    $procId = $s.ProcessId
    if (-not $map.ContainsKey($procId)) { $map[$procId] = @() }
    $map[$procId] += $s.Name
}

# Initial snapshot of CPU and WorkingSet
$initial = @{ }
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

# Prepare per-PID results
$results   = @()
$procCount = [Environment]::ProcessorCount
$totalMem  = try { [double](Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory } catch { 0.0 }

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

        # Memory percent per PID (we'll re-calc per-group from aggregated MemoryMB for accuracy)
        $memMB = [math]::Round($ws2 / 1MB, 2)

        $results += [PSCustomObject]@{
            RawSvcNames      = ($map[$procId] -join ",")
            PID              = $procId
            PROCNAME         = $initial[$procId].Name
            CPU              = [math]::Round($cpuPercent, 2)
            MemoryMB         = $memMB
        }
    } catch {
        # process gone — ignore
    }
}

# Aggregate by PROCNAME
$grouped = @{}

foreach ($r in $results) {
    $name = $r.PROCNAME
    if (-not $grouped.ContainsKey($name)) {
        $grouped[$name] = [PSCustomObject]@{
            PROCNAME     = $name
            PIDS         = @()
            SVCNAMES     = @()
            CPU          = 0.0
            MemoryMB     = 0.0
            Count        = 0
        }
    }
    $g = $grouped[$name]
    $g.CPU      = $g.CPU + ($r.CPU -as [double])
    $g.MemoryMB = $g.MemoryMB + ($r.MemoryMB -as [double])
    $g.PIDS     = $g.PIDS + ,([string]$r.PID)
    if ($r.RawSvcNames) {
        # RawSvcNames may be comma-separated list; add each unique service name
        $parts = $r.RawSvcNames -split '\s*,\s*' | Where-Object { $_ -ne '' }
        foreach ($p in $parts) {
            if (-not ($g.SVCNAMES -contains $p)) { $g.SVCNAMES += $p }
        }
    }
    $g.Count = $g.Count + 1
}

# Build LLD entries from groups
$data = @()
foreach ($k in $grouped.Keys) {
    $g = $grouped[$k]
    # compute MemoryPercent from aggregated MemoryMB for accuracy
    $memPercent = 0.0
    if ($totalMem -gt 0) {
        $memPercent = [math]::Round((($g.MemoryMB * 1MB) / $totalMem) * 100.0, 2)
    }
    $data += [PSCustomObject]@{
        "{#PROCNAME}"     = $g.PROCNAME
        "{#SVCNAME}"      = ($g.SVCNAMES -join ",")
        "{#PIDS}"         = ($g.PIDS -join ",")
        "CPU"             = [math]::Round($g.CPU, 2)
        "MemoryMB"        = [math]::Round($g.MemoryMB, 2)
        "MemoryPercent"   = $memPercent
    }
}

# Select top N by CPU then MemoryMB
$top = @()
if ($data.Count -gt 0) {
    $top = $data |
           Sort-Object -Property @{Expression='CPU';Descending=$true}, @{Expression='MemoryMB';Descending=$true} |
           Select-Object -First $TopN
}

# Emit JSON for Zabbix LLD: always produce {"data":[ ... ]}
$lld = @{ data = $top }
$lld | ConvertTo-Json -Depth 6 -Compress
