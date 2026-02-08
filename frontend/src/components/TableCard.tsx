import React from "react";

export function TableCard({
  title,
  columns,
  rows,
  colors,
}: {
  title: string;
  columns: string[];
  rows: (string | React.ReactNode)[][];
  colors: any;
}) {
  return (
    <div
      style={{
        background: colors.surface,
        padding: "1.25rem",
        borderRadius: "12px",
        border: "1px solid rgba(255,255,255,0.05)",
      }}
    >
      <h3 style={{ marginTop: 0 }}>{title}</h3>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", color: colors.text }}>
          <thead>
            <tr>
              {columns.map((c) => (
                <th
                  key={c}
                  style={{
                    textAlign: "left",
                    borderBottom: `1px solid rgba(255,255,255,0.07)`,
                    padding: "8px 4px",
                    color: colors.muted,
                  }}
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                {r.map((cell, j) => (
                  <td
                    key={j}
                    style={{
                      padding: "8px 4px",
                      borderBottom: `1px solid rgba(255,255,255,0.04)`,
                    }}
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
