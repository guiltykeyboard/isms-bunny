# Authentication and Identity Plan

Last updated: 2026-02-08

## Modes
- **Local auth**: email + password (argon2id hashing), optional TOTP MFA, optional WebAuthn (passkeys) for phishing resistance.
- **OIDC**: Okta, Azure AD/Entra, Google Workspace; generic OIDC provider config with issuer/client/secret/redirects.
- **SAML 2.0**: bring-your-own IdP for other providers (upload metadata / URL + cert).
- **Session tokens**: short-lived access tokens (JWT) + refresh tokens; API keys scoped per tenant for automation.

## Multi-tenant / roles
- MSP Admin role: can access all tenants (internal MSP tenant + customers); bypasses RLS tenant filter via `app.current_is_msp_admin`.
- Tenant CISO / Auditor / Manager roles remain tenant-scoped.
- Tenant types: `internal_msp` (parent) and `customer` (default).

## Enrollment flows
- Local: admin invites user → email link → set password → optional TOTP + passkey registration.
- IdP: admin creates IdP connection → users authenticate via enterprise login; optional requirement for MFA from IdP.

## Security controls
- Enforce HTTPS; secure cookies with SameSite=Lax/Strict for app; separate domain for trust pages.
- Rate limits on auth endpoints; lockout/backoff on failed logins.
- WebAuthn ceremony for passkeys; store credentials server-side with per-user handle.
- TOTP secrets stored encrypted at rest.
- Rotate signing keys; support JWKS endpoint for OIDC if needed.

## Open items
- Decide on cookie vs SPA token storage (prefer httpOnly cookies).
- Add optional device/email verification.
- Map IdP groups to roles (configurable claims mapping).
