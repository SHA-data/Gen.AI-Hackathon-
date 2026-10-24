import React, { useState } from 'react';

export interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess?: (batchId: string) => void;
  apiBaseUrl?: string;
  authToken?: string;
}

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  onUploadSuccess,
  apiBaseUrl = 'http://localhost:8000',
  authToken,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState<string>('invoices');
  const [uploading, setUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [qualityReport, setQualityReport] = useState<any | null>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError(null);
      setQualityReport(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a CSV file first.');
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', fileType);

    try {
      const headers: Record<string, string> = {
        'Idempotency-Key': `${file.name}-${file.size}-${file.lastModified}`,
      };
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const resp = await fetch(`${apiBaseUrl}/v1/finance/imports`, {
        method: 'POST',
        headers,
        body: formData,
      });

      const res = await resp.json();
      if (!resp.ok) {
        throw new Error(res.error?.message || 'Upload failed');
      }

      setQualityReport(res);
      if (onUploadSuccess) {
        onUploadSuccess(res.batch_id);
      }
    } catch (err: any) {
      setError(err.message || 'Error uploading file');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 font-sans">
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 w-full max-w-xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Upload Financial CSV</h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Ingest raw invoices, payroll records, or historical transactions with zero data loss.
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
        </div>

        {/* Form Body */}
        <div className="p-6 overflow-y-auto space-y-5">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
              File Category
            </label>
            <select
              value={fileType}
              onChange={(e) => setFileType(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm bg-white"
            >
              <option value="invoices">Receivable Invoices (invoices.csv)</option>
              <option value="payroll">Payroll Items (payroll.csv)</option>
              <option value="transactions">Historical Actuals (transactions.csv)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
              Select CSV Document
            </label>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="w-full border border-dashed border-gray-300 rounded-lg p-4 text-sm text-gray-600 bg-gray-50 hover:bg-gray-100 cursor-pointer"
            />
          </div>

          {/* Quality Report Output */}
          {qualityReport && (
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 text-xs space-y-3 font-mono">
              <div className="flex justify-between items-center border-b border-slate-200 pb-2">
                <span className="font-bold text-slate-800">IMPORT QUALITY REPORT</span>
                <span className={`px-2 py-0.5 rounded uppercase font-bold ${qualityReport.status === 'completed' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>
                  {qualityReport.status}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-slate-700">
                <div>Total Rows: <span className="font-bold">{qualityReport.total_rows}</span></div>
                <div>Accepted: <span className="font-bold text-emerald-600">{qualityReport.accepted_rows}</span></div>
                <div>Rejected: <span className="font-bold text-rose-600">{qualityReport.rejected_rows}</span></div>
                <div>Flagged Anomalies: <span className="font-bold text-amber-600">{qualityReport.flagged_rows}</span></div>
              </div>

              {qualityReport.quality_report?.flagged_anomalies?.length > 0 && (
                <div className="mt-2 text-amber-800 bg-amber-50 p-2 rounded border border-amber-200">
                  <span className="font-bold">Flagged Duplicates (Preserved, not deleted):</span>
                  {qualityReport.quality_report.flagged_anomalies.map((a: any, i: number) => (
                    <div key={i} className="text-[11px] mt-0.5">
                      Row #{a.row_number}: Duplicate invoice number {a.invoice_number}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-100"
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={uploading || !file}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-sm font-semibold shadow"
          >
            {uploading ? 'Validating...' : 'Upload & Validate'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default UploadModal;
