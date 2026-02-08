#!/usr/bin/env bash
set -euo pipefail

DB_URL="${DATABASE_URL:-postgresql://isms:isms@localhost:5432/isms}"

echo "Applying migrations to ${DB_URL}"

psql "${DB_URL}" -f db/migrations/001_init.sql
if [ -f db/migrations/002_user_theme_pref.sql ]; then
  psql "${DB_URL}" -f db/migrations/002_user_theme_pref.sql
fi

echo "Migrations applied."
