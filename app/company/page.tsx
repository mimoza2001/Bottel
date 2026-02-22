import type { Metadata } from 'next';
import Link from 'next/link';
import { getAllEmployers, formatSalary, formatCount } from '@/lib/db';

export const metadata: Metadata = {
  title: 'Top Companies by H1B Salary',
  description:
    'Browse H1B salary data for all companies. See median salaries, application counts, and top job titles for Google, Amazon, Microsoft, Meta, and thousands more.',
};

export default function CompaniesPage() {
  const employers = getAllEmployers();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        Companies — H1B Salary Data
      </h1>
      <p className="text-gray-500 mb-8">
        {employers.length.toLocaleString()} companies with verified H1B salary data
      </p>

      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              <th className="text-left py-3 px-4 font-semibold text-gray-500">#</th>
              <th className="text-left py-3 px-4 font-semibold text-gray-500">Company</th>
              <th className="text-right py-3 px-4 font-semibold text-gray-500">Median Salary</th>
              <th className="text-right py-3 px-4 font-semibold text-gray-500 hidden sm:table-cell">H1B Applications</th>
              <th className="text-left py-3 px-4 font-semibold text-gray-500 hidden md:table-cell">Top Role</th>
            </tr>
          </thead>
          <tbody>
            {employers.map((emp, i) => (
              <tr
                key={emp.slug}
                className="border-b border-gray-50 hover:bg-blue-50/30 transition-colors"
              >
                <td className="py-3 px-4 text-gray-400 font-mono text-xs">{i + 1}</td>
                <td className="py-3 px-4">
                  <Link
                    href={`/company/${emp.slug}`}
                    className="font-medium text-gray-900 hover:text-blue-600 transition-colors"
                  >
                    {emp.display_name}
                  </Link>
                </td>
                <td className="py-3 px-4 text-right font-semibold text-blue-700">
                  {formatSalary(emp.median_salary)}
                </td>
                <td className="py-3 px-4 text-right text-gray-500 hidden sm:table-cell">
                  {formatCount(emp.total_h1b_count)}
                </td>
                <td className="py-3 px-4 text-gray-500 hidden md:table-cell text-xs">
                  {emp.top_job_category ?? '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
