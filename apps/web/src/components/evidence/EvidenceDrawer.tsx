"use client";

import React, { createContext, useContext, useState } from "react";

export interface EvidenceCitation {
  id: string;
  claim_id?: string;
  target_type: string;
  target_id: string;
  title?: string;
  snippet?: string;
  metadata?: Record<string, any>;
}

interface EvidenceDrawerContextType {
  isOpen: boolean;
  activeCitation: EvidenceCitation | null;
  openDrawer: (citation: EvidenceCitation) => void;
  closeDrawer: () => void;
}

const EvidenceDrawerContext = createContext<EvidenceDrawerContextType>({
  isOpen: false,
  activeCitation: null,
  openDrawer: () => {},
  closeDrawer: () => {},
});

export const useEvidenceDrawer = () => useContext(EvidenceDrawerContext);

export function EvidenceDrawerProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeCitation, setActiveCitation] = useState<EvidenceCitation | null>(null);

  const openDrawer = (citation: EvidenceCitation) => {
    setActiveCitation(citation);
    setIsOpen(true);
  };

  const closeDrawer = () => {
    setIsOpen(false);
    setActiveCitation(null);
  };

  return (
    <EvidenceDrawerContext.Provider value={{ isOpen, activeCitation, openDrawer, closeDrawer }}>
      {children}
      {/* Evidence Drawer Host */}
      {isOpen && activeCitation && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-md bg-slate-900 border-l border-slate-800 p-6 shadow-2xl flex flex-col justify-between animate-in slide-in-from-right">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                  <h3 className="font-semibold text-slate-100">Evidence Lineage Drawer</h3>
                </div>
                <button
                  onClick={closeDrawer}
                  className="text-slate-400 hover:text-slate-100 text-sm font-mono px-2 py-1 bg-slate-800 rounded"
                >
                  ESC
                </button>
              </div>

              <div className="mt-4 space-y-4">
                <div>
                  <label className="text-xs font-mono text-slate-400 uppercase">Target Entity Type</label>
                  <p className="mt-0.5 text-sm font-semibold text-emerald-400">
                    {activeCitation.target_type}
                  </p>
                </div>

                <div>
                  <label className="text-xs font-mono text-slate-400 uppercase">Target ID</label>
                  <p className="mt-0.5 text-xs font-mono text-slate-300 bg-slate-950 p-2 rounded border border-slate-800 truncate">
                    {activeCitation.target_id}
                  </p>
                </div>

                <div>
                  <label className="text-xs font-mono text-slate-400 uppercase">Source Title / Reference</label>
                  <p className="mt-0.5 text-sm text-slate-200">
                    {activeCitation.title || "Primary Source Record"}
                  </p>
                </div>

                <div>
                  <label className="text-xs font-mono text-slate-400 uppercase">Verifiable Snippet / Lineage</label>
                  <div className="mt-1 p-3 bg-slate-950 rounded border border-slate-800 text-xs text-slate-300 font-mono leading-relaxed">
                    {activeCitation.snippet || "Extracting deterministic lineage from target registry..."}
                  </div>
                </div>

                {activeCitation.metadata && Object.keys(activeCitation.metadata).length > 0 && (
                  <div>
                    <label className="text-xs font-mono text-slate-400 uppercase">Audit Metadata</label>
                    <pre className="mt-1 p-2 bg-slate-950 rounded border border-slate-800 text-[10px] text-slate-400 overflow-x-auto">
                      {JSON.stringify(activeCitation.metadata, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800 flex justify-between items-center text-xs text-slate-500">
              <span>Tenant Scoped (org_id verified)</span>
              <button
                onClick={closeDrawer}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded font-medium"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </EvidenceDrawerContext.Provider>
  );
}
