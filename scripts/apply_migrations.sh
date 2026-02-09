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
if [ -f db/migrations/005_auth.sql ]; then
  psql "${DB_URL}" -f db/migrations/005_auth.sql
fi
if [ -f db/migrations/006_webauthn.sql ]; then
  psql "${DB_URL}" -f db/migrations/006_webauthn.sql
fi
if [ -f db/migrations/007_settings.sql ]; then
  psql "${DB_URL}" -f db/migrations/007_settings.sql
fi
if [ -f db/migrations/008_multitenant_flag.sql ]; then
  psql "${DB_URL}" -f db/migrations/008_multitenant_flag.sql
fi
if [ -f db/migrations/003_seed_dev.sql ]; then
  psql "${DB_URL}" -f db/migrations/003_seed_dev.sql
fi
if [ -f db/migrations/009_idp_roles.sql ]; then
  psql "${DB_URL}" -f db/migrations/009_idp_roles.sql
fi
if [ -f db/migrations/010_saml_logs.sql ]; then
  psql "${DB_URL}" -f db/migrations/010_saml_logs.sql
fi
if [ -f db/migrations/011_auth_pref.sql ]; then
  psql "${DB_URL}" -f db/migrations/011_auth_pref.sql
fi
if [ -f db/migrations/012_trust_meta.sql ]; then
  psql "${DB_URL}" -f db/migrations/012_trust_meta.sql
fi
if [ -f db/migrations/013_trust_request_status.sql ]; then
  psql "${DB_URL}" -f db/migrations/013_trust_request_status.sql
fi
if [ -f db/migrations/014_smtp_per_tenant.sql ]; then
  psql "${DB_URL}" -f db/migrations/014_smtp_per_tenant.sql
fi

echo "Migrations applied."
