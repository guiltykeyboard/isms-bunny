#!/usr/bin/env bash
set -euo pipefail

DB_URL="${DATABASE_URL:-postgresql://isms:isms@localhost:5432/isms}"

echo "Applying migrations to ${DB_URL}"

for file in $(ls db/migrations/*.sql | sort); do
  echo "Applying $file"
  psql -v ON_ERROR_STOP=1 "${DB_URL}" -f "$file"
done

echo "Migrations applied."
