import React, { useState } from 'react';

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
  authToken,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [sourceType, setSourceType] = useState<string>('invoices');
  const [uploading, setUploading] = useState<boolean>(false);
  const [report, setReport] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    setReport(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_type', sourceType);

    try {
      const res = await fetch(`${apiBaseUrl}/v1/finance/imports`, {
        method: 'POST',
        headers: {
          ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        },
        body: formData,
      });

      const json = await res.json();
      if (!res.ok) {
        throw new Error(json.error?.message || `Upload failed (HTTP ${res.status})`);
      }

      setReport(json.data);
      onSuccess(json.data);
    } catch (err: any) {
      setError(err.message || 'Error uploading file');
    } finally {
      setUploading(false);
    }
  };

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
            <h3 className="text-base font-bold" style={{ color: 'var(--text)' }}>
              Ingest Financial CSV
            </h3>
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
              className="p-4 rounded-[var(--radius-control)] border text-xs space-y-2"
              style={{
                backgroundColor: 'var(--bg)',
                borderColor: 'var(--divider)',
              }}
            >
              <div className="flex justify-between items-center">
                <span className="font-bold uppercase" style={{ color: 'var(--muted)' }}>
                  Ingestion Quality Report
                </span>
                <span
                  className="px-2 py-0.5 rounded-[var(--radius-chip)] text-[11px] font-semibold"
                  style={{
                    backgroundColor: report.anomalies_flagged > 0 ? 'var(--status-warning-bg)' : 'var(--status-verified-bg)',
                    color: report.anomalies_flagged > 0 ? 'var(--status-warning)' : 'var(--status-verified)',
                  }}
                >
                  {report.anomalies_flagged > 0 ? '⚠ Anomalies Detected' : '✓ Clean Ingestion'}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 font-[var(--font-mono)] tabular-nums">
                <div>Total Rows: <span className="font-bold">{report.total_rows}</span></div>
                <div>Imported: <span className="font-bold">{report.valid_rows}</span></div>
                <div>Anomalies: <span className="font-bold">{report.anomalies_flagged}</span></div>
                <div>Hash: <span className="font-bold">{report.content_hash?.slice(0, 8)}...</span></div>
              </div>
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
