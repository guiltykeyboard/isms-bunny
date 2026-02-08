<p align="center">
  <img src="assets/logo.svg" alt="ISMS-Bunny logo" width="140">
</p>

<h1 align="center">ISMS-Bunny</h1>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white">
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white">
  <img alt="Redis" src="https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white">
  <img alt="Caddy" src="https://img.shields.io/badge/Caddy-2-2EAD6D">
  <img alt="Docker Compose" src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white">
  <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-000000">
</p>

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
   - For local dev you can run `scripts/apply_migrations.sh` (uses `DATABASE_URL` if set).
4. Open `http://localhost:8000/health` for a quick check.
5. Dev auth stub: send headers `X-User-Id: <uuid>` and optional `X-Is-Msp-Admin: true` to hit protected endpoints. Real auth to be added later.

Theme preference
- Modes: `system` (default, honors browser `prefers-color-scheme`), `dark`, `light`.
- API: `GET /users/me` returns `theme_preference`; `PATCH /users/me/theme` with `{"theme_preference":"dark"}` updates it.

Dev defaults
- Seeded tenant: `Dev Tenant` (`fqdn=localhost`, id `00000000-0000-0000-0000-000000000001`).
- Seeded MSP admin user: `admin@example.com` (id `00000000-0000-0000-0000-000000000002`, theme `system`).
- Host resolution: requests to `localhost` map to the seeded tenant; replace with real FQDNs in production.

## Structure
- `design/` — requirements, architecture, trust page notes, theme.
- `infra/` — docker-compose and Caddy placeholder.
- `app/` — FastAPI skeleton.
- `db/migrations/` — initial schema with RLS.
- `iso27001/` — starter content for ISO 27001 alignment.

## Theme
Dark-mode forward with light-mode option (see `design/theme.md` for details).

| Mode  | Background | Surface | Primary | Accent | Text Primary | Text Muted |
| --- | --- | --- | --- | --- | --- | --- |
| Dark | `#0F1116` | `#1A1D24` | `#4B2C82` | `#6F3CCF` | `#F4F5FB` | `#C5C8D4` |
| Light | `#F7F8FB` | `#E6E8EF` | `#4B2C82` | `#6F3CCF` | `#0F1116` | `#4B5565` |
