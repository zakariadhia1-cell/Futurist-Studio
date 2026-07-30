#!/usr/bin/env bash
# Restores a Postgres dump produced by backup.sh, into the running docker-compose stack.
#
# Redis is intentionally NOT restored here: it holds cache/pub-sub state, not data of
# record (architecture doc, section 1.3), so silently overwriting a live redis_data
# volume from an old snapshot is more likely to cause confusion (stale rate-limit
# counters, etc.) than help. To restore it anyway: stop the redis container, replace its
# /data/dump.rdb with the snapshot from backup.sh, then start it again.
#
# Usage: ./restore.sh path/to/postgres-TIMESTAMP.sql.gz
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <postgres-backup.sql.gz>" >&2
  exit 1
fi

DUMP_FILE="$1"
if [ ! -f "$DUMP_FILE" ]; then
  echo "Datei nicht gefunden: $DUMP_FILE" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
cd "$INFRA_DIR"

POSTGRES_USER="${POSTGRES_USER:-futurist}"
POSTGRES_DB="${POSTGRES_DB:-futurist_os}"

read -r -p "Dies ueberschreibt die Datenbank '$POSTGRES_DB' vollstaendig. Fortfahren? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "Abgebrochen."
  exit 1
fi

echo "==> Stelle '$POSTGRES_DB' aus $DUMP_FILE wieder her..."
gunzip -c "$DUMP_FILE" | docker compose exec -T postgres psql -U "$POSTGRES_USER" "$POSTGRES_DB"
echo "==> Fertig."
