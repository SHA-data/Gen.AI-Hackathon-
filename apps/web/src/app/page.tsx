"use client";

import React, { useState } from "react";
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
} from "lucide-react";

export type NavPart = "overview" | "chat" | "cfo" | "moonshot";

export default function UnifiedSystemCockpit() {
  const [activePart, setActivePart] = useState<NavPart>("overview");
  const [searchQuery, setSearchQuery] = useState("");
  const [sliderPrepay, setSliderPrepay] = useState(40);
  const [activeTab, setActiveTab] = useState<"hover" | "completed" | "selected">("hover");
  const [toggleActive, setToggleActive] = useState(true);

  return (
    <div className="flex h-screen w-screen overflow-hidden p-3 gap-3">
      {/* ============================================================== */}
      {/* 1. LEFT NAVIGATION RAIL (Image 1 Style: Deep Navy Claymorphic)  */}
      {/* ============================================================== */}
      <aside className="w-64 flex-shrink-0 flex flex-col justify-between p-4 clay-sidebar text-slate-200 relative overflow-hidden">
        {/* Subtle Ambient Backlights */}
        <div className="absolute -top-10 -left-10 w-40 h-40 rounded-full bg-cyan-500/15 blur-3xl pointer-events-none" />
        <div className="absolute bottom-16 -right-10 w-40 h-40 rounded-full bg-purple-500/15 blur-3xl pointer-events-none" />

        {/* Top Profile / User Avatar (Image 1 Style) */}
        <div className="relative z-10 flex flex-col items-center text-center pb-3">
          <div className="relative mb-2 group cursor-pointer">
            <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-cyan-400 via-indigo-500 to-purple-500 p-[3px] shadow-[0_8px_20px_rgba(0,0,0,0.4)] transition-transform duration-300 group-hover:scale-105 flex items-center justify-center">
              <div className="w-full h-full rounded-full bg-[#1e293b] flex items-center justify-center overflow-hidden border-2 border-white/20">
                <Music className="w-8 h-8 text-cyan-300" />
              </div>
            </div>
            <span className="absolute bottom-0 right-0 w-4 h-4 rounded-full bg-emerald-400 border-2 border-[#182337] shadow-sm animate-pulse" />
          </div>

          <h2 className="text-sm font-bold text-white tracking-wide font-mono">
            Hi, Aryan!
          </h2>
          <p className="text-[10px] text-slate-400 font-mono">
            Acme Digital Agency
          </p>
        </div>

        {/* Navigation Items (Image 1 Style) */}
        <nav className="relative z-10 flex-1 py-2 flex flex-col space-y-1.5 overflow-y-auto">
          {/* Dashboard / Executive Overview */}
          <button
            onClick={() => setActivePart("overview")}
            className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-2xl text-left transition-all ${
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
            className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-2xl text-left transition-all ${
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
            className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-2xl text-left transition-all ${
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
            className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-2xl text-left transition-all ${
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
              className="w-full flex items-center space-x-3 px-3.5 py-2 rounded-xl text-left text-slate-400 hover:text-slate-200 transition-colors"
            >
              <Heart className="w-4 h-4 text-rose-400" />
              <span className="text-xs font-medium">Favorites & Levers</span>
            </button>

            <button
              onClick={() => setActivePart("chat")}
              className="w-full flex items-center space-x-3 px-3.5 py-2 rounded-xl text-left text-slate-400 hover:text-slate-200 transition-colors"
            >
              <Zap className="w-4 h-4 text-amber-400" />
              <span className="text-xs font-medium">Activity & Audit</span>
            </button>
          </div>
        </nav>

        {/* Bottom Banner Card (Image 1 "Go Premium" card style) */}
        <div className="relative z-10 pt-2">
          <div className="p-3 rounded-2xl clay-dark-card border border-white/10 flex flex-col items-center text-center space-y-2">
            <div className="w-8 h-8 rounded-full bg-cyan-950/80 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-sm">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[11px] font-bold text-white tracking-wide">
                NeuralCFO Sovereign
              </div>
              <div className="text-[9px] text-slate-400 leading-tight">
                Zetaris Data & Meterless Verified
              </div>
            </div>
            <button
              onClick={() => setActivePart("cfo")}
              className="w-full py-1.5 px-3 rounded-xl clay-pill-sage text-[11px] tracking-wide shadow-md"
            >
              Live Health Status
            </button>
          </div>
        </div>
      </aside>

      {/* ============================================================== */}
      {/* 2. MAIN WORKSPACE AREA                                         */}
      {/* ============================================================== */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden space-y-3">
        {/* Top Header Bar (Image 1 Style) */}
        <header className="flex items-center justify-between gap-4 py-1">
          {/* Page Title */}
          <h1 className="text-2xl font-black text-slate-800 tracking-tight font-sans">
            {activePart === "overview" && "Dashboard"}
            {activePart === "chat" && "Chat Co-Pilot"}
            {activePart === "cfo" && "CFO Finance Engine"}
            {activePart === "moonshot" && "Moonshot Strategic Studio"}
          </h1>

          {/* Search Pill (Image 1 Style: Debossed inset pill) */}
          <div className="flex-1 max-w-md relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-4 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search for scenarios, runway, models..."
              className="w-full clay-card-inset py-2 pl-10 pr-4 text-xs text-slate-700 placeholder-slate-500 focus:outline-none transition-all font-sans"
            />
          </div>

          {/* Right Header Buttons (Image 1 Style) */}
          <div className="flex items-center space-x-2.5">
            {/* Notification Bell */}
            <button className="w-10 h-10 clay-btn flex items-center justify-center text-slate-600 hover:text-slate-900 relative">
              <Bell className="w-4 h-4" />
              <span className="w-2 h-2 rounded-full bg-cyan-500 absolute top-2.5 right-2.5 shadow-sm" />
            </button>

            {/* Profile Squircle */}
            <button
              onClick={() => setActivePart("overview")}
              className="w-10 h-10 clay-btn flex items-center justify-center text-slate-700 font-bold text-xs"
            >
              <div className="w-6 h-6 rounded-full bg-[#648283] text-white flex items-center justify-center text-[10px]">
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
            <div className="space-y-4 pb-4">
              {/* Hero Banner Card (Image 1 Style: Dark curved card with 3D headphone icon & CTA) */}
              <div className="relative clay-dark-card p-6 overflow-hidden flex items-center justify-between text-white shadow-xl">
                <div className="absolute top-0 right-0 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
                <div className="relative z-10 max-w-lg space-y-2">
                  <div className="flex items-center space-x-2 text-cyan-400 text-xs font-mono">
                    <Music className="w-3.5 h-3.5" />
                    <span>NeuralCFO Multi-Agent Decision Engine</span>
                  </div>
                  <h2 className="text-xl font-bold tracking-tight">
                    Good Evening, Aryan!
                  </h2>
                  <p className="text-xs text-slate-300 leading-relaxed font-sans">
                    Your small business runway is currently solvent at <strong className="text-emerald-400">18.4 weeks</strong>. 
                    Simulate hiring 2 developers or deploy upfront retainers to push cash reserves past <strong className="text-cyan-300">$143,250</strong>.
                  </p>
                  <div className="pt-1 flex items-center space-x-3">
                    <button
                      onClick={() => setActivePart("cfo")}
                      className="px-5 py-2 clay-pill-sage text-xs flex items-center space-x-2 shadow-lg"
                    >
                      <Play className="w-3.5 h-3.5 fill-current" />
                      <span>Play Something</span>
                    </button>
                    <button
                      onClick={() => setActivePart("chat")}
                      className="px-4 py-2 rounded-full bg-white/10 hover:bg-white/20 text-white text-xs font-semibold backdrop-blur-md border border-white/20 transition-colors"
                    >
                      Ask AI Co-Pilot
                    </button>
                  </div>
                </div>

                {/* 3D Visual Mascot / Art Element */}
                <div className="hidden md:flex relative z-10 w-36 h-36 rounded-3xl bg-gradient-to-tr from-cyan-500/20 via-indigo-500/20 to-purple-500/20 border border-white/10 items-center justify-center backdrop-blur-xl shadow-2xl">
                  <Sparkles className="w-16 h-16 text-cyan-300 animate-pulse" />
                </div>
              </div>

              {/* 4 Raised Clay Cushion Metric Cards (New Image 1 Cushions & Image 1 Dashboard) */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {/* Metric 1: Cash Runway (Sage Mint Cushion) */}
                <div className="clay-cushion p-4 space-y-2">
                  <div className="w-10 h-10 clay-squircle flex items-center justify-center text-[#648283]">
                    <Music className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-[11px] font-bold text-slate-500">
                      Cash Runway
                    </div>
                    <div className="text-2xl font-black text-slate-800 tracking-tight font-sans">
                      18.4 w
                    </div>
                    <div className="text-[10px] font-bold text-[#648283] mt-0.5">
                      +16% this week
                    </div>
                  </div>
                </div>

                {/* Metric 2: Floor Reserve (Pastel Coral/Rose Cushion) */}
                <div className="clay-cushion p-4 space-y-2">
                  <div className="w-10 h-10 clay-squircle flex items-center justify-center text-[#cb7a72]">
                    <Heart className="w-5 h-5 fill-current" />
                  </div>
                  <div>
                    <div className="text-[11px] font-bold text-slate-500">
                      Floor Reserve
                    </div>
                    <div className="text-2xl font-black text-slate-800 tracking-tight font-sans">
                      $143k
                    </div>
                    <div className="text-[10px] font-bold text-[#cb7a72] mt-0.5">
                      +$23k safe buffer
                    </div>
                  </div>
                </div>

                {/* Metric 3: Reversibility (Slate Teal Cushion) */}
                <div className="clay-cushion p-4 space-y-2">
                  <div className="w-10 h-10 clay-squircle flex items-center justify-center text-[#4c6b6c]">
                    <Clock className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-[11px] font-bold text-slate-500">
                      Reversibility
                    </div>
                    <div className="text-2xl font-black text-slate-800 tracking-tight font-sans">
                      &lt; $5k
                    </div>
                    <div className="text-[10px] font-bold text-emerald-700 mt-0.5">
                      14-day window
                    </div>
                  </div>
                </div>

                {/* Metric 4: Proof Streak (Lavender Cushion) */}
                <div className="clay-cushion p-4 space-y-2">
                  <div className="w-10 h-10 clay-squircle flex items-center justify-center text-[#8e7ca8]">
                    <Flame className="w-5 h-5 fill-current" />
                  </div>
                  <div>
                    <div className="text-[11px] font-bold text-slate-500">
                      Proof Streak
                    </div>
                    <div className="text-2xl font-black text-slate-800 tracking-tight font-sans">
                      100%
                    </div>
                    <div className="text-[10px] font-bold text-[#8e7ca8] mt-0.5">
                      0 unverified claims
                    </div>
                  </div>
                </div>
              </div>

              {/* Middle Row: Runway Bar Chart + Donut Allocation Chart */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
                {/* 26-Week Cash Runway Chart (Image 1's "Listening Overview") */}
                <div className="lg:col-span-2 clay-card p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-extrabold text-slate-800 font-sans">
                        Runway Cash Overview
                      </h3>
                      <p className="text-[11px] text-slate-500">
                        26-week baseline vs scenario simulation
                      </p>
                    </div>

                    <div className="clay-btn px-3 py-1 text-xs font-semibold text-slate-700 flex items-center space-x-1 cursor-pointer">
                      <span>This Quarter</span>
                      <ChevronDown className="w-3.5 h-3.5" />
                    </div>
                  </div>

                  {/* 3D Rounded Vertical Pillar Bars (Image 1 Style) */}
                  <div className="h-44 flex items-end justify-between px-4 pt-6 pb-2 clay-card-inset">
                    {[
                      { label: "W1", height: "55%", color: "from-[#94af9f] to-[#648283]", val: "$185k" },
                      { label: "W2", height: "70%", color: "from-[#a8c4b3] to-[#7a9d89]", val: "$172k" },
                      { label: "W3", height: "48%", color: "from-[#648283] to-[#4c6b6c]", val: "$161k" },
                      { label: "W4", height: "85%", color: "from-[#94af9f] to-[#648283]", val: "$154k" },
                      { label: "W5", height: "62%", color: "from-[#c5b8d8] to-[#9e8eb3]", val: "$147k" },
                      { label: "W6", height: "78%", color: "from-[#648283] to-[#3d5a5b]", val: "$155k" },
                      { label: "W7", height: "92%", color: "from-[#c5b8d8] to-[#806f97]", val: "$168k" },
                    ].map((bar, i) => (
                      <div key={i} className="flex flex-col items-center space-y-2 h-full justify-end group cursor-pointer">
                        <span className="text-[9px] font-bold text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity">
                          {bar.val}
                        </span>
                        <div
                          style={{ height: bar.height }}
                          className={`w-7 bg-gradient-to-t ${bar.color} clay-bar relative`}
                        />
                        <span className="text-[10px] font-bold text-slate-600">
                          {bar.label}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Capital Allocation Donut Chart (Image 1's "Top Genres") */}
                <div className="clay-card p-5 space-y-3">
                  <div>
                    <h3 className="text-sm font-extrabold text-slate-800 font-sans">
                      Capital Allocation
                    </h3>
                    <p className="text-[11px] text-slate-500">
                      Portfolio resource distribution
                    </p>
                  </div>

                  {/* Donut Graphic & Legend */}
                  <div className="flex flex-col items-center justify-center py-1">
                    <div className="relative w-28 h-28 flex items-center justify-center">
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
                        <span className="text-sm font-black text-slate-800">45%</span>
                        <span className="text-[8px] font-bold text-slate-400 uppercase">Retainers</span>
                      </div>
                    </div>

                    {/* Legend */}
                    <div className="w-full mt-3 space-y-1.5 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="flex items-center space-x-1.5 text-slate-600 font-medium">
                          <span className="w-2.5 h-2.5 rounded-full bg-[#648283]" />
                          <span>Upfront Retainers</span>
                        </span>
                        <span className="font-bold text-slate-800">45%</span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="flex items-center space-x-1.5 text-slate-600 font-medium">
                          <span className="w-2.5 h-2.5 rounded-full bg-[#94af9f]" />
                          <span>Dev Payroll</span>
                        </span>
                        <span className="font-bold text-slate-800">25%</span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="flex items-center space-x-1.5 text-slate-600 font-medium">
                          <span className="w-2.5 h-2.5 rounded-full bg-[#c5b8d8]" />
                          <span>Prepay Float</span>
                        </span>
                        <span className="font-bold text-slate-800">15%</span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="flex items-center space-x-1.5 text-slate-600 font-medium">
                          <span className="w-2.5 h-2.5 rounded-full bg-slate-400" />
                          <span>Working Buffer</span>
                        </span>
                        <span className="font-bold text-slate-800">15%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Bottom Row: Recently Modeled + Clay UI Kit (New Image 2 Elements) */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                {/* Recently Modeled Scenarios (Image 1's "Recently Played") */}
                <div className="clay-card p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-extrabold text-slate-800 font-sans">
                      Recently Analyzed Levers
                    </h3>
                    <button
                      onClick={() => setActivePart("cfo")}
                      className="text-xs font-bold text-[#4c6b6c] hover:underline"
                    >
                      See All
                    </button>
                  </div>

                  <div className="space-y-2.5">
                    {/* Scenario 1 */}
                    <div className="flex items-center justify-between p-2 rounded-2xl hover:bg-white/40 transition-colors">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-xl bg-[#94af9f] flex items-center justify-center text-white shadow-sm font-bold text-xs">
                          UR
                        </div>
                        <div>
                          <div className="text-xs font-bold text-slate-800">
                            Upfront Retainers
                          </div>
                          <div className="text-[10px] text-slate-500">
                            Shift hourly billing to $15k/mo upfront
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => setActivePart("cfo")}
                        className="w-8 h-8 clay-btn flex items-center justify-center text-[#648283] hover:text-[#4c6b6c]"
                      >
                        <Play className="w-3.5 h-3.5 fill-current" />
                      </button>
                    </div>

                    {/* Scenario 2 */}
                    <div className="flex items-center justify-between p-2 rounded-2xl hover:bg-white/40 transition-colors">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-xl bg-[#648283] flex items-center justify-center text-white shadow-sm font-bold text-xs">
                          HD
                        </div>
                        <div>
                          <div className="text-xs font-bold text-slate-800">
                            Hire 2 Developers
                          </div>
                          <div className="text-[10px] text-slate-500">
                            30-day delay + $14k monthly burn
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => setActivePart("cfo")}
                        className="w-8 h-8 clay-btn flex items-center justify-center text-[#648283] hover:text-[#4c6b6c]"
                      >
                        <Play className="w-3.5 h-3.5 fill-current" />
                      </button>
                    </div>

                    {/* Scenario 3 */}
                    <div className="flex items-center justify-between p-2 rounded-2xl hover:bg-white/40 transition-colors">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-xl bg-[#c5b8d8] flex items-center justify-center text-[#3b2852] shadow-sm font-bold text-xs">
                          N15
                        </div>
                        <div>
                          <div className="text-xs font-bold text-slate-800">
                            Net 15 Terms
                          </div>
                          <div className="text-[10px] text-slate-500">
                            Accelerates client receivables by 15 days
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => setActivePart("moonshot")}
                        className="w-8 h-8 clay-btn flex items-center justify-center text-[#8e7ca8] hover:text-[#3b2852]"
                      >
                        <Play className="w-3.5 h-3.5 fill-current" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Tactile Clay UI Kit Interactive Playground (New Image 2 Style) */}
                <div className="clay-card p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-extrabold text-slate-900 font-sans tracking-wide">
                      Clay UI Lever Kit
                    </h3>
                    {/* Segmented Tab Pill from Image 2 */}
                    <div className="clay-segmented-bar flex items-center space-x-1 text-[11px] font-bold">
                      <button
                        onClick={() => setActiveTab("hover")}
                        className={`px-3 py-1 rounded-xl transition-all ${
                          activeTab === "hover" ? "clay-pill-sage" : "text-slate-600 hover:text-slate-900"
                        }`}
                      >
                        Hover
                      </button>
                      <button
                        onClick={() => setActiveTab("completed")}
                        className={`px-3 py-1 rounded-xl transition-all ${
                          activeTab === "completed" ? "clay-pill-teal" : "text-slate-600 hover:text-slate-900"
                        }`}
                      >
                        Complete
                      </button>
                      <button
                        onClick={() => setActiveTab("selected")}
                        className={`px-3 py-1 rounded-xl transition-all ${
                          activeTab === "selected" ? "bg-white shadow text-slate-900" : "text-slate-600 hover:text-slate-900"
                        }`}
                      >
                        Doiders
                      </button>
                    </div>
                  </div>

                  {/* Pill Buttons from Image 2 */}
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setActivePart("moonshot")}
                      className="px-4 py-2 clay-pill-lavender text-xs flex-1 text-center"
                    >
                      + Hover
                    </button>
                    <button
                      onClick={() => setActivePart("cfo")}
                      className="px-4 py-2 clay-pill-teal text-xs flex-1 text-center"
                    >
                      Pressed
                    </button>
                    <button
                      onClick={() => setActivePart("cfo")}
                      className="px-4 py-2 clay-pill-sage text-xs flex-1 text-center"
                    >
                      # Toguben
                    </button>
                  </div>

                  {/* Lavender Bordered Form Pill from Image 2 */}
                  <div className="clay-input-lavender px-4 py-2 flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-700">
                      Upfront Prepayment Acceptance
                    </span>
                    <span className="text-xs font-black text-[#648283] font-mono">
                      {sliderPrepay}%
                    </span>
                  </div>

                  {/* Notched Slider Bar from Image 2 */}
                  <div className="space-y-1">
                    <div className="relative flex items-center py-2">
                      <div className="w-full clay-notched-track h-6 px-3 flex items-center justify-between text-slate-400 font-mono text-[9px] select-none pointer-events-none">
                        <span>|</span>
                        <span>|</span>
                        <span>|</span>
                        <span>|</span>
                        <span>|</span>
                        <span>|</span>
                        <span>|</span>
                        <span>|</span>
                        <span>|</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={sliderPrepay}
                        onChange={(e) => setSliderPrepay(Number(e.target.value))}
                        className="absolute inset-0 w-full opacity-0 cursor-pointer"
                      />
                    </div>
                  </div>

                  {/* Toggle Switch from Image 2 */}
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-xs font-bold text-slate-800">
                      Zero-Debt Verification Covenant
                    </span>
                    <button
                      onClick={() => setToggleActive(!toggleActive)}
                      className={`w-14 h-7 rounded-full transition-colors relative p-1 ${
                        toggleActive ? "bg-[#648283]" : "bg-slate-300"
                      }`}
                    >
                      <div
                        className={`w-5 h-5 rounded-full bg-[#f7f5f0] shadow-md transform transition-transform ${
                          toggleActive ? "translate-x-7" : "translate-x-0"
                        }`}
                      />
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
            <div className="h-full flex flex-col clay-dark-card border border-white/10 rounded-3xl overflow-hidden shadow-2xl p-2">
              <div className="flex items-center justify-between px-4 py-2 border-b border-white/10 text-xs text-slate-300 font-mono">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <strong className="text-white font-bold">[Part 1] Conversational CFO Co-Pilot</strong>
                </div>
                <div className="flex items-center space-x-3 text-[11px] text-slate-400">
                  <span>SSE Streaming: Active</span>
                  <span>Meterless Memory: Tracing</span>
                </div>
              </div>
              <div className="flex-1 min-h-0">
                <ChatView compact={false} />
              </div>
            </div>
          )}

          {/* ============================================================== */}
          {/* PART 2: CFO FINANCE ENGINE MATRIX                              */}
          {/* ============================================================== */}
          {activePart === "cfo" && (
            <div className="h-full flex flex-col clay-dark-card border border-white/10 rounded-3xl overflow-hidden shadow-2xl p-2">
              <div className="flex items-center justify-between px-4 py-2 border-b border-white/10 text-xs text-slate-300 font-mono">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                  <strong className="text-white font-bold">[Part 2] CFO Finance Engine & Runway Matrix</strong>
                </div>
                <div className="flex items-center space-x-3 text-[11px] text-slate-400">
                  <span>Zetaris Bridge: Federated</span>
                  <span>Horizon: 26 Weeks</span>
                </div>
              </div>
              <div className="flex-1 min-h-0 overflow-y-auto">
                <CfoDashboard />
              </div>
            </div>
          )}

          {/* ============================================================== */}
          {/* PART 3: MOONSHOT STRATEGIC REASONING STUDIO                    */}
          {/* ============================================================== */}
          {activePart === "moonshot" && (
            <div className="h-full flex flex-col clay-dark-card border border-white/10 rounded-3xl overflow-hidden shadow-2xl p-2">
              <div className="flex items-center justify-between px-4 py-2 border-b border-white/10 text-xs text-slate-300 font-mono">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
                  <strong className="text-white font-bold">[Part 3] Moonshot 8-Stage Strategic Studio</strong>
                </div>
                <div className="flex items-center space-x-3 text-[11px] text-slate-400">
                  <span>Verifier: HR-01 to HR-12 Enforced</span>
                  <span>Proofs: 100% Deterministic</span>
                </div>
              </div>
              <div className="flex-1 min-h-0 overflow-y-auto">
                <MoonshotView />
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
