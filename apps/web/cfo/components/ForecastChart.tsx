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
  onSelectPoint?: (pointId?: string) => void;
}

export const ForecastChart: React.FC<ForecastChartProps> = ({
  points,
  reserveAmount = 50000,
  cashFloorAmount = 207692,
  onSelectPoint,
}) => {
  if (!points || points.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500 bg-gray-50 rounded-lg border border-dashed border-gray-300">
        No forecast data available. Run baseline or scenario simulation first.
      </div>
    );
  }

  const values = points.map((p) => parseFloat(p.closing_cash));
  const maxVal = Math.max(...values, reserveAmount, cashFloorAmount) * 1.1;
  const minVal = Math.min(...values, 0) * 0.9;
  const range = maxVal - minVal || 1;

  const width = 800;
  const height = 260;
  const padding = 40;

  const getY = (val: number) => {
    return height - padding - ((val - minVal) / range) * (height - 2 * padding);
  };

  const getX = (idx: number) => {
    return padding + (idx / (points.length - 1)) * (width - 2 * padding);
  };

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
    <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6 font-sans">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-base font-bold text-gray-900">26-Week Canonical Cash Forecast</h3>
          <p className="text-xs text-gray-500">Weekly resolution starting on ISO Monday</p>
        </div>
        <div className="flex items-center space-x-4 text-xs font-medium">
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-0.5 bg-blue-600 inline-block"></span>
            <span className="text-gray-700">Projected Cash</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-0.5 bg-red-500 border-dashed inline-block"></span>
            <span className="text-red-600">Reserve Floor ($50k)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-0.5 bg-amber-500 border-dashed inline-block"></span>
            <span className="text-amber-600">12-Week Cash Floor</span>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto">
          {/* Grid lines */}
          <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#E5E7EB" />
          <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#E5E7EB" />

          {/* Reserve line */}
          <line
            x1={padding}
            y1={reserveY}
            x2={width - padding}
            y2={reserveY}
            stroke="#EF4444"
            strokeDasharray="4 4"
            strokeWidth="1.5"
          />

          {/* 12-week cash floor line */}
          <line
            x1={padding}
            y1={floorY}
            x2={width - padding}
            y2={floorY}
            stroke="#F59E0B"
            strokeDasharray="4 4"
            strokeWidth="1.5"
          />

          {/* Cash curve */}
          <path d={pathD} fill="none" stroke="#2563EB" strokeWidth="2.5" />

          {/* Points */}
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
                r={isBreach ? 5 : 3.5}
                fill={isBreach ? '#EF4444' : '#2563EB'}
                className="cursor-pointer hover:r-6 transition"
                onClick={() => onSelectPoint && onSelectPoint()}
              >
                <title>{`Week ${p.week_number} (${p.week_start}): $${val.toLocaleString()}`}</title>
              </circle>
            );
          })}
        </svg>
      </div>
    </div>
  );
};

export default ForecastChart;
