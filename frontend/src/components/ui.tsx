"use client";

import type { ReactNode } from "react";

export function RagBadge({ rag, size = "sm" }: { rag: string; size?: "sm" | "lg" }) {
  const label = rag?.toUpperCase() || "-";
  const cls = `rag-${rag}`;
  const dot: Record<string, string> = {
    red: "bg-red-600",
    amber: "bg-amber-500",
    green: "bg-emerald-600",
  };
  return (
    <span className={`badge ${cls} ${size === "lg" ? "text-sm px-3 py-1" : ""}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dot[rag] || "bg-slate-400"}`} />
      {label}
    </span>
  );
}

export function KpiCard({
  label,
  value,
  sub,
  accent = "slate",
  icon,
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: "slate" | "blue" | "red" | "amber" | "green";
  icon?: ReactNode;
}) {
  const accents: Record<string, string> = {
    slate: "text-slate-900",
    blue: "text-blue-700",
    red: "text-red-600",
    amber: "text-amber-600",
    green: "text-emerald-600",
  };
  const iconBg: Record<string, string> = {
    slate: "bg-slate-100 text-slate-600",
    blue: "bg-blue-50 text-blue-700",
    red: "bg-red-50 text-red-600",
    amber: "bg-amber-50 text-amber-600",
    green: "bg-emerald-50 text-emerald-600",
  };
  return (
    <div className="card card-hover p-5">
      <div className="flex items-start justify-between">
        <div className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</div>
        {icon && (
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${iconBg[accent]}`}>
            {icon}
          </div>
        )}
      </div>
      <div className={`text-2xl font-bold mt-2 ${accents[accent]}`}>{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-1">{sub}</div>}
    </div>
  );
}

export function Card({
  title,
  children,
  actions,
  className = "",
}: {
  title?: string;
  children: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div className={`card p-5 ${className}`}>
      {(title || actions) && (
        <div className="flex items-center justify-between mb-4">
          {title && <h2 className="font-semibold text-slate-900">{title}</h2>}
          {actions}
        </div>
      )}
      {children}
    </div>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton ${className}`} />;
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="card p-6 border-red-200 bg-red-50">
      <p className="font-semibold text-red-700">Cannot connect to the scoring API</p>
      <p className="text-sm mt-2 text-red-600">{message}</p>
      <p className="text-xs mt-3 text-slate-500">
        Start the backend: <code className="bg-white px-1.5 py-0.5 rounded border">uvicorn app.main:app --reload</code>
      </p>
    </div>
  );
}
