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
    <div
      className="rounded-[var(--radius-card)] border shadow-sm overflow-hidden font-[var(--font-ui)] transition-colors"
      style={{
        backgroundColor: 'var(--surface)',
        borderColor: 'var(--divider)',
      }}
    >
      <div
        className="p-6 border-b flex justify-between items-center"
        style={{
          borderColor: 'var(--divider)',
          backgroundColor: 'var(--bg)',
        }}
      >
        <div>
          <span
            className="text-xs font-semibold uppercase px-2.5 py-1 rounded-[var(--radius-chip)] inline-flex items-center space-x-1"
            style={{
              backgroundColor: 'var(--tag-computed-bg)',
              color: 'var(--tag-computed)',
            }}
          >
            <span>⚡</span>
            <span>Scenario Multi-Case Comparison</span>
          </span>
          <h2 className="text-xl font-bold mt-2" style={{ color: 'var(--text)' }}>
            {scenarioName}
          </h2>
        </div>
        {onOpenEvidence && (
          <button
            onClick={onOpenEvidence}
            className="px-3.5 py-2 text-xs font-semibold rounded-[var(--radius-control)] shadow-sm transition hover:opacity-95"
            style={{
              backgroundColor: 'var(--primary)',
              color: 'var(--on-primary)',
            }}
          >
            Open Evidence Drawer
          </button>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead
            className="uppercase text-xs font-semibold"
            style={{
              backgroundColor: 'var(--bg)',
              color: 'var(--muted)',
            }}
          >
            <tr>
              <th className="py-3 px-4">Metric</th>
              <th className="py-3 px-4">Baseline</th>
              <th className="py-3 px-4">Expected Case</th>
              <th className="py-3 px-4">Worst Case (+14d Delay)</th>
              <th className="py-3 px-4">Best Case (-7d Advance)</th>
            </tr>
          </thead>
          <tbody
            className="divide-y font-[var(--font-mono)] tabular-nums"
            style={{ borderColor: 'var(--divider)' }}
          >
            <tr style={{ borderTopColor: 'var(--divider)' }}>
              <td className="py-3 px-4 font-[var(--font-ui)] font-medium" style={{ color: 'var(--text)' }}>
                Minimum Cash Balance
              </td>
              <td className="py-3 px-4" style={{ color: 'var(--text)' }}>
                ${parseFloat(baseline.min_cash).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </td>
              <td className="py-3 px-4 font-semibold" style={{ color: 'var(--highlight-text)' }}>
                ${parseFloat(expected.min_cash).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </td>
              <td className="py-3 px-4 font-semibold" style={{ color: 'var(--status-failed)' }}>
                ${parseFloat(worst.min_cash).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </td>
              <td className="py-3 px-4 font-semibold" style={{ color: 'var(--status-verified)' }}>
                ${parseFloat(best.min_cash).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </td>
            </tr>

            <tr>
              <td className="py-3 px-4 font-[var(--font-ui)] font-medium" style={{ color: 'var(--text)' }}>
                Ending Cash (Week 26)
              </td>
              <td className="py-3 px-4" style={{ color: 'var(--text)' }}>
                ${parseFloat(baseline.end_cash).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </td>
              <td className="py-3 px-4" style={{ color: 'var(--text)' }}>
                ${parseFloat(expected.end_cash).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </td>
              <td className="py-3 px-4" style={{ color: 'var(--text)' }}>
                ${parseFloat(worst.end_cash).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </td>
              <td className="py-3 px-4" style={{ color: 'var(--text)' }}>
                ${parseFloat(best.end_cash).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </td>
            </tr>

            <tr>
              <td className="py-3 px-4 font-[var(--font-ui)] font-medium" style={{ color: 'var(--text)' }}>
                Projected Runway
              </td>
              <td className="py-3 px-4 font-[var(--font-ui)]" style={{ color: 'var(--text)' }}>
                {baseline.runway_weeks ? `${baseline.runway_weeks} weeks` : '26+ weeks (Solvent)'}
              </td>
              <td className="py-3 px-4 font-[var(--font-ui)]" style={{ color: 'var(--text)' }}>
                {expected.runway_weeks ? `${expected.runway_weeks} weeks` : '26+ weeks (Solvent)'}
              </td>
              <td className="py-3 px-4 font-[var(--font-ui)]" style={{ color: 'var(--text)' }}>
                {worst.runway_weeks ? `${worst.runway_weeks} weeks` : '26+ weeks (Solvent)'}
              </td>
              <td className="py-3 px-4 font-[var(--font-ui)]" style={{ color: 'var(--text)' }}>
                {best.runway_weeks ? `${best.runway_weeks} weeks` : '26+ weeks (Solvent)'}
              </td>
            </tr>

            <tr>
              <td className="py-3 px-4 font-[var(--font-ui)] font-medium" style={{ color: 'var(--text)' }}>
                Risk & Breach Status
              </td>
              <td className="py-3 px-4 font-[var(--font-ui)]">
                {baseline.cash_floor_breach ? (
                  <span
                    className="inline-flex items-center px-2 py-0.5 rounded-[var(--radius-chip)] text-xs font-semibold"
                    style={{
                      backgroundColor: 'var(--status-warning-bg)',
                      color: 'var(--status-warning)',
                    }}
                  >
                    ⚠ Warning: Floor Breach
                  </span>
                ) : (
                  <span
                    className="inline-flex items-center px-2 py-0.5 rounded-[var(--radius-chip)] text-xs font-semibold"
                    style={{
                      backgroundColor: 'var(--status-verified-bg)',
                      color: 'var(--status-verified)',
                    }}
                  >
                    ✓ Verified Healthy
                  </span>
                )}
              </td>
              <td className="py-3 px-4 font-[var(--font-ui)]">
                {expected.cash_floor_breach ? (
                  <span
                    className="inline-flex items-center px-2 py-0.5 rounded-[var(--radius-chip)] text-xs font-semibold"
                    style={{
                      backgroundColor: 'var(--status-warning-bg)',
                      color: 'var(--status-warning)',
                    }}
                  >
                    ⚠ Warning: Low Buffer
                  </span>
                ) : (
                  <span
                    className="inline-flex items-center px-2 py-0.5 rounded-[var(--radius-chip)] text-xs font-semibold"
                    style={{
                      backgroundColor: 'var(--status-verified-bg)',
                      color: 'var(--status-verified)',
                    }}
                  >
                    ✓ Healthy
                  </span>
                )}
              </td>
              <td className="py-3 px-4 font-[var(--font-ui)]">
                {worst.reserve_breach ? (
                  <span
                    className="inline-flex items-center px-2 py-0.5 rounded-[var(--radius-chip)] text-xs font-semibold"
                    style={{
                      backgroundColor: 'var(--status-failed-bg)',
                      color: 'var(--status-failed)',
                    }}
                  >
                    ✕ Failed: Breaches $50k
                  </span>
                ) : (
                  <span
                    className="inline-flex items-center px-2 py-0.5 rounded-[var(--radius-chip)] text-xs font-semibold"
                    style={{
                      backgroundColor: 'var(--status-warning-bg)',
                      color: 'var(--status-warning)',
                    }}
                  >
                    ⚠ Reserve Intact
                  </span>
                )}
              </td>
              <td className="py-3 px-4 font-[var(--font-ui)]">
                <span
                  className="inline-flex items-center px-2 py-0.5 rounded-[var(--radius-chip)] text-xs font-semibold"
                  style={{
                    backgroundColor: 'var(--status-verified-bg)',
                    color: 'var(--status-verified)',
                  }}
                >
                  ✓ Verified Solvent
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
