import React from 'react';

export interface WeeklyPoint {
  week_number: number;
  week_start: string;
  closing_cash: string;
}

export interface ForecastChartProps {
  points: WeeklyPoint[];
  reserveAmount?: number;
  cashFloorAmount?: number;
  minCashDate?: string;
  minCashValue?: string;
  onSelectPoint?: (pointId?: string) => void;
}

export const ForecastChart: React.FC<ForecastChartProps> = ({
  points,
  reserveAmount = 50000,
  cashFloorAmount = 207692,
  minCashDate,
  minCashValue,
  onSelectPoint,
}) => {
  if (!points || points.length === 0) {
    return (
      <div
        className="p-8 text-center rounded-[var(--radius-control)] border border-dashed"
        style={{
          backgroundColor: 'var(--bg)',
          borderColor: 'var(--ui-border)',
          color: 'var(--muted)',
        }}
      >
        No forecast data available. Run baseline or scenario simulation first.
      </div>
    );
  }

  const values = points.map((p) => parseFloat(p.closing_cash));
  const maxVal = Math.max(...values, reserveAmount, cashFloorAmount) * 1.1;
  const minVal = Math.min(...values, 0) * 0.9;
  const range = maxVal - minVal || 1;

  const width = 800;
  const height = 280;
  const padding = 45;

  const getY = (val: number) => {
    return height - padding - ((val - minVal) / range) * (height - 2 * padding);
  };

  const getX = (idx: number) => {
    return padding + (idx / (points.length - 1)) * (width - 2 * padding);
  };

  // Find minimum cash point
  let minPointIdx = 0;
  let minPointVal = values[0];
  values.forEach((v, idx) => {
    if (v < minPointVal) {
      minPointVal = v;
      minPointIdx = idx;
    }
  });

  const minX = getX(minPointIdx);
  const minY = getY(minPointVal);
  const minDateLabel = minCashDate || points[minPointIdx].week_start;

  // Generate SVG path for cash line
  const pathD = points
    .map((p, idx) => {
      const x = getX(idx);
      const y = getY(parseFloat(p.closing_cash));
      return `${idx === 0 ? 'M' : 'L'} ${x} ${y}`;
    })
    .join(' ');

  const reserveY = getY(reserveAmount);
  const floorY = getY(cashFloorAmount);

  return (
    <div
      className="rounded-[var(--radius-card)] p-6 font-[var(--font-ui)] border shadow-sm transition-colors"
      style={{
        backgroundColor: 'var(--surface)',
        borderColor: 'var(--divider)',
        color: 'var(--text)',
      }}
    >
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-base font-semibold" style={{ color: 'var(--text)' }}>
            26-Week Canonical Cash Forecast
          </h3>
          <p className="text-xs" style={{ color: 'var(--muted)' }}>
            Weekly resolution starting on ISO Monday · Deterministic Engine
          </p>
        </div>
        <div className="flex items-center space-x-4 text-xs font-medium">
          <div className="flex items-center space-x-1.5">
            <span
              className="w-3.5 h-0.5 inline-block"
              style={{ backgroundColor: 'var(--chart-combined)' }}
            ></span>
            <span style={{ color: 'var(--text)' }}>Projected Cash</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span
              className="w-3.5 h-0.5 border-dashed border-t-2 inline-block"
              style={{ borderColor: 'var(--status-failed)' }}
            ></span>
            <span style={{ color: 'var(--status-failed)' }}>Reserve Floor ($50k)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span
              className="w-3.5 h-0.5 border-dashed border-t-2 inline-block"
              style={{ borderColor: 'var(--status-warning)' }}
            ></span>
            <span style={{ color: 'var(--status-warning)' }}>12-Week Cash Floor</span>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto">
          {/* Axis dividers */}
          <line
            x1={padding}
            y1={padding}
            x2={padding}
            y2={height - padding}
            stroke="var(--divider)"
            strokeWidth="1"
          />
          <line
            x1={padding}
            y1={height - padding}
            x2={width - padding}
            y2={height - padding}
            stroke="var(--divider)"
            strokeWidth="1"
          />

          {/* Reserve line */}
          <line
            x1={padding}
            y1={reserveY}
            x2={width - padding}
            y2={reserveY}
            stroke="var(--status-failed)"
            strokeDasharray="4 4"
            strokeWidth="1.5"
          />
          <text
            x={width - padding}
            y={reserveY - 4}
            textAnchor="end"
            fontSize="10"
            fill="var(--status-failed)"
            fontFamily="var(--font-mono)"
          >
            Hard Reserve ($50k)
          </text>

          {/* 12-week cash floor line */}
          <line
            x1={padding}
            y1={floorY}
            x2={width - padding}
            y2={floorY}
            stroke="var(--status-warning)"
            strokeDasharray="4 4"
            strokeWidth="1.5"
          />
          <text
            x={width - padding}
            y={floorY - 4}
            textAnchor="end"
            fontSize="10"
            fill="var(--status-warning)"
            fontFamily="var(--font-mono)"
          >
            12-Wk Floor (~$207k)
          </text>

          {/* Canonical forecast line */}
          <path
            d={pathD}
            fill="none"
            stroke="var(--chart-combined)"
            strokeWidth="2.5"
          />

          {/* Interactive weekly points */}
          {points.map((p, idx) => {
            const x = getX(idx);
            const val = parseFloat(p.closing_cash);
            const y = getY(val);
            const isBreach = val < reserveAmount;
            return (
              <circle
                key={idx}
                cx={x}
                cy={y}
                r={isBreach ? 4.5 : 3}
                fill={isBreach ? 'var(--status-failed)' : 'var(--chart-combined)'}
                className="cursor-pointer hover:r-5 transition-all"
                onClick={() => onSelectPoint && onSelectPoint()}
              >
                <title>{`Week ${p.week_number} (${p.week_start}): $${val.toLocaleString()}`}</title>
              </circle>
            );
          })}

          {/* Minimum cash callout point & label */}
          <circle
            cx={minX}
            cy={minY}
            r="6"
            fill="var(--highlight-fill)"
            stroke="var(--highlight-text)"
            strokeWidth="2"
          />
          <text
            x={minX}
            y={minY - 12}
            textAnchor="middle"
            fontSize="11"
            fontWeight="600"
            fill="var(--highlight-text)"
            fontFamily="var(--font-ui)"
          >
            {`Min cash, ${minDateLabel}`}
          </text>
        </svg>
      </div>
    </div>
  );
};

export default ForecastChart;
