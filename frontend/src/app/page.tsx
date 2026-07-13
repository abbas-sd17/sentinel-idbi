"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie,
} from "recharts";
import {
  getPortfolioSummary, getAccounts, formatINR,
  type PortfolioSummary, type AccountRow,
} from "@/lib/api";
import { RagBadge, KpiCard, Card, Skeleton, ErrorState } from "@/components/ui";

const RAG_COLORS: Record<string, string> = { red: "#dc2626", amber: "#d97706", green: "#059669" };
const RAG_ORDER = ["red", "amber", "green"];
const RAG_TEXT: Record<string, string> = {
  red: "text-red-600",
  amber: "text-amber-600",
  green: "text-emerald-600",
};
const SMA_ORDER = ["Standard", "SMA-0", "SMA-1", "SMA-2"];
const SMA_TONES: Record<string, string> = {
  Standard: "bg-emerald-50 text-emerald-700 border-emerald-200",
  "SMA-0": "bg-amber-50 text-amber-700 border-amber-200",
  "SMA-1": "bg-orange-50 text-orange-700 border-orange-200",
  "SMA-2": "bg-red-50 text-red-700 border-red-200",
};
const PAGE_SIZE = 25;

export default function DashboardPage() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [accounts, setAccounts] = useState<AccountRow[]>([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState("");
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("predicted_pd");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [tableLoading, setTableLoading] = useState(false);

  useEffect(() => {
    getPortfolioSummary()
      .then(setSummary)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setTableLoading(true);
    const t = setTimeout(() => {
      getAccounts({
        rag: filter || undefined,
        search: search || undefined,
        sortBy,
        sortDir,
        limit: PAGE_SIZE,
        offset,
      })
        .then((a) => {
          setAccounts(a.accounts);
          setTotal(a.total);
        })
        .catch(() => {})
        .finally(() => setTableLoading(false));
    }, search ? 300 : 0);
    return () => clearTimeout(t);
  }, [filter, search, sortBy, sortDir, offset]);

  const ragData = useMemo(() => {
    if (!summary) return [];
    return RAG_ORDER.filter((r) => summary.rag_breakdown[r]).map((name) => ({
      name,
      value: summary.rag_breakdown[name] || 0,
      fill: RAG_COLORS[name],
    }));
  }, [summary]);

  function toggleSort(col: string) {
    if (sortBy === col) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(col);
      setSortDir("desc");
    }
  }

  if (error) return <ErrorState message={error} />;

  if (loading || !summary) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-72" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}
        </div>
        <div className="grid lg:grid-cols-3 gap-6">
          <Skeleton className="h-72" /><Skeleton className="h-72 lg:col-span-2" />
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  const metrics = summary.model_metrics;
  const redCount = summary.rag_breakdown.red || 0;
  const stages = summary.ifrs9_stage_breakdown || {};
  const stageLine = "Stage 3" in stages
    ? `Stage 3: ${stages["Stage 3"]}`
    : `Stage 2: ${stages["Stage 2"] ?? 0}`;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Portfolio Risk Overview</h1>
          <p className="text-slate-500 text-sm mt-1">
            12-month default early-warning across {summary.total_accounts.toLocaleString()} MSME loan accounts
          </p>
        </div>
        <div className="text-right">
          <div className="text-xs text-slate-500">Discrimination (held-out test)</div>
          <div className="text-lg font-bold text-blue-700">
            AUC {metrics.auc_roc ?? "N/A"}
            <span className="text-slate-300 mx-1">·</span>
            KS {metrics.ks_statistic ?? "N/A"}
            <span className="text-slate-300 mx-1">·</span>
            Gini {metrics.gini ?? "N/A"}
          </div>
          <div className="text-[11px] text-slate-400">bank-grade separation, honestly validated</div>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Total Exposure"
          value={formatINR(summary.total_exposure)}
          sub={`${summary.total_accounts.toLocaleString()} accounts`}
          accent="blue"
          icon={<span className="text-sm font-bold">&#8377;</span>}
        />
        <KpiCard
          label="Exposure at Risk"
          value={formatINR(summary.exposure_at_risk)}
          sub={`${redCount} red accounts`}
          accent="red"
          icon={<span className="text-base">&#9650;</span>}
        />
        <KpiCard
          label="ECL Provision (PD×LGD×EAD)"
          value={formatINR(summary.ecl_provision)}
          sub={`${stageLine} · ${summary.ecl_method}`}
          accent="amber"
          icon={<span className="text-base">&#8776;</span>}
        />
        <KpiCard
          label="Avg Probability of Default"
          value={`${(summary.avg_pd * 100).toFixed(1)}%`}
          sub={`Actual default rate ${(summary.default_rate_actual * 100).toFixed(1)}%`}
          accent="green"
          icon={<span className="text-base">&#8962;</span>}
        />
      </div>

      {/* RBI SMA strip */}
      <div className="card px-5 py-3 flex flex-wrap items-center gap-x-4 gap-y-2">
        <div className="text-xs font-medium text-slate-500 uppercase tracking-wide">
          RBI SMA view (trailing-12m worst)
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {SMA_ORDER.map((cat) => (
            <span
              key={cat}
              className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${SMA_TONES[cat]}`}
            >
              {cat}
              <span className="font-mono">{(summary.sma_breakdown?.[cat] ?? 0).toLocaleString()}</span>
            </span>
          ))}
        </div>
      </div>

      {/* Charts */}
      <div className="grid lg:grid-cols-3 gap-6">
        <Card title="RAG (Red / Amber / Green) Risk Distribution">
          <ResponsiveContainer width="100%" height={230}>
            <PieChart>
              <Pie data={ragData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={2} isAnimationActive={false}>
                {ragData.map((e) => <Cell key={e.name} fill={e.fill} />)}
              </Pie>
              <Tooltip formatter={(v: number, n: string) => [`${v} accounts`, n.toUpperCase()]} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 mt-2">
            {ragData.map((e) => (
              <div key={e.name} className="flex items-center gap-1.5 text-xs text-slate-600">
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: e.fill }} />
                {e.name} ({((e.value / summary.total_accounts) * 100).toFixed(0)}%)
              </div>
            ))}
          </div>
        </Card>

        <Card title="Sector Risk (avg PD)" className="lg:col-span-2">
          <ResponsiveContainer width="100%" height={230}>
            <BarChart data={summary.sector_risk} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
              <XAxis dataKey="sector" tick={{ fill: "#64748b", fontSize: 11 }} tickFormatter={(s: string) => s.replace("_", " ")} />
              <YAxis tick={{ fill: "#64748b", fontSize: 11 }} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
              <Tooltip
                formatter={(v: number, n: string) => n === "avg_pd" ? [`${(v * 100).toFixed(1)}%`, "Avg PD"] : [v, n]}
                labelFormatter={(l: string) => l.replace("_", " ")}
              />
              <Bar dataKey="avg_pd" radius={[6, 6, 0, 0]} isAnimationActive={false}>
                {summary.sector_risk.map((s, i) => {
                  const max = Math.max(...summary.sector_risk.map((x) => x.avg_pd), 0.0001);
                  const t = s.avg_pd / max;
                  const shade = t > 0.92 ? "#1e3a8a" : t > 0.8 ? "#1d4ed8" : "#3b82f6";
                  return <Cell key={i} fill={shade} />;
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Benchmarks */}
      {metrics.auc_roc && (
        <Card title="Model Benchmarks (synthetic holdout)">
          <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
            {[
              ["AUC-ROC", metrics.auc_roc],
              ["PR-AUC", metrics.pr_auc],
              ["KS", metrics.ks_statistic],
              ["Gini", metrics.gini],
              ["Recall", metrics.recall],
              ["Lift@10%", metrics.lift_at_10pct],
            ].map(([label, val]) => (
              <div key={String(label)} className="bg-blue-50/60 border border-blue-100 rounded-xl p-3 text-center">
                <div className="text-[11px] text-slate-500 uppercase tracking-wide">{label}</div>
                <div className="font-bold text-blue-700 text-lg">{val}</div>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-500 mt-3">{metrics.note as string}</p>
        </Card>
      )}

      {/* Account table */}
      <Card
        title="Accounts"
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <input
              value={search}
              onChange={(e) => { setSearch(e.target.value); setOffset(0); }}
              placeholder="Search account ID..."
              className="px-3 py-1.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-44"
            />
            <div className="flex gap-1">
              {["", "red", "amber", "green"].map((f) => (
                <button
                  key={f}
                  onClick={() => { setFilter(f); setOffset(0); }}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    filter === f ? "bg-blue-700 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  {f === "" ? "All" : f.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        }
      >
        <div className="text-xs text-slate-500 mb-2">
          Showing {total === 0 ? 0 : (offset + 1).toLocaleString()}&ndash;{(offset + accounts.length).toLocaleString()} of {total.toLocaleString()} matching accounts
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-500 border-b border-slate-200 text-left">
                <SortTh label="Account" col="account_id" {...{ sortBy, sortDir, toggleSort }} />
                <th className="py-2.5 px-2 font-medium">Sector</th>
                <th className="py-2.5 px-2 font-medium">Loan Type</th>
                <th className="py-2.5 px-2 font-medium">Profile</th>
                <SortTh label="Exposure" col="loan_amount" align="right" {...{ sortBy, sortDir, toggleSort }} />
                <SortTh label="PD" col="predicted_pd" align="right" {...{ sortBy, sortDir, toggleSort }} />
                <th className="py-2.5 px-2 font-medium text-center">Risk</th>
              </tr>
            </thead>
            <tbody className={tableLoading ? "opacity-50" : ""}>
              {accounts.map((a) => (
                <tr key={a.account_id} className="border-b border-slate-100 hover:bg-blue-50/40 transition-colors">
                  <td className="py-2.5 px-2">
                    <a href={`/account/${a.account_id}`} className="text-blue-700 hover:underline font-mono text-xs font-medium">
                      {a.account_id}
                    </a>
                  </td>
                  <td className="py-2.5 px-2 capitalize text-slate-700">{a.sector.replace("_", " ")}</td>
                  <td className="py-2.5 px-2 capitalize text-slate-700">{a.loan_type.replace("_", " ")}</td>
                  <td className="py-2.5 px-2 uppercase text-xs text-slate-500">{a.borrower_profile}</td>
                  <td className="py-2.5 px-2 text-right font-medium text-slate-700">{formatINR(a.loan_amount)}</td>
                  <td className={`py-2.5 px-2 text-right font-mono font-semibold ${RAG_TEXT[a.rag] || "text-slate-700"}`}>
                    {(a.predicted_pd * 100).toFixed(1)}%
                  </td>
                  <td className="py-2.5 px-2 text-center"><RagBadge rag={a.rag} /></td>
                </tr>
              ))}
              {accounts.length === 0 && !tableLoading && (
                <tr><td colSpan={7} className="py-10 text-center text-slate-400">No accounts match your filters</td></tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-100">
          <button
            onClick={() => setOffset((o) => Math.max(o - PAGE_SIZE, 0))}
            disabled={offset === 0 || tableLoading}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-slate-100"
          >
            &larr; Prev
          </button>
          <div className="text-xs text-slate-500">
            Page {Math.floor(offset / PAGE_SIZE) + 1} of {Math.max(Math.ceil(total / PAGE_SIZE), 1)}
          </div>
          <button
            onClick={() => setOffset((o) => o + PAGE_SIZE)}
            disabled={offset + PAGE_SIZE >= total || tableLoading}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-slate-100"
          >
            Next &rarr;
          </button>
        </div>
      </Card>
    </div>
  );
}

function SortTh({
  label, col, align = "left", sortBy, sortDir, toggleSort,
}: {
  label: string; col: string; align?: "left" | "right";
  sortBy: string; sortDir: string; toggleSort: (c: string) => void;
}) {
  const active = sortBy === col;
  return (
    <th
      onClick={() => toggleSort(col)}
      className={`py-2.5 px-2 font-medium cursor-pointer select-none hover:text-blue-700 ${align === "right" ? "text-right" : "text-left"}`}
    >
      {label}
      <span className="ml-1 text-[10px]">{active ? (sortDir === "asc" ? "\u25b2" : "\u25bc") : "\u21c5"}</span>
    </th>
  );
}
