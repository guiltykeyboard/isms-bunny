# ISO 27001:2022 Starter Pack for the MSP

This folder is a lightweight scaffold to help the MSP stand up and iterate an Information Security Management System (ISMS) aligned to ISO 27001:2022.

## How to use this scaffold
- Treat each subfolder as a workstream (context, scope, policies, risks, assets, Statement of Applicability, procedures, metrics).
- Copy or expand the provided stubs; delete anything you do not need.
- Keep live evidence (screenshots, exports) in the tracked folders; keep sensitive raw notes inside the ignored `context/` folder at the repo root.
- Date-stamp drafts with `YYYY-MM-DD` in the filename when versioning manually.

## Quick-start checklist
- Define organizational context and interested parties (`01-context`).
- Fix ISMS scope boundaries and exclusions (`02-scope`).
- Build the asset register and owners (`05-assets/asset-register.csv`).
- Run an initial risk assessment and treatments (`04-risk/risk-register.csv`).
- Complete a first pass Statement of Applicability (`06-soa/soa.md`).
- Adopt baseline policies from `03-policies` and wire to procedures in `07-procedures`.
- Track ISMS health metrics (`08-metrics`).

## MSP service lines (for tailoring controls)
- Managed IT (includes Cyber and VoIP)
- Print (managed print/Xerox dealership)
- Physical security (Analog/PoE surveillance, access control, fire/burglary alarm monitoring, lock & key)

## Peer group
- Member of TAG (Technology Assurance Group, tagnational.com) — note any shared requirements or resources here.

## Contributing
- Prefer small, reviewable commits by workstream.
- Use clear titles: `Update scope`, `Add risk entries for VoIP`, etc.
