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
    <div className="min-h-screen bg-gray-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        <header className="flex justify-between items-center bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div>
            <h1 className="text-2xl font-black text-gray-900 tracking-tight">NeuralCFO Mode</h1>
            <p className="text-sm text-gray-500">
              Deterministic Decision Support · Acme Digital Agency
            </p>
          </div>
          <button
            onClick={() => setIsUploadOpen(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm rounded-lg shadow transition"
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
            cash_floor_breach: true,
          }}
          onOpenEvidence={() => setSelectedPointId('demo-point-uuid')}
        />

        {/* Modals & Drawers */}
        <UploadModal isOpen={isUploadOpen} onClose={() => setIsUploadOpen(false)} />
        <EvidenceDrawer pointId={selectedPointId} onClose={() => setSelectedPointId(null)} />
      </div>
    </div>
  );
};

export default CfoDashboard;
