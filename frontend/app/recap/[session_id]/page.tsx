"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

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

interface RecapData {
  session_id: string;
  video_url: string;
  insights: Insights;
  processing_time_ms: number;
  b2_keys: Record<string, string>;
}

const PERSONALITY_THEMES: Record<string, { color: string; bg: string; icon: string; tagline: string }> = {
  "Financial Builder":   { color: "#F59E0B", bg: "rgba(245,158,11,0.15)",  icon: "🏗️", tagline: "Laying the foundation — brick by brick." },
  "Financial Explorer":  { color: "#14B8A6", bg: "rgba(20,184,166,0.15)",  icon: "🌍", tagline: "You invest in experiences that last a lifetime." },
  "Financial Achiever":  { color: "#8B5CF6", bg: "rgba(139,92,246,0.15)", icon: "🏆", tagline: "Your discipline is paying off — literally." },
  "Financial Optimizer": { color: "#3B82F6", bg: "rgba(59,130,246,0.15)", icon: "⚙️", tagline: "Every dollar has a purpose in your world." },
};

const PERSONALITY_CLASS: Record<string, string> = {
  "Financial Builder":   "bw-theme--builder",
  "Financial Explorer":  "bw-theme--explorer",
  "Financial Achiever":  "bw-theme--achiever",
  "Financial Optimizer": "bw-theme--optimizer",
};

function getTheme(personality: string) {
  return PERSONALITY_THEMES[personality] ?? { color: "#6366f1", bg: "rgba(99,102,241,0.15)", icon: "💰", tagline: "" };
}

function fmt(amount: number, currency: string) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(amount);
}

export default function SharePage() {
  const params = useParams();
  const session_id = params.session_id as string;

  const [data, setData] = useState<RecapData | null>(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!session_id) return;
    fetch(`${API_URL}/api/v1/recap/${session_id}`)
      .then((r) => {
        if (!r.ok) throw new Error("Recap not found");
        return r.json() as Promise<RecapData>;
      })
      .then(setData)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Not found"));
  }, [session_id]);

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
    } catch {
      const el = document.createElement("textarea");
      el.value = window.location.href;
      document.body.appendChild(el);
      el.select();
      document.execCommand("copy");
      document.body.removeChild(el);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  if (error) {
    return (
      <main className="bw-main">
        <div className="bw-card">
          <div className="bw-header">
            <h1 className="bw-title">Banker&apos;s Wrapped</h1>
          </div>
          <div className="bw-error-box">
            <p className="bw-error-text">⚠️ {error}</p>
            <Link href="/" className="bw-btn" style={{ display: "block", textAlign: "center", textDecoration: "none" }}>
              Create your own recap →
            </Link>
          </div>
        </div>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="bw-main">
        <div className="bw-card">
          <div className="bw-processing">
            <div className="bw-spinner" />
            <p className="bw-processing-text">Loading recap…</p>
          </div>
        </div>
      </main>
    );
  }

  const theme = getTheme(data.insights.personality);
  const themeClass = PERSONALITY_CLASS[data.insights.personality] ?? "";

  return (
    <main className="bw-main">
      <div className="bw-card">
        <div className="bw-header">
          <h1 className="bw-title">Banker&apos;s Wrapped</h1>
          <p className="bw-subtitle">Someone shared their financial story with you.</p>
        </div>

        <div className={`bw-result ${themeClass}`}>
          <div className="bw-personality-badge">
            <span className="bw-personality-icon">{theme.icon}</span>
            <div>
              <div className="bw-personality-name">{data.insights.personality}</div>
              <div className="bw-personality-tagline">&ldquo;{theme.tagline}&rdquo;</div>
            </div>
          </div>

          <h2 className="bw-period-label">{data.insights.period_label}</h2>

          <div className="bw-metrics">
            <div className="bw-metric">
              <span className="bw-metric-label">Income</span>
              <span className="bw-metric-value">{fmt(data.insights.total_income, data.insights.currency)}</span>
            </div>
            <div className="bw-metric">
              <span className="bw-metric-label">Expenses</span>
              <span className="bw-metric-value">{fmt(data.insights.total_expenses, data.insights.currency)}</span>
            </div>
            <div className="bw-metric">
              <span className="bw-metric-label">Saved</span>
              <span className="bw-metric-value bw-metric-accent">{data.insights.savings_rate.toFixed(1)}%</span>
            </div>
          </div>

          {data.insights.achievements.length > 0 && (
            <div className="bw-achievements">
              {data.insights.achievements.map((a, i) => (
                <div key={i} className="bw-achievement">✓ {a}</div>
              ))}
            </div>
          )}

          <div className="bw-video-section">
            <video className="bw-video" src={data.video_url} controls autoPlay muted />
            <a className="bw-download-link" href={data.video_url} download="recap.mp4">
              ↓ Download MP4
            </a>
          </div>

          <button type="button" className="bw-share-btn" onClick={copyLink}>
            {copied ? "✓ Link copied!" : "Copy share link"}
          </button>

          <details className="bw-artifacts">
            <summary className="bw-artifacts-summary">▸ Pipeline Artifacts (Backblaze B2)</summary>
            <div className="bw-artifacts-list">
              {Object.entries(data.b2_keys).map(([k]) => (
                <div key={k} className="bw-artifact-item">
                  <span className="bw-artifact-key">{k}</span>
                </div>
              ))}
            </div>
          </details>

          <p className="bw-meta">
            Generated in {(data.processing_time_ms / 1000).toFixed(1)}s ·
            Session {data.session_id.slice(0, 8)} ·
            Powered by Backblaze B2 + Genblaze
          </p>

          <Link href="/" className="bw-btn-secondary" style={{ display: "block", textAlign: "center", textDecoration: "none" }}>
            Create your own recap →
          </Link>
        </div>
      </div>
    </main>
  );
}
