export default function ArchitecturePage() {
  const nodes = [
    { label: "CSV Upload / Plaid",    sub: "Transaction history",           color: "#6b7280" },
    { label: "Document Agent",        sub: "Parse & normalise rows",        color: "#F59E0B" },
    { label: "Analytics Agent",       sub: "Insights + Financial Personality", color: "#F59E0B" },
    { label: "Narrative Agent",       sub: "Genblaze chat · GMI Cloud (NIM fallback)", color: "#8B5CF6" },
    { label: "Genblaze",              sub: "Media orchestration layer",     color: "#14B8A6" },
    { label: "Parallel Image Gen ×5", sub: "GMI Cloud · Seedream",         color: "#14B8A6" },
    { label: "Narration Audio",       sub: "OpenAI TTS · via GenblazeClient", color: "#14B8A6" },
    { label: "FFmpeg Composer",       sub: "segment + concat · H.264 · AAC", color: "#3B82F6" },
    { label: "Backblaze B2",          sub: "14 files · 10 artifact types per session", color: "#3B82F6" },
    { label: "Shareable Recap URL",   sub: "/recap/{session_id}",          color: "#6366f1" },
  ];

  return (
    <main style={{
      minHeight: "100vh",
      background: "#0a0a0f",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: "2rem",
      fontFamily: "system-ui, sans-serif",
    }}>
      <h1 style={{ color: "#fff", fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.25rem", letterSpacing: "-0.02em" }}>
        Banker&apos;s Wrapped
      </h1>
      <p style={{ color: "#6b7280", fontSize: "0.85rem", marginBottom: "2.5rem" }}>
        Agentic AI Pipeline
      </p>

      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 0 }}>
        {nodes.map((node, i) => (
          <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
            <div style={{
              background: "#13131f",
              border: `1.5px solid ${node.color}44`,
              borderLeft: `3px solid ${node.color}`,
              borderRadius: "10px",
              padding: "0.7rem 1.6rem",
              minWidth: "280px",
              textAlign: "center",
            }}>
              <div style={{ color: "#fff", fontWeight: 600, fontSize: "0.95rem" }}>{node.label}</div>
              <div style={{ color: "#6b7280", fontSize: "0.75rem", marginTop: "2px" }}>{node.sub}</div>
            </div>
            {i < nodes.length - 1 && (
              <div style={{ color: "#374151", fontSize: "1.1rem", lineHeight: 1, margin: "4px 0" }}>↓</div>
            )}
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: "1.5rem", marginTop: "2.5rem", flexWrap: "wrap", justifyContent: "center" }}>
        {[
          { label: "Genblaze", color: "#14B8A6" },
          { label: "Backblaze B2", color: "#3B82F6" },
          { label: "NVIDIA NIM", color: "#8B5CF6" },
          { label: "FFmpeg", color: "#F59E0B" },
        ].map((b) => (
          <span key={b.label} style={{
            background: `${b.color}18`,
            border: `1px solid ${b.color}55`,
            color: b.color,
            borderRadius: "999px",
            padding: "4px 14px",
            fontSize: "0.75rem",
            fontWeight: 600,
          }}>{b.label}</span>
        ))}
      </div>
    </main>
  );
}
