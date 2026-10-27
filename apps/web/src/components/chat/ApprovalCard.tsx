"use client";

import React, { useState } from "react";
import { Check, X, ShieldAlert } from "lucide-react";

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
    <div className="my-3 p-4 clay-card rounded-3xl shadow-sm max-w-lg font-sans border border-white/90">
      <div className="flex items-center justify-between pb-2.5 border-b border-slate-300">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300 uppercase flex items-center space-x-1">
            <ShieldAlert className="w-3 h-3 text-amber-700" />
            <span>{proposal.risk_level} Risk Action</span>
          </span>
          <span className="text-sm font-extrabold text-slate-900">{proposal.action_type}</span>
        </div>
        <span className="text-xs text-slate-500 font-bold font-mono">
          {decided ? decided.toUpperCase() : "Awaiting Decision"}
        </span>
      </div>

      <div className="my-3 text-xs text-slate-800 font-mono clay-card-inset p-3 rounded-2xl overflow-x-auto">
        <pre className="overflow-x-auto leading-relaxed">{JSON.stringify(proposal.preview, null, 2)}</pre>
      </div>

      {!decided ? (
        <div className="flex space-x-2.5 pt-1">
          <button
            onClick={handleApprove}
            className="flex-1 py-2 px-3.5 clay-pill-sage text-slate-900 rounded-full text-xs font-bold shadow-md transition-transform hover:-translate-y-0.5 flex items-center justify-center space-x-1.5"
          >
            <Check className="w-3.5 h-3.5" />
            <span>Approve & Apply</span>
          </button>
          <button
            onClick={handleReject}
            className="py-2 px-4 clay-btn text-rose-700 hover:text-rose-900 rounded-full text-xs font-bold transition-transform hover:-translate-y-0.5 flex items-center justify-center space-x-1.5"
          >
            <X className="w-3.5 h-3.5" />
            <span>Reject</span>
          </button>
        </div>
      ) : (
        <div className="text-xs font-bold text-slate-600 italic">
          Decision recorded: {decided}. Audit event logged.
        </div>
      )}
    </div>
  );
}
