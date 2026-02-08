# ISMS-Bunny

Open-source, MSP-friendly ISMS and trust center scaffold. Goals:

- ISO 27001:2022 first, multi-tenant, security-first.
- Deployable with docker-compose (Caddy + FastAPI/Next.js + Postgres + Redis + S3-compatible storage).
- Trust page per tenant with custom domain and automatic TLS.

## Getting started (dev)

1. Copy `.env.example` to `.env` and adjust secrets/bucket values.
2. Build and run (dev):
   ```bash
   docker compose -f infra/docker-compose.yml up --build
   ```
3. Migrations: apply `db/migrations/001_init.sql` to the Postgres instance.
4. Open `http://localhost:8000/health` for a quick check.

## Structure
- `design/` — requirements, architecture, trust page notes, theme.
- `infra/` — docker-compose and Caddy placeholder.
- `app/` — FastAPI skeleton.
- `db/migrations/` — initial schema with RLS.
- `iso27001/` — starter content for ISO 27001 alignment.

## Theme
Dark purple primary, soft white text, dark grey surfaces (see `design/theme.md`).
