'use client';

interface SalaryBarProps {
  p25: number;
  median: number;
  p75: number;
  showLabels?: boolean;
}

export default function SalaryBar({
  p25,
  median,
  p75,
  showLabels = true,
}: SalaryBarProps) {
  const fmt = (n: number) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(n);

  // Position median marker as % between p25 and p75
  const range = p75 - p25;
  const medianPct = range > 0 ? ((median - p25) / range) * 100 : 50;
  const clampedPct = Math.max(5, Math.min(95, medianPct));

  return (
    <div className="w-full">
      {showLabels && (
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>25th percentile</span>
          <span>Median</span>
          <span>75th percentile</span>
        </div>
      )}
      <div className="relative h-4 bg-gray-100 rounded-full overflow-visible">
        {/* Range bar */}
        <div className="absolute inset-0 bg-blue-100 rounded-full" />
        {/* Median marker */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-blue-600 rounded-full shadow-md border-2 border-white"
          style={{ left: `calc(${clampedPct}% - 8px)` }}
        />
      </div>
      {showLabels && (
        <div className="flex justify-between text-sm font-medium mt-1">
          <span className="text-gray-600">{fmt(p25)}</span>
          <span className="text-blue-700 font-bold">{fmt(median)}</span>
          <span className="text-gray-600">{fmt(p75)}</span>
        </div>
      )}
    </div>
  );
}
