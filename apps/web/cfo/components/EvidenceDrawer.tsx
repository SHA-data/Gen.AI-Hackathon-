import React, { useEffect, useState, useRef } from 'react';

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
  const drawerRef = useRef<HTMLDivElement>(null);

  // Close on Escape key press and focus management
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    if (pointId) {
      window.addEventListener('keydown', handleKeyDown);
      drawerRef.current?.focus();
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [pointId, onClose]);

  useEffect(() => {
    if (!pointId) {
      setData(null);
      return;
    }

    setLoading(true);
    setError(null);

    fetch(`${apiBaseUrl}/v1/finance/forecast-points/${pointId}/lineage`, {
      headers: {
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      },
    })
      .then(async (res) => {
        if (!res.ok) {
          throw new Error(`Failed to load evidence lineage (HTTP ${res.status})`);
        }
        return res.json();
      })
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Error loading lineage');
        setLoading(false);
      });
  }, [pointId, apiBaseUrl, authToken]);

  if (!pointId) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 flex justify-end transition-opacity">
      <div
        ref={drawerRef}
        tabIndex={-1}
        role="dialog"
        aria-label="Evidence & Mathematical Lineage Inspector"
        className="w-full max-w-xl h-full shadow-2xl flex flex-col font-[var(--font-ui)] overflow-y-auto outline-none transition-colors"
        style={{
          backgroundColor: 'var(--surface)',
          borderLeft: '1px solid var(--ui-border)',
          color: 'var(--text)',
        }}
      >
        {/* Header */}
        <div
          className="p-6 border-b flex justify-between items-start"
          style={{
            borderColor: 'var(--divider)',
            backgroundColor: 'var(--bg)',
          }}
        >
          <div>
            <div className="flex items-center space-x-2">
              <span
                className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-[var(--radius-chip)] text-xs font-semibold"
                style={{
                  backgroundColor: 'var(--tag-computed-bg)',
                  color: 'var(--tag-computed)',
                }}
              >
                <span>🧮</span>
                <span>Computed Evidence</span>
              </span>
              <span
                className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-[var(--radius-chip)] text-xs font-semibold"
                style={{
                  backgroundColor: 'var(--status-verified-bg)',
                  color: 'var(--status-verified)',
                }}
              >
                <span>✓</span>
                <span>Cryptographic Lineage</span>
              </span>
            </div>
            <h2 className="text-xl font-bold mt-2" style={{ color: 'var(--text)' }}>
              Forecast Point Lineage
            </h2>
            <p className="text-xs font-[var(--font-mono)] mt-1" style={{ color: 'var(--muted)' }}>
              Point ID: {pointId}
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close evidence drawer"
            className="p-2 rounded-[var(--radius-control)] hover:opacity-80 transition"
            style={{ color: 'var(--muted)' }}
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 flex-1">
          {loading && (
            <div className="flex justify-center items-center py-12">
              <span className="text-sm font-medium" style={{ color: 'var(--muted)' }}>
                Verifying mathematical lineage...
              </span>
            </div>
          )}

          {error && (
            <div
              className="p-4 rounded-[var(--radius-control)] text-sm border flex items-center space-x-2"
              style={{
                backgroundColor: 'var(--status-failed-bg)',
                borderColor: 'var(--status-failed)',
                color: 'var(--status-failed)',
              }}
            >
              <span>✕</span>
              <span>{error}</span>
            </div>
          )}

          {data && (
            <>
              {/* Formula & Deterministic Math */}
              <div
                className="p-4 rounded-[var(--radius-control)] border"
                style={{
                  backgroundColor: 'var(--bg)',
                  borderColor: 'var(--divider)',
                }}
              >
                <div className="text-xs font-bold uppercase mb-2" style={{ color: 'var(--muted)' }}>
                  Deterministic Recurrence Formula
                </div>
                <div
                  className="font-[var(--font-mono)] text-sm p-3 rounded-[var(--radius-control)] border font-semibold"
                  style={{
                    backgroundColor: 'var(--surface)',
                    borderColor: 'var(--divider)',
                    color: 'var(--text)',
                  }}
                >
                  {data.formula}
                </div>
                <div className="grid grid-cols-2 gap-3 mt-3 text-xs font-[var(--font-mono)] tabular-nums">
                  <div>
                    <span style={{ color: 'var(--muted)' }}>Opening Cash:</span>{' '}
                    <span className="font-semibold" style={{ color: 'var(--text)' }}>
                      ${data.calculation.opening_cash}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--muted)' }}>Inflows:</span>{' '}
                    <span className="font-semibold" style={{ color: 'var(--status-verified)' }}>
                      +${data.calculation.projected_inflows}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--muted)' }}>Outflows:</span>{' '}
                    <span className="font-semibold" style={{ color: 'var(--status-failed)' }}>
                      -${data.calculation.projected_outflows}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--muted)' }}>Closing Cash:</span>{' '}
                    <span className="font-semibold" style={{ color: 'var(--highlight-text)' }}>
                      ${data.calculation.closing_cash}
                    </span>
                  </div>
                </div>
              </div>

              {/* Invoices Contributing */}
              <div>
                <h3 className="text-sm font-bold uppercase mb-2" style={{ color: 'var(--text)' }}>
                  Contributing Invoices ({data.contributing_events.invoices.length})
                </h3>
                {data.contributing_events.invoices.length === 0 ? (
                  <p className="text-xs" style={{ color: 'var(--muted)' }}>
                    No receivable receipts expected in this weekly window.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {data.contributing_events.invoices.map((inv, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-[var(--radius-control)] border flex justify-between items-center text-xs"
                        style={{
                          backgroundColor: 'var(--surface)',
                          borderColor: 'var(--divider)',
                        }}
                      >
                        <div>
                          <div className="font-bold" style={{ color: 'var(--text)' }}>
                            {inv.invoice_number} · {inv.client}
                          </div>
                          <div style={{ color: 'var(--muted)' }}>
                            Expected: {inv.expected_payment_date}
                          </div>
                        </div>
                        <div className="font-[var(--font-mono)] font-bold text-sm" style={{ color: 'var(--status-verified)' }}>
                          +${inv.amount}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Source Rows */}
              <div>
                <h3 className="text-sm font-bold uppercase mb-2" style={{ color: 'var(--text)' }}>
                  Underlying Raw Source Rows ({data.source_rows.length})
                </h3>
                {data.source_rows.length === 0 ? (
                  <p className="text-xs" style={{ color: 'var(--muted)' }}>
                    No direct CSV source rows mapped to this specific window.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {data.source_rows.map((row) => (
                      <div
                        key={row.id}
                        className="p-3 rounded-[var(--radius-control)] border text-xs font-[var(--font-mono)]"
                        style={{
                          backgroundColor: 'var(--bg)',
                          borderColor: 'var(--divider)',
                        }}
                      >
                        <div className="flex justify-between font-semibold pb-1 border-b" style={{ borderColor: 'var(--divider)', color: 'var(--text)' }}>
                          <span>Source Row #{row.row_number}</span>
                          <span className="text-[11px]" style={{ color: 'var(--muted)' }}>
                            ID: {row.id.slice(0, 8)}...
                          </span>
                        </div>
                        <pre className="mt-2 text-[11px] overflow-x-auto" style={{ color: 'var(--muted)' }}>
                          {JSON.stringify(row.payload, null, 2)}
                        </pre>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Assumptions */}
              {data.active_assumptions && data.active_assumptions.length > 0 && (
                <div>
                  <h3 className="text-sm font-bold uppercase mb-2" style={{ color: 'var(--text)' }}>
                    Active Assumptions
                  </h3>
                  <div className="space-y-2">
                    {data.active_assumptions.map((assump) => (
                      <div
                        key={assump.id}
                        className="p-3 rounded-[var(--radius-control)] border text-xs"
                        style={{
                          backgroundColor: 'var(--surface)',
                          borderColor: 'var(--divider)',
                        }}
                      >
                        <div className="flex justify-between items-center">
                          <span
                            className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-[var(--radius-chip)] text-[11px] font-semibold"
                            style={{
                              backgroundColor: 'var(--tag-inferred-bg)',
                              color: 'var(--tag-inferred)',
                            }}
                          >
                            <span>✨</span>
                            <span>Assumption</span>
                          </span>
                          <span className="font-[var(--font-mono)] font-bold" style={{ color: 'var(--text)' }}>
                            {assump.key}
                          </span>
                        </div>
                        <pre className="mt-1 text-[11px] font-[var(--font-mono)]" style={{ color: 'var(--muted)' }}>
                          {JSON.stringify(assump.value)}
                        </pre>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div
          className="p-4 border-t flex justify-end"
          style={{
            borderColor: 'var(--divider)',
            backgroundColor: 'var(--bg)',
          }}
        >
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-[var(--radius-control)] border transition"
            style={{
              backgroundColor: 'var(--surface)',
              borderColor: 'var(--ui-border)',
              color: 'var(--text)',
            }}
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};

export default EvidenceDrawer;
