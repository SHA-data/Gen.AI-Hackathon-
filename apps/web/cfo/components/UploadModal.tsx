import React, { useState, useEffect } from 'react';

export interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (report: any) => void;
  apiBaseUrl?: string;
  authToken?: string;
}

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  apiBaseUrl = 'http://localhost:8000',
  authToken: initialAuthToken,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [sourceType, setSourceType] = useState<string>('invoices');
  const [uploading, setUploading] = useState<boolean>(false);
  const [report, setReport] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeToken, setActiveToken] = useState<string>(initialAuthToken || '');
  const [tokenStatus, setTokenStatus] = useState<string>('Obtaining token...');

  // Auto-acquire dev token if not provided
  useEffect(() => {
    if (initialAuthToken) {
      setActiveToken(initialAuthToken);
      setTokenStatus('Authenticated (Prop)');
      return;
    }

    const resolveToken = async () => {
      if (typeof window !== 'undefined') {
        const cached = localStorage.getItem('cfo_auth_token');
        if (cached) {
          setActiveToken(cached);
          setTokenStatus('Authenticated (Cached)');
          return;
        }
      }

      try {
        const tokenRes = await fetch(`${apiBaseUrl}/v1/dev/token`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: '10000000-0000-0000-0000-000000000001',
            org_id: '00000000-0000-0000-0000-000000000001',
            role: 'owner',
          }),
        });

        if (tokenRes.ok) {
          const data = await tokenRes.json();
          const jwt = data.access_token;
          setActiveToken(jwt);
          setTokenStatus('Authenticated (Acme Owner)');
          if (typeof window !== 'undefined') {
            localStorage.setItem('cfo_auth_token', jwt);
          }
        } else {
          setTokenStatus('Token endpoint unavailable');
        }
      } catch (err) {
        setTokenStatus('Offline token error');
      }
    };

    if (isOpen) {
      resolveToken();
    }
  }, [isOpen, initialAuthToken, apiBaseUrl]);

  if (!isOpen) return null;

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    setReport(null);

    let token = activeToken;
    if (!token) {
      try {
        const tokenRes = await fetch(`${apiBaseUrl}/v1/dev/token`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: '10000000-0000-0000-0000-000000000001',
            org_id: '00000000-0000-0000-0000-000000000001',
            role: 'owner',
          }),
        });
        if (tokenRes.ok) {
          const data = await tokenRes.json();
          token = data.access_token;
          setActiveToken(token);
          if (typeof window !== 'undefined') {
            localStorage.setItem('cfo_auth_token', token);
          }
        }
      } catch (e) {
        // Will be caught below if token is still missing
      }
    }

    if (!token) {
      setError('Unable to authenticate. Please ensure the backend server is running on http://localhost:8000.');
      setUploading(false);
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', sourceType);
    formData.append('source_type', sourceType);

    try {
      const res = await fetch(`${apiBaseUrl}/v1/finance/imports`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      const json = await res.json();
      if (!res.ok) {
        throw new Error(json.error?.message || `Upload failed (HTTP ${res.status})`);
      }

      const reportData = json.data || json;
      setReport(reportData);
      onSuccess(reportData);
    } catch (err: any) {
      setError(err.message || 'Error uploading file');
    } finally {
      setUploading(false);
    }
  };

  const flaggedCount = report ? (report.flagged_rows ?? report.anomalies_flagged ?? 0) : 0;
  const acceptedCount = report ? (report.accepted_rows ?? report.valid_rows ?? 0) : 0;
  const rejectedCount = report ? (report.rejected_rows ?? 0) : 0;
  const totalCount = report ? (report.total_rows ?? 0) : 0;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/40 flex items-center justify-center p-4">
      <div
        className="w-full max-w-lg rounded-[var(--radius-card)] shadow-xl border overflow-hidden font-[var(--font-ui)] transition-colors"
        style={{
          backgroundColor: 'var(--surface)',
          borderColor: 'var(--divider)',
          color: 'var(--text)',
        }}
      >
        <div
          className="p-5 border-b flex justify-between items-center"
          style={{
            borderColor: 'var(--divider)',
            backgroundColor: 'var(--bg)',
          }}
        >
          <div className="flex items-center space-x-2">
            <span
              className="w-6 h-6 rounded-full inline-flex items-center justify-center text-xs font-bold"
              style={{
                backgroundColor: 'var(--primary)',
                color: 'var(--on-primary)',
              }}
            >
              ↑
            </span>
            <div>
              <h3 className="text-base font-bold" style={{ color: 'var(--text)' }}>
                Ingest Financial CSV
              </h3>
              <p className="text-[11px]" style={{ color: 'var(--muted)' }}>
                Session: <span className="font-medium text-emerald-600 dark:text-emerald-400">● {tokenStatus}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close modal"
            className="p-1 rounded-[var(--radius-control)] hover:opacity-80 transition"
            style={{ color: 'var(--muted)' }}
          >
            ✕
          </button>
        </div>

        <div className="p-6 space-y-4">
          {error && (
            <div
              className="p-3 text-xs rounded-[var(--radius-control)] border flex items-center space-x-2"
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

          <div>
            <label className="block text-xs font-bold uppercase mb-1" style={{ color: 'var(--muted)' }}>
              Source Type
            </label>
            <select
              value={sourceType}
              onChange={(e) => setSourceType(e.target.value)}
              className="w-full text-sm rounded-[var(--radius-control)] p-2.5 border outline-none font-[var(--font-ui)]"
              style={{
                backgroundColor: 'var(--surface)',
                borderColor: 'var(--ui-border)',
                color: 'var(--text)',
              }}
            >
              <option value="invoices">Invoices / Receivables Schedule</option>
              <option value="payroll">Payroll Roster</option>
              <option value="transactions">Bank Transactions / Overhead</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase mb-1" style={{ color: 'var(--muted)' }}>
              Select CSV File
            </label>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="w-full text-xs p-2 rounded-[var(--radius-control)] border outline-none file:mr-3 file:py-1 file:px-3 file:rounded-[var(--radius-control)] file:border-0 file:text-xs file:font-semibold"
              style={{
                backgroundColor: 'var(--bg)',
                borderColor: 'var(--ui-border)',
                color: 'var(--text)',
              }}
            />
          </div>

          {report && (
            <div
              className="p-4 rounded-[var(--radius-control)] border text-xs space-y-3"
              style={{
                backgroundColor: 'var(--bg)',
                borderColor: 'var(--divider)',
              }}
            >
              <div className="flex justify-between items-center">
                <span className="font-bold uppercase tracking-wide" style={{ color: 'var(--muted)' }}>
                  Ingestion Quality Report
                </span>
                <span
                  className="px-2.5 py-1 rounded-[var(--radius-chip)] text-[11px] font-semibold"
                  style={{
                    backgroundColor: flaggedCount > 0 ? 'var(--status-warning-bg)' : 'var(--status-verified-bg)',
                    color: flaggedCount > 0 ? 'var(--status-warning)' : 'var(--status-verified)',
                  }}
                >
                  {flaggedCount > 0 ? `⚠ ${flaggedCount} Anomalies Flagged` : '✓ Clean Ingestion (100% Accepted)'}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2.5 font-[var(--font-mono)] tabular-nums text-xs">
                <div>Total Rows: <span className="font-bold">{totalCount}</span></div>
                <div>Accepted: <span className="font-bold text-emerald-600 dark:text-emerald-400">{acceptedCount}</span></div>
                <div>Flagged Anomalies: <span className="font-bold text-amber-600 dark:text-amber-400">{flaggedCount}</span></div>
                <div>Rejected: <span className="font-bold text-rose-600 dark:text-rose-400">{rejectedCount}</span></div>
              </div>
              {report.batch_id && (
                <div className="text-[11px] font-[var(--font-mono)] opacity-70 truncate">
                  Batch ID: {report.batch_id}
                </div>
              )}
            </div>
          )}
        </div>

        <div
          className="p-4 border-t flex justify-end space-x-2"
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
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="px-4 py-2 text-xs font-semibold rounded-[var(--radius-control)] transition disabled:opacity-50"
            style={{
              backgroundColor: 'var(--primary)',
              color: 'var(--on-primary)',
            }}
          >
            {uploading ? 'Validating...' : 'Upload & Verify'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default UploadModal;
