"use client";

import { useState, useRef, useEffect } from "react";

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
  b2_keys: Record<string, string>;
}

interface ProgressEvent {
  event: string;
  detail: string;
  ts: number;
}

type Stage = "idle" | "uploading" | "processing" | "done" | "error";

const PIPELINE_STEPS = [
  { key: "parsing",           label: "Parsing transactions" },
  { key: "analyzing",         label: "Calculating insights" },
  { key: "scripting",         label: "Writing narrative script" },
  { key: "generating_images", label: "Generating scene images + narration" },
  { key: "uploading",         label: "Uploading to Backblaze B2" },
];

const PERSONALITY_THEMES: Record<string, { color: string; bg: string; icon: string; tagline: string }> = {
  "Financial Builder":   { color: "#F59E0B", bg: "rgba(245,158,11,0.15)",  icon: "🏗️", tagline: "Laying the foundation — brick by brick." },
  "Financial Explorer":  { color: "#14B8A6", bg: "rgba(20,184,166,0.15)",  icon: "🌍", tagline: "You invest in experiences that last a lifetime." },
  "Financial Achiever":  { color: "#8B5CF6", bg: "rgba(139,92,246,0.15)", icon: "🏆", tagline: "Your discipline is paying off — literally." },
  "Financial Optimizer": { color: "#3B82F6", bg: "rgba(59,130,246,0.15)", icon: "⚙️", tagline: "Every dollar has a purpose in your world." },
};

function getTheme(personality: string) {
  return PERSONALITY_THEMES[personality] ?? { color: "#6366f1", bg: "rgba(99,102,241,0.15)", icon: "💰", tagline: "" };
}

const PERSONALITY_CLASS: Record<string, string> = {
  "Financial Builder":   "bw-theme--builder",
  "Financial Explorer":  "bw-theme--explorer",
  "Financial Achiever":  "bw-theme--achiever",
  "Financial Optimizer": "bw-theme--optimizer",
};

