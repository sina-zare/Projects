<#
Generates CPU and memory load by spawning background PowerShell worker processes.
Outputs worker PIDs to C:\temp\test_pids.txt for later monitoring.
#>

param(
  [int]$Workers = 4,                      # number of worker processes
  [int]$CpuPercentPerWorker = 110,         # approx CPU percent per worker (0-100)
  [int]$MemoryMBPerWorker = 7000,          # memory to allocate per worker (MB)
  [int]$DurationSeconds = 300             # how long workers run (seconds)
)

$pidFile = 'C:\temp\test_pids.txt'
New-Item -Path (Split-Path $pidFile) -ItemType Directory -Force | Out-Null
if (Test-Path $pidFile) { Remove-Item $pidFile -Force }

Write-Host "Spawning $Workers workers; approx $CpuPercentPerWorker% CPU per worker; $MemoryMBPerWorker MB each; duration $DurationSeconds s."

# Helper: scriptblock for worker process
$workerCode = @'
param($cpuPct,$memMB,$duration)
# Convert to numeric
$cpuPct = [double]$cpuPct
$memMB = [int]$memMB
$duration = [int]$duration

# allocate memory
if ($memMB -gt 0) {
  try {
    # allocate a single big byte[] to use memory
    $bytes = New-Object byte[] ($memMB * 1MB)
    # touch memory to ensure OS allocates pages
    for ($i=0; $i -lt $bytes.Length; $i += 4096) { $bytes[$i] = 1 }
  } catch {
    # ignore allocation failure
  }
}

# approximate CPU busy/sleep cycle
# We will busy-wait for busyMs and sleep for idleMs in a loop.
# busyFraction = cpuPct/100.0
$busyFraction = [Math]::Min([Math]::Max($cpuPct/100.0, 0.0), 0.99)
if ($busyFraction -le 0) { Start-Sleep -Seconds $duration; exit 0 }

# base interval in ms - shorter interval yields smoother CPU control; keep not too small
$intervalMs = 200
$busyMs = [int]([Math]::Max(1, [Math]::Round($intervalMs * $busyFraction)))
$idleMs = [int]([Math]::Max(0, $intervalMs - $busyMs))

$sw = [System.Diagnostics.Stopwatch]::StartNew()
while ($sw.Elapsed.TotalSeconds -lt $duration) {
  $t0 = [System.Diagnostics.Stopwatch]::StartNew()
  # busy loop approximately busyMs
  while ($t0.ElapsedMilliseconds -lt $busyMs) {
    # simple math to keep CPU busy
    [math]::Sqrt(12345.6789) | Out-Null
  }
  if ($idleMs -gt 0) { Start-Sleep -Milliseconds $idleMs }
}
'@

# Start the workers as background PowerShell processes (not jobs) so they appear as processes
for ($i=1; $i -le $Workers; $i++) {
  $args = @(
    '-NoProfile','-WindowStyle','Hidden','-Command',
    "& { param(`$cpuPct,`$memMB,`$duration) $([ScriptBlock]::Create($workerCode)) -cpuPct `$cpuPct -memMB `$memMB -duration `$duration }",
    '--', $CpuPercentPerWorker, $MemoryMBPerWorker, $DurationSeconds
  )

  # Start-Process powershell and get PID
  $proc = Start-Process -FilePath "$PSHOME\powershell.exe" -ArgumentList $args -PassThru -WindowStyle Hidden
  Write-Host "Started worker PID $($proc.Id)"
  Add-Content -Path $pidFile -Value $proc.Id
}

Write-Host "Worker PIDs written to $pidFile"
