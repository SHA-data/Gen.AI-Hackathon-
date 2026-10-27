import React from "react";
import Link from "next/link";
import "./globals.css";
import { EvidenceDrawerProvider } from "@/components/evidence/EvidenceDrawer";

export const metadata = {
  title: "NeuralCFO + Moonshot Mode (Unified System)",
  description: "Unified AI Decision Engine for Small Business Finance & Strategy",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 min-h-screen flex flex-col font-sans">
        <EvidenceDrawerProvider>
          {/* Global Header */}
          <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40">
            <div className="max-w-[1750px] mx-auto px-4 h-14 flex items-center justify-between">
              <div className="flex items-center space-x-6">
                <Link href="/" className="flex items-center space-x-2 font-bold text-lg text-emerald-400">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span>NeuralCFO</span>
                  <span className="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono">
                    UNIFIED
                  </span>
                </Link>
                <nav className="flex space-x-4 text-sm font-medium text-slate-400">
                  <Link href="/" className="hover:text-emerald-400 transition-colors font-mono text-xs uppercase px-2 py-1 rounded bg-slate-800 text-slate-200">
                    [Merged Suite]
                  </Link>
                  <Link href="/chat" className="hover:text-slate-200 transition-colors text-xs font-mono">
                    Chat Gateway
                  </Link>
                  <Link href="/moonshot" className="hover:text-slate-200 transition-colors text-xs font-mono">
                    Moonshot Mode
                  </Link>
                  <Link href="/cfo" className="hover:text-slate-200 transition-colors text-xs font-mono">
                    CFO Mode
                  </Link>
                </nav>
              </div>
              <div className="flex items-center space-x-3 text-xs">
                <span className="px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700 font-mono">
                  Org: <strong className="text-emerald-400">Acme Agency Demo</strong>
                </span>
                <span className="px-2 py-1 rounded bg-blue-950 text-blue-300 border border-blue-800 font-mono text-[11px]">
                  Role: Member
                </span>
              </div>
            </div>
          </header>

          {/* Main Workspace Area */}
          <main className="flex-1 max-w-[1750px] w-full mx-auto p-4 flex flex-col">
            {children}
          </main>
        </EvidenceDrawerProvider>
      </body>
    </html>
  );
}
