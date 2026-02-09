import Link from "next/link";

export default function AdminIndex() {
  const links = [
    { href: "/admin/tenants", label: "Tenants" },
    { href: "/admin/memberships", label: "Memberships" },
    { href: "/admin/providers", label: "Identity Providers" },
    { href: "/admin/webauthn", label: "Passkeys" },
    { href: "/admin/saml-logs", label: "SAML Logs" },
    { href: "/admin/users", label: "Users" },
    { href: "/admin/controls", label: "Controls / SoA" },
    { href: "/admin/trust-editor", label: "Trust Editor" },
    { href: "/admin/access-requests", label: "Trust Access Requests" },
    { href: "/admin/trust-audit", label: "Trust Audit" },
    { href: "/admin/smtp", label: "SMTP" },
  ];
  return (
    <div
      style={{ padding: "2rem", fontFamily: "Inter, system-ui, sans-serif" }}
    >
      <h1>Admin</h1>
      <ul>
        {links.map((l) => (
          <li key={l.href}>
            <Link href={l.href}>{l.label}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
