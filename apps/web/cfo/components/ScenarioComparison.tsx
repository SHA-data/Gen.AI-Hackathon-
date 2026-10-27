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
    <div className="glass-panel overflow-hidden font-[var(--font-ui)] transition-all">
      {/* Frosted Header */}
      <div
        className="p-6 border-b flex flex-wrap justify-between items-center gap-4 bg-white/40 dark:bg-black/15 backdrop-blur-md"
        style={{ borderColor: 'var(--divider)' }}
      >
        <div>
          <div className="flex items-center space-x-2">
            <span
              className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-[var(--radius-chip)] inline-flex items-center space-x-1.5 glass-pill shadow-xs"
              style={{
                backgroundColor: 'var(--tag-computed-bg)',
                color: 'var(--tag-computed)',
              }}
            >
              <span>⚡</span>
              <span>Scenario Multi-Case Comparison</span>
            </span>
            <span
              className="text-xs font-semibold px-2 py-0.5 rounded-[var(--radius-chip)] glass-pill"
              style={{
                backgroundColor: 'var(--status-verified-bg)',
                color: 'var(--status-verified)',
              }}
            >
              ✓ Deterministic Math
            </span>
          </div>
          <h2 className="text-xl font-bold mt-2 text-gradient-hero tracking-tight">
            {scenarioName}
          </h2>
          <p className="text-xs mt-0.5" style={{ color: 'var(--muted)' }}>
            Comparing immutable baseline against 3 discrete scenario simulation cases
          </p>
        </div>

        {onOpenEvidence && (
          <button
            onClick={onOpenEvidence}
            className="px-4 py-2 text-xs font-bold rounded-[var(--radius-control)] shadow-md transition-all duration-200 hover:scale-102 active:scale-98 inline-flex items-center space-x-1.5"
            style={{
              background: 'var(--primary-gradient)',
              color: 'var(--on-primary)',
            }}
          >
            <span>🧮</span>
            <span>Open Evidence Drawer</span>
          </button>
        )}
      </div>

      {/* Table with Frosted Sheen */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead
            className="uppercase text-xs font-bold tracking-wider"
            style={{
              backgroundColor: 'rgba(244, 247, 250, 0.7)',
              color: 'var(--muted)',
            }}
          >
            <tr className="border-b" style={{ borderColor: 'var(--divider)' }}>
              <th className="py-3.5 px-5">Financial Metric</th>
              <th className="py-3.5 px-5">Immutable Baseline</th>
              <th className="py-3.5 px-5">Expected Case</th>
              <th className="py-3.5 px-5">Worst Case (+14d Delay)</th>
              <th className="py-3.5 px-5">Best Case (-7d Advance)</th>
            </tr>
          </thead>
          <tbody
            className="divide-y font-[var(--font-mono)] tabular-nums"
            style={{ borderColor: 'var(--divider)' }}
          >
            {/* Minimum Cash Balance Row */}
            <tr
              className="hover:bg-teal-500/[0.04] dark:hover:bg-teal-400/[0.06] transition-colors duration-150"
              style={{ borderTopColor: 'var(--divider)' }}
            >
              <td className="py-3.5 px-5 font-[var(--font-ui)] font-semibold" style={{ color: 'var(--text)' }}>
                Minimum Projected Cash
              </td>
              <td className="py-3.5 px-5" style={{ color: 'var(--text)' }}>
                ${parseFloat(baseline.min_cash).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </td>
              <td className="py-3.5 px-5 font-bold text-gradient-amber">
                ${parseFloat(expected.min_cash).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </td>
              <td className="py-3.5 px-5 font-bold" style={{ color: 'var(--status-failed)' }}>
                ${parseFloat(worst.min_cash).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </td>
              <td className="py-3.5 px-5 font-bold" style={{ color: 'var(--status-verified)' }}>
                ${parseFloat(best.min_cash).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </td>
            </tr>

            {/* Ending Cash Balance Row */}
            <tr className="hover:bg-teal-500/[0.04] dark:hover:bg-teal-400/[0.06] transition-colors duration-150">
              <td className="py-3.5 px-5 font-[var(--font-ui)] font-semibold" style={{ color: 'var(--text)' }}>
                Ending Cash (Week 26)
              </td>
              <td className="py-3.5 px-5" style={{ color: 'var(--text)' }}>
                ${parseFloat(baseline.end_cash).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </td>
              <td className="py-3.5 px-5 font-semibold" style={{ color: 'var(--text)' }}>
                ${parseFloat(expected.end_cash).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </td>
              <td className="py-3.5 px-5" style={{ color: 'var(--status-failed)' }}>
                ${parseFloat(worst.end_cash).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </td>
              <td className="py-3.5 px-5" style={{ color: 'var(--status-verified)' }}>
                ${parseFloat(best.end_cash).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </td>
            </tr>

            {/* Runway Weeks Row */}
            <tr className="hover:bg-teal-500/[0.04] dark:hover:bg-teal-400/[0.06] transition-colors duration-150">
              <td className="py-3.5 px-5 font-[var(--font-ui)] font-semibold" style={{ color: 'var(--text)' }}>
                Projected Runway (Weeks)
              </td>
              <td className="py-3.5 px-5" style={{ color: 'var(--muted)' }}>
                {baseline.runway_weeks !== null ? `${baseline.runway_weeks} wks` : '> 26 wks (Unbounded)'}
              </td>
              <td className="py-3.5 px-5 font-semibold" style={{ color: 'var(--text)' }}>
                {expected.runway_weeks !== null ? (
                  <span className="px-2 py-0.5 rounded text-xs font-bold glass-pill bg-amber-500/15 text-amber-800 dark:text-amber-300">
                    {expected.runway_weeks} wks
                  </span>
                ) : (
                  '> 26 wks'
                )}
              </td>
              <td className="py-3.5 px-5" style={{ color: 'var(--status-failed)' }}>
                {worst.runway_weeks !== null ? (
                  <span className="px-2 py-0.5 rounded text-xs font-bold glass-pill" style={{ backgroundColor: 'var(--status-failed-bg)', color: 'var(--status-failed)' }}>
                    {worst.runway_weeks} wks
                  </span>
                ) : (
                  '> 26 wks'
                )}
              </td>
              <td className="py-3.5 px-5 font-semibold" style={{ color: 'var(--status-verified)' }}>
                {best.runway_weeks !== null ? `${best.runway_weeks} wks` : '> 26 wks'}
              </td>
            </tr>

            {/* 12-Week Cash Floor Policy Breach */}
            <tr className="hover:bg-teal-500/[0.04] dark:hover:bg-teal-400/[0.06] transition-colors duration-150">
              <td className="py-3.5 px-5 font-[var(--font-ui)] font-semibold" style={{ color: 'var(--text)' }}>
                12-Week Floor Breached?
              </td>
              <td className="py-3.5 px-5">
                <span
                  className="px-2.5 py-0.5 rounded-[var(--radius-chip)] text-xs font-bold glass-pill inline-flex items-center space-x-1"
                  style={{
                    backgroundColor: baseline.cash_floor_breach ? 'var(--status-warning-bg)' : 'var(--status-verified-bg)',
                    color: baseline.cash_floor_breach ? 'var(--status-warning)' : 'var(--status-verified)',
                  }}
                >
                  <span>{baseline.cash_floor_breach ? '⚠' : '✓'}</span>
                  <span>{baseline.cash_floor_breach ? 'Breached' : 'Maintained'}</span>
                </span>
              </td>
              <td className="py-3.5 px-5">
                <span
                  className="px-2.5 py-0.5 rounded-[var(--radius-chip)] text-xs font-bold glass-pill inline-flex items-center space-x-1"
                  style={{
                    backgroundColor: expected.cash_floor_breach ? 'var(--status-warning-bg)' : 'var(--status-verified-bg)',
                    color: expected.cash_floor_breach ? 'var(--status-warning)' : 'var(--status-verified)',
                  }}
                >
                  <span>{expected.cash_floor_breach ? '⚠' : '✓'}</span>
                  <span>{expected.cash_floor_breach ? 'Breached' : 'Maintained'}</span>
                </span>
              </td>
              <td className="py-3.5 px-5">
                <span
                  className="px-2.5 py-0.5 rounded-[var(--radius-chip)] text-xs font-bold glass-pill inline-flex items-center space-x-1"
                  style={{
                    backgroundColor: worst.cash_floor_breach ? 'var(--status-warning-bg)' : 'var(--status-verified-bg)',
                    color: worst.cash_floor_breach ? 'var(--status-warning)' : 'var(--status-verified)',
                  }}
                >
                  <span>{worst.cash_floor_breach ? '⚠' : '✓'}</span>
                  <span>{worst.cash_floor_breach ? 'Breached' : 'Maintained'}</span>
                </span>
              </td>
              <td className="py-3.5 px-5">
                <span
                  className="px-2.5 py-0.5 rounded-[var(--radius-chip)] text-xs font-bold glass-pill inline-flex items-center space-x-1"
                  style={{
                    backgroundColor: best.cash_floor_breach ? 'var(--status-warning-bg)' : 'var(--status-verified-bg)',
                    color: best.cash_floor_breach ? 'var(--status-warning)' : 'var(--status-verified)',
                  }}
                >
                  <span>{best.cash_floor_breach ? '⚠' : '✓'}</span>
                  <span>{best.cash_floor_breach ? 'Breached' : 'Maintained'}</span>
                </span>
              </td>
            </tr>

            {/* Hard Reserve ($50k) Breach */}
            <tr className="hover:bg-teal-500/[0.04] dark:hover:bg-teal-400/[0.06] transition-colors duration-150">
              <td className="py-3.5 px-5 font-[var(--font-ui)] font-semibold" style={{ color: 'var(--text)' }}>
                Hard Reserve ($50k) Breached?
              </td>
              <td className="py-3.5 px-5">
                <span
                  className="px-2.5 py-0.5 rounded-[var(--radius-chip)] text-xs font-bold glass-pill inline-flex items-center space-x-1"
                  style={{
                    backgroundColor: baseline.reserve_breach ? 'var(--status-failed-bg)' : 'var(--status-verified-bg)',
                    color: baseline.reserve_breach ? 'var(--status-failed)' : 'var(--status-verified)',
                  }}
                >
                  <span>{baseline.reserve_breach ? '✕' : '✓'}</span>
                  <span>{baseline.reserve_breach ? 'Breached' : 'Protected'}</span>
                </span>
              </td>
              <td className="py-3.5 px-5">
                <span
                  className="px-2.5 py-0.5 rounded-[var(--radius-chip)] text-xs font-bold glass-pill inline-flex items-center space-x-1"
                  style={{
                    backgroundColor: expected.reserve_breach ? 'var(--status-failed-bg)' : 'var(--status-verified-bg)',
                    color: expected.reserve_breach ? 'var(--status-failed)' : 'var(--status-verified)',
                  }}
                >
                  <span>{expected.reserve_breach ? '✕' : '✓'}</span>
                  <span>{expected.reserve_breach ? 'Breached' : 'Protected'}</span>
                </span>
              </td>
              <td className="py-3.5 px-5">
                <span
                  className="px-2.5 py-0.5 rounded-[var(--radius-chip)] text-xs font-bold glass-pill inline-flex items-center space-x-1"
                  style={{
                    backgroundColor: worst.reserve_breach ? 'var(--status-failed-bg)' : 'var(--status-verified-bg)',
                    color: worst.reserve_breach ? 'var(--status-failed)' : 'var(--status-verified)',
                  }}
                >
                  <span>{worst.reserve_breach ? '✕' : '✓'}</span>
                  <span>{worst.reserve_breach ? 'Breached' : 'Protected'}</span>
                </span>
              </td>
              <td className="py-3.5 px-5">
                <span
                  className="px-2.5 py-0.5 rounded-[var(--radius-chip)] text-xs font-bold glass-pill inline-flex items-center space-x-1"
                  style={{
                    backgroundColor: best.reserve_breach ? 'var(--status-failed-bg)' : 'var(--status-verified-bg)',
                    color: best.reserve_breach ? 'var(--status-failed)' : 'var(--status-verified)',
                  }}
                >
                  <span>{best.reserve_breach ? '✕' : '✓'}</span>
                  <span>{best.reserve_breach ? 'Breached' : 'Protected'}</span>
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
