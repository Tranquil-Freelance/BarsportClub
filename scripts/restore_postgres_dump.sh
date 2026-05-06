#!/usr/bin/env bash
# Restore a Postgres dump from the client into your local Barsport DB.
#
# Usage:
#   ./scripts/restore_postgres_dump.sh /path/to/backup.sql
#   ./scripts/restore_postgres_dump.sh /path/to/backup.dump   # custom format
#   ./scripts/restore_postgres_dump.sh /path/to/backup.sql xpalermostat
#
# Prerequisites:
#   - PostgreSQL running (e.g. brew services start postgresql@15)
#   - Stop the backend (uvicorn) before restore so no connections block DROP.
#
# Reads: backend/.env — POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_SERVER, POSTGRES_PORT, POSTGRES_DB

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${ROOT}/backend/.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE" >&2
  exit 1
fi

# Load POSTGRES_* from backend/.env (strip CRLF; value may contain '=')
while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line//$'\r'/}"
  [[ "$line" =~ ^# ]] && continue
  [[ -z "${line// }" ]] && continue
  case "$line" in
    POSTGRES_USER=*)      POSTGRES_USER="${line#POSTGRES_USER=}" ;;
    POSTGRES_PASSWORD=*)  POSTGRES_PASSWORD="${line#POSTGRES_PASSWORD=}" ;;
    POSTGRES_SERVER=*)    POSTGRES_SERVER="${line#POSTGRES_SERVER=}" ;;
    POSTGRES_PORT=*)      POSTGRES_PORT="${line#POSTGRES_PORT=}" ;;
    POSTGRES_DB=*)        POSTGRES_DB="${line#POSTGRES_DB=}" ;;
  esac
done < "$ENV_FILE"

PGUSER="${POSTGRES_USER:-postgres}"
PGPASSWORD="${POSTGRES_PASSWORD:-}"
PGHOST="${POSTGRES_SERVER:-127.0.0.1}"
PGPORT="${POSTGRES_PORT:-5432}"
DEFAULT_DB="${POSTGRES_DB:-xpalermostat_db}"

DUMP_PATH="${1:-}"
TARGET_DB="${2:-$DEFAULT_DB}"

if [[ -z "$DUMP_PATH" || ! -f "$DUMP_PATH" ]]; then
  echo "Usage: $0 <dump.sql|dump.dump|dump.backup> [target_database_name]" >&2
  echo "Example: $0 ~/Downloads/barsport_backup.sql" >&2
  exit 1
fi

export PGPASSWORD PGUSER PGHOST PGPORT

PSQL="$(command -v psql || true)"
if [[ -z "$PSQL" && -x /opt/homebrew/opt/postgresql@15/bin/psql ]]; then
  PSQL="/opt/homebrew/opt/postgresql@15/bin/psql"
fi
if [[ -z "$PSQL" ]]; then
  echo "psql not found. Install Postgres (e.g. brew install postgresql@15) or add psql to PATH." >&2
  exit 1
fi

# Prefer newest Homebrew pg_restore (PG16 dumps need PG16+ client even if server is older)
PG_RESTORE=""
for CAND in \
  /opt/homebrew/opt/postgresql@17/bin/pg_restore \
  /opt/homebrew/opt/postgresql@16/bin/pg_restore \
  /opt/homebrew/opt/postgresql@15/bin/pg_restore; do
  if [[ -x "$CAND" ]]; then
    PG_RESTORE="$CAND"
    break
  fi
done
if [[ -z "$PG_RESTORE" ]]; then
  PG_RESTORE="$(command -v pg_restore || true)"
fi

echo "→ Host: $PGHOST:$PGPORT  User: $PGUSER  Target DB: $TARGET_DB"
echo "→ Dump:  $DUMP_PATH"

# Terminate other sessions on this DB so DROP / restore can proceed
"$PSQL" -d postgres -v ON_ERROR_STOP=1 <<SQL
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '${TARGET_DB}' AND pid <> pg_backend_pid();
SQL

"$PSQL" -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS \"${TARGET_DB}\";"
"$PSQL" -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE \"${TARGET_DB}\" OWNER \"${PGUSER}\";"

EXT="${DUMP_PATH##*.}"
# Custom-format pg_dump (-Fc) files are often misnamed as .sql — detect by magic bytes
DUMP_KIND="plain"
if command -v file >/dev/null 2>&1 && file -b "$DUMP_PATH" 2>/dev/null | grep -qi 'PostgreSQL custom database dump'; then
  DUMP_KIND="custom"
fi

shopt -s nocasematch
if [[ "$DUMP_KIND" == "custom" ]]; then
  if [[ -z "$PG_RESTORE" ]]; then
    echo "pg_restore not found; install postgresql client tools." >&2
    exit 1
  fi
  echo "→ Restoring custom-format archive with pg_restore..."
  "$PG_RESTORE" --verbose --no-owner --no-acl -d "$TARGET_DB" "$DUMP_PATH"
else
  case "$EXT" in
    sql)
      echo "→ Restoring plain SQL with psql..."
      "$PSQL" -d "$TARGET_DB" -v ON_ERROR_STOP=1 -f "$DUMP_PATH"
      ;;
    dump|backup)
      if [[ -z "$PG_RESTORE" ]]; then
        echo "pg_restore not found; install postgresql client tools." >&2
        exit 1
      fi
      echo "→ Restoring custom-format archive with pg_restore..."
      "$PG_RESTORE" --verbose --no-owner --no-acl -d "$TARGET_DB" "$DUMP_PATH"
      ;;
    *)
      echo "Unknown extension .$EXT — use .sql or custom .dump from pg_dump -Fc" >&2
      exit 1
      ;;
  esac
fi
shopt -u nocasematch

echo ""
echo "Done. Ensure backend/.env has:"
echo "  POSTGRES_DB=${TARGET_DB}"
echo "  DATABASE_URL=postgresql+asyncpg://${PGUSER}:***@${PGHOST}:${PGPORT}/${TARGET_DB}"
echo ""
echo "Restart uvicorn, then: curl -s \"http://127.0.0.1:8000/api/meritometro/standings?league=Serie%20A\""
