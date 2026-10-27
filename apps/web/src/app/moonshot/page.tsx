import React from "react";

export default function MoonshotPage() {
  return (
    <div className="p-8 max-w-4xl mx-auto bg-slate-900 border border-slate-800 rounded-xl mt-6">
      <div className="flex items-center space-x-3 mb-4">
        <span className="text-2xl">🚀</span>
        <div>
          <h1 className="text-xl font-bold text-slate-100">Moonshot Mode: Strategy & Experimentation</h1>
          <p className="text-xs text-slate-400 font-mono">Module Owner: Aleena (/services/api/app/moonshot)</p>
        </div>
      </div>
      <p className="text-sm text-slate-300 leading-relaxed mb-6">
        This sub-page is reserved for Aleena to display the 6-Card Moonshot Strategy Explorer,
        Gated Criteria Scoring Matrices, Weight Sensitivity Analysis, and 30-Day Experiment Plans.
      </p>
      <div className="grid grid-cols-2 gap-4 text-xs font-mono">
        <div className="p-4 bg-slate-950 rounded border border-slate-800">
          <div className="text-purple-400 font-semibold mb-1">Workflow Pipeline Active:</div>
          <ul className="text-slate-400 space-y-1">
            <li>• POST /v1/moonshot/run (SSE Stage Events)</li>
            <li>• GET /v1/moonshot/reports/:id</li>
            <li>• POST /v1/moonshot/requests/:id/answers</li>
          </ul>
        </div>
        <div className="p-4 bg-slate-950 rounded border border-slate-800">
          <div className="text-amber-400 font-semibold mb-1">Disclaimer & Citations:</div>
          <p className="text-slate-400">
            All strategy cards link to verified knowledge excerpts; disclaimers are enforced by verifier check V8.
          </p>
        </div>
      </div>
    </div>
  );
}
