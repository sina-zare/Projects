from colorama import Fore, Style, init
from tabulate import tabulate

init(autoreset=True)

# Example restic_clients dictionary
restic_clients = {
    1: {'host_name': 'db-server-1', 'backup_type': 'psql', 'backup_dir': None},
    2: {'host_name': 'web-server-1', 'backup_type': 'dir', 'backup_dir': '/var/www/html'},
    3: {'host_name': 'app-server-1', 'backup_type': 'dir', 'backup_dir': '/opt/app/data'},
}

# Build the table data
table_data = []
for i, host in enumerate(restic_clients.values(), 1):
    hostname = Fore.CYAN + host['host_name'] + Style.RESET_ALL
    backup_type = (
        Fore.YELLOW + host['backup_type'] + Style.RESET_ALL
        if host['backup_type'] == 'dir'
        else Fore.GREEN + host['backup_type'] + Style.RESET_ALL
    )
    backup_dir = (
        Fore.MAGENTA + "PostgreSQL dump" + Style.RESET_ALL
        if host['backup_type'] == 'psql'
        else Fore.MAGENTA + host['backup_dir'] + Style.RESET_ALL
    )
    table_data.append([i, hostname, backup_type, backup_dir])

# Print the prompt with the table
print("Select one host ID to backup:\n")
print(tabulate(table_data, headers=["ID", "Hostname", "Backup Type", "Backup Dir/File"], tablefmt="rounded_outline"))


choice = input("\nEnter your choice: ")
