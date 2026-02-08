# ISMS-Bunny Theme

Dark-mode forward, playful but professional.

## Palette (dark)
- Primary: Dark Purple `#4B2C82`
- Accent: Brighter Purple `#6F3CCF`
- Background: Soft Near-Black `#0F1116`
- Surface: Dark Grey `#1A1D24`
- Text Primary: Soft White `#F4F5FB`
- Text Muted: `#C5C8D4`
- Success: `#2ECC71`
- Warning: `#F1C40F`
- Danger: `#E74C3C`
- Info: `#3498DB`

## Palette (light)
- Primary: Dark Purple `#4B2C82`
- Accent: Brighter Purple `#6F3CCF`
- Background: Soft White `#F7F8FB`
- Surface: Light Grey `#E6E8EF`
- Text Primary: Near-Black `#0F1116`
- Text Muted: `#4B5565`
- Success: `#229954`
- Warning: `#D4AC0D`
- Danger: `#C0392B`
- Info: `#2874A6`

## Mode switching
- Modes: `system` (default, respects `prefers-color-scheme`), `dark`, `light`.
- Per-user preference stored in profile; fallback to `system` if unset.
- On first load: read user preference → if `system`, use media query to select palette; persist choice in local storage and user profile when authenticated.
- Provide quick toggle in header and in user settings.

## UI notes
- Rounded corners, medium radius; avoid heavy drop-shadows.
- Trust page: hero with tenant logo, security posture badges, quick links (Policies, Attestations, Status, Subprocessors, Contact).
- Buttons: primary = dark purple, secondary = ghost on dark.
- Charts/tables: high-contrast grid lines; use accent purple for focus/highlight.
