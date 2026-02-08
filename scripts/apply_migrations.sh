#!/usr/bin/env bash
set -euo pipefail

DB_URL="${DATABASE_URL:-postgresql://isms:isms@localhost:5432/isms}"

echo "Applying migrations to ${DB_URL}"

psql "${DB_URL}" -f db/migrations/001_init.sql
if [ -f db/migrations/002_user_theme_pref.sql ]; then
  psql "${DB_URL}" -f db/migrations/002_user_theme_pref.sql
fi
if [ -f db/migrations/004_tenant_type.sql ]; then
  psql "${DB_URL}" -f db/migrations/004_tenant_type.sql
fi
if [ -f db/migrations/003_seed_dev.sql ]; then
  psql "${DB_URL}" -f db/migrations/003_seed_dev.sql
fi

echo "Migrations applied."
