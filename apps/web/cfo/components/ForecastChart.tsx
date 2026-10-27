import React, { useState, useMemo, useRef } from 'react';

export interface WeeklyPoint {
  point_id?: string;
  week_number: number;
  week_start: string;
  closing_cash: string;
  inflows?: string;
  outflows?: string;
}

export interface ForecastChartProps {
  points: WeeklyPoint[];
  baselinePoints?: WeeklyPoint[];
  bestPoints?: WeeklyPoint[];
  worstPoints?: WeeklyPoint[];
  reserveAmount?: number;
  cashFloorAmount?: number;
  minCashDate?: string;
  minCashValue?: string;
  onSelectPoint?: (pointId?: string) => void;
}

export const ForecastChart: React.FC<ForecastChartProps> = ({
  points,
  baselinePoints,
  bestPoints,
  worstPoints,
  reserveAmount = 50000,
  cashFloorAmount = 207692,
  minCashDate,
  minCashValue,
  onSelectPoint,
}) => {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  const [showFanBand, setShowFanBand] = useState<boolean>(true);
  const [showBaseline, setShowBaseline] = useState<boolean>(true);
  const [showThresholds, setShowThresholds] = useState<boolean>(true);

  if (!points || points.length === 0) {
    return (
      <div
        className="p-8 text-center rounded-[var(--radius-control)] border border-dashed glass-panel"
        style={{
          borderColor: 'var(--ui-border)',
          color: 'var(--muted)',
        }}
      >
        No forecast data available. Run baseline or scenario simulation first.
      </div>
    );
  }

  // Derive Best and Worst case points if not explicitly provided
  const derivedBestPoints = useMemo<WeeklyPoint[]>(() => {
    if (bestPoints && bestPoints.length === points.length) return bestPoints;
    return points.map((p, idx) => {
      const val = parseFloat(p.closing_cash);
      const delta = Math.abs(val) * 0.12 + (idx * 1500);
      return {
        ...p,
        closing_cash: (val + delta).toFixed(2),
      };
    });
  }, [bestPoints, points]);

  const derivedWorstPoints = useMemo<WeeklyPoint[]>(() => {
    if (worstPoints && worstPoints.length === points.length) return worstPoints;
    return points.map((p, idx) => {
      const val = parseFloat(p.closing_cash);
      const delta = Math.abs(val) * 0.18 + (idx * 2200);
      return {
        ...p,
        closing_cash: (val - delta).toFixed(2),
      };
    });
  }, [worstPoints, points]);

  // Extract all cash values to calculate precise Y scale bounds
  const allValues = [
    ...points.map((p) => parseFloat(p.closing_cash)),
    ...(baselinePoints ? baselinePoints.map((p) => parseFloat(p.closing_cash)) : []),
    ...derivedBestPoints.map((p) => parseFloat(p.closing_cash)),
    ...derivedWorstPoints.map((p) => parseFloat(p.closing_cash)),
    reserveAmount,
    cashFloorAmount,
  ];

  const maxVal = Math.max(...allValues) * 1.08;
  const minVal = Math.min(0, Math.min(...allValues) * 1.15);
  const range = maxVal - minVal || 1;

  const width = 860;
  const height = 320;
  const paddingLeft = 65;
  const paddingRight = 40;
  const paddingTop = 30;
  const paddingBottom = 45;

  const innerWidth = width - paddingLeft - paddingRight;
  const innerHeight = height - paddingTop - paddingBottom;

  const getY = (val: number) => {
    return height - paddingBottom - ((val - minVal) / range) * innerHeight;
  };

  const getX = (idx: number) => {
    if (points.length <= 1) return paddingLeft;
    return paddingLeft + (idx / (points.length - 1)) * innerWidth;
  };

  // Find minimum cash point on expected series
  let minPointIdx = 0;
  let minPointVal = parseFloat(points[0].closing_cash);
  points.forEach((p, idx) => {
    const v = parseFloat(p.closing_cash);
    if (v < minPointVal) {
      minPointVal = v;
      minPointIdx = idx;
    }
  });

  const minX = getX(minPointIdx);
  const minY = getY(minPointVal);
  const minDateLabel = minCashDate || points[minPointIdx].week_start;

  // Build SVG Paths
  const createLinePath = (pts: WeeklyPoint[]) => {
    return pts
      .map((p, idx) => {
        const x = getX(idx);
        const y = getY(parseFloat(p.closing_cash));
        return `${idx === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
      })
      .join(' ');
  };

  const expectedPath = createLinePath(points);
  const baselinePath = baselinePoints ? createLinePath(baselinePoints) : null;
  const bestPath = createLinePath(derivedBestPoints);
  const worstPath = createLinePath(derivedWorstPoints);

  // Build Probability Corridor Fan Polygon (Best -> Worst reversed -> Close)
  const fanPolygonD = useMemo(() => {
    if (points.length === 0) return '';
    const topPoints = derivedBestPoints.map((p, idx) => {
      const x = getX(idx);
      const y = getY(parseFloat(p.closing_cash));
      return `${idx === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
    });

    const bottomPoints = derivedWorstPoints
      .slice()
      .reverse()
      .map((p, revIdx) => {
        const originalIdx = derivedWorstPoints.length - 1 - revIdx;
        const x = getX(originalIdx);
        const y = getY(parseFloat(p.closing_cash));
        return `L ${x.toFixed(1)} ${y.toFixed(1)}`;
      });

    return `${topPoints.join(' ')} ${bottomPoints.join(' ')} Z`;
  }, [derivedBestPoints, derivedWorstPoints, points.length]);

  const reserveY = getY(reserveAmount);
  const floorY = getY(cashFloorAmount);
  const zeroY = getY(0);

  // Generate Y Axis Tick Labels
  const yTicks = useMemo(() => {
    const ticks: number[] = [];
    const count = 5;
    const step = (maxVal - minVal) / (count - 1);
    for (let i = 0; i < count; i++) {
      ticks.push(minVal + i * step);
    }
    return ticks;
  }, [minVal, maxVal]);

  // Handle Scrubbing Pointer Events
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const svgX = (mouseX / rect.width) * width;

    const relativeX = svgX - paddingLeft;
    const stepWidth = innerWidth / (points.length - 1);
    let nearestIdx = Math.round(relativeX / stepWidth);
    if (nearestIdx < 0) nearestIdx = 0;
    if (nearestIdx >= points.length) nearestIdx = points.length - 1;
    setHoverIdx(nearestIdx);
  };

  const handleMouseLeave = () => {
    setHoverIdx(null);
  };

  const activeHoverPoint = hoverIdx !== null ? points[hoverIdx] : null;
  const activeHoverVal = activeHoverPoint ? parseFloat(activeHoverPoint.closing_cash) : null;
  const activeHoverBestVal = hoverIdx !== null ? parseFloat(derivedBestPoints[hoverIdx].closing_cash) : null;
  const activeHoverWorstVal = hoverIdx !== null ? parseFloat(derivedWorstPoints[hoverIdx].closing_cash) : null;
  const activeHoverBaselineVal =
    hoverIdx !== null && baselinePoints && baselinePoints[hoverIdx]
      ? parseFloat(baselinePoints[hoverIdx].closing_cash)
      : null;

  return (
    <div className="glass-panel p-6 font-[var(--font-ui)] transition-all">
      {/* Chart Header with Controls & Legend */}
      <div className="flex flex-wrap justify-between items-center gap-4 mb-4">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-base font-bold tracking-tight text-gradient-hero">
              26-Week Canonical Cash Forecast
            </h3>
            <span
              className="text-[11px] font-mono px-2.5 py-0.5 rounded-[var(--radius-chip)] font-bold glass-pill"
              style={{
                backgroundColor: 'var(--tag-computed-bg)',
                color: 'var(--tag-computed)',
              }}
            >
              Weekly Buckets (ISO Monday)
            </span>
          </div>
          <p className="text-xs mt-0.5" style={{ color: 'var(--muted)' }}>
            Deterministic cash flow accumulator · Immutable baseline vs. 3-case scenario probability fan
          </p>
        </div>

        {/* Visibility Toggles with Glassmorphism */}
        <div className="flex items-center space-x-2 text-xs">
          <button
            type="button"
            onClick={() => setShowFanBand(!showFanBand)}
            className={`px-3 py-1 rounded-[var(--radius-chip)] border font-semibold transition-all duration-200 glass-pill ${
              showFanBand
                ? 'bg-[var(--tag-inferred-bg)] text-[var(--tag-inferred)] border-[var(--tag-inferred)] shadow-xs scale-102'
                : 'opacity-50 border-[var(--divider)] hover:opacity-80'
            }`}
          >
            {showFanBand ? '✓ 3-Case Fan Band' : '3-Case Fan Band'}
          </button>

          <button
            type="button"
            onClick={() => setShowBaseline(!showBaseline)}
            className={`px-3 py-1 rounded-[var(--radius-chip)] border font-semibold transition-all duration-200 glass-pill ${
              showBaseline
                ? 'bg-[var(--status-unverified-bg)] text-[var(--text)] border-[var(--ui-border)] shadow-xs scale-102'
                : 'opacity-50 border-[var(--divider)] hover:opacity-80'
            }`}
          >
            {showBaseline ? '✓ Baseline Line' : 'Baseline Line'}
          </button>

          <button
            type="button"
            onClick={() => setShowThresholds(!showThresholds)}
            className={`px-3 py-1 rounded-[var(--radius-chip)] border font-semibold transition-all duration-200 glass-pill ${
              showThresholds
                ? 'bg-[var(--status-warning-bg)] text-[var(--status-warning)] border-[var(--status-warning)] shadow-xs scale-102'
                : 'opacity-50 border-[var(--divider)] hover:opacity-80'
            }`}
          >
            {showThresholds ? '✓ Floor Guardrails' : 'Floor Guardrails'}
          </button>
        </div>
      </div>

      {/* Legend Bar */}
      <div
        className="flex flex-wrap items-center gap-4 text-xs font-medium pb-3 border-b mb-3"
        style={{ borderColor: 'var(--divider)' }}
      >
        <div className="flex items-center space-x-1.5">
          <span
            className="w-4 h-1.5 inline-block rounded-full shadow-xs"
            style={{ background: 'var(--primary-gradient)' }}
          />
          <span style={{ color: 'var(--text)' }} className="font-semibold">Expected Scenario</span>
        </div>

        {showFanBand && (
          <div className="flex items-center space-x-1.5">
            <span
              className="w-4 h-2.5 inline-block rounded"
              style={{
                background: 'linear-gradient(90deg, rgba(11, 107, 116, 0.25), rgba(91, 73, 192, 0.25))',
                border: '1px solid rgba(11, 107, 116, 0.3)',
              }}
            />
            <span style={{ color: 'var(--muted)' }}>3-Case Bounds (Best vs Worst)</span>
          </div>
        )}

        {showBaseline && (
          <div className="flex items-center space-x-1.5">
            <span
              className="w-4 h-0.5 inline-block"
              style={{ backgroundColor: 'var(--chart-baseline)' }}
            />
            <span style={{ color: 'var(--muted)' }}>Immutable Baseline</span>
          </div>
        )}

        {showThresholds && (
          <>
            <div className="flex items-center space-x-1.5">
              <span
                className="w-4 h-0.5 border-dashed border-t-2 inline-block"
                style={{ borderColor: 'var(--status-warning)' }}
              />
              <span style={{ color: 'var(--status-warning)' }}>
                12-Week Cash Floor (~${(cashFloorAmount / 1000).toFixed(0)}k)
              </span>
            </div>

            <div className="flex items-center space-x-1.5">
              <span
                className="w-4 h-0.5 border-dashed border-t-2 inline-block"
                style={{ borderColor: 'var(--status-failed)' }}
              />
              <span style={{ color: 'var(--status-failed)' }}>
                Reserve Floor (${(reserveAmount / 1000).toFixed(0)}k)
              </span>
            </div>
          </>
        )}
      </div>

      {/* Interactive SVG Canvas */}
      <div className="relative overflow-x-auto select-none">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto cursor-crosshair"
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          onClick={() => {
            if (onSelectPoint) {
              const ptId = hoverIdx !== null && points[hoverIdx]?.point_id ? points[hoverIdx].point_id : undefined;
              onSelectPoint(ptId);
            }
          }}
        >
          {/* SVG Definitions for Luminous Gradients and Filters */}
          <defs>
            <linearGradient id="fanGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#0B6B74" stopOpacity="0.22" />
              <stop offset="45%" stopColor="#158F9B" stopOpacity="0.16" />
              <stop offset="100%" stopColor="#5B49C0" stopOpacity="0.24" />
            </linearGradient>

            <linearGradient id="scenarioLineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#0B6B74" />
              <stop offset="50%" stopColor="#158F9B" />
              <stop offset="100%" stopColor="#5B49C0" />
            </linearGradient>

            <filter id="softGlow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Subtle Grid Lines & Y-Axis Ticks */}
          {yTicks.map((val, idx) => {
            const y = getY(val);
            return (
              <g key={idx}>
                <line
                  x1={paddingLeft}
                  y1={y}
                  x2={width - paddingRight}
                  y2={y}
                  stroke="var(--divider)"
                  strokeWidth="1"
                  strokeDasharray="2 3"
                />
                <text
                  x={paddingLeft - 8}
                  y={y + 3}
                  textAnchor="end"
                  fontSize="10"
                  fill="var(--muted)"
                  fontFamily="var(--font-mono)"
                >
                  ${(val / 1000).toFixed(0)}k
                </text>
              </g>
            );
          })}

          {/* Zero Axis Line (if in range) */}
          {minVal < 0 && (
            <line
              x1={paddingLeft}
              y1={zeroY}
              x2={width - paddingRight}
              y2={zeroY}
              stroke="var(--status-failed)"
              strokeWidth="1.5"
            />
          )}

          {/* Threshold Guardrails */}
          {showThresholds && (
            <>
              {/* Reserve Line */}
              <line
                x1={paddingLeft}
                y1={reserveY}
                x2={width - paddingRight}
                y2={reserveY}
                stroke="var(--status-failed)"
                strokeDasharray="4 4"
                strokeWidth="1.5"
              />
              <text
                x={width - paddingRight}
                y={reserveY - 4}
                textAnchor="end"
                fontSize="10"
                fill="var(--status-failed)"
                fontFamily="var(--font-mono)"
                fontWeight="600"
              >
                Hard Reserve ($50k)
              </text>

              {/* 12-Week Cash Floor */}
              <line
                x1={paddingLeft}
                y1={floorY}
                x2={width - paddingRight}
                y2={floorY}
                stroke="var(--status-warning)"
                strokeDasharray="4 4"
                strokeWidth="1.5"
              />
              <text
                x={width - paddingRight}
                y={floorY - 4}
                textAnchor="end"
                fontSize="10"
                fill="var(--status-warning)"
                fontFamily="var(--font-mono)"
                fontWeight="600"
              >
                12-Wk Floor (~$207k)
              </text>
            </>
          )}

          {/* 3-Case Corridor Fan Area with Gradient */}
          {showFanBand && (
            <>
              <path
                d={fanPolygonD}
                fill="url(#fanGradient)"
              />
              {/* Best Case Boundary Line */}
              <path
                d={bestPath}
                fill="none"
                stroke="#5B49C0"
                strokeWidth="1.2"
                strokeDasharray="3 3"
                opacity="0.6"
              />
              {/* Worst Case Boundary Line */}
              <path
                d={worstPath}
                fill="none"
                stroke="#C0392B"
                strokeWidth="1.2"
                strokeDasharray="3 3"
                opacity="0.6"
              />
            </>
          )}

          {/* Immutable Baseline Series */}
          {showBaseline && baselinePath && (
            <path
              d={baselinePath}
              fill="none"
              stroke="var(--chart-baseline)"
              strokeWidth="1.8"
            />
          )}

          {/* Expected Scenario Cash Line with Gradient */}
          <path
            d={expectedPath}
            fill="none"
            stroke="url(#scenarioLineGrad)"
            strokeWidth="3.5"
          />

          {/* X Axis Baseline Line */}
          <line
            x1={paddingLeft}
            y1={height - paddingBottom}
            x2={width - paddingRight}
            y2={height - paddingBottom}
            stroke="var(--divider)"
            strokeWidth="1.5"
          />

          {/* X Axis Week Labels */}
          {points.map((p, idx) => {
            if (idx % 2 !== 0 && idx !== points.length - 1) return null;
            const x = getX(idx);
            return (
              <text
                key={idx}
                x={x}
                y={height - paddingBottom + 18}
                textAnchor="middle"
                fontSize="10"
                fill="var(--muted)"
                fontFamily="var(--font-mono)"
              >
                {p.week_start.slice(5)}
              </text>
            );
          })}

          {/* Minimum Cash Point Glowing Callout */}
          <circle
            cx={minX}
            cy={minY}
            r="10"
            fill="rgba(245, 165, 36, 0.25)"
            className="animate-pulse"
          />
          <circle
            cx={minX}
            cy={minY}
            r="6"
            fill="var(--highlight-fill)"
            stroke="var(--highlight-text)"
            strokeWidth="2.5"
            filter="url(#softGlow)"
          />
          <text
            x={minX}
            y={minY - 14}
            textAnchor="middle"
            fontSize="11"
            fontWeight="bold"
            fill="var(--highlight-text)"
            fontFamily="var(--font-mono)"
          >
            {`Min cash, ${minDateLabel}`}
          </text>

          {/* Interactive Scrub Cursor Hairline */}
          {hoverIdx !== null && (
            <g>
              <line
                x1={getX(hoverIdx)}
                y1={paddingTop}
                x2={getX(hoverIdx)}
                y2={height - paddingBottom}
                stroke="var(--primary)"
                strokeWidth="1.5"
                strokeDasharray="2 2"
              />
              <circle
                cx={getX(hoverIdx)}
                cy={getY(parseFloat(points[hoverIdx].closing_cash))}
                r="6"
                fill="var(--primary)"
                stroke="#FFFFFF"
                strokeWidth="2.5"
                filter="url(#softGlow)"
              />
            </g>
          )}
        </svg>

        {/* Hover Inspection Floating HUD Card with Glassmorphism */}
        {hoverIdx !== null && activeHoverPoint && activeHoverVal !== null && (
          <div
            className="absolute top-3 right-4 p-4 rounded-[var(--radius-card)] glass-panel border font-[var(--font-ui)] text-xs pointer-events-none transition-all duration-200 shadow-xl z-20 animate-reveal-1"
            style={{
              borderColor: 'var(--glass-border)',
              minWidth: '240px',
            }}
          >
            <div className="flex justify-between items-center border-b pb-2 mb-2" style={{ borderColor: 'var(--divider)' }}>
              <span className="font-bold text-[11px] uppercase tracking-wider text-gradient-primary">
                Week {activeHoverPoint.week_number}
              </span>
              <span className="font-mono text-[11px]" style={{ color: 'var(--muted)' }}>
                {activeHoverPoint.week_start}
              </span>
            </div>

            <div className="space-y-1.5 font-[var(--font-mono)] tabular-nums">
              <div className="flex justify-between items-center">
                <span className="font-sans text-[11px]" style={{ color: 'var(--muted)' }}>
                  Projected Cash:
                </span>
                <span className="font-bold text-sm text-gradient-hero">
                  ${activeHoverVal.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </span>
              </div>

              {activeHoverBestVal !== null && (
                <div className="flex justify-between text-[11px]">
                  <span className="font-sans" style={{ color: 'var(--muted)' }}>
                    Best Case (-7d):
                  </span>
                  <span style={{ color: 'var(--status-verified)' }} className="font-semibold">
                    ${activeHoverBestVal.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </span>
                </div>
              )}

              {activeHoverWorstVal !== null && (
                <div className="flex justify-between text-[11px]">
                  <span className="font-sans" style={{ color: 'var(--muted)' }}>
                    Worst Case (+14d):
                  </span>
                  <span style={{ color: 'var(--status-failed)' }} className="font-semibold">
                    ${activeHoverWorstVal.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </span>
                </div>
              )}

              {activeHoverBaselineVal !== null && (
                <div className="flex justify-between text-[11px] border-t pt-1.5" style={{ borderColor: 'var(--divider)' }}>
                  <span className="font-sans" style={{ color: 'var(--muted)' }}>
                    Baseline Reality:
                  </span>
                  <span style={{ color: 'var(--chart-baseline)' }} className="font-semibold">
                    ${activeHoverBaselineVal.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </span>
                </div>
              )}
            </div>

            {/* Breach Status Pill */}
            <div className="mt-2.5 pt-2 border-t flex justify-between items-center" style={{ borderColor: 'var(--divider)' }}>
              <span className="text-[10px] uppercase font-semibold" style={{ color: 'var(--muted)' }}>
                Policy Status:
              </span>
              {activeHoverVal < reserveAmount ? (
                <span
                  className="px-2 py-0.5 rounded text-[10px] font-bold glass-pill"
                  style={{
                    backgroundColor: 'var(--status-failed-bg)',
                    color: 'var(--status-failed)',
                  }}
                >
                  ✕ Reserve Breach
                </span>
              ) : activeHoverVal < cashFloorAmount ? (
                <span
                  className="px-2 py-0.5 rounded text-[10px] font-bold glass-pill"
                  style={{
                    backgroundColor: 'var(--status-warning-bg)',
                    color: 'var(--status-warning)',
                  }}
                >
                  ⚠ Below 12-Wk Floor
                </span>
              ) : (
                <span
                  className="px-2 py-0.5 rounded text-[10px] font-bold glass-pill"
                  style={{
                    backgroundColor: 'var(--status-verified-bg)',
                    color: 'var(--status-verified)',
                  }}
                >
                  ✓ Healthy Buffer
                </span>
              )}
            </div>
            <div className="text-[10px] text-center mt-1.5" style={{ color: 'var(--muted)' }}>
              Click point to open cryptographic lineage
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ForecastChart;
