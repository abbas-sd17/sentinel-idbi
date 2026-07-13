"use client";

import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Portfolio" },
  { href: "/upload", label: "Batch Scoring" },
];

export default function NavBar() {
  const pathname = usePathname();
  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <a href="/" className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-700 flex items-center justify-center text-white font-bold shadow-sm">
            S
          </div>
          <div className="leading-tight">
            <div className="font-bold text-slate-900">Sentinel</div>
            <div className="text-[11px] text-slate-500">MSME Default Early-Warning</div>
          </div>
        </a>

        <nav className="flex items-center gap-1">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className={`nav-link ${isActive(l.href) ? "nav-link-active" : ""}`}
            >
              {l.label}
            </a>
          ))}
        </nav>

        <div className="hidden sm:flex items-center gap-2 text-xs text-slate-500">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          IDBI Innovate 2026 &middot; Track 04
        </div>
      </div>
    </header>
  );
}
