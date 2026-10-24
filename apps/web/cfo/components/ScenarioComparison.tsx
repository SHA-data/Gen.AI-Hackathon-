import React from 'react';

export interface ComparisonCase {
  min_cash: string;
  end_cash: string;
  runway_weeks: number | null;
  reserve_breach: boolean;
  cash_floor_breach: boolean;
}

export interface ScenarioComparisonProps {
  baseline: ComparisonCase;
  expected: ComparisonCase;
  worst: ComparisonCase;
  best: ComparisonCase;
  scenarioName?: string;
  onOpenEvidence?: () => void;
}

export const ScenarioComparison: React.FC<ScenarioComparisonProps> = ({
  baseline,
  expected,
  worst,
  best,
  scenarioName = 'Hire Two Developers + Apex 30-Day Delay',
  onOpenEvidence,
}) => {
  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden font-sans">
      <div className="p-6 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
        <div>
          <span className="text-xs font-semibold uppercase px-2 py-0.5 rounded bg-purple-100 text-purple-800">
            Scenario Multi-Case Comparison
          </span>
          <h2 className="text-xl font-bold text-gray-900 mt-1">{scenarioName}</h2>
        </div>
        {onOpenEvidence && (
          <button
            onClick={onOpenEvidence}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded shadow transition"
          >
            Open Evidence Drawer
          </button>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-100 text-gray-600 uppercase text-xs font-semibold">
            <tr>
              <th className="py-3 px-4">Metric</th>
              <th className="py-3 px-4">Baseline</th>
              <th className="py-3 px-4 bg-blue-50 text-blue-900">Expected Case</th>
              <th className="py-3 px-4 bg-rose-50 text-rose-900">Worst Case (+14d Delay)</th>
              <th className="py-3 px-4 bg-emerald-50 text-emerald-900">Best Case (-7d Advance)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 font-mono">
            <tr>
              <td className="py-3 px-4 font-sans font-medium text-gray-900">Minimum Cash Balance</td>
              <td className="py-3 px-4 text-gray-700">${baseline.min_cash}</td>
              <td className="py-3 px-4 font-bold text-blue-800 bg-blue-50/50">${expected.min_cash}</td>
              <td className={`py-3 px-4 font-bold bg-rose-50/50 ${parseFloat(worst.min_cash) < 0 ? 'text-rose-600' : 'text-gray-900'}`}>
                ${worst.min_cash}
              </td>
              <td className="py-3 px-4 font-bold text-emerald-700 bg-emerald-50/50">${best.min_cash}</td>
            </tr>
            <tr>
              <td className="py-3 px-4 font-sans font-medium text-gray-900">Ending Cash Balance</td>
              <td className="py-3 px-4 text-gray-700">${baseline.end_cash}</td>
              <td className="py-3 px-4 text-gray-900 bg-blue-50/50">${expected.end_cash}</td>
              <td className="py-3 px-4 text-gray-900 bg-rose-50/50">${worst.end_cash}</td>
              <td className="py-3 px-4 text-gray-900 bg-emerald-50/50">${best.end_cash}</td>
            </tr>
            <tr>
              <td className="py-3 px-4 font-sans font-medium text-gray-900">Runway Weeks</td>
              <td className="py-3 px-4 text-gray-700">{baseline.runway_weeks ?? 'Solvent (> 26w)'}</td>
              <td className="py-3 px-4 text-gray-900 bg-blue-50/50">{expected.runway_weeks ?? 'Solvent (> 26w)'}</td>
              <td className="py-3 px-4 font-bold text-rose-600 bg-rose-50/50">
                {worst.runway_weeks ? `${worst.runway_weeks} weeks` : 'Solvent (> 26w)'}
              </td>
              <td className="py-3 px-4 text-gray-900 bg-emerald-50/50">{best.runway_weeks ?? 'Solvent (> 26w)'}</td>
            </tr>
            <tr>
              <td className="py-3 px-4 font-sans font-medium text-gray-900">Reserve Breach ($50k)</td>
              <td className="py-3 px-4">
                <span className={`px-2 py-0.5 rounded text-xs font-sans font-semibold ${baseline.reserve_breach ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                  {baseline.reserve_breach ? 'BREACH' : 'SAFE'}
                </span>
              </td>
              <td className="py-3 px-4 bg-blue-50/50">
                <span className={`px-2 py-0.5 rounded text-xs font-sans font-semibold ${expected.reserve_breach ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                  {expected.reserve_breach ? 'BREACH' : 'SAFE'}
                </span>
              </td>
              <td className="py-3 px-4 bg-rose-50/50">
                <span className={`px-2 py-0.5 rounded text-xs font-sans font-semibold ${worst.reserve_breach ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                  {worst.reserve_breach ? 'BREACH' : 'SAFE'}
                </span>
              </td>
              <td className="py-3 px-4 bg-emerald-50/50">
                <span className={`px-2 py-0.5 rounded text-xs font-sans font-semibold ${best.reserve_breach ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                  {best.reserve_breach ? 'BREACH' : 'SAFE'}
                </span>
              </td>
            </tr>
            <tr>
              <td className="py-3 px-4 font-sans font-medium text-gray-900">12-Week Cash Floor Breach</td>
              <td className="py-3 px-4">
                <span className={`px-2 py-0.5 rounded text-xs font-sans font-semibold ${baseline.cash_floor_breach ? 'bg-amber-100 text-amber-800' : 'bg-green-100 text-green-800'}`}>
                  {baseline.cash_floor_breach ? 'RISK' : 'SAFE'}
                </span>
              </td>
              <td className="py-3 px-4 bg-blue-50/50">
                <span className={`px-2 py-0.5 rounded text-xs font-sans font-semibold ${expected.cash_floor_breach ? 'bg-amber-100 text-amber-800' : 'bg-green-100 text-green-800'}`}>
                  {expected.cash_floor_breach ? 'RISK' : 'SAFE'}
                </span>
              </td>
              <td className="py-3 px-4 bg-rose-50/50">
                <span className={`px-2 py-0.5 rounded text-xs font-sans font-semibold ${worst.cash_floor_breach ? 'bg-amber-100 text-amber-800' : 'bg-green-100 text-green-800'}`}>
                  {worst.cash_floor_breach ? 'RISK' : 'SAFE'}
                </span>
              </td>
              <td className="py-3 px-4 bg-emerald-50/50">
                <span className={`px-2 py-0.5 rounded text-xs font-sans font-semibold ${best.cash_floor_breach ? 'bg-amber-100 text-amber-800' : 'bg-green-100 text-green-800'}`}>
                  {best.cash_floor_breach ? 'RISK' : 'SAFE'}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ScenarioComparison;
