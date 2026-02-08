# ISMS-Bunny Architecture (draft)

Last updated: 2026-02-08

## Stack choices
- Reverse proxy/TLS: Caddy (ACME, SNI routing, simple config API).
- Backend: Python + FastAPI (typed, async), Uvicorn/Gunicorn.
- Frontend: Next.js/React served via the same container (or separate static container later).
- Database: Postgres with Row-Level Security (RLS) enforcing tenant isolation.
- Cache/queue: Redis (rate limits, background jobs).
- Object storage: S3-compatible (Wasabi preferred); pluggable per-tenant credentials; MinIO only for local dev.
- Async tasks: Celery/RQ for evidence processing, exports, scheduled reminders.
- Auth: OIDC-ready; local login + TOTP; JWT access tokens; per-tenant API keys; optional SSO later.

## Containers (docker-compose)
- `caddy`: terminates TLS, handles SNI, routes `Host` to app; serves static trust pages from cache; auto-cert with ACME.
- `app`: FastAPI + Next.js app server; enforces tenant context from host header; connects to Postgres/Redis/object storage.
- `worker`: same image as app, runs background jobs.
- `db`: Postgres.
- `cache`: Redis.
- `minio`: optional local object storage for dev (disabled in prod).

## Tenancy model
- Host-based resolution: `tenant.example.com` → lookup tenant by FQDN → set `current_tenant_id` in request context.
- Postgres RLS: tables include `tenant_id`; RLS policies restrict CRUD to current tenant; MSP admins bypass via admin role.
- Storage isolation: default single bucket with `tenant_id` prefix; BYO bucket/credentials stored encrypted per tenant.
- Public trust page: read-only view resolved by host; served via app or cached artifact; no authenticated data leakage.

## Data model (initial)
- `tenants` (id, name, fqdn, storage_config, status)
- `users` (id, email, auth_provider, mfa, status)
- `memberships` (user_id, tenant_id, roles:[msp_admin | tenant_ciso | auditor | manager])
- `controls`, `frameworks`, `mappings`, `statements_of_applicability`
- `assets`, `risks`, `treatments`, `tasks`
- `evidence` (metadata + object storage pointer)
- `trust_pages` (sections: overview, policies, attestations, subprocessors, status, documents)
- `audit_logs`

## Roles and permissions
- MSP Admin: manage all tenants, users, configs.
- Tenant CISO: full manage within assigned tenants.
- Auditor: read-only access within assigned tenants; can export.
- Manager/Leadership: can submit records (meeting minutes, NC reports) and view assigned areas; limited admin.

## Security controls (built-in)
- HTTPS-only; HSTS; CSP; secure cookies.
- RLS + least-privileged DB roles; migrations enforce policies.
- Rate limiting per tenant/user and per trust-page host.
- Secrets via env/secret store; no secrets baked into images.
- SBOM generation in CI; dependency pinning; vulnerability scans.
- Structured audit logging on all mutations; immutable log sink option.

## Trust page flow
1) DNS: tenant CNAME/A -> platform.
2) Caddy ACME issues cert per host (SNI).
3) Request routed to app; app resolves tenant by host.
4) Public content served; gated documents require short-lived signed URLs; optionally NDA gate before release.

## Extensibility
- Control catalogs imported via YAML/CSV.
- Framework mappings (ISO 27001, SOC 2, CIS, NIST CSF) added incrementally.
- Webhooks/integrations for ticketing/alerting optional.

## Licensing direction
- If code is original: target Apache 2.0 or MIT for MSP adoption.
- If incorporating AGPL components (e.g., CISO Assistant code), overall project must be AGPLv3—decide before import.
