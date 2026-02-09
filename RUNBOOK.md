# ISMS-Bunny Ops Runbook (quick)

## Secrets/keys
- JWT/refresh secrets: rotate `jwt_secret` / `secret_key` in `.env` and restart; rotate cookies by expiring sessions.
- OIDC/SAML: update provider configs via `/admin/providers` or setup wizard; keep IdP signing certs current.
- DB creds: change in the backing Postgres and update `DATABASE_URL` env.

## Backups
- Postgres: take regular `pg_dump` of the `isms` DB (volumes `db_data` in compose). Restore with `psql` and rerun migrations if needed.
- Caddy data: stored in named volumes `caddy_data`, `caddy_config`.
- Assets: stored in S3/BYO buckets—ensure external backups/retention there.

## S3 migration
Use `scripts/s3_migrate.py` to copy a tenant prefix between buckets:
```
python scripts/s3_migrate.py --tenant-id <uuid> \
  --source '{"bucket":"old","region":"us-east-1","endpoint":"https://s3.wasabisys.com","access_key":"...","secret_key":"..."}' \
  --dest   '{"bucket":"new","region":"us-east-1","endpoint":"https://s3.wasabisys.com","access_key":"...","secret_key":"..."}' \
  --prefix tenants/<tenant-id>
```
Use `--dry-run` to list without copying.

## Logs & troubleshooting
- SAML: view per-tenant logs at `/admin/saml-logs`; MSP admins can clear/view any tenant. Backend logs also stored in `saml_logs` table.
- Auth: use `/auth/method?email=` to see what the system will do for a user.

## CI
- Nightly runs lint + pytest with Postgres + migrations. Pip/npm audits and LOC badge run on push to main.

## First deploy
1) `docker compose -f infra/docker-compose.yml up -d`
2) Run `scripts/apply_migrations.sh` (or let app start and run migrations in CI step).
3) Go to `/setup` to create MSP tenant/admin and storage settings.
4) Add IdP configs and decide break-glass users; ensure allow_local_login toggle set appropriately.
