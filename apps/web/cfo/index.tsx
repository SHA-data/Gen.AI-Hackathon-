import React, { useState } from 'react';
import EvidenceDrawer from './components/EvidenceDrawer';
import ForecastChart from './components/ForecastChart';
import ScenarioComparison from './components/ScenarioComparison';
import UploadModal from './components/UploadModal';

export { EvidenceDrawer, ForecastChart, ScenarioComparison, UploadModal };

export const CfoDashboard: React.FC = () => {
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [selectedPointId, setSelectedPointId] = useState<string | null>(null);

  return (
    <div
      className="min-h-screen p-8 font-[var(--font-ui)] transition-colors"
      style={{
        backgroundColor: 'var(--bg)',
        color: 'var(--text)',
      }}
    >
      <div className="max-w-[1200px] mx-auto space-y-6">
        {/* Header / Brand Wordmark */}
        <header
          className="flex justify-between items-center p-6 rounded-[var(--radius-card)] border shadow-sm transition-colors"
          style={{
            backgroundColor: 'var(--surface)',
            borderColor: 'var(--divider)',
          }}
        >
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-2xl font-bold tracking-tight" style={{ color: 'var(--text)' }}>
                Neural<span style={{ color: 'var(--primary)' }}>CFO</span>
              </span>
              <span
                className="px-2.5 py-0.5 rounded-[var(--radius-chip)] text-xs font-semibold"
                style={{
                  backgroundColor: 'var(--status-verified-bg)',
                  color: 'var(--status-verified)',
                }}
              >
                ✓ CFO Mode Active
              </span>
            </div>
            <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
              Bold ideas with the numbers to check them. · Acme Digital Agency
            </p>
          </div>
          <button
            onClick={() => setIsUploadOpen(true)}
            className="px-4 py-2 font-semibold text-xs rounded-[var(--radius-control)] shadow-sm transition hover:opacity-95"
            style={{
              backgroundColor: 'var(--primary)',
              color: 'var(--on-primary)',
            }}
          >
            Upload Financial CSV
          </button>
        </header>

        {/* Forecast Chart */}
        <ForecastChart
          points={[
            { week_number: 1, week_start: '2026-10-19', closing_cash: '185000.00' },
            { week_number: 2, week_start: '2026-10-26', closing_cash: '110769.23' },
            { week_number: 3, week_start: '2026-11-02', closing_cash: '117538.46' },
            { week_number: 4, week_start: '2026-11-09', closing_cash: '127307.69' },
            { week_number: 5, week_start: '2026-11-16', closing_cash: '151076.92' },
          ]}
          minCashDate="1 Feb 2027"
          onSelectPoint={() => setSelectedPointId('demo-point-uuid')}
        />

        {/* Scenario Comparison */}
        <ScenarioComparison
          baseline={{
            min_cash: '147000.00',
            end_cash: '182000.00',
            runway_weeks: null,
            reserve_breach: false,
            cash_floor_breach: true,
          }}
          expected={{
            min_cash: '67461.54',
            end_cash: '99230.77',
            runway_weeks: null,
            reserve_breach: false,
            cash_floor_breach: true,
          }}
          worst={{
            min_cash: '33923.08',
            end_cash: '54230.77',
            runway_weeks: null,
            reserve_breach: true,
            cash_floor_breach: true,
          }}
          best={{
            min_cash: '70692.31',
            end_cash: '99230.77',
            runway_weeks: null,
            reserve_breach: false,
            cash_floor_breach: false,
          }}
          onOpenEvidence={() => setSelectedPointId('demo-point-uuid')}
        />

        {/* Mandatory Legal & Analytical Disclaimer */}
        <footer
          className="pt-4 pb-8 text-center text-[13px] leading-relaxed border-t"
          style={{
            borderColor: 'var(--divider)',
            color: 'var(--muted)',
          }}
        >
          Decision support, not financial advice. Forecasts depend on the assumptions shown and are not guaranteed predictions.
        </footer>

        {/* Upload Modal */}
        <UploadModal
          isOpen={isUploadOpen}
          onClose={() => setIsUploadOpen(false)}
          onSuccess={(rep) => console.log('Import finished:', rep)}
        />

        {/* Evidence Drawer */}
        <EvidenceDrawer
          pointId={selectedPointId}
          onClose={() => setSelectedPointId(null)}
        />
      </div>
    </div>
  );
};

export default CfoDashboard;
