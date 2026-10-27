import React from "react";

export default function CfoPage() {
  return (
    <div className="p-8 max-w-4xl mx-auto bg-slate-900 border border-slate-800 rounded-xl mt-6">
      <div className="flex items-center space-x-3 mb-4">
        <span className="text-2xl">📊</span>
        <div>
          <h1 className="text-xl font-bold text-slate-100">NeuralCFO Mode: Finance Engine Workspace</h1>
          <p className="text-xs text-slate-400 font-mono">Module Owner: Sharjeel (/services/api/app/cfo)</p>
        </div>
      </div>
      <p className="text-sm text-slate-300 leading-relaxed mb-6">
        This sub-page is reserved for Sharjeel to render the full-page Scenario Comparison Matrix,
        Cash Runway Trajectory, Baseline Settings, and CSV Import Quality Reports.
      </p>
      <div className="grid grid-cols-2 gap-4 text-xs font-mono">
        <div className="p-4 bg-slate-950 rounded border border-slate-800">
          <div className="text-emerald-400 font-semibold mb-1">Contract v1 Endpoints Active:</div>
          <ul className="text-slate-400 space-y-1">
            <li>• POST /v1/finance/scenarios/run</li>
            <li>• GET /v1/finance/metrics</li>
            <li>• POST /v1/finance/imports</li>
          </ul>
        </div>
        <div className="p-4 bg-slate-950 rounded border border-slate-800">
          <div className="text-blue-400 font-semibold mb-1">Evidence Drawer Integration:</div>
          <p className="text-slate-400">
            Clicking any scenario point automatically connects to the global Evidence Drawer host mounted in the root layout.
          </p>
        </div>
      </div>
    </div>
  );
}
