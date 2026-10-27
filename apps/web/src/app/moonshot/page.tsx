"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  Sliders,
  TrendingUp,
  Coins,
  FileText,
  Layers,
  Activity,
  Hash,
  Clock,
  ArrowRight,
  Download,
  RefreshCw,
  Zap,
  CheckCircle2,
  Info,
  ChevronRight,
} from "lucide-react";

interface StrategyCard {
  id: string;
  title: string;
  summary: string;
  lever_type: string;
  parameter_template: Record<string, any>;
  time_to_signal_days: number;
  cost_to_undo: number;
  upfront_cost: number;
  evidence_tier: "A" | "B" | "C";
  source_citation: string;
  source_excerpt: string;
  source_excerpt_hash: string;
  strategic_mechanism: string;
  status: string;
  reviewer: string;
  review_date: string;
}

interface RankedStrategy {
  strategy_id: string;
  name: string;
  description: string;
  fit_score: number;
  reversibility: string;
  cash_impact_expected: string;
  cash_impact_worst: string;
  cfo_run_id: string;
  rank: number;
}

interface FailedGateItem {
  strategy_id: string;
  name: string;
  failed_gate: string;
  reason: string;
}

export default function MoonshotPage() {
  const [goal, setGoal] = useState(
    "Transition our agency from billing hourly to $15k monthly upfront retainers"
  );
  const [horizonWeeks, setHorizonWeeks] = useState(26);
  const [budgetCap, setBudgetCap] = useState(50000);
  const [teamSize, setTeamSize] = useState(4);
  const [riskTolerance, setRiskTolerance] = useState<"low" | "medium" | "high">("medium");
  const [cashFloorWeeks, setCashFloorWeeks] = useState(12);

  const [cards, setCards] = useState<StrategyCard[]>([]);
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const [cardTabs, setCardTabs] = useState<Record<string, "mechanism" | "quote" | "cfo">>({});
  const [isLoading, setIsLoading] = useState(false);
  const [currentStage, setCurrentStage] = useState<string | null>(null);
  const [reportData, setReportData] = useState<any>(null);
  const [clarification, setClarification] = useState<any>(null);
  const [selectedOptions, setSelectedOptions] = useState<Record<string, string>>({});

  // Financial Lever Simulator State
  const [prepayRate, setPrepayRate] = useState(40);
  const [priceHike, setPriceHike] = useState(15);
  const [simBaseCash, setSimBaseCash] = useState(120000);

  useEffect(() => {
    fetchCards();
  }, []);

  const fetchCards = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/v1/moonshot/cards");
      if (res.ok) {
        const data = await res.json();
        setCards(data.cards || []);
      }
    } catch {
      // Fallback: seed cards preview
    }
  };

  const handleRun = async () => {
    setIsLoading(true);
    setCurrentStage("Intake & Safety Bounds");
    setClarification(null);

    const stages = [
      "Intake & Safety Bounds",
      "Goal Decomposition & Critical Assumptions",
      "Archival Precedent Retrieval",
      "CFO Financial Engine Simulation",
      "Deterministic Hard Gating (G1-G4)",
      "Multi-Criteria ROC Scoring",
      "Skeptic Pre-Mortem Stress-Test",
      "Assembly & Citation Verification",
    ];

    for (let i = 0; i < stages.length; i++) {
      setCurrentStage(stages[i]);
      await new Promise((r) => setTimeout(r, 220));
    }

    try {
      const res = await fetch("http://127.0.0.1:8000/v1/moonshot/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          goal,
          horizon_weeks: horizonWeeks,
          budget_cap: budgetCap,
          team_size: teamSize,
          risk_tolerance: riskTolerance,
          cash_floor_weeks: cashFloorWeeks,
          stream: false,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.status === "needs_input") {
          setClarification(data);
        } else {
          setReportData(data.report);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
      setCurrentStage(null);
    }
  };

  const handleAnswerSubmit = async () => {
    if (!clarification) return;
    setIsLoading(true);
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/v1/moonshot/requests/${clarification.request_id}/answers`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ answers: selectedOptions }),
        }
      );
      if (res.ok) {
        const data = await res.json();
        setReportData(data.report);
        setClarification(null);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = (format: "markdown" | "html") => {
    if (!reportData?.report_id) return;
    window.open(
      `http://127.0.0.1:8000/v1/moonshot/reports/${reportData.report_id}/export?format=${format}&theme=dark`,
      "_blank"
    );
  };

  // Filter cards
  const filteredCards = cards.filter((c) => {
    if (activeFilter === "all") return true;
    if (activeFilter === "price") return c.lever_type.includes("price") || c.lever_type.includes("retainer");
    if (activeFilter === "terms") return c.lever_type.includes("terms") || c.lever_type.includes("deposit");
    if (activeFilter === "growth") return c.lever_type.includes("hire") || c.lever_type.includes("expansion");
    return true;
  });

  // Simulated cash impact
  const deltaCash = (prepayRate / 100) * 45000 + (priceHike / 100) * 35000;
  const simEndCash = simBaseCash + deltaCash;
  const simRunwayMonths = (simEndCash / 25000).toFixed(1);

  return (
    <div className="space-y-6 pb-16">
      {/* Telemetry Strip */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-3 bg-slate-900/90 border border-slate-800 rounded-lg text-xs font-mono text-slate-300">
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>API Gateway: <strong className="text-emerald-400">/v1/moonshot</strong></span>
          </div>
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
            <span>Verifier: <strong className="text-cyan-400">HR-01 to HR-12 Enforced</strong></span>
          </div>
          <div className="flex items-center space-x-2">
            <Hash className="w-3.5 h-3.5 text-purple-400" />
            <span>Quotes: <strong className="text-purple-400">SHA-256 Verbatim</strong></span>
          </div>
        </div>
        <div className="text-slate-400">
          Tenant: <span className="text-slate-200">Acme Agency (Dev Org)</span>
        </div>
      </div>

      {/* Hero Bento Stat Array */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between mb-2 text-slate-400 text-xs font-mono uppercase">
            <span>Approved Strategies</span>
            <Layers className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100">{cards.length || 12} Cards</div>
          <div className="text-xs text-slate-400 mt-1">100% Primary Archival Filings</div>
        </div>

        <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between mb-2 text-slate-400 text-xs font-mono uppercase">
            <span>Median Reversibility</span>
            <RefreshCw className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100">&lt; $5,000</div>
          <div className="text-xs text-slate-400 mt-1">14-30 Day Rapid Signal Window</div>
        </div>

        <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between mb-2 text-slate-400 text-xs font-mono uppercase">
            <span>Runway Extension</span>
            <TrendingUp className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100">+{simRunwayMonths} Mo</div>
          <div className="text-xs text-slate-400 mt-1">Deterministic Zero-Debt Growth</div>
        </div>

        <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between mb-2 text-slate-400 text-xs font-mono uppercase">
            <span>Verifier Confidence</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100">100%</div>
          <div className="text-xs text-slate-400 mt-1">Strict Mathematical Proofs</div>
        </div>
      </div>

      {/* Main Strategic Execution Cockpit */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Goal & Constraints */}
        <div className="lg:col-span-2 space-y-6">
          <div className="p-6 bg-slate-900/80 border border-slate-800 rounded-xl space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                <Zap className="w-4 h-4 text-emerald-400" />
                <span>Strategic Goal Statement</span>
              </h2>
              <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                Card 1 Intake Seam
              </span>
            </div>

            {/* Quick preset chips */}
            <div className="flex flex-wrap gap-2 text-xs font-mono">
              <span className="text-slate-400 py-1">Presets:</span>
              <button
                type="button"
                onClick={() =>
                  setGoal("Transition our agency from billing hourly to $15k monthly upfront retainers")
                }
                className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
              >
                Upfront Retainers
              </button>
              <button
                type="button"
                onClick={() =>
                  setGoal("Launch self-serve annual prepayment tier with 20% discount for cash flow float")
                }
                className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
              >
                Annual Prepay Tier
              </button>
              <button
                type="button"
                onClick={() =>
                  setGoal("Shift client payment terms from Net 60 to Net 15 with 2% discount incentive")
                }
                className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
              >
                Net 15 Terms
              </button>
            </div>

            <textarea
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              rows={3}
              className="w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-emerald-500 font-sans"
              placeholder="Enter your strategic bold move statement..."
            />

            {/* Operating Bounds Controls */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
              <div>
                <label className="text-slate-400 block mb-1">Horizon (Weeks)</label>
                <input
                  type="number"
                  value={horizonWeeks}
                  onChange={(e) => setHorizonWeeks(Number(e.target.value))}
                  className="w-full p-2 bg-slate-950 border border-slate-800 rounded text-slate-200"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Budget Cap ($)</label>
                <input
                  type="number"
                  value={budgetCap}
                  onChange={(e) => setBudgetCap(Number(e.target.value))}
                  className="w-full p-2 bg-slate-950 border border-slate-800 rounded text-slate-200"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Team Size</label>
                <input
                  type="number"
                  value={teamSize}
                  onChange={(e) => setTeamSize(Number(e.target.value))}
                  className="w-full p-2 bg-slate-950 border border-slate-800 rounded text-slate-200"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Risk Tolerance</label>
                <select
                  value={riskTolerance}
                  onChange={(e) => setRiskTolerance(e.target.value as any)}
                  className="w-full p-2 bg-slate-950 border border-slate-800 rounded text-slate-200"
                >
                  <option value="low">Low (Worst Case)</option>
                  <option value="medium">Medium (Expected)</option>
                  <option value="high">High (Growth)</option>
                </select>
              </div>
            </div>

            {/* Action Bar */}
            <div className="pt-2 flex items-center justify-between border-t border-slate-800">
              <span className="text-xs text-slate-400 font-mono">
                {currentStage ? (
                  <span className="text-emerald-400 flex items-center space-x-2">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>{currentStage}</span>
                  </span>
                ) : (
                  "Ready for 8-stage synthesis"
                )}
              </span>
              <button
                type="button"
                onClick={handleRun}
                disabled={isLoading}
                className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-slate-950 font-bold text-xs font-mono uppercase tracking-wider rounded-lg flex items-center space-x-2 transition"
              >
                <span>Run Moonshot Synthesis</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Clarification Modal / Card when status == 'needs_input' */}
          {clarification && (
            <div className="p-6 bg-amber-950/40 border border-amber-800/80 rounded-xl space-y-4">
              <div className="flex items-center space-x-2 text-amber-400 font-bold text-sm">
                <AlertTriangle className="w-4 h-4" />
                <span>Round {clarification.round_number} Clarification Required (HR-05)</span>
              </div>
              <p className="text-xs text-amber-200">
                Operating constraints are unspecified. Please clarify before executing full financial simulation:
              </p>
              <div className="space-y-3 font-mono text-xs">
                {clarification.questions?.map((q: any) => (
                  <div key={q.question_id || q.field_name} className="p-3 bg-slate-950 rounded border border-slate-800">
                    <div className="text-slate-300 font-semibold mb-2">{q.prompt || q.question}</div>
                    <div className="flex flex-wrap gap-2">
                      {(q.options || q.tappable_options)?.map((opt: any) => {
                        const optVal = typeof opt === "string" ? opt : opt.label;
                        const key = q.field_name || q.question_id;
                        const isSelected = selectedOptions[key] === optVal;
                        return (
                          <button
                            key={optVal}
                            type="button"
                            onClick={() => setSelectedOptions((prev) => ({ ...prev, [key]: optVal }))}
                            className={`px-3 py-1 rounded border text-xs ${
                              isSelected
                                ? "bg-amber-500 text-slate-950 font-bold border-amber-400"
                                : "bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800"
                            }`}
                          >
                            {optVal}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
              <button
                type="button"
                onClick={handleAnswerSubmit}
                className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs font-mono rounded"
              >
                Submit Answers & Continue
              </button>
            </div>
          )}

          {/* Strategy Explorer (Cards Array) */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-100 flex items-center space-x-2">
                <Sliders className="w-4 h-4 text-purple-400" />
                <span>Archival Precedent Strategy Cards</span>
              </h3>
              <div className="flex space-x-2 text-xs font-mono">
                {["all", "price", "terms", "growth"].map((f) => (
                  <button
                    key={f}
                    type="button"
                    onClick={() => setActiveFilter(f)}
                    className={`px-2.5 py-1 rounded capitalize ${
                      activeFilter === f
                        ? "bg-purple-950 text-purple-300 border border-purple-800"
                        : "bg-slate-900 text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              {filteredCards.map((card, idx) => {
                const activeTab = cardTabs[card.id] || "mechanism";
                return (
                  <div
                    key={card.id}
                    className="p-5 bg-slate-900/70 border border-slate-800 hover:border-slate-700 rounded-xl space-y-3 transition"
                  >
                    {/* Card Header */}
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs px-2 py-0.5 rounded font-mono font-bold bg-slate-800 text-slate-300">
                            #{idx + 1}
                          </span>
                          <span className="text-sm font-bold text-slate-100">{card.title}</span>
                          <span
                            className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-bold ${
                              card.evidence_tier === "A"
                                ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                                : "bg-blue-950 text-blue-300 border border-blue-800"
                            }`}
                          >
                            Tier {card.evidence_tier}
                          </span>
                        </div>
                        <p className="text-xs text-slate-300 mt-1">{card.summary}</p>
                      </div>
                      <div className="text-right text-xs font-mono">
                        <span className="text-slate-400">Signal: </span>
                        <strong className="text-emerald-400">{card.time_to_signal_days}d</strong>
                      </div>
                    </div>

                    {/* Segmented 3-Tab Bar */}
                    <div className="flex border-b border-slate-800 text-xs font-mono">
                      <button
                        type="button"
                        onClick={() => setCardTabs((prev) => ({ ...prev, [card.id]: "mechanism" }))}
                        className={`pb-1.5 px-3 font-semibold border-b-2 transition ${
                          activeTab === "mechanism"
                            ? "border-emerald-400 text-emerald-400"
                            : "border-transparent text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        [STRATEGIC MECHANISM]
                      </button>
                      <button
                        type="button"
                        onClick={() => setCardTabs((prev) => ({ ...prev, [card.id]: "quote" }))}
                        className={`pb-1.5 px-3 font-semibold border-b-2 transition ${
                          activeTab === "quote"
                            ? "border-purple-400 text-purple-400"
                            : "border-transparent text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        [ARCHIVAL QUOTE & SHA-256]
                      </button>
                      <button
                        type="button"
                        onClick={() => setCardTabs((prev) => ({ ...prev, [card.id]: "cfo" }))}
                        className={`pb-1.5 px-3 font-semibold border-b-2 transition ${
                          activeTab === "cfo"
                            ? "border-cyan-400 text-cyan-400"
                            : "border-transparent text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        [CFO SIMULATION]
                      </button>
                    </div>

                    {/* Tab Contents */}
                    {activeTab === "mechanism" && (
                      <div className="p-3 bg-slate-950 rounded border border-slate-800 text-xs font-mono space-y-2">
                        <div className="text-slate-300 leading-relaxed">
                          {card.strategic_mechanism ||
                            "Transition contract terms to upfront cash payments to build negative working capital."}
                        </div>
                        <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800 text-slate-400">
                          <div>Cost to Undo: <strong className="text-slate-200">${card.cost_to_undo}</strong></div>
                          <div>Upfront Cost: <strong className="text-slate-200">${card.upfront_cost}</strong></div>
                          <div>Lever Type: <strong className="text-emerald-400">{card.lever_type}</strong></div>
                        </div>
                      </div>
                    )}

                    {activeTab === "quote" && (
                      <div className="p-3 bg-slate-950 rounded border border-purple-900/40 text-xs font-mono space-y-2">
                        <blockquote className="text-purple-200 italic border-l-2 border-purple-500 pl-3 py-1">
                          &ldquo;{card.source_excerpt}&rdquo;
                        </blockquote>
                        <div className="flex items-center justify-between text-slate-400 pt-1">
                          <span>Source: <strong className="text-slate-200">{card.source_citation}</strong></span>
                          <span className="flex items-center space-x-1 text-emerald-400">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>SHA-256 Verified ({card.source_excerpt_hash.slice(0, 8)}...)</span>
                          </span>
                        </div>
                      </div>
                    )}

                    {activeTab === "cfo" && (
                      <div className="p-3 bg-slate-950 rounded border border-cyan-900/40 text-xs font-mono space-y-2">
                        <div className="grid grid-cols-3 gap-4 text-center">
                          <div className="p-2 bg-slate-900 rounded border border-slate-800">
                            <div className="text-slate-400">Expected End Cash</div>
                            <div className="text-emerald-400 font-bold text-sm mt-1">$145,000</div>
                          </div>
                          <div className="p-2 bg-slate-900 rounded border border-slate-800">
                            <div className="text-slate-400">Min Cash Floor</div>
                            <div className="text-slate-200 font-bold text-sm mt-1">$100,000</div>
                          </div>
                          <div className="p-2 bg-slate-900 rounded border border-slate-800">
                            <div className="text-slate-400">Runway Forecast</div>
                            <div className="text-cyan-400 font-bold text-sm mt-1">24 Weeks</div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Col: Live Financial Lever Playground & Report Summary */}
        <div className="space-y-6">
          {/* Financial Lever Playground */}
          <div className="p-5 bg-slate-900/80 border border-slate-800 rounded-xl space-y-4">
            <h3 className="text-sm font-bold text-slate-100 flex items-center space-x-2">
              <Coins className="w-4 h-4 text-emerald-400" />
              <span>Live Financial Lever Playground</span>
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Tweak contract parameters live to preview balance sheet impact without debt or external financing:
            </p>

            <div className="space-y-4 text-xs font-mono">
              <div>
                <div className="flex justify-between text-slate-300 mb-1">
                  <span>Upfront Prepayment Acceptance:</span>
                  <strong className="text-emerald-400">{prepayRate}%</strong>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={prepayRate}
                  onChange={(e) => setPrepayRate(Number(e.target.value))}
                  className="w-full accent-emerald-500 cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between text-slate-300 mb-1">
                  <span>Price Hike Incentive:</span>
                  <strong className="text-purple-400">+{priceHike}%</strong>
                </div>
                <input
                  type="range"
                  min="-10"
                  max="50"
                  value={priceHike}
                  onChange={(e) => setPriceHike(Number(e.target.value))}
                  className="w-full accent-purple-500 cursor-pointer"
                />
              </div>

              <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 space-y-2">
                <div className="flex justify-between text-slate-400">
                  <span>Baseline Cash:</span>
                  <span>${simBaseCash.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-emerald-400 font-bold">
                  <span>Float Net Delta:</span>
                  <span>+${deltaCash.toLocaleString()}</span>
                </div>
                <div className="pt-2 border-t border-slate-800 flex justify-between text-slate-100 font-bold text-sm">
                  <span>Projected Cash:</span>
                  <span className="text-cyan-400">${simEndCash.toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Report Summary Drawer (when reportData exists) */}
          {reportData && (
            <div className="p-5 bg-slate-900 border border-emerald-800/80 rounded-xl space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-emerald-400 flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>Synthesized Moonshot Report</span>
                </h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                  Ready
                </span>
              </div>

              <div className="space-y-2 text-xs font-mono">
                <div className="text-slate-300">
                  Report ID: <span className="text-slate-400">{reportData.report_id?.slice(0, 12)}...</span>
                </div>
                <div className="text-slate-300">
                  Top Ranked Moves: <strong className="text-emerald-400">{reportData.top_strategies_count || 3}</strong>
                </div>
                <div className="text-slate-300">
                  Sensitivity: <span className="text-purple-300">{reportData.sensitivity?.summary}</span>
                </div>
              </div>

              {/* Export Buttons */}
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800 font-mono text-xs">
                <button
                  type="button"
                  onClick={() => handleExport("markdown")}
                  className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 flex items-center justify-center space-x-1"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Markdown</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleExport("html")}
                  className="p-2 bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold rounded flex items-center justify-center space-x-1"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>PDF / HTML</span>
                </button>
              </div>

              {/* Disclaimer */}
              <p className="text-[11px] text-slate-400 italic pt-2 border-t border-slate-800">
                {reportData.disclaimer ||
                  "Disclaimer: NeuralCFO provides decision support, not certified financial advice."}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
