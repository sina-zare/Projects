import subprocess
import datetime
import os
import signal

# List of (hostname, ip) pairs
hosts = [
    ("vra-host009","172.29.0.9"),
    ("vr4-host003","172.29.23.3"),
    ("vra-host023","172.29.0.23"),
    ("vra-host006","172.29.0.6"),
    ("vr4-host001","172.29.23.1"),
    ("vra-host005","172.29.0.5"),
    ("vra-host020","172.29.0.20"),
    ("vra-host027","172.29.0.27"),
    ("vr4-host002","172.29.23.2"),
    ("vra-host011","172.29.0.11"),
    ("vra-host001","172.29.0.1"),
    ("vra-host024","172.29.0.24"),
    ("vra-host004","172.29.0.4"),
    ("vra-host010","172.29.0.10"),
    ("vra-host029","172.29.0.29"),
    ("vra-host022","172.29.0.22"),
    ("vra-host028","172.29.0.28"),
    ("vra-host002","172.29.0.2"),
    ("vra-host021","172.29.0.21"),
    ("vra-host012","172.29.0.12"),
    ("vra-host003","172.29.0.3"),
    ("vra-host025","172.29.0.25"),
    ("vra-host026","172.29.0.26"),
    ("ved-host001","172.29.30.1"),
    ("ved-host003","172.29.30.3"),
    ("ved-host002","172.29.30.2"),
    ("vts-host002","172.29.46.2"),
    ("vts-host003","172.29.46.3"),
    ("vts-host001","172.29.46.1"),
    ("vab-mgmhost001","172.29.12.1"),
    ("vab-dcimhost001","10.1.5.1"),
    ("vab-host002","172.29.12.4"),
    ("vab-mgmhost002","172.29.12.3"),
    ("vab-host001","172.29.12.2"),
    ("vab-dcimhost002","10.1.5.2"),
    ("ved-host006","172.29.30.6"),
    ("ved-host007","172.29.30.7"),
    ("ved-host008","172.29.30.8"),
    ("ved-host009","172.29.30.9"),
    ("vab-host003","172.29.12.9"),
    ("vab-host004","172.29.12.10"),
    ("vk8s-host002","172.29.12.12"),
    ("vab-host022","172.29.12.22"),
    ("vab-host021","172.29.12.21"),
    ("vab-host020","172.29.12.20"),
    ("vra-host031","172.29.0.31"),
    ("vra-host030","172.29.0.30"),
    ("vda-host003","172.29.34.3"),
    ("vda-host001","172.29.34.1"),
    ("vda-host002","172.29.34.2"),
    ("vts-lab-host003","172.29.46.13"),
    ("vts-lab-host002","172.29.46.12"),
    ("vts-lab-host001","172.29.46.11"),
    ("vab-host005","172.29.12.23"),
    ("vra-host032","172.29.0.32"),
]

processes = []

for hostname, ip in hosts:
    outfile = f"{hostname}.ping"
    f = open(outfile, "a")

    # Spawn ping process
    process = subprocess.Popen(
        ["ping", ip],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    # Spawn a lightweight process to add timestamps per line
    def log_output(proc, file):
        for line in proc.stdout:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file.write(f"{timestamp} {line}")
            file.flush()

    import threading
    t = threading.Thread(target=log_output, args=(process, f), daemon=True)
    t.start()

    processes.append((process, f))

print(f"Started {len(processes)} ping processes in background.")

# Keep the script running like `nohup`
try:
    signal.pause()  # wait forever, until killed
except KeyboardInterrupt:
    print("Stopping all ping processes...")
    for proc, f in processes:
        proc.terminate()
        f.close()
