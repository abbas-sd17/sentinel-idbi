"use client";

import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadialBarChart, RadialBar, PolarAngleAxis,
} from "recharts";
import {
  getAccountDetail, postDecision, getDecisions,
  type PredictionResult, type DecisionRecord,
} from "@/lib/api";
import { RagBadge, Card, Skeleton, ErrorState } from "@/components/ui";

function ragHex(rag: string): string {
  return { red: "#dc2626", amber: "#d97706", green: "#059669" }[rag] || "#64748b";
}

const DECISION_BUTTONS: { decision: "acknowledge" | "override" | "escalate"; label: string; cls: string }[] = [
  { decision: "acknowledge", label: "Acknowledge", cls: "bg-blue-700 hover:bg-blue-800" },
  { decision: "override", label: "Override", cls: "bg-amber-600 hover:bg-amber-700" },
  { decision: "escalate", label: "Escalate", cls: "bg-red-600 hover:bg-red-700" },
];

export default function AccountPage({ params }: { params: { account_id: string } }) {
  const [data, setData] = useState<PredictionResult | null>(null);
  const [error, setError] = useState("");
  const [officer, setOfficer] = useState("");
  const [note, setNote] = useState("");
  const [decisions, setDecisions] = useState<DecisionRecord[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [decisionError, setDecisionError] = useState("");

  useEffect(() => {
    getAccountDetail(params.account_id).then(setData).catch((e) => setError(e.message));
    getDecisions(params.account_id).then(setDecisions).catch(() => {});
  }, [params.account_id]);

  async function submitDecision(decision: "acknowledge" | "override" | "escalate") {
    setSubmitting(true);
    setDecisionError("");
    try {
      await postDecision({ account_id: params.account_id, decision, note, officer });
      setNote("");
      const list = await getDecisions(params.account_id);
      setDecisions(list);
    } catch (e) {
      setDecisionError(e instanceof Error ? e.message : "Failed to record decision");
    } finally {
      setSubmitting(false);
    }
  }

  if (error) return <ErrorState message={error} />;

  if (!data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid md:grid-cols-3 gap-4">
          <Skeleton className="h-52" /><Skeleton className="h-52 md:col-span-2" />
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  const color = ragHex(data.rag_bucket);
  const gaugeData = [{ name: "pd", value: data.pd_percent, fill: color }];
  const maxImpact = Math.max(...data.reason_codes.map((r) => Math.abs(r.impact)), 0.0001);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <a href="/" className="text-xs text-blue-700 hover:underline">&larr; Back to Portfolio</a>
          <h1 className="text-2xl font-bold mt-2 font-mono text-slate-900">{data.account_id}</h1>
          <p className="text-slate-500 text-sm mt-1">
            Segment: <span className="font-medium text-slate-700">{data.segment.replace(/\|/g, " / ")}</span>
          </p>
          <div className="flex flex-wrap gap-2 mt-3">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-700">
              Rating <span className="font-mono font-bold text-slate-900">{data.rating_grade}</span>
              <span className="text-slate-400">· {data.rating_band}</span>
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-700">
              IFRS-9 <span className="font-bold text-slate-900">{data.ifrs9_stage}</span>
              <span className="text-slate-400">· {data.ifrs9_basis}</span>
            </span>
            <span
              title={data.sma_definition}
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-700 cursor-help"
            >
              RBI SMA <span className="font-bold text-slate-900">{data.sma_category}</span>
            </span>
          </div>
        </div>
        <RagBadge rag={data.rag_bucket} size="lg" />
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        {/* PD gauge */}
        <Card>
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wide text-center">
            Probability of Default
          </div>
          <div className="relative">
            <ResponsiveContainer width="100%" height={190}>
              <RadialBarChart
                innerRadius="78%" outerRadius="100%" data={gaugeData}
                startAngle={220} endAngle={-40}
              >
                <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                <RadialBar background dataKey="value" cornerRadius={12} isAnimationActive={false} />
              </RadialBarChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <div className="text-3xl font-bold tracking-tight" style={{ color }}>{data.pd_percent}%</div>
              <div className="text-[11px] text-slate-500 mt-0.5">12-month PD</div>
            </div>
          </div>
        </Card>

        {/* Recommended action */}
        <Card className="md:col-span-2 flex flex-col">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">
            Recommended Early-Warning Action
          </div>
          <div
            className="rounded-xl p-4 flex-1 border"
            style={{ background: `${color}0d`, borderColor: `${color}33` }}
          >
            <p className="text-slate-800 leading-relaxed">{data.recommended_action}</p>
          </div>
          <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
            <span className="w-2 h-2 rounded-full bg-blue-600" />
            Model {data.model_version} &middot; scored {new Date(data.timestamp).toLocaleString()}
          </div>
        </Card>
      </div>

      {/* Hazard curve */}
      <Card title="12-Month Hazard Curve">
        <p className="text-xs text-slate-500 -mt-2 mb-3">
          Cumulative probability of default over the next 12 months, and the monthly marginal hazard.
        </p>
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={data.hazard_curve} margin={{ top: 5, right: 15, bottom: 5, left: 0 }}>
            <XAxis dataKey="month" tick={{ fill: "#64748b", fontSize: 12 }} label={{ value: "Month", position: "insideBottom", offset: -2, fill: "#94a3b8", fontSize: 11 }} />
            <YAxis tick={{ fill: "#64748b", fontSize: 12 }} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
            <Tooltip formatter={(v: number, n: string) => [`${(v * 100).toFixed(2)}%`, n === "cumulative_pd" ? "Cumulative PD" : "Monthly hazard"]} labelFormatter={(l) => `Month ${l}`} />
            <Line type="monotone" dataKey="cumulative_pd" stroke="#1d4ed8" strokeWidth={2.5} dot={false} isAnimationActive={false} />
            <Line type="monotone" dataKey="hazard" stroke="#d97706" strokeWidth={1.5} strokeDasharray="4 3" dot={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      {/* Reason codes */}
      <Card
        title="Explainability - Top Reason Codes"
        actions={
          <span
            className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
              data.explanation_method === "shap"
                ? "bg-blue-50 text-blue-700 border-blue-200"
                : "bg-slate-100 text-slate-600 border-slate-200"
            }`}
          >
            {data.explanation_method === "shap" ? "SHAP" : "Proxy"}
          </span>
        }
      >
        <p className="text-xs text-slate-500 -mt-2 mb-4">
          Feature contributions driving this account&apos;s risk score.
        </p>
        <div className="space-y-2.5">
          {data.reason_codes.map((rc) => {
            const up = rc.direction === "increases_risk";
            const width = (Math.abs(rc.impact) / maxImpact) * 100;
            return (
              <div key={rc.feature} className="flex items-center gap-3">
                <div className="w-56 shrink-0">
                  <div className="text-sm font-medium text-slate-800">{rc.description}</div>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="text-[10px] font-mono font-semibold text-slate-600 bg-slate-100 rounded px-1 py-0.5">{rc.code}</span>
                    <span className="text-[11px] text-slate-400">{rc.category}</span>
                  </div>
                </div>
                <div className="flex-1 h-6 bg-slate-100 rounded-md overflow-hidden relative">
                  <div
                    className={`h-full ${up ? "bg-red-500" : "bg-emerald-500"}`}
                    style={{ width: `${Math.max(width, 4)}%` }}
                  />
                </div>
                <div className={`w-24 text-right text-sm font-mono font-semibold ${up ? "text-red-600" : "text-emerald-600"}`}>
                  {rc.impact > 0 ? "+" : ""}{rc.impact.toFixed(4)}
                </div>
              </div>
            );
          })}
        </div>
        <div className="mt-4 flex items-center gap-4 text-xs text-slate-500">
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-red-500" /> increases risk</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-emerald-500" /> decreases risk</span>
        </div>
        <p className="text-xs text-slate-400 mt-3 border-t border-slate-100 pt-3">
          AI advisory only. Final credit decision remains with the human underwriter (RBI AI norms).
        </p>
      </Card>

      {/* Officer decision */}
      <Card title="Officer Decision (Human-in-the-loop)">
        <p className="text-xs text-slate-500 -mt-2 mb-4">
          Record how you are acting on this model output. Every decision is logged with the model&apos;s PD and RAG at the time.
        </p>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-500 uppercase tracking-wide mb-1.5">
              Officer name
            </label>
            <input
              value={officer}
              onChange={(e) => setOfficer(e.target.value)}
              placeholder="e.g. R. Sharma"
              className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 uppercase tracking-wide mb-1.5">
              Note
            </label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Rationale, follow-up actions, borrower contact..."
              rows={2}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            />
          </div>
        </div>
        <div className="flex flex-wrap gap-2 mt-4">
          {DECISION_BUTTONS.map((b) => (
            <button
              key={b.decision}
              onClick={() => submitDecision(b.decision)}
              disabled={!officer.trim() || submitting}
              className={`px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${b.cls}`}
            >
              {b.label}
            </button>
          ))}
          {!officer.trim() && (
            <span className="text-xs text-slate-400 self-center">Enter your name to enable decisions</span>
          )}
        </div>
        {decisionError && (
          <div className="card p-4 border-red-200 bg-red-50 text-sm text-red-700 mt-4">{decisionError}</div>
        )}
        {decisions.length > 0 && (
          <div className="mt-5 border-t border-slate-100 pt-4">
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-3">
              Decision Log ({decisions.length})
            </div>
            <div className="space-y-2">
              {decisions.map((d, i) => (
                <div key={`${d.timestamp}-${i}`} className="rounded-xl border border-slate-200 bg-slate-50/60 px-3 py-2.5">
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <span className={`badge ${
                      d.decision === "escalate" ? "rag-red" : d.decision === "override" ? "rag-amber" : "rag-green"
                    }`}>
                      {d.decision}
                    </span>
                    <span className="font-medium text-slate-700">{d.officer}</span>
                    <span className="text-slate-400">
                      · PD {(d.model_pd * 100).toFixed(1)}% · {d.model_rag?.toUpperCase()}
                    </span>
                    <span className="text-slate-400 ml-auto">{new Date(d.timestamp).toLocaleString()}</span>
                  </div>
                  {d.note && <p className="text-sm text-slate-600 mt-1.5">{d.note}</p>}
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
