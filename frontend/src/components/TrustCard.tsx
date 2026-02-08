import React from "react";

export const TrustCard = ({ title, children }: { title: string; children: React.ReactNode }) => {
  return (
    <div
      style={{
        background: "var(--surface)",
        padding: "1.25rem",
        borderRadius: "12px",
        border: "1px solid rgba(255,255,255,0.05)",
      }}
    >
      <h3 style={{ marginTop: 0 }}>{title}</h3>
      {children}
    </div>
  );
};
