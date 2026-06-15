#!/bin/bash

# --- Configuration ---
RESTIC_PASSWORD="Qotg61W2lu121pNs" # Restic repo password
RESTIC_REST_USERNAME='me-zabbix-db-user'
RESTIC_REST_PASSWORD='p7DgwFtH2Y2RCwa1'
RESTIC_REPO="rest:http://$RESTIC_REST_USERNAME:$RESTIC_REST_PASSWORD@172.17.234.20:8010/$RESTIC_REST_USERNAME"
PG_PASS="O!-%IBW326Dokla"
DUMP_FILE="/tmp/pg_dump.sql"
RESTIC_CACHE_DIR="/var/cache/restic"
RESTIC_RESTORE_DIR="/tmp/restic_restore"

export RESTIC_REPOSITORY="$RESTIC_REPO"
export RESTIC_PASSWORD="$RESTIC_PASSWORD"
export RESTIC_CACHE_DIR="$RESTIC_CACHE_DIR"

# --- Initialize Restic if repo doesn't exist ---
init_restic_repo() {
    echo "Checking if restic repository exists..."
    if ! restic cat config >/dev/null 2>&1; then
        echo "Repository not found. Initializing..."
        restic init
        if [ $? -ne 0 ]; then
            echo "❌ Failed to initialize restic repository!"
            exit 1
        fi
    else
        echo "✅ Repository exists. Proceeding..."
    fi
}

# --- Run pg_dumpall and restic backup ---
pgdump_backup() {
    echo "Dumping PostgreSQL database..."
    PGPASSWORD="$PG_PASS" pg_dumpall -U postgres -h localhost -f "$DUMP_FILE"
    if [ $? -ne 0 ]; then
        echo "❌ pg_dump failed!"
        exit 1
    fi
}

run_backup() {
    echo "Backing up with restic..."
    restic backup --host "$HOSTNAME" "$DUMP_FILE"
    if [ $? -ne 0 ]; then
        echo "❌ Restic backup failed!"
        exit 1
    fi
    echo "✅ Backup completed successfully!"
}

pgdump_backup_streamed() {
    echo "Dumping PostgreSQL database and backing up using stream..."
    TMPDIR=$(mktemp -d)
    PIPE="$TMPDIR/pg_dump.sql"

    mkfifo "$PIPE"
    PGPASSWORD="$PG_PASS" pg_dumpall -U postgres -h localhost > "$PIPE" &
    PG_PID=$!

    restic backup "$PIPE"
    RETVAL=$?

    wait $PG_PID
    rm -f "$PIPE"
    rmdir "$TMPDIR"

    if [ $RETVAL -ne 0 ]; then
        echo "❌ pg_dumpall or restic backup failed!"
        exit 1
    fi

    echo "✅ Streamed backup completed successfully!"
}

pgdump_backup_remote() {

  FILE_PATH="input.txt"

  # Read file into an array
  mapfile -t lines < "$FILE_PATH"

  # Loop through each line
  for line in "${lines[@]}"; do
      server_name="${line%%:*}"   # Everything before the colon
      ip_address="${line##*:}"    # Everything after the colon

      echo "Server Name: $server_name, IP Address: $ip_address"
  done


  DUMP_PATH="/home/sysops/dump-tmp/sina_pg_dump.sql"
  REMOTE_HOST="172.29.48.2"
  REMOTE_USER="sysops"
  SSH_KEY="/home/sysops/.ssh/id_ed25519_pgbackup"

  echo "Starting PostgreSQL dump from $REMOTE_HOST..."

  # Clear old dump if exists
  #rm -f "$DUMP_PATH"

  # Start SSH pg_dumpall in background and write to file
  ssh -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST" "pg_dumpall -U postgres -h localhost" > "$DUMP_PATH" &

  # Get PID of background SSH process
  PID=$!

  # Track file size in real-time
  echo "Tracking dump file at: $DUMP_PATH"
  while kill -0 $PID 2>/dev/null; do
      ls -lh "$DUMP_PATH"
      sleep 2
  done

  echo "✅ Dump completed."
  ls -lh "$DUMP_PATH"

}
restore_backup() {
    echo "Restoring with restic..."
    mkdir -p "$RESTIC_RESTORE_DIR"
    restic restore latest --host "$HOSTNAME" --verify --target "$RESTIC_RESTORE_DIR"
    if [ $? -ne 0 ]; then
        echo "❌ Restic restore failed!"
        exit 1
    fi
    echo "✅ Backup restore completed successfully into: $RESTIC_RESTORE_DIR"
}

list_backups() {
    echo "Listing backups:"
    restic snapshots
}

# --- Cleanup ---
cleanup() {
    echo "Cleaning up..."
    rm -f "$DUMP_FILE"
}

# --- Main Execution ---
if [[ $# -ne 1 ]]; then
    echo 'Too many/few arguments, expecting one [backup | restore | list]' >&2
    exit 1
fi

case $1 in
    backup)
        echo "Backing up..."
        init_restic_repo
        pgdump_backup_streamed
        run_backup
        cleanup
        ;;
    restore)
        echo "Restoring..."
        restore_backup
        ;;
    list)
        echo "Listing..."
        list_backups
        ;;
    *)
        echo "Invalid argument: $1"
        echo "Usage: $0 [backup|restore|list]"
        exit 1
        ;;
esac

exit 0
