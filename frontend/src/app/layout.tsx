import type { Metadata } from "next";
import "./globals.css";
import NavBar from "@/components/NavBar";

export const metadata: Metadata = {
  title: "Sentinel | MSME Default Early-Warning",
  description: "IDBI Innovate 2026 - Track 04 Default Prediction System",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-slate-100 text-slate-900 antialiased">
        <NavBar />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">{children}</main>
        <footer className="max-w-7xl mx-auto px-4 sm:px-6 py-8 mt-8 border-t border-slate-200 text-xs text-slate-500 flex flex-wrap items-center justify-between gap-2">
          <span>Sentinel &middot; Explainable AI for MSME credit risk</span>
          <span>Synthetic data (DPDP-safe) &middot; AI advisory only, human-in-the-loop per RBI norms</span>
        </footer>
      </body>
    </html>
  );
}
