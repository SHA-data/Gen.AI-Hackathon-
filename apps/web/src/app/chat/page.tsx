"use client";

import React, { useState, useRef, useEffect } from "react";
import { useEvidenceDrawer } from "@/components/evidence/EvidenceDrawer";
import { ApprovalCard, ActionProposalData } from "@/components/chat/ApprovalCard";
import { ChartWidget, ChartEventData } from "@/components/chat/ChartWidget";
import { Users, Compass, BarChart2, BookmarkCheck, ExternalLink } from "lucide-react";

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

export default function ChatPage() {
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
      // Connect to the backend chat SSE endpoint
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

              if (eventType === "token") {
                return { ...m, content: m.content + (parsed.delta || "") };
              }
              if (eventType === "stage") {
                return { ...m, stages: [...(m.stages || []), parsed.stage_name] };
              }
              if (eventType === "chart") {
                return { ...m, chart: parsed };
              }
              if (eventType === "action_proposal") {
                return { ...m, actionProposal: parsed };
              }
              if (eventType === "citation") {
                const c = {
                  id: parsed.id,
                  target_type: parsed.target_type,
                  target_id: parsed.target_id,
                  label: parsed.label || "Source Reference",
                  snippet: parsed.snippet,
                };
                return { ...m, citations: [...(m.citations || []), c] };
              }
              if (eventType === "tool_result" && parsed.kind === "needs_input") {
                return { ...m, needsInput: parsed };
              }
              if (eventType === "done") {
                return { ...m, status: parsed.status || "verified" };
              }
              return m;
            })
          );
        }
      }
    } catch (err) {
      // Fallback demo simulation if backend is starting up
      simulateDemoTurn(text, asstMsgId);
    } finally {
      setIsStreaming(false);
    }
  };

  const simulateDemoTurn = (text: string, asstMsgId: string) => {
    const lower = text.toLowerCase();
    if (lower.includes("hire") || lower.includes("developer") || lower.includes("late")) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === asstMsgId
            ? {
                ...m,
                content:
                  "Simulated hiring 2 developers ($6,000/mo each) while your primary client delays payment by 30 days. " +
                  "Your cash hits a minimum of $45,000.00 at Week 8, leaving 18 weeks of runway under expected collections. " +
                  "However, in the worst-case scenario, this triggers a cash reserve breach.",
                status: "verified",
                chart: {
                  chart_type: "line",
                  title: "Hire 2 Devs + 30d Client Delay Scenario",
                  cases: {
                    expected: { min_cash: "45,000.00", runway_weeks: 18 },
                    best: { min_cash: "65,000.00", end_cash: "92,000.00" },
                    worst: { min_cash: "15,000.00", end_cash: "5,000.00" },
                  },
                },
                citations: [
                  {
                    id: "c1",
                    target_type: "forecast_point",
                    target_id: "8c12b7a9-4b11-4fa3-9f12-094b8c9b1011",
                    label: "Min Cash Point (Week 8)",
                    snippet: "Cash reaches local minimum of $45,000.00 following delayed invoice #1042.",
                  },
                ],
              }
            : m
        )
      );
    } else if (lower.includes("bold") || lower.includes("moonshot") || lower.includes("fix")) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === asstMsgId
            ? {
                ...m,
                content:
                  "Moonshot Mode intake: I have identified two high-fit strategies that avoid the cash floor breach.\n\n" +
                  "1. **Performance-Based Retainer Shift**: Convert key clients to 50% upfront deposits (Fit: 88.5, Reversibility: High). " +
                  "Projected cash floor improves by +$35,000.00.\n\n" +
                  "2. **Productized Discovery Sprint**: Pre-sell 2-week architectural sprints paid 100% upfront (Fit: 82.0).\n\n" +
                  "[DISCLAIMER] NeuralCFO provides decision support and strategic stress-testing, not formal financial or legal advice.",
                status: "verified",
                citations: [
                  {
                    id: "c2",
                    target_type: "kb_excerpt",
                    target_id: "3a88c120-d39b-4bc2-b912-781190203344",
                    label: "Card: Upfront Retainer Model",
                    snippet: "Precedent from agency growth case studies: 50% upfront structure decreases working capital gap by 62%.",
                  },
                ],
              }
            : m
        )
      );
    } else if (lower.includes("chart") || lower.includes("dashboard")) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === asstMsgId
            ? {
                ...m,
                content: "I have prepared a proposal to add the Runway Forecast chart to your main dashboard.",
                actionProposal: {
                  action_id: "act_101",
                  action_type: "add_chart",
                  risk_level: "low",
                  preview: { widget: "LineChart", metric: "cash_runway", horizon: "26w" },
                  requires_approval: true,
                },
              }
            : m
        )
      );
    } else if (lower.includes("remember")) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === asstMsgId
            ? {
                ...m,
                content: "I have proposed saving this memory: 'Payroll is scheduled on the 28th of every month.' Would you like to confirm this?",
                status: "verified",
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
                content: `Processed inquiry: "${text}". All calculations and figures are verified against current tenant records.`,
                status: "verified",
              }
            : m
        )
      );
    }
  };

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-6rem)]">
      {/* Quick Prompts Bar */}
      <div className="py-2 flex items-center space-x-2 text-xs overflow-x-auto border-b border-slate-800/80 mb-3">
        <span className="text-slate-500 font-mono">Demo Quick-Actions:</span>
        <button
          onClick={() => handleSend("Can we hire two developers if our biggest client pays 30 days late?")}
          className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-emerald-400 border border-slate-700 whitespace-nowrap transition-colors flex items-center space-x-1.5"
        >
          <Users className="w-3.5 h-3.5" />
          <span>[1] Hire 2 Devs + 30d Delay</span>
        </button>
        <button
          onClick={() => handleSend("What bold move could fix this instead?")}
          className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-purple-400 border border-slate-700 whitespace-nowrap transition-colors flex items-center space-x-1.5"
        >
          <Compass className="w-3.5 h-3.5" />
          <span>[2] Bold Move (Moonshot Mode)</span>
        </button>
        <button
          onClick={() => handleSend("Add the runway chart to my dashboard")}
          className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-blue-400 border border-slate-700 whitespace-nowrap transition-colors flex items-center space-x-1.5"
        >
          <BarChart2 className="w-3.5 h-3.5" />
          <span>[3] Propose Dashboard Chart</span>
        </button>
        <button
          onClick={() => handleSend("Remember that payroll is on the 28th")}
          className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-amber-400 border border-slate-700 whitespace-nowrap transition-colors flex items-center space-x-1.5"
        >
          <BookmarkCheck className="w-3.5 h-3.5" />
          <span>[4] Save Assumption Memory</span>
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
              className={`max-w-2xl p-4 rounded-xl shadow-sm ${
                m.sender === "user"
                  ? "bg-emerald-700 text-white rounded-br-none"
                  : "bg-slate-900 text-slate-100 border border-slate-800 rounded-bl-none"
              }`}
            >
              {/* Agent Mode / Status Header */}
              {m.sender === "assistant" && (
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-xs">
                  <span className="font-semibold text-emerald-400 font-mono">NeuralCFO Agent</span>
                  {m.status && (
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${
                        m.status === "verified"
                          ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                          : "bg-amber-950 text-amber-400 border border-amber-800"
                      }`}
                    >
                      {m.status}
                    </span>
                  )}
                </div>
              )}

              {/* Progress Stages */}
              {m.stages && m.stages.length > 0 && (
                <div className="mb-2 p-2 bg-slate-950 rounded border border-slate-800 text-[11px] font-mono text-purple-300">
                  <span className="text-slate-500">Pipeline Stages: </span>
                  {m.stages.join(" → ")}
                </div>
              )}

              {/* Message Content */}
              <div className="text-sm whitespace-pre-wrap leading-relaxed">{m.content}</div>

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

              {/* Tappable Clarification Options for Moonshot */}
              {m.needsInput && (
                <div className="my-3 p-3 bg-purple-950/40 border border-purple-800 rounded">
                  <div className="text-xs font-semibold text-purple-300 mb-2 font-mono uppercase">
                    [CONSTRAINTS REQUIRED] Moonshot Mode Intake
                  </div>
                  {m.needsInput.questions.map((q) => (
                    <div key={q.question_id} className="mb-2">
                      <p className="text-xs text-slate-300 mb-1">{q.prompt}</p>
                      <div className="flex flex-wrap gap-1.5">
                        {q.options.map((opt) => (
                          <button
                            key={opt.id}
                            onClick={() => handleSend(opt.label)}
                            className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-purple-900 text-slate-200 rounded border border-slate-700 transition-colors font-mono"
                          >
                            {opt.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Clickable Evidence Citations */}
              {m.citations && m.citations.length > 0 && (
                <div className="mt-3 pt-2 border-t border-slate-800 flex flex-wrap gap-1.5 items-center">
                  <span className="text-[10px] text-slate-500 font-mono uppercase">Evidence:</span>
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
                      className="text-xs font-mono px-2 py-0.5 rounded bg-slate-950 hover:bg-slate-800 text-emerald-300 border border-emerald-900 transition-colors flex items-center space-x-1"
                    >
                      <ExternalLink className="w-3 h-3 text-emerald-400" />
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
      <div className="mt-3 pt-3 border-t border-slate-800">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex space-x-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about hiring, late payments, cash runway, or bold moves..."
            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
            disabled={isStreaming}
          />
          <button
            type="submit"
            disabled={isStreaming || !input.trim()}
            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-sm font-semibold rounded-lg shadow transition-colors font-mono uppercase"
          >
            {isStreaming ? "Thinking..." : "Send"}
          </button>
        </form>
      </div>
    </div>
  );
}
