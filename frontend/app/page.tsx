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
  thumbnail_url: string;
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

function fmtDuration(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
}

const PIPELINE_STEPS = [
  { key: "parsing",           label: "Parsing transactions" },
  { key: "analyzing",         label: "Calculating financial insights" },
  { key: "scripting",         label: "Writing narrative script" },
  { key: "generating_images", label: "Generating scenes + narration" },
  { key: "composing_video",   label: "Composing video with FFmpeg" },
  { key: "uploading_to_b2",   label: "Saving recap video to Backblaze B2" },
  { key: "uploading",         label: "Finalising recap" },
];

const SCENE_KEYS = ["scene_0_done","scene_1_done","scene_2_done","scene_3_done","scene_4_done"];
const TOTAL_SCENES = SCENE_KEYS.length;

// Tuned to a realistic ~5 min total (observed range 4–7 min). Image generation
// dominates; NIM 70B scripting is the next-largest chunk.
const STAGE_WEIGHTS: Record<string, number> = {
  parsing: 2, analyzing: 2, scripting: 55, generating_images: 200,
  composing_video: 15, uploading_to_b2: 20, uploading: 6,
};
const TOTAL_ESTIMATED_S = Object.values(STAGE_WEIGHTS).reduce((a, b) => a + b, 0);

