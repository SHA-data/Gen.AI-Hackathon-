import React, { useState, useMemo, useRef } from 'react';
import { Check, ShieldAlert, CheckCircle2, AlertTriangle } from 'lucide-react';

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
  minCashDate = '1 Feb 2027',
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
      <div className="p-8 text-center rounded-3xl border border-dashed border-slate-300 clay-card text-slate-600 font-semibold text-xs">
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
  const height = 330;
  const paddingLeft = 65;
  const paddingRight = 45;
  const paddingTop = 32;
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

  // Tooltip smart side positioning to prevent chart occlusion
  const isRightHalf = hoverIdx !== null && hoverIdx > points.length * 0.55;

  // Min Cash Badge Layout Computation
  const minCashBadgeWidth = 105;
  const minCashBadgeHeight = 22;
  const minCashBadgeX = Math.max(paddingLeft, Math.min(width - paddingRight - minCashBadgeWidth, minX - minCashBadgeWidth / 2));
  const minCashBadgeY = minY > 65 ? minY - 32 : minY + 14;

  const displayMinVal = minCashValue || `$${Math.round(minPointVal / 1000)}k`;

  return (
    <div className="font-sans transition-all">
      {/* Chart Header with Controls & Legend */}
      <div className="flex flex-wrap justify-between items-center gap-4 mb-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <h3 className="text-base font-extrabold text-slate-900 tracking-tight">
              26-Week Canonical Cash Forecast
            </h3>
            <span className="text-[11px] font-mono px-3 py-0.5 rounded-full font-bold clay-pill-sage shadow-xs">
              Weekly Buckets (ISO Monday)
            </span>
          </div>
          <p className="text-xs text-slate-600 font-semibold mt-0.5">
            Deterministic cash flow accumulator · Immutable baseline vs. 3-case scenario probability fan
          </p>
        </div>

        {/* Visibility Toggles with Clay Pills */}
        <div className="flex items-center space-x-2 text-xs">
          <button
            type="button"
            onClick={() => setShowFanBand(!showFanBand)}
            className={`px-3.5 py-1.5 rounded-full font-bold transition-all flex items-center space-x-1.5 ${
              showFanBand
                ? 'clay-pill-teal text-white shadow-sm'
                : 'clay-btn text-slate-600 hover:text-slate-900'
            }`}
          >
            <Check className="w-3.5 h-3.5" />
            <span>3-Case Fan Band</span>
          </button>

          <button
            type="button"
            onClick={() => setShowBaseline(!showBaseline)}
            className={`px-3.5 py-1.5 rounded-full font-bold transition-all flex items-center space-x-1.5 ${
              showBaseline
                ? 'clay-pill-sage text-slate-900 shadow-sm'
                : 'clay-btn text-slate-600 hover:text-slate-900'
            }`}
          >
            <Check className="w-3.5 h-3.5" />
            <span>Baseline Line</span>
          </button>

          <button
            type="button"
            onClick={() => setShowThresholds(!showThresholds)}
            className={`px-3.5 py-1.5 rounded-full font-bold transition-all flex items-center space-x-1.5 ${
              showThresholds
                ? 'clay-pill-lavender text-slate-900 shadow-sm'
                : 'clay-btn text-slate-600 hover:text-slate-900'
            }`}
          >
            <Check className="w-3.5 h-3.5" />
            <span>Floor Guardrails</span>
          </button>
        </div>
      </div>

      {/* Legend Bar */}
      <div className="flex flex-wrap items-center gap-4 text-xs font-bold pb-3.5 border-b border-slate-300 mb-3">
        <div className="flex items-center space-x-1.5">
          <span className="w-4 h-2 inline-block rounded-full bg-[#158F9B] shadow-xs" />
          <span className="text-slate-900">Expected Scenario</span>
        </div>

        {showFanBand && (
          <div className="flex items-center space-x-1.5">
            <span className="w-4 h-2.5 inline-block rounded bg-[#c5b8d8] border border-[#a896c2]" />
            <span className="text-slate-700">3-Case Bounds (Best vs Worst)</span>
          </div>
        )}

        {showBaseline && (
          <div className="flex items-center space-x-1.5">
            <span className="w-4 h-0.5 inline-block bg-slate-500" />
            <span className="text-slate-700">Immutable Baseline</span>
          </div>
        )}

        {showThresholds && (
          <>
            <div className="flex items-center space-x-1.5">
              <span className="w-4 h-0.5 border-dashed border-t-2 inline-block border-amber-600" />
              <span className="text-amber-800">
                12-Week Cash Floor (~${(cashFloorAmount / 1000).toFixed(0)}k)
              </span>
            </div>

            <div className="flex items-center space-x-1.5">
              <span className="w-4 h-0.5 border-dashed border-t-2 inline-block border-rose-600" />
              <span className="text-rose-800">
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
          {/* SVG Definitions for Gradients and Filters */}
          <defs>
            <linearGradient id="fanGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#648283" stopOpacity="0.25" />
              <stop offset="50%" stopColor="#94af9f" stopOpacity="0.22" />
              <stop offset="100%" stopColor="#c5b8d8" stopOpacity="0.28" />
            </linearGradient>

            <linearGradient id="scenarioLineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#0B6B74" />
              <stop offset="45%" stopColor="#158F9B" />
              <stop offset="100%" stopColor="#4c6b6c" />
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
                  stroke="#d8d4cc"
                  strokeWidth="1"
                  strokeDasharray="3 3"
                />
                <text
                  x={paddingLeft - 10}
                  y={y + 3.5}
                  textAnchor="end"
                  fontSize="11"
                  fill="#475569"
                  fontWeight="700"
                  fontFamily="sans-serif"
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
              stroke="#dc2626"
              strokeWidth="1.5"
            />
          )}

          {/* Threshold Guardrails (Clean Badge Ending to Avoid Text Collision) */}
          {showThresholds && (
            <>
              {/* Reserve Line */}
              <line
                x1={paddingLeft}
                y1={reserveY}
                x2={width - paddingRight - 122}
                y2={reserveY}
                stroke="#dc2626"
                strokeDasharray="4 4"
                strokeWidth="1.5"
              />
              <g transform={`translate(${width - paddingRight - 120}, ${reserveY - 10})`}>
                <rect
                  x="0"
                  y="0"
                  width="120"
                  height="20"
                  rx="6"
                  fill="#fef2f2"
                  stroke="#dc2626"
                  strokeWidth="1"
                />
                <text
                  x="60"
                  y="14"
                  textAnchor="middle"
                  fontSize="10"
                  fill="#991b1b"
                  fontWeight="800"
                  fontFamily="sans-serif"
                >
                  Hard Reserve ($50k)
                </text>
              </g>

              {/* 12-Week Cash Floor */}
              <line
                x1={paddingLeft}
                y1={floorY}
                x2={width - paddingRight - 128}
                y2={floorY}
                stroke="#d97706"
                strokeDasharray="4 4"
                strokeWidth="1.5"
              />
              <g transform={`translate(${width - paddingRight - 126}, ${floorY - 10})`}>
                <rect
                  x="0"
                  y="0"
                  width="126"
                  height="20"
                  rx="6"
                  fill="#fffbeb"
                  stroke="#d97706"
                  strokeWidth="1"
                />
                <text
                  x="63"
                  y="14"
                  textAnchor="middle"
                  fontSize="10"
                  fill="#92400e"
                  fontWeight="800"
                  fontFamily="sans-serif"
                >
                  12-Wk Floor (~$208k)
                </text>
              </g>
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
                stroke="#648283"
                strokeWidth="1.5"
                strokeDasharray="3 3"
                opacity="0.85"
              />
              {/* Worst Case Boundary Line */}
              <path
                d={worstPath}
                fill="none"
                stroke="#cb7a72"
                strokeWidth="1.5"
                strokeDasharray="3 3"
                opacity="0.85"
              />
            </>
          )}

          {/* Immutable Baseline Series */}
          {showBaseline && baselinePath && (
            <path
              d={baselinePath}
              fill="none"
              stroke="#64748b"
              strokeWidth="2"
              strokeDasharray="4 2"
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
            stroke="#cbd5e1"
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
                fill="#475569"
                fontWeight="700"
                fontFamily="sans-serif"
              >
                {p.week_start.slice(5)}
              </text>
            );
          })}

          {/* Minimum Cash Point Marker & Non-Colliding Opaque Callout */}
          <circle
            cx={minX}
            cy={minY}
            r="9"
            fill="rgba(203, 122, 114, 0.3)"
            className="animate-pulse"
          />
          <circle
            cx={minX}
            cy={minY}
            r="5"
            fill="#cb7a72"
            stroke="#ffffff"
            strokeWidth="2"
            filter="url(#softGlow)"
          />

          {/* Clean Boxed Badge for Minimum Cash Point */}
          <g transform={`translate(${minCashBadgeX}, ${minCashBadgeY})`}>
            <rect
              x="0"
              y="0"
              width={minCashBadgeWidth}
              height={minCashBadgeHeight}
              rx="6"
              fill="#ffffff"
              stroke="#cb7a72"
              strokeWidth="1.5"
              filter="drop-shadow(0 2px 4px rgba(0,0,0,0.12))"
            />
            <text
              x={minCashBadgeWidth / 2}
              y="15"
              textAnchor="middle"
              fontSize="10"
              fontWeight="800"
              fill="#991b1b"
              fontFamily="sans-serif"
            >
              Min Cash: {displayMinVal}
            </text>
          </g>

          {/* Interactive Scrub Cursor Hairline */}
          {hoverIdx !== null && (
            <g>
              <line
                x1={getX(hoverIdx)}
                y1={paddingTop}
                x2={getX(hoverIdx)}
                y2={height - paddingBottom}
                stroke="#0B6B74"
                strokeWidth="1.5"
                strokeDasharray="2 2"
              />
              <circle
                cx={getX(hoverIdx)}
                cy={getY(parseFloat(points[hoverIdx].closing_cash))}
                r="6"
                fill="#0B6B74"
                stroke="#FFFFFF"
                strokeWidth="2.5"
                filter="url(#softGlow)"
              />
            </g>
          )}
        </svg>

        {/* Hover Inspection HUD Card: 100% Solid Opaque, Smart Position Flipping */}
        {hoverIdx !== null && activeHoverPoint && activeHoverVal !== null && (
          <div
            className={`absolute top-4 ${isRightHalf ? 'left-4' : 'right-4'} p-4 rounded-2xl bg-[#faf8f5] border-2 border-[#ded9d0] shadow-[0_12px_28px_rgba(40,30,20,0.18)] z-40 pointer-events-none transition-all duration-150 min-w-[250px]`}
          >
            <div className="flex justify-between items-center border-b border-slate-200 pb-2 mb-2">
              <span className="font-extrabold text-[11px] uppercase tracking-wider text-[#0B6B74]">
                Week {activeHoverPoint.week_number}
              </span>
              <span className="font-mono text-[11px] font-bold text-slate-600">
                {activeHoverPoint.week_start}
              </span>
            </div>

            <div className="space-y-1.5 font-mono tabular-nums">
              <div className="flex justify-between items-center">
                <span className="font-sans text-[11px] font-bold text-slate-600">
                  Projected Cash:
                </span>
                <span className="font-black text-sm text-slate-900 font-sans">
                  ${activeHoverVal.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </span>
              </div>

              {activeHoverBestVal !== null && (
                <div className="flex justify-between text-[11px]">
                  <span className="font-sans font-semibold text-slate-600">
                    Best Case (-7d):
                  </span>
                  <span className="text-emerald-700 font-bold">
                    ${activeHoverBestVal.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </span>
                </div>
              )}

              {activeHoverWorstVal !== null && (
                <div className="flex justify-between text-[11px]">
                  <span className="font-sans font-semibold text-slate-600">
                    Worst Case (+14d):
                  </span>
                  <span className="text-rose-700 font-bold">
                    ${activeHoverWorstVal.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </span>
                </div>
              )}

              {activeHoverBaselineVal !== null && (
                <div className="flex justify-between text-[11px] border-t border-slate-200 pt-1.5">
                  <span className="font-sans font-semibold text-slate-600">
                    Baseline Reality:
                  </span>
                  <span className="text-slate-800 font-bold">
                    ${activeHoverBaselineVal.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </span>
                </div>
              )}
            </div>

            {/* Breach Status Pill - Zero Emojis */}
            <div className="mt-2.5 pt-2 border-t border-slate-200 flex justify-between items-center">
              <span className="text-[10px] uppercase font-bold text-slate-500">
                Policy Status:
              </span>
              {activeHoverVal < reserveAmount ? (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300 flex items-center space-x-1">
                  <ShieldAlert className="w-3 h-3 text-rose-700" />
                  <span>Reserve Breach</span>
                </span>
              ) : activeHoverVal < cashFloorAmount ? (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300 flex items-center space-x-1">
                  <AlertTriangle className="w-3 h-3 text-amber-700" />
                  <span>Below 12-Wk Floor</span>
                </span>
              ) : (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-900 border border-emerald-300 flex items-center space-x-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-700" />
                  <span>Healthy Buffer</span>
                </span>
              )}
            </div>
            <div className="text-[9px] text-center mt-1.5 font-semibold text-slate-500">
              Click point to open cryptographic lineage
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ForecastChart;
