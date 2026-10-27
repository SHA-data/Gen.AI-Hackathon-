"use client";

import React, { useState } from "react";

export interface ActionProposalData {
  action_id: string;
  action_type: string;
  risk_level: "low" | "medium" | "high";
  preview: Record<string, any>;
  requires_approval: boolean;
}

export function ApprovalCard({
  proposal,
  onApprove,
  onReject,
}: {
  proposal: ActionProposalData;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}) {
  const [decided, setDecided] = useState<"approved" | "rejected" | null>(null);

  const handleApprove = () => {
    setDecided("approved");
    onApprove(proposal.action_id);
  };

  const handleReject = () => {
    setDecided("rejected");
    onReject(proposal.action_id);
  };

  return (
    <div className="my-3 p-4 bg-slate-900 border border-slate-700 rounded-lg shadow-md max-w-lg">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 uppercase">
            {proposal.risk_level} Risk Action
          </span>
          <span className="text-sm font-semibold text-slate-200">{proposal.action_type}</span>
        </div>
        <span className="text-xs text-slate-400 font-mono">
          {decided ? decided.toUpperCase() : "Awaiting Decision"}
        </span>
      </div>

      <div className="my-3 text-xs text-slate-300 font-mono bg-slate-950 p-2.5 rounded border border-slate-800">
        <pre className="overflow-x-auto">{JSON.stringify(proposal.preview, null, 2)}</pre>
      </div>

      {!decided ? (
        <div className="flex space-x-3 pt-2">
          <button
            onClick={handleApprove}
            className="flex-1 py-1.5 px-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold shadow transition-colors"
          >
            ✓ Approve & Apply
          </button>
          <button
            onClick={handleReject}
            className="py-1.5 px-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-semibold transition-colors"
          >
            ✕ Reject
          </button>
        </div>
      ) : (
        <div className="text-xs font-medium text-slate-400 italic">
          Decision recorded: {decided}. Audit event logged.
        </div>
      )}
    </div>
  );
}
