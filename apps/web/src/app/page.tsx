"use client";

import React, { useState } from "react";
import { ChatView } from "@/components/chat/ChatView";
import { MoonshotView } from "@/components/moonshot/MoonshotView";
import { CfoDashboard } from "@/components/cfo";
import {
  MessageSquare,
  Compass,
  BarChart3,
  Split,
  Database,
  Cpu,
  ShieldCheck,
  Search,
  Sparkles,
  Layers,
  Activity,
  ArrowUpRight,
  TrendingUp,
  Zap,
  CheckCircle2,
  ExternalLink,
} from "lucide-react";

export type NavPart = "chat" | "cfo" | "moonshot" | "merged";

export default function UnifiedSystemCockpit() {
  const [activePart, setActivePart] = useState<NavPart>("merged");
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <div className="flex h-screen w-screen overflow-hidden p-3 gap-3 bg-[#070c18]">
      {/* ============================================================== */}
      {/* 1. LEFT NAVIGATION RAIL (Image 1 Style: Neumorphic Clay + Glass) */}
      {/* ============================================================== */}
      <aside className="w-72 flex-shrink-0 flex flex-col justify-between p-4 rounded-3xl glass-panel border border-white/10 shadow-2xl relative overflow-hidden">
        {/* Ambient Top Glow Orb */}
        <div className="absolute -top-16 -left-16 w-44 h-44 rounded-full bg-cyan-500/15 blur-3xl pointer-events-none" />
        <div className="absolute top-1/2 -right-20 w-44 h-44 rounded-full bg-purple-500/15 blur-3xl pointer-events-none" />

        {/* Top Profile & Brand Header */}
        <div className="relative z-10 flex flex-col items-center text-center pb-4 border-b border-white/10">
          <div className="relative mb-3 group cursor-pointer">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-cyan-600 via-indigo-600 to-purple-600 p-[2px] shadow-[0_0_25px_rgba(56,189,248,0.35)] transition-transform duration-300 group-hover:scale-105">
              <div className="w-full h-full rounded-2xl bg-slate-950/90 flex items-center justify-center backdrop-blur-xl">
                <Sparkles className="w-8 h-8 text-cyan-400" />
              </div>
            </div>
            <span className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-emerald-500 border-2 border-slate-950 animate-pulse" />
          </div>

          <h2 className="text-base font-bold text-white tracking-wide font-mono flex items-center space-x-1.5">
            <span>NeuralCFO</span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-300 border border-cyan-800">
              v1.0
            </span>
          </h2>
          <p className="text-[11px] text-slate-400 font-mono mt-0.5">
            Acme Digital Agency (Demo Org)
          </p>
        </div>

        {/* Middle Navigation Group: 3 Distinct Parts */}
        <div className="relative z-10 flex-1 py-4 flex flex-col space-y-2 overflow-y-auto">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 px-3 mb-1">
            System Modules
          </div>

          {/* Part 1: Chat Copilot */}
          <button
            onClick={() => setActivePart("chat")}
            className={`w-full flex items-center space-x-3 px-3.5 py-3 rounded-2xl text-left transition-all ${
              activePart === "chat"
                ? "glass-pill-active font-semibold shadow-lg"
                : "glass-pill text-slate-300 hover:text-white"
            }`}
          >
            <div className="p-2 rounded-xl bg-slate-900/80 border border-white/10 text-cyan-400">
              <MessageSquare className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-semibold leading-tight font-mono">
                [1] Chat Co-Pilot
              </div>
              <div className="text-[10px] text-slate-400 truncate">
                Conversational CFO & Actions
              </div>
            </div>
          </button>

          {/* Part 2: CFO Mode */}
          <button
            onClick={() => setActivePart("cfo")}
            className={`w-full flex items-center space-x-3 px-3.5 py-3 rounded-2xl text-left transition-all ${
              activePart === "cfo"
                ? "glass-pill-active font-semibold shadow-lg"
                : "glass-pill text-slate-300 hover:text-white"
            }`}
          >
            <div className="p-2 rounded-xl bg-slate-900/80 border border-white/10 text-emerald-400">
              <BarChart3 className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-semibold leading-tight font-mono">
                [2] CFO Finance Engine
              </div>
              <div className="text-[10px] text-slate-400 truncate">
                Runway, Scenarios & Zetaris
              </div>
            </div>
          </button>

          {/* Part 3: Moonshot Mode */}
          <button
            onClick={() => setActivePart("moonshot")}
            className={`w-full flex items-center space-x-3 px-3.5 py-3 rounded-2xl text-left transition-all ${
              activePart === "moonshot"
                ? "glass-pill-active font-semibold shadow-lg text-purple-300"
                : "glass-pill text-slate-300 hover:text-white"
            }`}
          >
            <div className="p-2 rounded-xl bg-slate-900/80 border border-white/10 text-purple-400">
              <Compass className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-semibold leading-tight font-mono">
                [3] Moonshot Engine
              </div>
              <div className="text-[10px] text-slate-400 truncate">
                8-Stage Reasoning & Levers
              </div>
            </div>
          </button>

          {/* Dual Unified Cockpit */}
          <div className="pt-2">
            <button
              onClick={() => setActivePart("merged")}
              className={`w-full flex items-center space-x-3 px-3.5 py-3 rounded-2xl text-left transition-all ${
                activePart === "merged"
                  ? "bg-gradient-to-r from-cyan-600/30 to-purple-600/30 border border-cyan-400/50 shadow-[0_0_20px_rgba(56,189,248,0.25)] text-cyan-200 font-semibold"
                  : "glass-pill text-slate-300 hover:text-white"
              }`}
            >
              <div className="p-2 rounded-xl bg-cyan-950/60 border border-cyan-800 text-cyan-400">
                <Split className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-semibold leading-tight font-mono">
                  [Merged Cockpit]
                </div>
                <div className="text-[10px] text-slate-400 truncate">
                  Side-by-side Dual View
                </div>
              </div>
            </button>
          </div>
        </div>

        {/* Bottom Sponsor Technologies & System Health Capsule */}
        <div className="relative z-10 pt-3 border-t border-white/10 flex flex-col space-y-2 text-xs font-mono">
          <div className="p-2.5 rounded-xl bg-slate-950/60 border border-white/5 space-y-1.5">
            <div className="flex items-center justify-between text-[10px]">
              <span className="text-slate-400 flex items-center space-x-1">
                <Database className="w-3 h-3 text-cyan-400" />
                <span>Zetaris Data</span>
              </span>
              <span className="px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-[9px]">
                Active
              </span>
            </div>

            <div className="flex items-center justify-between text-[10px]">
              <span className="text-slate-400 flex items-center space-x-1">
                <Cpu className="w-3 h-3 text-purple-400" />
                <span>Meterless Memory</span>
              </span>
              <span className="px-1.5 py-0.2 rounded bg-purple-950 text-purple-300 border border-purple-800 text-[9px]">
                Tracing
              </span>
            </div>

            <div className="flex items-center justify-between text-[10px] pt-1 border-t border-white/5">
              <span className="text-slate-500">RBAC Role</span>
              <span className="text-slate-300">Member</span>
            </div>
          </div>
        </div>
      </aside>

      {/* ============================================================== */}
      {/* 2. MAIN WORKSPACE WITH LIQUID GLASS KIT STYLING (Image 2 Style) */}
      {/* ============================================================== */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden space-y-3">
        {/* Top Liquid Glass Cockpit Header */}
        <header className="glass-panel rounded-2xl px-5 py-3 flex items-center justify-between gap-4 border border-white/10 shadow-lg">
          {/* Search bar with glowing glass aesthetics */}
          <div className="flex-1 max-w-md relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Ask NeuralCFO anything about runway, hiring, or bold moves..."
              className="w-full bg-slate-950/70 border border-white/10 rounded-xl pl-9 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition-colors font-mono"
            />
          </div>

          {/* Quick Metrics Bar (Claymorphic / Soft 3D Style) */}
          <div className="hidden lg:flex items-center space-x-3 text-xs font-mono">
            <div className="px-3 py-1.5 rounded-xl glass-card border border-white/10 flex items-center space-x-2">
              <span className="text-slate-400 text-[11px]">Runway:</span>
              <strong className="text-emerald-400 font-bold">18.4 w</strong>
            </div>

            <div className="px-3 py-1.5 rounded-xl glass-card border border-white/10 flex items-center space-x-2">
              <span className="text-slate-400 text-[11px]">Floor Reserve:</span>
              <strong className="text-cyan-300 font-bold">$45,000</strong>
            </div>

            <div className="px-3 py-1.5 rounded-xl glass-card border border-white/10 flex items-center space-x-2">
              <span className="text-slate-400 text-[11px]">Moonshot Fit:</span>
              <strong className="text-purple-300 font-bold">88.5 ROC</strong>
            </div>
          </div>

          {/* Active Navigation Badge */}
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-mono px-3 py-1 rounded-full bg-cyan-950/70 text-cyan-300 border border-cyan-700/60 flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
              <span className="uppercase font-semibold">
                {activePart === "merged" ? "Dual Merged View" : `Part: ${activePart}`}
              </span>
            </span>
          </div>
        </header>

        {/* Dynamic Workspace Container */}
        <div className="flex-1 min-h-0 overflow-hidden">
          {/* ============================================================== */}
          {/* OPTION A: DUAL MERGED VIEW (Side-by-side synchronized) */}
          {/* ============================================================== */}
          {activePart === "merged" && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 h-full">
              {/* Left Column: Chat Co-Pilot (44% width) */}
              <div className="lg:col-span-5 flex flex-col glass-panel rounded-2xl p-3 border border-white/10 shadow-xl overflow-hidden h-full">
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-white/10 text-xs font-mono">
                  <div className="flex items-center space-x-2 text-cyan-400 font-semibold">
                    <MessageSquare className="w-4 h-4" />
                    <span>[PART 1] CONVERSATIONAL COPILOT & GATEWAY</span>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                    SSE Live
                  </span>
                </div>
                <div className="flex-1 overflow-hidden">
                  <ChatView compact={true} />
                </div>
              </div>

              {/* Right Column: Moonshot 8-Stage Cockpit (56% width) */}
              <div className="lg:col-span-7 flex flex-col glass-panel rounded-2xl p-3 border border-white/10 shadow-xl overflow-y-auto h-full">
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-white/10 text-xs font-mono sticky top-0 bg-slate-900/95 backdrop-blur z-20">
                  <div className="flex items-center space-x-2 text-purple-300 font-semibold">
                    <Compass className="w-4 h-4" />
                    <span>[PART 3] MOONSHOT 8-STAGE REASONING & LEVERS</span>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800">
                    SHA-256 Citations Active
                  </span>
                </div>
                <MoonshotView compact={true} />
              </div>
            </div>
          )}

          {/* ============================================================== */}
          {/* OPTION B: FULL SCREEN CHAT COPILOT */}
          {/* ============================================================== */}
          {activePart === "chat" && (
            <div className="h-full glass-panel rounded-2xl p-4 border border-white/10 shadow-xl overflow-hidden">
              <ChatView compact={false} />
            </div>
          )}

          {/* ============================================================== */}
          {/* OPTION C: FULL SCREEN CFO FINANCE ENGINE */}
          {/* ============================================================== */}
          {activePart === "cfo" && (
            <div className="h-full glass-panel rounded-2xl p-4 border border-white/10 shadow-xl overflow-y-auto">
              <CfoDashboard />
            </div>
          )}

          {/* ============================================================== */}
          {/* OPTION D: FULL SCREEN MOONSHOT STRATEGIC ENGINE */}
          {/* ============================================================== */}
          {activePart === "moonshot" && (
            <div className="h-full glass-panel rounded-2xl p-4 border border-white/10 shadow-xl overflow-y-auto">
              <MoonshotView compact={false} />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
