"use client";

import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadialBarChart, RadialBar, PolarAngleAxis,
} from "recharts";
import { getAccountDetail, type PredictionResult } from "@/lib/api";
import { RagBadge, Card, Skeleton, ErrorState } from "@/components/ui";

function ragHex(rag: string): string {
  return { red: "#dc2626", amber: "#d97706", green: "#059669" }[rag] || "#64748b";
}

export default function AccountPage({ params }: { params: { account_id: string } }) {
  const [data, setData] = useState<PredictionResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getAccountDetail(params.account_id).then(setData).catch((e) => setError(e.message));
  }, [params.account_id]);

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
      <Card title="Explainability - Top Reason Codes">
        <p className="text-xs text-slate-500 -mt-2 mb-4">
          SHAP-based feature contributions driving this account&apos;s risk score.
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
    </div>
  );
}