export default function Home() {
  const [stage, setStage] = useState<Stage>("idle");
  const [result, setResult] = useState<RecapResult | null>(null);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const [progressEvents, setProgressEvents] = useState<ProgressEvent[]>([]);
  const [artifactsOpen, setArtifactsOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const sseRef = useRef<EventSource | null>(null);

  useEffect(() => {
    return () => { sseRef.current?.close(); };
  }, []);

  const handleFile = async (file: File) => {
    if (!file.name.endsWith(".csv")) {
      setError("Please upload a .csv file.");
      return;
    }
    setStage("uploading");
    setError("");
    setProgressEvents([]);

    const sessionId = crypto.randomUUID();

    sseRef.current?.close();
    const sse = new EventSource(`${API_URL}/api/v1/recap/${sessionId}/progress`);
    sseRef.current = sse;
    sse.onmessage = (e) => {
      try {
        const ev: ProgressEvent = JSON.parse(e.data as string);
        setProgressEvents((prev) => [...prev, ev]);
      } catch { /* ignore malformed events */ }
    };
    sse.onerror = () => sse.close();

    const form = new FormData();
    form.append("file", file);

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 300_000);

    try {
      setStage("processing");
      const res = await fetch(`${API_URL}/api/v1/recap/generate`, {
        method: "POST",
        body: form,
        signal: controller.signal,
        headers: { "X-Session-ID": sessionId },
      });
      clearTimeout(timeout);
      sse.close();

      if (!res.ok) {
        const data = await res.json() as { detail?: string };
        throw new Error(data.detail ?? "Pipeline failed");
      }

      const data = await res.json() as RecapResult;
      setResult(data);
      setStage("done");
    } catch (err: unknown) {
      clearTimeout(timeout);
      sse.close();
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
    sseRef.current?.close();
    setStage("idle");
    setResult(null);
    setError("");
    setProgressEvents([]);
    setArtifactsOpen(false);
  };

  const copyShareLink = async () => {
    if (!result) return;
    const url = `${window.location.origin}/recap/${result.session_id}`;
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      // Fallback for browsers that block clipboard API
      const el = document.createElement("textarea");
      el.value = url;
      document.body.appendChild(el);
      el.select();
      document.execCommand("copy");
      document.body.removeChild(el);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const theme = result ? getTheme(result.insights.personality) : null;
  const completedKeys = new Set(progressEvents.map((e) => e.event));
  const currentIdx = (() => {
    for (let i = PIPELINE_STEPS.length - 1; i >= 0; i--) {
      if (completedKeys.has(PIPELINE_STEPS[i].key)) return i;
    }
    return -1;
  })();

  const themeClass = result ? (PERSONALITY_CLASS[result.insights.personality] ?? "") : "";

  return (
    <main className="bw-main">
      <div className="bw-card">
        <div className="bw-header">
          <img src="/icon.svg" alt="" aria-hidden="true" className="bw-logo-icon" width="72" height="72" />
          <span className="bw-brand-label">BANKER&apos;S</span>
          <h1 className="bw-title">Wrapped</h1>
          <p className="bw-subtitle">Your financial year, told as a story.</p>
        </div>

        {/* Upload zone */}
        {stage === "idle" && (
          <div
            className={`bw-dropzone${dragging ? " bw-dropzone-active" : ""}`}
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => fileRef.current?.click()}
          >
            <div className="bw-drop-icon">📊</div>
            <p className="bw-drop-text">Drop your CSV transaction export here</p>
            <p className="bw-drop-hint">or click to browse · max 5 MB</p>
            <input
              ref={fileRef}
              type="file"
              accept=".csv"
              hidden
              onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            />
            <button
              type="button"
              className="bw-demo-btn"
              onClick={(e) => {
                e.stopPropagation();
                fetch("/data/synthetic/transactions_jan_2026.csv")
                  .then((r) => r.blob())
                  .then((b) => handleFile(new File([b], "transactions_jan_2026.csv", { type: "text/csv" })));
              }}
            >
              Try demo dataset
            </button>
          </div>
        )}

        {/* Live pipeline progress */}
        {(stage === "uploading" || stage === "processing") && (
          <div className="bw-processing">
            <div className="bw-spinner" />
            <p className="bw-processing-text">Generating your recap…</p>
            <div className="bw-steps">
              {PIPELINE_STEPS.map((step, i) => {
                const done   = completedKeys.has(step.key);
                const active = i === currentIdx + 1 && !done;
                return (
                  <div key={step.key} className="bw-step-row">
                    <span className={`bw-step-icon ${done ? "bw-step-done" : active ? "bw-step-active" : "bw-step-idle"}`}>
                      {done ? "✅" : active ? "⏳" : "○"}
                    </span>
                    <span className={`bw-step-label ${done ? "bw-label-done" : active ? "bw-label-active" : "bw-label-idle"}`}>
                      {step.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Error */}
        {stage === "error" && (
          <div className="bw-error-box">
            <p className="bw-error-text">⚠️ {error}</p>
            <button type="button" className="bw-btn" onClick={reset}>Try again</button>
          </div>
        )}

        {/* Result */}
        {stage === "done" && result && theme && (
          <div className={`bw-result ${themeClass}`}>
            <div className="bw-personality-badge">
              <span className="bw-personality-icon">{theme.icon}</span>
              <div>
                <div className="bw-personality-name">{result.insights.personality}</div>
                <div className="bw-personality-tagline">&ldquo;{theme.tagline}&rdquo;</div>
              </div>
            </div>

            <h2 className="bw-period-label">{result.insights.period_label}</h2>

            <div className="bw-metrics">
              <Metric label="Income"   value={fmt(result.insights.total_income, result.insights.currency)} />
              <Metric label="Expenses" value={fmt(result.insights.total_expenses, result.insights.currency)} />
              <Metric label="Saved"    value={`${result.insights.savings_rate.toFixed(1)}%`} accent />
            </div>

            {result.insights.achievements.length > 0 && (
              <div className="bw-achievements">
                {result.insights.achievements.map((a, i) => (
                  <div key={i} className="bw-achievement">✓ {a}</div>
                ))}
              </div>
            )}

            <div className="bw-video-section">
              <video className="bw-video" src={result.video_url} controls autoPlay muted />
              <a className="bw-download-link" href={result.video_url} download="recap.mp4">
                ↓ Download MP4
              </a>
            </div>

            <button type="button" className="bw-share-btn" onClick={copyShareLink}>
              {copied ? "✓ Link copied!" : "Share your recap →"}
            </button>

            <details
              className="bw-artifacts"
              onToggle={(e) => setArtifactsOpen((e.target as HTMLDetailsElement).open)}
            >
              <summary className="bw-artifacts-summary">
                {artifactsOpen ? "▾" : "▸"} Pipeline Artifacts (Backblaze B2)
              </summary>
              <div className="bw-artifacts-list">
                {Object.entries(result.b2_keys).map(([k]) => (
                  <div key={k} className="bw-artifact-item">
                    <span className="bw-artifact-key">{k}</span>
                  </div>
                ))}
              </div>
            </details>

            <p className="bw-meta">
              Generated in {(result.processing_time_ms / 1000).toFixed(1)}s ·
              Session {result.session_id.slice(0, 8)} ·
              Powered by Backblaze B2 + Genblaze
            </p>
            <button type="button" className="bw-btn-secondary" onClick={reset}>Generate another</button>
          </div>
        )}
      </div>
    </main>
  );
}

function Metric({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="bw-metric">
      <span className="bw-metric-label">{label}</span>
      <span className={`bw-metric-value${accent ? " bw-metric-accent" : ""}`}>{value}</span>
    </div>
  );
}

function fmt(amount: number, currency: string) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(amount);
}
