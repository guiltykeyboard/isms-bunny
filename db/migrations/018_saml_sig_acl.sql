-- SAML hardening: mark whether assertions/messages must be signed and store ACS URL override

ALTER TABLE idp_connections
  ADD COLUMN IF NOT EXISTS saml_require_signed_assertions boolean DEFAULT true,
  ADD COLUMN IF NOT EXISTS saml_require_signed_messages boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS saml_sp_acs_override text;
