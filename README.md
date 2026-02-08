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
  <img alt="Lint" src="https://github.com/guiltykeyboard/isms-bunny/actions/workflows/lint.yml/badge.svg">
</p>

Open-source, MSP-friendly ISMS and trust center scaffold. Goals:

- ISO 27001:2022 first, multi-tenant, security-first.
- Deployable with docker-compose (Caddy + FastAPI/Next.js + Postgres + Redis + S3-compatible storage).
- Trust page per tenant with custom domain and automatic TLS.
- Auth: local (password + TOTP + passkeys) and enterprise (OIDC for Okta/Azure/Google; SAML 2.0 BYO).

## Getting started (dev)

1. Copy `.env.example` to `.env` and adjust secrets/bucket values.
2. Build and run (dev):
   ```bash
   docker compose -f infra/docker-compose.yml up --build
   ```
3. Migrations: apply `db/migrations/001_init.sql` to the Postgres instance.
   - For local dev you can run `scripts/apply_migrations.sh` (uses `DATABASE_URL` if set).
4. Open `http://localhost:8000/health` for a quick check.
5. Auth (alpha): local login via `POST /auth/login` (email/password, optional `totp_code`) sets an httpOnly `access_token` cookie and returns a bearer token. Logout via `POST /auth/logout`. Dev headers `X-User-Id` / `X-Is-Msp-Admin` still work for local testing. OIDC/SAML endpoints stubbed for Okta/Azure/Google/BYO.
6. Setup wizard: visit `/setup` (frontend dev server) to set MSP tenant name/FQDN, admin user, and S3 settings on first run—no manual .env edits needed for basics.

Theme preference
- Modes: `system` (default, honors browser `prefers-color-scheme`), `dark`, `light`.
- API: `GET /users/me` returns `theme_preference`; `PATCH /users/me/theme` with `{"theme_preference":"dark"}` updates it.

Dev defaults
- Seeded tenant: `Dev Tenant` (`fqdn=localhost`, id `00000000-0000-0000-0000-000000000001`).
- Seeded MSP admin user: `admin@example.com` (id `00000000-0000-0000-0000-000000000002`, theme `system`).
- Host resolution: requests to `localhost` map to the seeded tenant; replace with real FQDNs in production.

Dev quality checks
- Ruff lint: `pip install -r requirements-dev.txt` then `ruff check .`
- CI lint workflow auto-creates/updates an issue (label `ci:lint`) on failures and auto-closes when passing.

Frontend
- Minimal Next.js scaffold in `frontend/` with light/dark/system toggle and trust-page teaser.
- Run with `npm install` then `npm run dev` inside `frontend/`.
- Setup UI available at `/setup` (dev server) for first-time config.

Data durability
- Postgres and Caddy cert/config data use named volumes (`db_data`, `caddy_data`, `caddy_config`), so pulling new images will not lose state.
- Object storage is external S3-compatible (Wasabi/AWS/etc.); assets survive container refreshes.

## UI Screens (dark theme)
- Setup wizard (MSP toggle, S3, admin user):  
  ![Setup Wizard](assets/ui-setup.png)
- Admin tenants & memberships:  
  ![Admin](assets/ui-admin.png)
- Trust page preview:  
  ![Trust Preview](assets/ui-trust.png)

## Structure
- `design/` — requirements, architecture, trust page notes, theme.
- `infra/` — docker-compose and Caddy placeholder.
- `app/` — FastAPI skeleton.
- `db/migrations/` — initial schema with RLS.
- `iso27001/` — starter content for ISO 27001 alignment.

## Theme
Dark-mode forward with light-mode option (see `design/theme.md` for details).

| Mode | Background | Surface | Primary | Accent | Text Primary | Text Muted |
| --- | --- | --- | --- | --- | --- | --- |
| Dark | ![#0F1116](assets/swatch-0F1116.svg) `#0F1116` | ![#1A1D24](assets/swatch-1A1D24.svg) `#1A1D24` | ![#4B2C82](assets/swatch-4B2C82.svg) `#4B2C82` | ![#6F3CCF](assets/swatch-6F3CCF.svg) `#6F3CCF` | ![#F4F5FB](assets/swatch-F4F5FB.svg) `#F4F5FB` | ![#C5C8D4](assets/swatch-C5C8D4.svg) `#C5C8D4` |
| Light | ![#F7F8FB](assets/swatch-F7F8FB.svg) `#F7F8FB` | ![#E6E8EF](assets/swatch-E6E8EF.svg) `#E6E8EF` | ![#4B2C82](assets/swatch-4B2C82.svg) `#4B2C82` | ![#6F3CCF](assets/swatch-6F3CCF.svg) `#6F3CCF` | ![#0F1116](assets/swatch-0F1116.svg) `#0F1116` | ![#4B5565](assets/swatch-4B5565.svg) `#4B5565` |
