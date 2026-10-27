"use client";

import React, { useState, useMemo } from "react";
import { ChatView } from "@/components/chat/ChatView";
import { MoonshotView } from "@/components/moonshot/MoonshotView";
import { CfoDashboard } from "@/components/cfo";
import {
  MessageSquare,
  Compass,
  BarChart3,
  LayoutDashboard,
  Search,
  Sparkles,
  Zap,
  Play,
  Heart,
  Clock,
  Flame,
  Music,
  Bell,
  ChevronDown,
  ShieldCheck,
  Plus,
  Sliders,
  Check,
  Layers,
  ArrowRight,
  TrendingUp,
} from "lucide-react";

export type NavPart = "overview" | "chat" | "cfo" | "moonshot";

export default function UnifiedSystemCockpit() {
  const [activePart, setActivePart] = useState<NavPart>("overview");
  const [searchQuery, setSearchQuery] = useState("");

  // =========================================================================
  // REAL FINANCIAL LEVER SIMULATION LOGIC
  // =========================================================================
  const [leverTab, setLeverTab] = useState<"capital" | "staff" | "terms">("capital");
  const [retainerActive, setRetainerActive] = useState<boolean>(true);
  const [delayDefenseActive, setDelayDefenseActive] = useState<boolean>(false);
  const [covenantActive, setCovenantActive] = useState<boolean>(true);
  const [prepayRate, setPrepayRate] = useState<number>(40); // 0% to 100%

  // Real Small Business Cash Calculations:
  // Baseline Cash: $120,000 | Baseline Runway: 18.4 weeks
  const calculatedDelta = useMemo(() => {
    let delta = (prepayRate / 100) * 45000;
    if (retainerActive) delta += 15000;
    if (delayDefenseActive) delta += 12000;
    if (leverTab === "staff") delta -= 14000; // Dev payroll burden
    return Math.round(delta);
  }, [prepayRate, retainerActive, delayDefenseActive, leverTab]);

  const simulatedRunwayWeeks = useMemo(() => {
    const baseWeeks = 18.4;
    const additionalWeeks = (calculatedDelta / 28250) * 4.33;
    const res = Number((baseWeeks + additionalWeeks).toFixed(1));
    return res > 0 ? res : 0.0;
  }, [calculatedDelta]);

  const projectedCash = useMemo(() => {
    return 120000 + calculatedDelta;
  }, [calculatedDelta]);

  return (
    <div className="flex h-screen w-screen overflow-hidden p-2.5 gap-2.5 font-sans">
      {/* ============================================================== */}
      {/* 1. LEFT NAVIGATION RAIL (Image 1 Style: Deep Navy Claymorphic)  */}
      {/* ============================================================== */}
      <aside className="w-60 flex-shrink-0 flex flex-col justify-between p-3.5 clay-sidebar text-slate-200 relative overflow-hidden">
        {/* Subtle Ambient Backlights */}
        <div className="absolute -top-10 -left-10 w-40 h-40 rounded-full bg-cyan-500/15 blur-3xl pointer-events-none" />
        <div className="absolute bottom-16 -right-10 w-40 h-40 rounded-full bg-purple-500/15 blur-3xl pointer-events-none" />

        {/* Top Profile / User Avatar (Image 1 Style) */}
        <div className="relative z-10 flex flex-col items-center text-center pb-2.5">
          <div className="relative mb-2 group cursor-pointer">
            <div className="w-14 h-14 rounded-full bg-gradient-to-tr from-cyan-400 via-indigo-500 to-purple-500 p-[2.5px] shadow-[0_8px_20px_rgba(0,0,0,0.4)] transition-transform duration-300 group-hover:scale-105 flex items-center justify-center">
              <div className="w-full h-full rounded-full bg-[#1e293b] flex items-center justify-center overflow-hidden border-2 border-white/20">
                <Music className="w-7 h-7 text-cyan-300" />
              </div>
            </div>
            <span className="absolute bottom-0 right-0 w-3.5 h-3.5 rounded-full bg-emerald-400 border-2 border-[#182337] shadow-sm animate-pulse" />
          </div>

          <h2 className="text-sm font-bold text-white tracking-wide font-mono">
            Hi, Aryan!
          </h2>
          <p className="text-[10px] text-slate-400 font-mono">
            Acme Digital Agency
          </p>
        </div>

        {/* Navigation Items (Image 1 Style) */}
        <nav className="relative z-10 flex-1 py-1 flex flex-col space-y-1.5 overflow-y-auto">
          {/* Dashboard / Executive Overview */}
          <button
            onClick={() => setActivePart("overview")}
            className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-2xl text-left transition-all ${
              activePart === "overview"
                ? "clay-sidebar-item-active font-bold text-slate-900 shadow-md"
                : "clay-sidebar-item text-slate-300 hover:text-white"
            }`}
          >
            <div className={`p-1.5 rounded-xl ${activePart === "overview" ? "bg-slate-800 text-cyan-400" : "bg-slate-800/80 text-cyan-400"}`}>
              <LayoutDashboard className="w-4 h-4" />
            </div>
            <span className="text-xs font-semibold tracking-wide">
              Dashboard
            </span>
          </button>

          {/* Part 1: Chat Co-Pilot */}
          <button
            onClick={() => setActivePart("chat")}
            className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-2xl text-left transition-all ${
              activePart === "chat"
                ? "clay-sidebar-item-active font-bold text-slate-900 shadow-md"
                : "clay-sidebar-item text-slate-300 hover:text-white"
            }`}
          >
            <div className={`p-1.5 rounded-xl ${activePart === "chat" ? "bg-slate-800 text-emerald-400" : "bg-slate-800/80 text-emerald-400"}`}>
              <MessageSquare className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <span className="text-xs font-semibold tracking-wide block truncate">
                [Part 1] Chat Co-Pilot
              </span>
            </div>
          </button>

          {/* Part 2: CFO Matrix */}
          <button
            onClick={() => setActivePart("cfo")}
            className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-2xl text-left transition-all ${
              activePart === "cfo"
                ? "clay-sidebar-item-active font-bold text-slate-900 shadow-md"
                : "clay-sidebar-item text-slate-300 hover:text-white"
            }`}
          >
            <div className={`p-1.5 rounded-xl ${activePart === "cfo" ? "bg-slate-800 text-blue-400" : "bg-slate-800/80 text-blue-400"}`}>
              <BarChart3 className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <span className="text-xs font-semibold tracking-wide block truncate">
                [Part 2] CFO Matrix
              </span>
            </div>
          </button>

          {/* Part 3: Moonshot Studio */}
          <button
            onClick={() => setActivePart("moonshot")}
            className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-2xl text-left transition-all ${
              activePart === "moonshot"
                ? "clay-sidebar-item-active font-bold text-slate-900 shadow-md"
                : "clay-sidebar-item text-slate-300 hover:text-white"
            }`}
          >
            <div className={`p-1.5 rounded-xl ${activePart === "moonshot" ? "bg-slate-800 text-purple-400" : "bg-slate-800/80 text-purple-400"}`}>
              <Compass className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <span className="text-xs font-semibold tracking-wide block truncate">
                [Part 3] Moonshot Studio
              </span>
            </div>
          </button>

          {/* Secondary Links from Image 1 */}
          <div className="pt-2 border-t border-white/10 space-y-1">
            <button
              onClick={() => setActivePart("cfo")}
              className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-left text-slate-400 hover:text-slate-200 transition-colors"
            >
              <Heart className="w-3.5 h-3.5 text-rose-400" />
              <span className="text-xs font-medium">Favorites & Levers</span>
            </button>

            <button
              onClick={() => setActivePart("chat")}
              className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-left text-slate-400 hover:text-slate-200 transition-colors"
            >
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              <span className="text-xs font-medium">Activity & Audit</span>
            </button>
          </div>
        </nav>

        {/* Bottom Banner Card (Image 1 "Go Premium" card style) */}
        <div className="relative z-10 pt-2">
          <div className="p-3 rounded-2xl clay-dark-card border border-white/10 flex flex-col items-center text-center space-y-1.5">
            <div className="w-7 h-7 rounded-full bg-cyan-950/80 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-sm">
              <ShieldCheck className="w-3.5 h-3.5" />
            </div>
            <div>
              <div className="text-[10px] font-bold text-white tracking-wide">
                NeuralCFO Sovereign
              </div>
              <div className="text-[9px] text-slate-400 leading-tight">
                Zetaris Data & Meterless Verified
              </div>
            </div>
            <button
              onClick={() => setActivePart("cfo")}
              className="w-full py-1.5 px-3 rounded-xl clay-pill-sage text-[10px] tracking-wide shadow-md"
            >
              Live Health Status
            </button>
          </div>
        </div>
      </aside>

      {/* ============================================================== */}
      {/* 2. MAIN WORKSPACE AREA                                         */}
      {/* ============================================================== */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden space-y-2.5">
        {/* Top Header Bar (Image 1 Style) */}
        <header className="flex items-center justify-between gap-4 py-0.5">
          {/* Page Title */}
          <h1 className="text-xl font-black text-slate-900 tracking-tight font-sans">
            {activePart === "overview" && "Dashboard"}
            {activePart === "chat" && "Chat Co-Pilot"}
            {activePart === "cfo" && "CFO Finance Engine"}
            {activePart === "moonshot" && "Moonshot Strategic Studio"}
          </h1>

          {/* Search Pill (Image 1 Style: Debossed inset pill) */}
          <div className="flex-1 max-w-md relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-4 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search for scenarios, runway, models..."
              className="w-full clay-card-inset py-1.5 pl-9 pr-4 text-xs text-slate-800 placeholder-slate-500 focus:outline-none transition-all font-sans font-medium"
            />
          </div>

          {/* Right Header Buttons (Image 1 Style) */}
          <div className="flex items-center space-x-2">
            {/* Notification Bell */}
            <button className="w-9 h-9 clay-btn flex items-center justify-center text-slate-600 hover:text-slate-900 relative">
              <Bell className="w-3.5 h-3.5" />
              <span className="w-2 h-2 rounded-full bg-cyan-500 absolute top-2 right-2 shadow-sm" />
            </button>

            {/* Profile Squircle */}
            <button
              onClick={() => setActivePart("overview")}
              className="w-9 h-9 clay-btn flex items-center justify-center text-slate-700 font-bold text-xs"
            >
              <div className="w-5 h-5 rounded-full bg-[#648283] text-white flex items-center justify-center text-[9px]">
                A
              </div>
            </button>
          </div>
        </header>

        {/* Dynamic Navigable Content */}
        <div className="flex-1 min-h-0 overflow-y-auto">
          {/* ============================================================== */}
          {/* PART 0: DASHBOARD OVERVIEW (Image 1 + 2 + New Clay references) */}
          {/* ============================================================== */}
          {activePart === "overview" && (
            <div className="space-y-2.5 pb-2">
              {/* Hero Banner Card (Image 1 Style: Dark curved card with 3D headphone icon & CTA) */}
              <div className="relative clay-dark-card p-4 overflow-hidden flex items-center justify-between text-white shadow-xl">
                <div className="absolute top-0 right-0 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
                <div className="relative z-10 max-w-lg space-y-1">
                  <div className="flex items-center space-x-2 text-cyan-400 text-[11px] font-mono">
                    <Music className="w-3 h-3" />
                    <span>NeuralCFO Multi-Agent Decision Engine</span>
                  </div>
                  <h2 className="text-lg font-bold tracking-tight">
                    Good Evening, Aryan!
                  </h2>
                  <p className="text-xs text-slate-300 leading-relaxed font-sans">
                    Your small business runway is currently solvent at <strong className="text-emerald-400">18.4 weeks</strong>. 
                    Simulate hiring 2 developers or deploy upfront retainers to push cash reserves past <strong className="text-cyan-300">${(projectedCash).toLocaleString()}</strong>.
                  </p>
                  <div className="pt-1 flex items-center space-x-2.5">
                    <button
                      onClick={() => setActivePart("cfo")}
                      className="px-4 py-1.5 clay-pill-sage text-xs flex items-center space-x-1.5 shadow-md"
                    >
                      <Play className="w-3 h-3 fill-current" />
                      <span>Play Simulation</span>
                    </button>
                    <button
                      onClick={() => setActivePart("chat")}
                      className="px-3.5 py-1.5 rounded-full bg-white/10 hover:bg-white/20 text-white text-xs font-semibold backdrop-blur-md border border-white/20 transition-colors"
                    >
                      Ask AI Co-Pilot
                    </button>
                  </div>
                </div>

                {/* 3D Visual Mascot / Art Element */}
                <div className="hidden md:flex relative z-10 w-24 h-24 rounded-3xl bg-gradient-to-tr from-cyan-500/20 via-indigo-500/20 to-purple-500/20 border border-white/10 items-center justify-center backdrop-blur-xl shadow-xl">
                  <Sparkles className="w-10 h-10 text-cyan-300 animate-pulse" />
                </div>
              </div>

              {/* 4 Raised Clay Cushion Metric Cards */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
                {/* Metric 1: Cash Runway */}
                <div className="clay-cushion p-3.5 space-y-1">
                  <div className="w-8 h-8 clay-squircle flex items-center justify-center text-[#648283]">
                    <Music className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-[10px] font-bold text-slate-500">
                      Cash Runway
                    </div>
                    <div className="text-xl font-black text-slate-900 tracking-tight font-sans">
                      {simulatedRunwayWeeks} w
                    </div>
                    <div className="text-[9px] font-bold text-[#648283]">
                      +{(((simulatedRunwayWeeks - 18.4) / 18.4) * 100).toFixed(0)}% simulated gain
                    </div>
                  </div>
                </div>

                {/* Metric 2: Floor Reserve */}
                <div className="clay-cushion p-3.5 space-y-1">
                  <div className="w-8 h-8 clay-squircle flex items-center justify-center text-[#cb7a72]">
                    <Heart className="w-4 h-4 fill-current" />
                  </div>
                  <div>
                    <div className="text-[10px] font-bold text-slate-500">
                      Floor Reserve
                    </div>
                    <div className="text-xl font-black text-slate-900 tracking-tight font-sans">
                      ${Math.round(projectedCash / 1000)}k
                    </div>
                    <div className="text-[9px] font-bold text-[#cb7a72]">
                      +${(calculatedDelta).toLocaleString()} safe buffer
                    </div>
                  </div>
                </div>

                {/* Metric 3: Reversibility */}
                <div className="clay-cushion p-3.5 space-y-1">
                  <div className="w-8 h-8 clay-squircle flex items-center justify-center text-[#4c6b6c]">
                    <Clock className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-[10px] font-bold text-slate-500">
                      Reversibility
                    </div>
                    <div className="text-xl font-black text-slate-900 tracking-tight font-sans">
                      &lt; $5k
                    </div>
                    <div className="text-[9px] font-bold text-emerald-700">
                      14-day window
                    </div>
                  </div>
                </div>

                {/* Metric 4: Proof Streak */}
                <div className="clay-cushion p-3.5 space-y-1">
                  <div className="w-8 h-8 clay-squircle flex items-center justify-center text-[#8e7ca8]">
                    <Flame className="w-4 h-4 fill-current" />
                  </div>
                  <div>
                    <div className="text-[10px] font-bold text-slate-500">
                      Proof Streak
                    </div>
                    <div className="text-xl font-black text-slate-900 tracking-tight font-sans">
                      100%
                    </div>
                    <div className="text-[9px] font-bold text-[#8e7ca8]">
                      0 unverified claims
                    </div>
                  </div>
                </div>
              </div>

              {/* Middle Row: Runway Bar Chart + Donut Allocation Chart */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-2.5">
                {/* 26-Week Cash Runway Chart */}
                <div className="lg:col-span-2 clay-card p-4 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xs font-extrabold text-slate-900 font-sans">
                        Runway Cash Overview
                      </h3>
                      <p className="text-[10px] text-slate-600 font-medium">
                        26-week baseline vs live lever simulation
                      </p>
                    </div>

                    <div className="clay-btn px-2.5 py-0.5 text-[11px] font-semibold text-slate-700 flex items-center space-x-1 cursor-pointer">
                      <span>This Quarter</span>
                      <ChevronDown className="w-3 h-3" />
                    </div>
                  </div>

                  {/* 3D Rounded Vertical Pillar Bars */}
                  <div className="h-32 flex items-end justify-between px-3 pt-3 pb-1.5 clay-card-inset">
                    {[
                      { label: "W1", height: "55%", color: "from-[#94af9f] to-[#648283]", val: "$185k" },
                      { label: "W2", height: "70%", color: "from-[#a8c4b3] to-[#7a9d89]", val: "$172k" },
                      { label: "W3", height: "48%", color: "from-[#648283] to-[#4c6b6c]", val: "$161k" },
                      { label: "W4", height: "85%", color: "from-[#94af9f] to-[#648283]", val: "$154k" },
                      { label: "W5", height: "62%", color: "from-[#c5b8d8] to-[#9e8eb3]", val: "$147k" },
                      { label: "W6", height: "78%", color: "from-[#648283] to-[#3d5a5b]", val: "$155k" },
                      { label: "W7", height: "92%", color: "from-[#c5b8d8] to-[#806f97]", val: "$168k" },
                    ].map((bar, i) => (
                      <div key={i} className="flex flex-col items-center space-y-1.5 h-full justify-end group cursor-pointer">
                        <span className="text-[8px] font-bold text-slate-600 opacity-0 group-hover:opacity-100 transition-opacity">
                          {bar.val}
                        </span>
                        <div
                          style={{ height: bar.height }}
                          className={`w-6 bg-gradient-to-t ${bar.color} clay-bar relative`}
                        />
                        <span className="text-[9px] font-bold text-slate-700">
                          {bar.label}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Capital Allocation Donut Chart */}
                <div className="clay-card p-4 space-y-2">
                  <div>
                    <h3 className="text-xs font-extrabold text-slate-900 font-sans">
                      Capital Allocation
                    </h3>
                    <p className="text-[10px] text-slate-600 font-medium">
                      Portfolio resource distribution
                    </p>
                  </div>

                  {/* Donut Graphic & Legend */}
                  <div className="flex flex-col items-center justify-center">
                    <div className="relative w-24 h-24 flex items-center justify-center">
                      <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                        <path
                          className="text-slate-300"
                          strokeWidth="4"
                          stroke="currentColor"
                          fill="none"
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                        <path
                          className="text-[#648283]"
                          strokeDasharray="45, 100"
                          strokeWidth="4"
                          strokeLinecap="round"
                          stroke="currentColor"
                          fill="none"
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                        <path
                          className="text-[#94af9f]"
                          strokeDasharray="25, 100"
                          strokeDashoffset="-45"
                          strokeWidth="4"
                          strokeLinecap="round"
                          stroke="currentColor"
                          fill="none"
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                        <path
                          className="text-[#c5b8d8]"
                          strokeDasharray="15, 100"
                          strokeDashoffset="-70"
                          strokeWidth="4"
                          strokeLinecap="round"
                          stroke="currentColor"
                          fill="none"
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                      </svg>
                      <div className="absolute flex flex-col items-center">
                        <span className="text-xs font-black text-slate-900">45%</span>
                        <span className="text-[7px] font-bold text-slate-500 uppercase">Retainers</span>
                      </div>
                    </div>

                    {/* Legend */}
                    <div className="w-full mt-2 space-y-1 text-[11px]">
                      <div className="flex items-center justify-between">
                        <span className="flex items-center space-x-1.5 text-slate-700 font-bold">
                          <span className="w-2 h-2 rounded-full bg-[#648283]" />
                          <span>Upfront Retainers</span>
                        </span>
                        <span className="font-extrabold text-slate-900">45%</span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="flex items-center space-x-1.5 text-slate-700 font-bold">
                          <span className="w-2 h-2 rounded-full bg-[#94af9f]" />
                          <span>Dev Payroll</span>
                        </span>
                        <span className="font-extrabold text-slate-900">25%</span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="flex items-center space-x-1.5 text-slate-700 font-bold">
                          <span className="w-2 h-2 rounded-full bg-[#c5b8d8]" />
                          <span>Prepay Float</span>
                        </span>
                        <span className="font-extrabold text-slate-900">15%</span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="flex items-center space-x-1.5 text-slate-700 font-bold">
                          <span className="w-2 h-2 rounded-full bg-slate-400" />
                          <span>Working Buffer</span>
                        </span>
                        <span className="font-extrabold text-slate-900">15%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Bottom Row: Recently Modeled + Sensible Live Lever Simulator */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
                {/* Recently Modeled Scenarios */}
                <div className="clay-card p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-extrabold text-slate-900 font-sans">
                      Recently Analyzed Levers
                    </h3>
                    <button
                      onClick={() => setActivePart("cfo")}
                      className="text-[11px] font-bold text-[#4c6b6c] hover:underline"
                    >
                      See All
                    </button>
                  </div>

                  <div className="space-y-1.5">
                    {/* Scenario 1 */}
                    <div className="flex items-center justify-between p-1.5 rounded-2xl hover:bg-white/40 transition-colors">
                      <div className="flex items-center space-x-2.5">
                        <div className="w-8 h-8 rounded-xl bg-[#94af9f] flex items-center justify-center text-white shadow-sm font-bold text-[10px]">
                          UR
                        </div>
                        <div>
                          <div className="text-xs font-bold text-slate-900">
                            Upfront Retainers
                          </div>
                          <div className="text-[10px] text-slate-600 font-medium">
                            Shift hourly billing to $15k/mo upfront
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => setActivePart("cfo")}
                        className="w-7 h-7 clay-btn flex items-center justify-center text-[#648283] hover:text-[#4c6b6c]"
                      >
                        <Play className="w-3 h-3 fill-current" />
                      </button>
                    </div>

                    {/* Scenario 2 */}
                    <div className="flex items-center justify-between p-1.5 rounded-2xl hover:bg-white/40 transition-colors">
                      <div className="flex items-center space-x-2.5">
                        <div className="w-8 h-8 rounded-xl bg-[#648283] flex items-center justify-center text-white shadow-sm font-bold text-[10px]">
                          HD
                        </div>
                        <div>
                          <div className="text-xs font-bold text-slate-900">
                            Hire 2 Developers
                          </div>
                          <div className="text-[10px] text-slate-600 font-medium">
                            30-day delay + $14k monthly burn
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => setActivePart("cfo")}
                        className="w-7 h-7 clay-btn flex items-center justify-center text-[#648283] hover:text-[#4c6b6c]"
                      >
                        <Play className="w-3 h-3 fill-current" />
                      </button>
                    </div>

                    {/* Scenario 3 */}
                    <div className="flex items-center justify-between p-1.5 rounded-2xl hover:bg-white/40 transition-colors">
                      <div className="flex items-center space-x-2.5">
                        <div className="w-8 h-8 rounded-xl bg-[#c5b8d8] flex items-center justify-center text-[#3b2852] shadow-sm font-bold text-[10px]">
                          N15
                        </div>
                        <div>
                          <div className="text-xs font-bold text-slate-900">
                            Net 15 Terms
                          </div>
                          <div className="text-[10px] text-slate-600 font-medium">
                            Accelerates client receivables by 15 days
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => setActivePart("moonshot")}
                        className="w-7 h-7 clay-btn flex items-center justify-center text-[#8e7ca8] hover:text-[#3b2852]"
                      >
                        <Play className="w-3 h-3 fill-current" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* ========================================================== */}
                {/* SENSIBLE LIVE STRATEGIC LEVER PLAYGROUND WITH REAL SLIDER  */}
                {/* ========================================================== */}
                <div className="clay-card p-4 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xs font-extrabold text-slate-900 font-sans tracking-wide">
                        Live Strategic Lever Simulator
                      </h3>
                      <p className="text-[10px] text-slate-600 font-semibold">
                        Simulate cash float and runway impact in real time
                      </p>
                    </div>

                    {/* Sensible Category Tabs */}
                    <div className="clay-segmented-bar flex items-center space-x-1 text-[10px] font-bold">
                      <button
                        onClick={() => setLeverTab("capital")}
                        className={`px-2.5 py-0.5 rounded-full transition-all ${
                          leverTab === "capital" ? "clay-pill-sage text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
                        }`}
                      >
                        Working Capital
                      </button>
                      <button
                        onClick={() => setLeverTab("staff")}
                        className={`px-2.5 py-0.5 rounded-full transition-all ${
                          leverTab === "staff" ? "clay-pill-teal text-white shadow-sm" : "text-slate-600 hover:text-slate-900"
                        }`}
                      >
                        Staffing
                      </button>
                      <button
                        onClick={() => setLeverTab("terms")}
                        className={`px-2.5 py-0.5 rounded-full transition-all ${
                          leverTab === "terms" ? "clay-pill-lavender text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
                        }`}
                      >
                        Terms & Risk
                      </button>
                    </div>
                  </div>

                  {/* Sensible Scenario Toggle Buttons with Real Logic & Active States */}
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <button
                      onClick={() => setRetainerActive(!retainerActive)}
                      className={`px-2 py-1.5 rounded-full font-bold transition-all text-center flex items-center justify-center space-x-1 ${
                        retainerActive
                          ? "clay-pill-lavender shadow-md"
                          : "clay-btn text-slate-600 hover:text-slate-900"
                      }`}
                      title="Toggle $15,000 monthly upfront retainer contracts"
                    >
                      <span className="w-2 h-2 rounded-full bg-purple-700" />
                      <span className="truncate">Retainers (+15k)</span>
                    </button>

                    <button
                      onClick={() => setDelayDefenseActive(!delayDefenseActive)}
                      className={`px-2 py-1.5 rounded-full font-bold transition-all text-center flex items-center justify-center space-x-1 ${
                        delayDefenseActive
                          ? "clay-pill-teal shadow-md"
                          : "clay-btn text-slate-600 hover:text-slate-900"
                      }`}
                      title="Enforce 15-day late payment reserve buffer"
                    >
                      <span className="w-2 h-2 rounded-full bg-teal-200" />
                      <span className="truncate">Delay Defense</span>
                    </button>

                    <button
                      onClick={() => setCovenantActive(!covenantActive)}
                      className={`px-2 py-1.5 rounded-full font-bold transition-all text-center flex items-center justify-center space-x-1 ${
                        covenantActive
                          ? "clay-pill-sage shadow-md"
                          : "clay-btn text-slate-600 hover:text-slate-900"
                      }`}
                      title="Enforce strict zero-debt zero-dilution covenant"
                    >
                      <Check className="w-3 h-3 text-slate-900" />
                      <span className="truncate">Zero-Debt</span>
                    </button>
                  </div>

                  {/* Live Status Pill with Calculated Prepayment Metrics */}
                  <div className="clay-input-lavender px-3 py-1.5 flex items-center justify-between text-xs">
                    <span className="font-bold text-slate-800 text-[11px]">
                      Upfront Prepayment Acceptance
                    </span>
                    <div className="flex items-center space-x-1.5">
                      <span className="font-black text-[#648283] font-mono text-xs">
                        {prepayRate}%
                      </span>
                      <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full font-mono">
                        +${(Math.round((prepayRate / 100) * 45000)).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  {/* REAL 3D TACTILE CLAY SLIDER WITH VISIBLE SLIDING KNOB */}
                  <div className="relative flex items-center py-1">
                    {/* Notched track background with tick marks */}
                    <div className="w-full clay-notched-track h-6 px-3 flex items-center justify-between text-slate-500 font-mono text-[9px] select-none pointer-events-none relative">
                      <span>0%</span>
                      <span>|</span>
                      <span>25%</span>
                      <span>|</span>
                      <span>50%</span>
                      <span>|</span>
                      <span>75%</span>
                      <span>|</span>
                      <span>100%</span>

                      {/* Tactile 3D Clay Sliding Knob */}
                      <div
                        style={{ left: `calc(${prepayRate}% * 0.90 + 5%)` }}
                        className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-6 h-6 rounded-full bg-[#fbf9f5] border-2 border-[#648283] shadow-[0_3px_8px_rgba(0,0,0,0.35),inset_0_1px_2px_#ffffff] flex items-center justify-center pointer-events-none transition-all duration-75"
                      >
                        <div className="w-2 h-2 rounded-full bg-[#648283]" />
                      </div>
                    </div>

                    {/* Interactive Range Slider */}
                    <input
                      type="range"
                      min="0"
                      max="100"
                      step="5"
                      value={prepayRate}
                      onChange={(e) => setPrepayRate(Number(e.target.value))}
                      className="clay-slider absolute inset-0 opacity-0 cursor-pointer"
                    />
                  </div>

                  {/* Dynamic Simulation Output Row */}
                  <div className="clay-card-inset p-2.5 rounded-2xl flex items-center justify-between text-xs">
                    <div>
                      <span className="text-[9px] uppercase font-bold text-slate-500 block">
                        Net Float Delta
                      </span>
                      <strong className={`font-black font-mono text-xs ${calculatedDelta >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
                        {calculatedDelta >= 0 ? `+$${calculatedDelta.toLocaleString()}` : `-$${Math.abs(calculatedDelta).toLocaleString()}`}
                      </strong>
                    </div>

                    <div className="h-5 w-px bg-slate-300" />

                    <div>
                      <span className="text-[9px] uppercase font-bold text-slate-500 block">
                        Simulated Runway
                      </span>
                      <strong className="text-[#648283] font-black font-mono text-xs">
                        {simulatedRunwayWeeks} Weeks
                      </strong>
                    </div>

                    <div className="h-5 w-px bg-slate-300" />

                    <div>
                      <span className="text-[9px] uppercase font-bold text-slate-500 block">
                        Projected Floor
                      </span>
                      <strong className="text-slate-900 font-black font-mono text-xs">
                        ${projectedCash.toLocaleString()}
                      </strong>
                    </div>

                    <button
                      onClick={() => setActivePart("cfo")}
                      className="clay-pill-sage px-3 py-1 rounded-full text-[10px] font-black text-slate-900 flex items-center space-x-1 shadow-sm transition-transform hover:scale-105"
                      title="Load these levers directly into Part 2 CFO Matrix"
                    >
                      <span>Apply</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ============================================================== */}
          {/* PART 1: CONVERSATIONAL CFO CO-PILOT VIEW                       */}
          {/* ============================================================== */}
          {activePart === "chat" && (
            <div className="h-full flex flex-col overflow-y-auto">
              <ChatView compact={false} />
            </div>
          )}

          {/* ============================================================== */}
          {/* PART 2: CFO FINANCE ENGINE MATRIX                              */}
          {/* ============================================================== */}
          {activePart === "cfo" && (
            <div className="h-full flex flex-col overflow-y-auto pr-1">
              <CfoDashboard />
            </div>
          )}

          {/* ============================================================== */}
          {/* PART 3: MOONSHOT STRATEGIC REASONING STUDIO                    */}
          {/* ============================================================== */}
          {activePart === "moonshot" && (
            <div className="h-full flex flex-col overflow-y-auto pr-1">
              <MoonshotView />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
