import { formatSalary } from '@/lib/db';

interface SalaryCardProps {
  median: number;
  p25?: number | null;
  p75?: number | null;
  sampleCount: number;
  fiscalYear?: number | null;
  locationCount?: number;
}

export default function SalaryCard({
  median,
  p25,
  p75,
  sampleCount,
  fiscalYear,
  locationCount,
}: SalaryCardProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
      <div className="text-5xl font-bold text-blue-700 mb-1">
        {formatSalary(median)}
      </div>
      <div className="text-gray-500 text-sm mb-5">Median Annual Salary</div>

      <dl className="grid grid-cols-2 gap-4 text-sm">
        {p25 && (
          <div>
            <dt className="text-gray-500">25th Percentile</dt>
            <dd className="font-semibold text-gray-900">{formatSalary(p25)}</dd>
          </div>
        )}
        {p75 && (
          <div>
            <dt className="text-gray-500">75th Percentile</dt>
            <dd className="font-semibold text-gray-900">{formatSalary(p75)}</dd>
          </div>
        )}
        <div>
          <dt className="text-gray-500">H1B Applications</dt>
          <dd className="font-semibold text-gray-900">
            {sampleCount.toLocaleString()}
          </dd>
        </div>
        {fiscalYear && (
          <div>
            <dt className="text-gray-500">Most Recent Data</dt>
            <dd className="font-semibold text-gray-900">FY{fiscalYear}</dd>
          </div>
        )}
        {locationCount && (
          <div>
            <dt className="text-gray-500">Cities</dt>
            <dd className="font-semibold text-gray-900">
              {locationCount} cities
            </dd>
          </div>
        )}
      </dl>
    </div>
  );
}
