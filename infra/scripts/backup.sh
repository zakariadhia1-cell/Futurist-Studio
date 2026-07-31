#!/usr/bin/env bash
# Nightly backup: a compressed pg_dump of the Postgres database plus a Redis RDB
# snapshot, both timestamped. Intended to run against the docker-compose stack (see
# ../docker-compose.yml) - invoke it via a host cron job, e.g.:
#   0 3 * * * cd /path/to/futurist-os/infra && ./scripts/backup.sh >> /var/log/futuristos-backup.log 2>&1
#
# Redis here is cache/pub-sub state, not data of record (see the architecture doc,
# section 1.3) - it's still snapshotted for completeness/fast recovery, but restore.sh
# deliberately only restores Postgres; see the comment there for why.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-$INFRA_DIR/backups}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
POSTGRES_USER="${POSTGRES_USER:-futurist}"
POSTGRES_DB="${POSTGRES_DB:-futurist_os}"

mkdir -p "$BACKUP_DIR"
cd "$INFRA_DIR"

echo "==> Sichere PostgreSQL-Datenbank '$POSTGRES_DB'..."
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
  | gzip > "$BACKUP_DIR/postgres-$TIMESTAMP.sql.gz"

echo "==> Erzwinge Redis-Snapshot (SAVE) und kopiere dump.rdb..."
docker compose exec -T redis redis-cli SAVE
docker compose cp redis:/data/dump.rdb "$BACKUP_DIR/redis-$TIMESTAMP.rdb"

echo "==> Fertig:"
echo "    $BACKUP_DIR/postgres-$TIMESTAMP.sql.gz"
echo "    $BACKUP_DIR/redis-$TIMESTAMP.rdb"
