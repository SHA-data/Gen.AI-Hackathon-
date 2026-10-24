import React, { useEffect, useState } from 'react';

export interface EvidenceDrawerProps {
  pointId: string | null;
  onClose: () => void;
  apiBaseUrl?: string;
  authToken?: string;
}

export interface LineageData {
  point_id: string;
  run_id: string;
  week_number: number;
  week_start: string;
  formula: string;
  calculation: {
    opening_cash: string;
    projected_inflows: string;
    projected_outflows: string;
    net_cash_flow: string;
    closing_cash: string;
  };
  contributing_events: {
    invoices: Array<{
      invoice_number: string;
      client: string;
      amount: string;
      expected_payment_date: string;
    }>;
    payroll_count: number;
  };
  source_rows: Array<{
    id: string;
    row_number: number;
    batch_id: string;
    payload: Record<string, any>;
  }>;
  active_assumptions: Array<{
    id: string;
    category: string;
    key: string;
    value: Record<string, any>;
    valid_from: string;
  }>;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({
  pointId,
  onClose,
  apiBaseUrl = 'http://localhost:8000',
  authToken,
}) => {
  const [data, setData] = useState<LineageData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!pointId) {
      setData(null);
      return;
    }

    const fetchLineage = async () => {
      setLoading(true);
      setError(null);
      try {
        const headers: Record<string, string> = {};
        if (authToken) {
          headers['Authorization'] = `Bearer ${authToken}`;
        }
        const resp = await fetch(`${apiBaseUrl}/v1/finance/forecast-points/${pointId}/lineage`, {
          headers,
        });
        if (!resp.ok) {
          throw new Error(`Failed to load lineage: ${resp.statusText}`);
        }
        const json = await resp.json();
        setData(json);
      } catch (err: any) {
        setError(err.message || 'Error fetching lineage');
      } finally {
        setLoading(false);
      }
    };

    fetchLineage();
  }, [pointId, apiBaseUrl, authToken]);

  if (!pointId) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-lg bg-white shadow-2xl border-l border-gray-200 flex flex-col font-sans">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold uppercase px-2 py-0.5 rounded bg-blue-100 text-blue-800">
              Computed Claim
            </span>
            <span className="text-xs text-gray-500">ID: {pointId.slice(0, 8)}...</span>
          </div>
          <h2 className="text-lg font-bold text-gray-900 mt-1">
            {data ? `Week ${data.week_number} (${data.week_start})` : 'Evidence Drawer'}
          </h2>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 p-1 rounded-full hover:bg-gray-200 transition"
        >
          <span className="sr-only">Close</span>
          ✕
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {loading && (
          <div className="flex items-center justify-center py-12 text-gray-500">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
            Loading mathematical lineage...
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {data && (
          <>
            {/* Calculation Formula */}
            <div className="bg-slate-900 text-white rounded-lg p-4 font-mono text-xs shadow">
              <div className="text-gray-400 mb-1 font-bold">MATHEMATICAL ARITHMETIC:</div>
              <div className="text-green-400 font-semibold mb-3">{data.formula}</div>
              <div className="space-y-1 text-slate-300">
                <div className="flex justify-between">
                  <span>Opening Cash:</span>
                  <span className="font-bold text-white">${data.calculation.opening_cash}</span>
                </div>
                <div className="flex justify-between">
                  <span>+ Inflows:</span>
                  <span className="text-emerald-400 font-bold">+${data.calculation.projected_inflows}</span>
                </div>
                <div className="flex justify-between">
                  <span>- Outflows:</span>
                  <span className="text-rose-400 font-bold">-${data.calculation.projected_outflows}</span>
                </div>
                <div className="border-t border-slate-700 pt-1 mt-1 flex justify-between text-yellow-400 font-bold">
                  <span>Closing Balance:</span>
                  <span>${data.calculation.closing_cash}</span>
                </div>
              </div>
            </div>

            {/* Contributing Events */}
            <div>
              <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wider mb-2">
                Contributing Events
              </h3>
              {data.contributing_events.invoices.length > 0 ? (
                <div className="space-y-2">
                  {data.contributing_events.invoices.map((inv, idx) => (
                    <div key={idx} className="p-3 bg-gray-50 border border-gray-200 rounded flex justify-between items-center text-sm">
                      <div>
                        <div className="font-semibold text-gray-900">{inv.client}</div>
                        <div className="text-xs text-gray-500">{inv.invoice_number} · Due {inv.expected_payment_date}</div>
                      </div>
                      <div className="text-right font-mono font-bold text-emerald-600">+${inv.amount}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-xs text-gray-500 italic">No invoice inflows this week.</div>
              )}
            </div>

            {/* Raw Source Rows Traceability */}
            <div>
              <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wider mb-2">
                Source Row Audit Trail ({data.source_rows.length} rows)
              </h3>
              <div className="space-y-2">
                {data.source_rows.map((row, idx) => (
                  <div key={idx} className="p-3 bg-gray-50 border border-gray-200 rounded text-xs font-mono">
                    <div className="flex justify-between text-gray-500 mb-1">
                      <span>Row #{row.row_number}</span>
                      <span>Ref: {row.id.slice(0, 8)}</span>
                    </div>
                    <pre className="bg-white p-2 rounded border border-gray-200 overflow-x-auto text-gray-700">
                      {JSON.stringify(row.payload, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            </div>

            {/* Active Assumptions */}
            <div>
              <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wider mb-2">
                Active Finance Assumptions
              </h3>
              <div className="space-y-1">
                {data.active_assumptions.map((a, idx) => (
                  <div key={idx} className="text-xs text-gray-600 bg-amber-50 border border-amber-200 p-2 rounded flex justify-between">
                    <span className="font-semibold">{a.key}:</span>
                    <span>{JSON.stringify(a.value)}</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 bg-gray-50 text-right">
        <button
          onClick={onClose}
          className="px-4 py-2 bg-gray-800 hover:bg-gray-900 text-white text-sm font-medium rounded transition"
        >
          Close Drawer
        </button>
      </div>
    </div>
  );
};

export default EvidenceDrawer;
