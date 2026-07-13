"use client";

import { useState, useRef } from "react";
import { uploadBatch, formatINR, type PredictionResult } from "@/lib/api";
import { RagBadge, Card } from "@/components/ui";

const SAMPLES = [
  { file: "low_risk_portfolio.csv", label: "Low-Risk Portfolio", desc: "6 healthy MSMEs (all Green)", accent: "green" },
  { file: "mixed_portfolio.csv", label: "Mixed Portfolio", desc: "Realistic spread (Green + Amber + Red)", accent: "amber" },
  { file: "high_risk_watchlist.csv", label: "High-Risk Watchlist", desc: "6 stressed MSMEs (all Red)", accent: "red" },
];

// Show the top SPECIFIC risk driver, skipping the composite index so the
// column reads with real variety (GST delay, bureau, utilization...).
function topReason(r: PredictionResult): string {
  const specific = r.reason_codes.find(
    (rc) => rc.direction === "increases_risk" && rc.feature !== "behavioral_stress_index"
  );
  return (specific || r.reason_codes[0])?.description || "-";
}

export default function UploadPage() {
  const [results, setResults] = useState<PredictionResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fileName, setFileName] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function scoreFile(file: File) {
    setLoading(true);
    setError("");
    setFileName(file.name);
    try {
      const res = await uploadBatch(file);
      setResults(res.predictions);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  async function scoreSample(file: string) {
    setLoading(true);
    setError("");
    setFileName(file);
    try {
      const resp = await fetch(`/samples/${file}`);
      const blob = await resp.blob();
      const f = new File([blob], file, { type: "text/csv" });
      const res = await uploadBatch(f);
      setResults(res.predictions);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sample");
    } finally {
      setLoading(false);
    }
  }

  const counts = results.reduce(
    (acc, r) => { acc[r.rag_bucket] = (acc[r.rag_bucket] || 0) + 1; return acc; },
    {} as Record<string, number>
  );
  const avgPd = results.length
    ? results.reduce((s, r) => s + r.pd_percent, 0) / results.length
    : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Batch Scoring</h1>
        <p className="text-slate-500 text-sm mt-1">
          Upload a CSV of MSME accounts to score them instantly, or try a sample dataset.
        </p>
      </div>

      {/* Sample datasets */}
      <div className="grid sm:grid-cols-3 gap-4">
        {SAMPLES.map((s) => (
          <div key={s.file} className="card card-hover p-4 flex flex-col">
            <div className="flex items-center gap-2">
              <span className={`w-2.5 h-2.5 rounded-full ${
                s.accent === "green" ? "bg-emerald-500" : s.accent === "amber" ? "bg-amber-500" : "bg-red-500"
              }`} />
              <div className="font-semibold text-slate-800 text-sm">{s.label}</div>
            </div>
            <p className="text-xs text-slate-500 mt-1 flex-1">{s.desc}</p>
            <div className="flex gap-2 mt-3">
              <button onClick={() => scoreSample(s.file)} className="btn-primary text-xs py-1.5 px-3" disabled={loading}>
                Score now
              </button>
              <a href={`/samples/${s.file}`} download className="btn-ghost text-xs py-1.5 px-3">
                Download
              </a>
            </div>
          </div>
        ))}
      </div>

      {/* Dropzone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const f = e.dataTransfer.files?.[0];
          if (f) scoreFile(f);
        }}
        onClick={() => inputRef.current?.click()}
        className={`card border-2 border-dashed cursor-pointer p-10 text-center transition-colors ${
          dragOver ? "border-blue-500 bg-blue-50" : "border-slate-300 hover:border-blue-400"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) scoreFile(f); }}
        />
        <div className="text-4xl text-slate-300 mb-2">&#8681;</div>
        <div className="font-medium text-slate-700">
          {loading ? "Scoring accounts..." : "Drop a CSV here or click to browse"}
        </div>
        <div className="text-xs text-slate-500 mt-1">
          {fileName ? `Selected: ${fileName}` : "Columns must match the MSME schema (see sample files)"}
        </div>
      </div>

      {error && (
        <div className="card p-4 border-red-200 bg-red-50 text-sm text-red-700">{error}</div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <SummaryTile label="Accounts scored" value={String(results.length)} tone="blue" />
            <SummaryTile label="Red" value={String(counts.red || 0)} tone="red" />
            <SummaryTile label="Amber" value={String(counts.amber || 0)} tone="amber" />
            <SummaryTile label="Avg PD" value={`${avgPd.toFixed(1)}%`} tone="green" />
          </div>

          <Card title={`Scoring Results (${results.length})`}>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-500 border-b border-slate-200 text-left">
                    <th className="py-2.5 px-2 font-medium">Account</th>
                    <th className="py-2.5 px-2 font-medium">Segment</th>
                    <th className="py-2.5 px-2 font-medium text-right">PD</th>
                    <th className="py-2.5 px-2 font-medium text-center">Risk</th>
                    <th className="py-2.5 px-2 font-medium">Top Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r) => (
                    <tr key={r.account_id} className="border-b border-slate-100 hover:bg-blue-50/40">
                      <td className="py-2.5 px-2 font-mono text-xs font-medium text-slate-700">{r.account_id}</td>
                      <td className="py-2.5 px-2 text-xs text-slate-500">{r.segment.replace(/\|/g, " / ")}</td>
                      <td className="py-2.5 px-2 text-right font-mono font-semibold text-slate-800">{r.pd_percent}%</td>
                      <td className="py-2.5 px-2 text-center"><RagBadge rag={r.rag_bucket} /></td>
                      <td className="py-2.5 px-2 text-xs text-slate-600">{topReason(r)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

function SummaryTile({ label, value, tone }: { label: string; value: string; tone: string }) {
  const tones: Record<string, string> = {
    blue: "text-blue-700", red: "text-red-600", amber: "text-amber-600", green: "text-emerald-600",
  };
  return (
    <div className="card p-4">
      <div className="text-xs text-slate-500 uppercase tracking-wide">{label}</div>
      <div className={`text-2xl font-bold mt-1 ${tones[tone]}`}>{value}</div>
    </div>
  );
}
