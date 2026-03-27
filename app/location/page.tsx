import type { Metadata } from 'next';
import Link from 'next/link';
import { getAllLocations, formatSalary, formatCount } from '@/lib/db';

export const metadata: Metadata = {
  title: 'H1B Salaries by City',
  description:
    'Browse H1B salary data by city. Compare median salaries in San Francisco, Seattle, New York, Austin, and 50+ cities using verified DOL disclosure data.',
};

export default function LocationsPage() {
  const locations = getAllLocations();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        H1B Salaries by City
      </h1>
      <p className="text-gray-500 mb-8">
        {locations.length.toLocaleString()} cities with verified H1B salary data
      </p>

      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              <th className="text-left py-3 px-4 font-semibold text-gray-500">#</th>
              <th className="text-left py-3 px-4 font-semibold text-gray-500">City</th>
              <th className="text-left py-3 px-4 font-semibold text-gray-500 hidden md:table-cell">State</th>
              <th className="text-right py-3 px-4 font-semibold text-gray-500">Median Salary</th>
              <th className="text-right py-3 px-4 font-semibold text-gray-500 hidden sm:table-cell">H1B Records</th>
            </tr>
          </thead>
          <tbody>
            {locations.map((loc, i) => (
              <tr
                key={loc.slug}
                className="border-b border-gray-50 hover:bg-blue-50/30 transition-colors"
              >
                <td className="py-3 px-4 text-gray-400 font-mono text-xs">{i + 1}</td>
                <td className="py-3 px-4">
                  <Link
                    href={`/location/${loc.slug}`}
                    className="font-medium text-gray-900 hover:text-blue-600 transition-colors"
                  >
                    {loc.city}
                  </Link>
                </td>
                <td className="py-3 px-4 text-gray-500 hidden md:table-cell">
                  {loc.state_full ?? loc.state}
                </td>
                <td className="py-3 px-4 text-right font-semibold text-blue-700">
                  {formatSalary(loc.median_salary)}
                </td>
                <td className="py-3 px-4 text-right text-gray-500 hidden sm:table-cell">
                  {formatCount(loc.total_count)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
