"use client";

import React, { useState } from "react";
import { ChatView } from "@/components/chat/ChatView";
import { MoonshotView } from "@/components/moonshot/MoonshotView";
import CfoPage from "@/app/cfo/page";
import {
  Layers,
  MessageSquare,
  Compass,
  BarChart3,
  Server,
  ShieldCheck,
  CheckCircle2,
  Maximize2,
  Split,
} from "lucide-react";

export default function UnifiedSystemPage() {
  const [activeTab, setActiveTab] = useState<"merged" | "chat" | "moonshot" | "cfo">("merged");

  return (
    <div className="flex-1 flex flex-col space-y-3">
      {/* Top Cockpit Command Strip */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-3 bg-slate-900/90 border border-slate-800 rounded-xl shadow-lg">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-emerald-950/80 border border-emerald-800 text-emerald-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-bold text-slate-100 font-mono tracking-tight">
                NEURALCFO UNIFIED DECISION SUITE
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                ACTIVE MONOLITH
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono">
              Synchronized Copilot Gateway (Aroon) + 8-Stage Strategic Reasoning Engine (Aleena)
            </p>
          </div>
        </div>

        {/* View Mode Toggle Switcher */}
        <div className="flex items-center p-1 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono">
          <button
            onClick={() => setActiveTab("merged")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded transition-colors ${
              activeTab === "merged"
                ? "bg-emerald-600 text-slate-950 font-bold shadow"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Split className="w-3.5 h-3.5" />
            <span>[1] Merged Dual View</span>
          </button>

          <button
            onClick={() => setActiveTab("chat")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded transition-colors ${
              activeTab === "chat"
                ? "bg-emerald-600 text-slate-950 font-bold shadow"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>[2] Chat Copilot</span>
          </button>

          <button
            onClick={() => setActiveTab("moonshot")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded transition-colors ${
              activeTab === "moonshot"
                ? "bg-purple-600 text-white font-bold shadow"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Compass className="w-3.5 h-3.5" />
            <span>[3] Moonshot Cockpit</span>
          </button>

          <button
            onClick={() => setActiveTab("cfo")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded transition-colors ${
              activeTab === "cfo"
                ? "bg-blue-600 text-white font-bold shadow"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>[4] CFO Matrix</span>
          </button>
        </div>
      </div>

      {/* Main Workspace Render */}
      {activeTab === "merged" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1">
          {/* Left Column: Conversational Co-pilot Gateway (42% width) */}
          <div className="lg:col-span-5 flex flex-col bg-slate-900/60 border border-slate-800 rounded-xl p-4 shadow-xl">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-xs font-mono">
              <div className="flex items-center space-x-2 text-emerald-400 font-semibold">
                <MessageSquare className="w-4 h-4" />
                <span>CHAT COPILOT & DECISION GATEWAY</span>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                SSE Live Stream
              </span>
            </div>
            <div className="flex-1 overflow-hidden">
              <ChatView compact={true} />
            </div>
          </div>

          {/* Right Column: Moonshot 8-Stage Strategic Cockpit (58% width) */}
          <div className="lg:col-span-7 flex flex-col bg-slate-900/60 border border-slate-800 rounded-xl p-4 shadow-xl overflow-y-auto max-h-[calc(100vh-8.5rem)]">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-xs font-mono sticky top-0 bg-slate-900/90 backdrop-blur z-20">
              <div className="flex items-center space-x-2 text-purple-300 font-semibold">
                <Compass className="w-4 h-4" />
                <span>MOONSHOT 8-STAGE REASONING & FINANCIAL LEVERS</span>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800">
                SHA-256 Citations Active
              </span>
            </div>
            <MoonshotView compact={true} />
          </div>
        </div>
      )}

      {activeTab === "chat" && (
        <div className="flex-1 bg-slate-900/60 border border-slate-800 rounded-xl p-4 shadow-xl">
          <ChatView compact={false} />
        </div>
      )}

      {activeTab === "moonshot" && (
        <div className="flex-1 bg-slate-900/60 border border-slate-800 rounded-xl p-4 shadow-xl">
          <MoonshotView compact={false} />
        </div>
      )}

      {activeTab === "cfo" && (
        <div className="flex-1">
          <CfoPage />
        </div>
      )}
    </div>
  );
}