const ARTIFACT_LABELS: Record<string, string> = {
  csv:        "Input CSV",
  script:     "Narrative script",
  analytics:  "Financial analytics",
  prompts:    "Image prompts",
  generation: "Generation provenance",
  narration:  "Narration audio",
  thumbnail:  "Thumbnail",
  video:      "Recap video",
  metadata:   "Session metadata",
};

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
  const [pipelineStartTime, setPipelineStartTime] = useState<number | null>(null);
  const [elapsedS, setElapsedS] = useState(0);
  const fileRef = useRef<HTMLInputElement>(null);
  const sseRef = useRef<EventSource | null>(null);

  useEffect(() => {
    return () => { sseRef.current?.close(); };
  }, []);

  // Start pipeline timer on first SSE event (use > 0 to handle batched state updates)
  useEffect(() => {
    if (progressEvents.length > 0 && pipelineStartTime === null) {
      setPipelineStartTime(Date.now());
    }
  }, [progressEvents, pipelineStartTime]);

  // Tick elapsed time while processing
  useEffect(() => {
    if (!pipelineStartTime || stage !== "processing") return;
    const id = setInterval(() => {
      setElapsedS(Math.floor((Date.now() - pipelineStartTime) / 1000));
    }, 1000);
    return () => clearInterval(id);
  }, [pipelineStartTime, stage]);

  const handleFile = async (file: File) => {
    if (!file.name.endsWith(".csv")) {
      setError("Please upload a .csv file.");
      return;
    }
    setStage("uploading");
    setError("");
    setProgressEvents([]);
    setPipelineStartTime(null);
    setElapsedS(0);

    const sessionId = crypto.randomUUID();

    sseRef.current?.close();
    const sse = new EventSource(`${API_URL}/api/v1/recap/${sessionId}/progress`);
    sseRef.current = sse;

    sse.onmessage = async (e) => {
      try {
        const ev: ProgressEvent = JSON.parse(e.data as string);
        // Deduplicate by event key (handles SSE reconnects)
        setProgressEvents((prev) =>
          prev.some((p) => p.event === ev.event) ? prev : [...prev, ev]
        );

        if (ev.event === "complete") {
          sse.close();
          sseRef.current = null;
          try {
            const r = await fetch(`${API_URL}/api/v1/recap/${sessionId}`);
            if (!r.ok) throw new Error("Failed to load recap result");
            const data = await r.json() as RecapResult;
            setResult(data);
            setStage("done");
          } catch (fetchErr) {
            setError(fetchErr instanceof Error ? fetchErr.message : "Failed to load result");
            setStage("error");
          }
        } else if (ev.event === "failed") {
          sse.close();
          sseRef.current = null;
          setError(ev.detail || "Pipeline failed. Please try again.");
          setStage("error");
        }
      } catch { /* ignore malformed events */ }
    };

    sse.onerror = () => sse.close();

    const form = new FormData();
    form.append("file", file);

    try {
      setStage("processing");
      const res = await fetch(`${API_URL}/api/v1/recap/generate`, {
        method: "POST",
        body: form,
        headers: { "X-Session-ID": sessionId },
      });

      if (!res.ok) {
        const data = await res.json() as { detail?: string };
        sse.close();
        throw new Error(data.detail ?? "Upload failed");
      }
      // 202 Accepted — pipeline runs in background; SSE delivers progress + final result
    } catch (err: unknown) {
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
    setPipelineStartTime(null);
    setElapsedS(0);
  };

  const copyShareLink = async () => {
    if (!result) return;
    const url = `${window.location.origin}/recap/${result.session_id}`;
    try {
      await navigator.clipboard.writeText(url);
    } catch {
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
  const eventMap = new Map(progressEvents.map((e) => [e.event, e]));

  // Count how many of the 5 scenes have completed (used for "X/5 scenes" sub-label)
  const scenesDoneCount = SCENE_KEYS.filter((k) => completedKeys.has(k)).length;

  // "Generating scenes + narration" stays active until composing_video fires
  // (the generating_images SSE fires at the START of the media step, not the end)
  const composingOrLaterDone = PIPELINE_STEPS
    .slice(PIPELINE_STEPS.findIndex((s) => s.key === "composing_video"))
    .some((s) => completedKeys.has(s.key));

  const currentIdx = (() => {
    for (let i = PIPELINE_STEPS.length - 1; i >= 0; i--) {
      const { key } = PIPELINE_STEPS[i];
      // generating_images counts as done only once composing_video (or later) fires
      const done = key === "generating_images" ? composingOrLaterDone : completedKeys.has(key);
      if (done) return i;
    }
    return -1;
  })();

  // Each SSE event marks the START of its step, so a step's duration is
  // (start of the NEXT step) − (start of this step).
  const getStepDuration = (step: typeof PIPELINE_STEPS[0], stepIdx: number): string | null => {
    const startEv = eventMap.get(step.key);
    if (!startEv) return null;
    // Find the next pipeline step that has fired — its start is this step's end.
    for (let i = stepIdx + 1; i < PIPELINE_STEPS.length; i++) {
      const next = eventMap.get(PIPELINE_STEPS[i].key);
      if (next) return fmtDuration(next.ts - startEv.ts);
    }
    // Last step ends at the terminal "complete" event.
    const done = eventMap.get("complete");
    if (done) return fmtDuration(done.ts - startEv.ts);
    return null;
  };

  // Timestamp of the scripting event — used as baseline for generating_images timer
  // so the counter doesn't reset on every scene_X_done event
  const scriptingTs = eventMap.get("scripting")?.ts ?? null;

  // Timestamp of the most-recently-completed step — used as start of the active step's timer
  const lastCompletedTs = progressEvents.length > 0
    ? progressEvents[progressEvents.length - 1].ts
    : null;

  const themeClass = result ? (PERSONALITY_CLASS[result.insights.personality] ?? "") : "";
  const sceneCount = result
    ? Object.keys(result.b2_keys).filter((k) => k.startsWith("scene_")).length
    : 0;

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
                  .then((r) => {
                    if (!r.ok) throw new Error(`Demo CSV unavailable (${r.status})`);
                    return r.blob();
                  })
                  .then((b) => handleFile(new File([b], "transactions_jan_2026.csv", { type: "text/csv" })))
                  .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load demo file"));
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
                const done   = step.key === "generating_images"
                  ? composingOrLaterDone
                  : completedKeys.has(step.key);
                const active   = i === currentIdx + 1 && !done;
                const duration = done ? getStepDuration(step, i) : null;
                // For generating_images, anchor the running timer to when scripting finished
                // so it doesn't reset to 0 each time a scene_X_done event arrives
                const timerBase = (active && step.key === "generating_images" && scriptingTs !== null)
                  ? scriptingTs
                  : lastCompletedTs;
                const running  = (active && timerBase !== null)
                  ? fmtDuration(Math.max(0, Date.now() / 1000 - timerBase))
                  : null;
                return (
                  <div key={step.key} className="bw-step-row">
                    <span className={`bw-step-icon ${done ? "bw-step-done" : active ? "bw-step-active" : "bw-step-idle"}`}>
                      {done ? "✅" : active ? "⏳" : "○"}
                    </span>
                    <span className={`bw-step-label ${done ? "bw-label-done" : active ? "bw-label-active" : "bw-label-idle"}`}>
                      {step.label}
                      {step.key === "generating_images" && active && (
                        <span className="bw-step-sublabel"> — {scenesDoneCount}/{TOTAL_SCENES} scenes</span>
                      )}
                    </span>
                    {duration && <span className="bw-step-duration">{duration}</span>}
                    {running && !duration && <span className="bw-step-duration bw-step-running">{running}</span>}
                  </div>
                );
              })}
            </div>
            {pipelineStartTime !== null && (() => {
              const rem = Math.max(0, TOTAL_ESTIMATED_S - elapsedS);
              const m = Math.floor(rem / 60);
              const s = rem % 60;
              return (
                <p className="bw-time-estimate">
                  {rem > 0
                    ? `Est. remaining: ${m}:${String(s).padStart(2, "0")}`
                    : "Finishing up…"}
                </p>
              );
            })()}
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
            {/* Thumbnail */}
            {result.thumbnail_url && (
              <img
                src={result.thumbnail_url}
                alt="Recap thumbnail"
                className="bw-thumbnail"
              />
            )}

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
              <video className="bw-video" src={result.video_url} poster={result.thumbnail_url} controls autoPlay muted />
              <div className="bw-video-actions">
                <a className="bw-download-link" href={result.video_url} download="recap.mp4">
                  ↓ Download MP4
                </a>
                <a
                  className="bw-download-link"
                  href={`${API_URL}/api/v1/recap/${result.session_id}/download`}
                  download={`recap-${result.session_id.slice(0, 8)}.zip`}
                >
                  ↓ Download full package (ZIP)
                </a>
              </div>
            </div>

            <button type="button" className="bw-share-btn" onClick={copyShareLink}>
              {copied ? "✓ Link copied!" : "Share your recap →"}
            </button>

            <details
              className="bw-artifacts"
              onToggle={(e) => setArtifactsOpen((e.target as HTMLDetailsElement).open)}
            >
              <summary className="bw-artifacts-summary">
                {artifactsOpen ? "▾" : "▸"} Pipeline Artifacts — Backblaze B2 ({Object.keys(result.b2_keys).length} files)
              </summary>
              <div className="bw-artifacts-list">
                {Object.entries(result.b2_keys).map(([k, path]) => (
                  <div key={k} className="bw-artifact-item">
                    <span className="bw-artifact-key">{ARTIFACT_LABELS[k] ?? k}</span>
                    <span className="bw-artifact-path">{path}</span>
                  </div>
                ))}
              </div>
            </details>

            <p className="bw-meta">
              Generated in {(result.processing_time_ms / 1000).toFixed(1)}s ·
              {sceneCount} scenes ·
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
