"use client";

import React from "react";
import { BarChart2 } from "lucide-react";

export interface ChartEventData {
  chart_type: "line" | "bar" | "waterfall";
  title: string;
  cases?: {
    expected?: { min_cash: string; runway_weeks?: number; weekly_cash?: Array<{ week_start: string; cash: string }> };
    best?: { min_cash: string; end_cash: string };
    worst?: { min_cash: string; end_cash: string };
  };
}

export function ChartWidget({ chart }: { chart: ChartEventData }) {
  const expected = chart.cases?.expected;
  const worst = chart.cases?.worst;
  const best = chart.cases?.best;

  return (
    <div className="my-3 p-4 bg-slate-900/90 border border-slate-800 rounded-lg max-w-xl">
      <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-800">
        <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider font-mono flex items-center space-x-1.5">
          <BarChart2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>{chart.title}</span>
        </h4>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
          Canonical Weekly Series
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-3">
        <div className="p-2 bg-slate-950 rounded border border-slate-800/80">
          <div className="text-[10px] text-slate-400 font-mono">Expected Min Cash</div>
          <div className="text-sm font-bold text-slate-100 font-mono">
            ${expected?.min_cash || "N/A"}
          </div>
          <div className="text-[10px] text-slate-500 font-mono">
            Runway: {expected?.runway_weeks ? `${expected.runway_weeks}w` : "Solvent"}
          </div>
        </div>

        <div className="p-2 bg-slate-950 rounded border border-slate-800/80">
          <div className="text-[10px] text-emerald-400 font-mono">Best Case End</div>
          <div className="text-sm font-bold text-emerald-300 font-mono">
            ${best?.end_cash || "N/A"}
          </div>
          <div className="text-[10px] text-emerald-600 font-mono">Fast Collections (-7d)</div>
        </div>

        <div className="p-2 bg-slate-950 rounded border border-slate-800/80">
          <div className="text-[10px] text-rose-400 font-mono">Worst Case Min</div>
          <div className="text-sm font-bold text-rose-300 font-mono">
            ${worst?.min_cash || "N/A"}
          </div>
          <div className="text-[10px] text-rose-600 font-mono">Delays (+14d)</div>
        </div>
      </div>

      {expected?.weekly_cash && expected.weekly_cash.length > 0 && (
        <div className="p-2 bg-slate-950 rounded border border-slate-800 text-xs font-mono text-slate-400">
          <div className="text-[10px] text-slate-500 mb-1">Weekly Cash Trajectory (26 Weeks):</div>
          <div className="flex items-end space-x-1 h-12 pt-2">
            {expected.weekly_cash.slice(0, 16).map((pt, i) => {
              const val = Math.max(10, Math.min(100, Math.round(Number(pt.cash) / 1500)));
              return (
                <div
                  key={i}
                  title={`${pt.week_start}: $${pt.cash}`}
                  className="flex-1 bg-emerald-500/60 hover:bg-emerald-400 rounded-t transition-all cursor-pointer"
                  style={{ height: `${val}%` }}
                />
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
