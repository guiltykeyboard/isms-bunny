# Trust Page (public) design notes

## Goals
- Public, cacheable security overview per tenant with custom domain (CNAME/A) and automatic TLS via Caddy/ACME.
- No authenticated data leakage; only explicitly published content is exposed.
- Optional gating for sensitive docs (NDA clickthrough + short-lived signed URL).

## Host routing
- Tenant points `trust.customer.com` CNAME to platform.
- Caddy performs SNI/ACME and forwards based on `Host` header.
- App resolves tenant by `Host` -> tenant_id -> fetches public trust content.

## Content model (see `trust_pages` table)
- Overview (markdown)
- Policies / attestations (links)
- Subprocessors list
- Status banner (incidents/uptime)
- Contact/CTA (e.g., request access)
- Optional gated documents: stored in S3 with signed URLs (per-tenant bucket/prefix or BYO).

## Caching
- Cache rendered trust payloads per host in Redis with short TTL + manual purge on update.
- Caddy can serve stale-while-revalidate for resilience.

## Security controls
- Strict CSP, HSTS, no inline scripts.
- Separate public API surface for trust page; no authenticated cookies on that domain.
- Rate limiting per host to deter scraping.

## Storage
- Default: shared bucket with per-tenant prefix.
- Allow BYO S3 credentials per tenant; require bucket-scoped least-privilege policy.
