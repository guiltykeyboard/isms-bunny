# ISMS-Bunny Requirements (draft)

Last updated: 2026-02-08

## Mission
Open-source, MSP-friendly ISMS and trust center that supports ISO 27001:2022 (and other frameworks), is secure-by-default, multi-tenant, and deployable via docker-compose.

## Core capabilities
- Multi-tenant model with host-based routing; MSP operators can manage all tenants, tenant CISOs can manage assigned tenants.
- Control catalogs and Statement of Applicability (ISO 27001 first; extensible to other frameworks).
- Asset register, risk register, treatments, tasks, evidence links/uploads.
- Trust page per tenant (public, cacheable) with custom domain via CNAME/A record and SNI, showing security overview, policies/attestations, subprocessors, uptime/incidents, and request-access/NDA gate for sensitive docs.
- Role-based access: MSP admin (all tenants), Tenant CISO (full manage for assigned tenants), Auditor (read-only), Leadership/Manager (can submit records such as minutes, NC reports).
- Notifications/reminders for reviews (risks, controls, policies), evidence freshness, audit prep.
- API-first with UI parity; audit logging for all changes.

## Non-functional & security requirements
- Secure by default: HTTPS everywhere, CSP, no default passwords, MFA-ready, rate limiting, audit logs.
- Tenant isolation enforced in the backend (row-level security) plus per-tenant storage prefixes.
- Secrets management via env/secret stores; no secrets in repo or images.
- SBOM and dependency pinning; CI to scan deps and IaC.
- Minimal privileges for service accounts (DB roles, object storage access).
- Backups with tested restores; per-tenant export capability.

## Deployment
- docker-compose first; k8s/nomad later.
- Caddy for TLS (ACME) and SNI host routing; reverse proxy to app.
- Postgres primary datastore; Redis for cache/queues; object storage S3-compatible (Wasabi/AWS/Backblaze/MinIO). MinIO optional for local dev.
- Single image for API/UI where practical; separate worker for async jobs.

## Storage model (open questions)
- Option A: Single bucket with per-tenant prefixes.
- Option B: Bucket per tenant.
- Option C: Bring-your-own bucket (preferred flexibility) with per-tenant credentials; need health checks and least-privilege policies.
- Decision: evaluate cost/ops vs isolation; default to single bucket + prefixes, allow BYO bucket when provided.

## Integrations & imports
- Import existing ISMS content (TAG templates, current ISO folder, CISO Assistant exports if license-compatible).
- Optional ticketing/webhook integrations for tasks/incidents.

## Compliance scope (initial)
- ISO 27001:2022 controls and SoA.
- Map-able to other frameworks later (SOC 2, CIS, NIST CSF) via control mappings.

## UX & branding
- Name: ISMS-Bunny.
- Palette: dark purple primary, soft white, dark grey backgrounds; dark-mode first.
- Trust page per-tenant with custom domain branding.

## Out of scope (initial)
- Automated evidence collection agents.
- Full GRC marketplace-style app store.
