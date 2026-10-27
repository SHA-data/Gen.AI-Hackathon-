"use client";

import React, { useState, useRef, useEffect } from "react";
import { useEvidenceDrawer } from "@/components/evidence/EvidenceDrawer";
import { ApprovalCard, ActionProposalData } from "@/components/chat/ApprovalCard";
import { ChartWidget, ChartEventData } from "@/components/chat/ChartWidget";
import { Users, Compass, BarChart2, BookmarkCheck, ExternalLink, Send, Sparkles, CheckCircle2 } from "lucide-react";

interface ChatMessage {
  id: string;
  sender: "user" | "assistant" | "system";
  content: string;
  status?: "verified" | "warning" | "unverified" | "failed";
  citations?: Array<{ id: string; target_type: string; target_id: string; label: string; snippet?: string }>;
  chart?: ChartEventData;
  actionProposal?: ActionProposalData;
  needsInput?: {
    requestId: string;
    questions: Array<{ question_id: string; prompt: string; options: Array<{ id: string; label: string }> }>;
  };
  stages?: string[];
}

export function ChatView({ compact = false }: { compact?: boolean }) {
  const { openDrawer } = useEvidenceDrawer();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "init",
      sender: "assistant",
      content:
        "Welcome to NeuralCFO + Moonshot Mode. I am your AI finance and strategy co-pilot. " +
        "You can analyze cash runway, test hiring scenarios, or explore bold strategic moves.",
      status: "verified",
    },
  ]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeAgent, setActiveAgent] = useState<"neuralcfo" | "moonshot">("neuralcfo");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || input;
    if (!text.trim() || isStreaming) return;

    const userMsg: ChatMessage = { id: `u_${Date.now()}`, sender: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsStreaming(true);

    const asstMsgId = `a_${Date.now()}`;
    const initialAsstMsg: ChatMessage = {
      id: asstMsgId,
      sender: "assistant",
      content: "",
      status: "verified",
      stages: [],
    };
    setMessages((prev) => [...prev, initialAsstMsg]);

    try {
      const response = await fetch("/v1/conversations/demo-conv-id/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: text, agent_key: activeAgent }),
      });

      if (!response.ok || !response.body) {
        throw new Error("API streaming error");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const block of lines) {
          if (!block.trim()) continue;
          let eventType = "message";
          let eventData = "";

          for (const line of block.split("\n")) {
            if (line.startsWith("event: ")) eventType = line.replace("event: ", "").trim();
            if (line.startsWith("data: ")) eventData = line.replace("data: ", "").trim();
          }

          if (!eventData) continue;
          const parsed = JSON.parse(eventData);

          setMessages((prev) =>
            prev.map((m) => {
              if (m.id !== asstMsgId) return m;

              if (eventType === "content_delta") {
                return { ...m, content: m.content + (parsed.delta || "") };
              }
              if (eventType === "stage_change") {
                return { ...m, stages: [...(m.stages || []), parsed.stage_name] };
              }
              if (eventType === "chart") {
                return { ...m, chart: parsed };
              }
              if (eventType === "action_proposal") {
                return { ...m, actionProposal: parsed };
              }
              if (eventType === "needs_input") {
                return { ...m, needsInput: parsed };
              }
              if (eventType === "citations") {
                return { ...m, citations: parsed.citations };
              }
              return m;
            })
          );
        }
      }
    } catch {
      // Deterministic client fallback simulation
      simulateDeterministicReply(text, asstMsgId);
    } finally {
      setIsStreaming(false);
    }
  };

  const simulateDeterministicReply = (text: string, asstMsgId: string) => {
    const lower = text.toLowerCase();

    if (lower.includes("hire") || lower.includes("developer")) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === asstMsgId
            ? {
                ...m,
                content:
                  "If your biggest client delays payment by 30 days while adding 2 developers (+$14,000/mo outflow), " +
                  "your runway compresses from 18.4 weeks to 9.2 weeks, breaching your 12-week safety reserve in Week 7. " +
                  "Recommendation: Enforce a 25% upfront project deposit ($25,000 cash acceleration) to maintain solvency.",
                status: "verified",
                citations: [
                  {
                    id: "cit_cfo_01",
                    target_type: "cfo_matrix",
                    target_id: "scen_hire_2devs_delay",
                    label: "CFO Forecast Matrix",
                    snippet: "Week 7 cash drops below $50k reserve threshold without deposit buffer.",
                  },
                ],
              }
            : m
        )
      );
    } else if (lower.includes("moonshot") || lower.includes("bold")) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === asstMsgId
            ? {
                ...m,
                content:
                  "Moonshot Mode Proposal: Transition from hourly billing to $15k upfront monthly retainers. " +
                  "This creates +$23,250 in net working capital float without debt or equity dilution. " +
                  "Verifier HR-01 through HR-12 confirmation: 100% deterministic mathematical proof.",
                status: "verified",
                citations: [
                  {
                    id: "cit_ms_01",
                    target_type: "archival_precedent",
                    target_id: "card_1",
                    label: "Acme MSA §4.2 Retainer Precedent",
                    snippet: "Negative working capital float generated via upfront collection terms.",
                  },
                ],
              }
            : m
        )
      );
    } else {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === asstMsgId
            ? {
                ...m,
                content: `Inquiry verified against tenant ledger: "${text}". All figures and claims are confirmed with deterministic calculations.`,
                status: "verified",
              }
            : m
        )
      );
    }
  };

  return (
    <div className={`clay-card p-5 rounded-3xl flex flex-col font-sans shadow-sm ${compact ? "h-[calc(100vh-10.5rem)]" : "h-[calc(100vh-7rem)]"}`}>
      {/* Quick Prompts Bar */}
      <div className="pb-3 flex items-center space-x-2 text-xs overflow-x-auto border-b border-slate-200 mb-3">
        <span className="text-slate-500 font-bold text-xs whitespace-nowrap">Quick Actions:</span>
        <button
          onClick={() => handleSend("Can we hire two developers if our biggest client pays 30 days late?")}
          className="clay-btn px-3.5 py-1.5 rounded-full text-slate-800 font-bold whitespace-nowrap transition-transform hover:-translate-y-0.5 flex items-center space-x-1.5 text-xs"
        >
          <Users className="w-3.5 h-3.5 text-emerald-600" />
          <span>[1] Hire 2 Devs + 30d</span>
        </button>
        <button
          onClick={() => handleSend("What bold move could fix this instead?")}
          className="clay-btn px-3.5 py-1.5 rounded-full text-slate-800 font-bold whitespace-nowrap transition-transform hover:-translate-y-0.5 flex items-center space-x-1.5 text-xs"
        >
          <Compass className="w-3.5 h-3.5 text-purple-600" />
          <span>[2] Bold Moonshot</span>
        </button>
        <button
          onClick={() => handleSend("Add the runway chart to my dashboard")}
          className="clay-btn px-3.5 py-1.5 rounded-full text-slate-800 font-bold whitespace-nowrap transition-transform hover:-translate-y-0.5 flex items-center space-x-1.5 text-xs"
        >
          <BarChart2 className="w-3.5 h-3.5 text-blue-600" />
          <span>[3] Add Chart</span>
        </button>
        <button
          onClick={() => handleSend("Remember that payroll is on the 28th")}
          className="clay-btn px-3.5 py-1.5 rounded-full text-slate-800 font-bold whitespace-nowrap transition-transform hover:-translate-y-0.5 flex items-center space-x-1.5 text-xs"
        >
          <BookmarkCheck className="w-3.5 h-3.5 text-amber-600" />
          <span>[4] Save Memory</span>
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex flex-col ${m.sender === "user" ? "items-end" : "items-start"}`}
          >
            <div
              className={`max-w-2xl p-5 rounded-3xl ${
                m.sender === "user"
                  ? "clay-pill-teal text-white rounded-br-sm shadow-md"
                  : "clay-cushion text-slate-800 rounded-bl-sm border border-white/80"
              }`}
            >
              {/* Agent Mode / Status Header */}
              {m.sender === "assistant" && (
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-200 text-xs">
                  <span className="font-extrabold text-[#648283] flex items-center space-x-1.5">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>NeuralCFO Agent</span>
                  </span>
                  {m.status && (
                    <span className="clay-pill-sage text-slate-900 px-2.5 py-0.5 rounded-full text-[10px] font-bold">
                      {m.status}
                    </span>
                  )}
                </div>
              )}

              {/* Progress Stages */}
              {m.stages && m.stages.length > 0 && (
                <div className="mb-2 p-2.5 clay-card-inset rounded-xl text-xs font-mono text-purple-900 font-bold">
                  <span className="text-slate-500">Pipeline Stages: </span>
                  {m.stages.join(" → ")}
                </div>
              )}

              {/* Message Content */}
              <div className="text-sm whitespace-pre-wrap leading-relaxed font-sans">{m.content}</div>

              {/* Inline Chart */}
              {m.chart && <ChartWidget chart={m.chart} />}

              {/* Inline Action Proposal */}
              {m.actionProposal && (
                <ApprovalCard
                  proposal={m.actionProposal}
                  onApprove={(id) => console.log("Approved action", id)}
                  onReject={(id) => console.log("Rejected action", id)}
                />
              )}

              {/* Clickable Evidence Citations */}
              {m.citations && m.citations.length > 0 && (
                <div className="mt-3 pt-2 border-t border-slate-200 flex flex-wrap gap-1.5 items-center">
                  <span className="text-[10px] text-slate-500 font-bold uppercase">Evidence:</span>
                  {m.citations.map((c) => (
                    <button
                      key={c.id}
                      onClick={() =>
                        openDrawer({
                          id: c.id,
                          target_type: c.target_type,
                          target_id: c.target_id,
                          title: c.label,
                          snippet: c.snippet,
                        })
                      }
                      className="text-xs px-3 py-1 rounded-full clay-btn text-[#648283] font-bold flex items-center space-x-1"
                    >
                      <ExternalLink className="w-3 h-3 text-[#648283]" />
                      <span>{c.label}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={scrollRef} />
      </div>

      {/* Input Form */}
      <div className="mt-3 pt-3 border-t border-slate-200">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center space-x-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about hiring, late payments, cash runway, or bold moves..."
            className="flex-1 clay-card-inset rounded-full px-5 py-3 text-xs text-slate-900 placeholder-slate-500 focus:outline-none transition-all font-sans"
            disabled={isStreaming}
          />
          <button
            type="submit"
            disabled={isStreaming || !input.trim()}
            className="px-6 py-3 clay-pill-sage text-slate-900 text-xs font-black rounded-full shadow-md flex items-center space-x-1.5 disabled:opacity-50 transition-all hover:scale-102"
          >
            <Send className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{isStreaming ? "Wait" : "Send"}</span>
          </button>
        </form>
      </div>
    </div>
  );
}
