"use client";

import { useState, useRef } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Insights {
  period_label: string;
  total_income: number;
  total_expenses: number;
  savings_amount: number;
  savings_rate: number;
  personality: string;
  personality_reason: string;
  achievements: string[];
  top_categories: { category: string; amount: number; percentage: number }[];
  currency: string;
}

interface RecapResult {
  session_id: string;
  video_url: string;
  insights: Insights;
  processing_time_ms: number;
}

type Stage = "idle" | "uploading" | "processing" | "done" | "error";

export default function Home() {
  const [stage, setStage] = useState<Stage>("idle");
  const [result, setResult] = useState<RecapResult | null>(null);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (!file.name.endsWith(".csv")) {
      setError("Please upload a .csv file.");
      return;
    }
    setStage("uploading");
    setError("");

    const form = new FormData();
    form.append("file", file);

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 120_000);

    try {
      setStage("processing");
      const res = await fetch(`${API_URL}/api/v1/recap/generate`, {
        method: "POST",
        body: form,
        signal: controller.signal,
      });
      clearTimeout(timeout);

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Pipeline failed");
      }

      const data: RecapResult = await res.json();
      setResult(data);
      setStage("done");
    } catch (err: unknown) {
      clearTimeout(timeout);
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
      setStage("error");
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const reset = () => {
    setStage("idle");
    setResult(null);
    setError("");
  };

  return (
    <main style={styles.main}>
      <div style={styles.card}>
        {/* Header */}
        <div style={styles.header}>
          <h1 style={styles.title}>Banker's Wrapped</h1>
          <p style={styles.subtitle}>Your financial year, told as a story.</p>
        </div>

        {/* Upload Zone */}
        {stage === "idle" && (
          <div
            style={{ ...styles.dropzone, ...(dragging ? styles.dropzoneActive : {}) }}
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => fileRef.current?.click()}
          >
            <div style={styles.dropIcon}>📊</div>
            <p style={styles.dropText}>Drop your CSV transaction export here</p>
            <p style={styles.dropHint}>or click to browse</p>
            <input
              ref={fileRef}
              type="file"
              accept=".csv"
              style={{ display: "none" }}
              onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            />
            <button style={styles.demoBtn}
              onClick={(e) => {
                e.stopPropagation();
                fetch("/data/synthetic/transactions_jan_2026.csv")
                  .then(r => r.blob())
                  .then(b => handleFile(new File([b], "transactions_jan_2026.csv", { type: "text/csv" })));
              }}>
              Try demo dataset
            </button>
          </div>
        )}

        {/* Processing */}
        {(stage === "uploading" || stage === "processing") && (
          <div style={styles.processing}>
            <div style={styles.spinner} />
            <p style={styles.processingText}>
              {stage === "uploading" ? "Uploading..." : "Generating your recap…"}
            </p>
            <div style={styles.steps}>
              {["Parsing transactions", "Analysing finances", "Writing narrative",
                "Generating voice & visuals", "Composing video"].map((s, i) => (
                <div key={i} style={styles.step}>
                  <span style={styles.stepDot}>●</span> {s}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error */}
        {stage === "error" && (
          <div style={styles.errorBox}>
            <p style={styles.errorText}>⚠️ {error}</p>
            <button style={styles.btn} onClick={reset}>Try again</button>
          </div>
        )}

        {/* Result */}
        {stage === "done" && result && (
          <div style={styles.result}>
            <div style={styles.personalityBadge}>
              🏅 {result.insights.personality}
            </div>
            <h2 style={styles.periodLabel}>{result.insights.period_label}</h2>

            <div style={styles.metrics}>
              <Metric label="Income" value={fmt(result.insights.total_income, result.insights.currency)} />
              <Metric label="Expenses" value={fmt(result.insights.total_expenses, result.insights.currency)} />
              <Metric label="Saved" value={`${result.insights.savings_rate.toFixed(1)}%`} highlight />
            </div>

            <div style={styles.achievementsList}>
              {result.insights.achievements.map((a, i) => (
                <div key={i} style={styles.achievement}>✓ {a}</div>
              ))}
            </div>

            <div style={styles.videoSection}>
              <video
                src={result.video_url}
                controls
                autoPlay
                style={styles.video}
              />
            </div>

            <p style={styles.reason}>{result.insights.personality_reason}</p>
            <p style={styles.meta}>
              Generated in {(result.processing_time_ms / 1000).toFixed(1)}s ·
              Session {result.session_id.slice(0, 8)}
            </p>
            <button style={styles.btn} onClick={reset}>Generate another</button>
          </div>
        )}
      </div>
    </main>
  );
}

function Metric({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div style={styles.metric}>
      <span style={styles.metricLabel}>{label}</span>
      <span style={{ ...styles.metricValue, ...(highlight ? styles.metricHighlight : {}) }}>
        {value}
      </span>
    </div>
  );
}

function fmt(amount: number, currency: string) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(amount);
}

const styles: Record<string, React.CSSProperties> = {
  main: { minHeight: "100vh", background: "#0f0f13", display: "flex", alignItems: "center", justifyContent: "center", padding: "24px", fontFamily: "'Inter', sans-serif" },
  card: { background: "#1a1a24", borderRadius: "16px", padding: "40px", maxWidth: "580px", width: "100%", boxShadow: "0 20px 60px rgba(0,0,0,0.5)" },
  header: { textAlign: "center", marginBottom: "32px" },
  title: { fontSize: "32px", fontWeight: 700, color: "#fff", margin: 0 },
  subtitle: { color: "#888", marginTop: "8px", fontSize: "16px" },
  dropzone: { border: "2px dashed #333", borderRadius: "12px", padding: "48px 24px", textAlign: "center", cursor: "pointer", transition: "all 0.2s" },
  dropzoneActive: { borderColor: "#6366f1", background: "#1e1e30" },
  dropIcon: { fontSize: "48px", marginBottom: "16px" },
  dropText: { color: "#ccc", fontSize: "16px", margin: "0 0 8px" },
  dropHint: { color: "#555", fontSize: "14px", margin: "0 0 24px" },
  demoBtn: { background: "transparent", border: "1px solid #444", color: "#888", padding: "8px 20px", borderRadius: "8px", cursor: "pointer", fontSize: "13px" },
  processing: { textAlign: "center", padding: "32px 0" },
  spinner: { width: "40px", height: "40px", border: "3px solid #333", borderTop: "3px solid #6366f1", borderRadius: "50%", animation: "spin 0.8s linear infinite", margin: "0 auto 16px" },
  processingText: { color: "#ccc", fontSize: "16px", marginBottom: "24px" },
  steps: { display: "flex", flexDirection: "column", gap: "8px", alignItems: "flex-start", maxWidth: "240px", margin: "0 auto" },
  step: { color: "#555", fontSize: "13px" },
  stepDot: { color: "#6366f1" },
  errorBox: { textAlign: "center", padding: "32px 0" },
  errorText: { color: "#f87171", marginBottom: "16px" },
  result: { display: "flex", flexDirection: "column", gap: "16px" },
  personalityBadge: { background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", padding: "12px 20px", borderRadius: "12px", fontWeight: 700, fontSize: "18px", textAlign: "center" },
  periodLabel: { color: "#fff", textAlign: "center", margin: 0, fontSize: "20px" },
  metrics: { display: "flex", gap: "12px" },
  metric: { flex: 1, background: "#12121a", borderRadius: "8px", padding: "12px", display: "flex", flexDirection: "column", gap: "4px" },
  metricLabel: { color: "#666", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.05em" },
  metricValue: { color: "#ccc", fontSize: "16px", fontWeight: 600 },
  metricHighlight: { color: "#34d399" },
  achievementsList: { display: "flex", flexDirection: "column", gap: "6px" },
  achievement: { color: "#34d399", fontSize: "13px" },
  videoSection: { borderRadius: "8px", overflow: "hidden" },
  video: { width: "100%", borderRadius: "8px" },
  reason: { color: "#888", fontSize: "13px", textAlign: "center", fontStyle: "italic" },
  meta: { color: "#444", fontSize: "11px", textAlign: "center" },
  btn: { background: "#6366f1", color: "#fff", border: "none", padding: "12px 24px", borderRadius: "8px", cursor: "pointer", fontSize: "14px", fontWeight: 600 },
};
