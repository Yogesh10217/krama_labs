#!/usr/bin/env bash
# Backup script for Krama AI Database

set -euo pipefail

BACKUP_DIR="/var/backups/krama_db"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="krama_backup_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

if [[ -z "${DATABASE_URL:-}" ]]; then
    echo "Error: DATABASE_URL is not set."
    exit 1
fi

echo "Starting database backup to ${BACKUP_DIR}/${FILENAME}"

pg_dump "${DATABASE_URL}" | gzip > "${BACKUP_DIR}/${FILENAME}"

echo "Backup completed successfully."

# Optional: Clean up backups older than 30 days
find "${BACKUP_DIR}" -type f -name "*.sql.gz" -mtime +30 -exec rm {} \;
echo "Old backups cleaned up."
