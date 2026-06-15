#!/bin/bash

# --- Configuration ---
RESTIC_PASSWORD="ik.cv67" # Restic repo password
RESTIC_REST_USERNAME='bktest'
RESTIC_REST_PASSWORD='bkt3tt3t'
RESTIC_REPO="rest:http://$RESTIC_REST_USERNAME:$RESTIC_REST_PASSWORD@172.17.234.20:8010/$RESTIC_REST_USERNAME/me-powerdns-tst_pg"
#PG_USER="pdns_user"
#PG_DATABASE="powerdns"
PG_PASS="eraCryAsATiOnEN"
DUMP_FILE="/tmp/pg_dump.sql"
RESTIC_CACHE_DIR="/var/cache/restic"  # Persistent cache location
RESTIC_RESTORE_DIR="/tmp/restic_restore"

# --- Initialize Restic if repo doesn't exist ---
init_restic_repo() {
    echo "Checking if restic repository exists..."
    if ! docker run --rm \
        -e RESTIC_REPOSITORY="$RESTIC_REPO" \
        -e RESTIC_PASSWORD="$RESTIC_PASSWORD" \
        -v "$RESTIC_CACHE_DIR:/var/cache/restic" \
        restic/restic \
        cat config ; then

        echo "Repository not found. Initializing..."
        docker run --rm \
            -e RESTIC_REPOSITORY="$RESTIC_REPO" \
            -e RESTIC_PASSWORD="$RESTIC_PASSWORD" \
            -v "$RESTIC_CACHE_DIR:/var/cache/restic" \
            restic/restic \
            init
        if [ $? -ne 0 ]; then
            echo "❌ Failed to initialize restic repository!"
            exit 1
        fi
    else
        echo "✅ Repository exists. Proceeding..."
    fi
}

# --- Run pg_dump and restic backup ---
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
    docker run --rm \
        -e RESTIC_REPOSITORY="$RESTIC_REPO" \
        -e RESTIC_PASSWORD="$RESTIC_PASSWORD" \
        -v "$DUMP_FILE:/$DUMP_FILE" \
        -v "$RESTIC_CACHE_DIR:/var/cache/restic" \
        restic/restic \
        backup --host $HOSTNAME "$DUMP_FILE"
    if [ $? -ne 0 ]; then
        echo "❌ Restic backup failed!"
        exit 1
    fi

    echo "✅ Backup completed successfully!"
}

pgdump_remote_backup() {
    echo "Dumping PostgreSQL database from remote server and caching it on this server."

    ssh user@server-b-ip "PGPASSWORD='$PG_PASS' pg_dumpall -U postgres" > "$DUMP_FILE"

    if [ $? -ne 0 ]; then
        echo "❌ Remote pg_dump failed!"
        exit 1
    fi
}


pgdump_backup_streamed() {

    echo "Dumping PostgreSQL database and backing up using stream..."

    TMPDIR=$(mktemp -d)
    PIPE="$TMPDIR/pg_dump.sql"

    # Create a named pipe
    mkfifo "$PIPE"

    # Start pg_dumpall and write to the pipe
    PGPASSWORD="$PG_PASS" pg_dumpall -U postgres -h localhost > "$PIPE" &
    PG_PID=$!

    # Start restic docker backup using the pipe
    docker run --rm \
        -e RESTIC_REPOSITORY="$RESTIC_REPO" \
        -e RESTIC_PASSWORD="$RESTIC_PASSWORD" \
        -v "$PIPE:/pg_dump.sql" \
        -v "$RESTIC_CACHE_DIR:/var/cache/restic" \
        restic/restic \
        backup /pg_dump.sql

    # Wait for pg_dumpall to finish
    wait $PG_PID
    RETVAL=$?

    # Cleanup
    rm -f "$PIPE"
    rmdir "$TMPDIR"

    if [ $RETVAL -ne 0 ]; then
        echo "❌ pg_dumpall or restic backup failed!"
        exit 1
    fi

    echo "✅ Streamed backup completed successfully!"
}

restore_backup() {

    echo "Restoring with restic..."
    docker run --rm \
        -e RESTIC_REPOSITORY="$RESTIC_REPO" \
        -e RESTIC_PASSWORD="$RESTIC_PASSWORD" \
        -v "$RESTIC_RESTORE_DIR:/restore" \
        -v "$RESTIC_CACHE_DIR:/var/cache/restic" \
        restic/restic \
        restore latest --host $HOSTNAME  --verify --target "/restore"
    if [ $? -ne 0 ]; then
        echo "❌ Restic restore failed!"
        exit 1
    fi

    echo "✅ Backup restore completed successfully into: $RESTIC_RESTORE_DIR"
}

list_backups() {
    echo "Listing backups:"
    docker run --rm \
        -e RESTIC_REPOSITORY="$RESTIC_REPO" \
        -e RESTIC_PASSWORD="$RESTIC_PASSWORD" \
        -v "$RESTIC_CACHE_DIR:/var/cache/restic" \
        restic/restic \
        snapshots
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
    #backup)
    #  echo backing up
    #  init_restic_repo
    #  #pgdump_backup_streamed
    #  pgdump_backup
    #  run_backup
    #  cleanup
    #  ;;
    backup)
      echo backing up
      init_restic_repo
      pgdump_remote_backup  # creates the file locally on Server A
      run_backup            # backs up that file using restic
      cleanup
      ;;
    restore)
      echo restoring
      restore_backup
      ;;
    list)
      echo listing
      list_backups
      ;;
    *)
      echo "Invalid argument: $1"
      echo "Usage: $0 [backup|restore|list]"
      exit 1
      ;;
esac

exit 0

