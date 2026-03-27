import type { Metadata } from 'next';
import Link from 'next/link';
import { getAllJobs, formatSalary, formatCount } from '@/lib/db';

export const metadata: Metadata = {
  title: 'H1B Salary Data by Job Title',
  description:
    'Browse H1B salary data by job title. See national median salaries for Software Engineers, Data Scientists, Product Managers, and hundreds more roles.',
};

export default function JobsPage() {
  const jobs = getAllJobs();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        Job Titles — H1B Salary Data
      </h1>
      <p className="text-gray-500 mb-8">
        {jobs.length.toLocaleString()} job categories with verified H1B salary data
      </p>

      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              <th className="text-left py-3 px-4 font-semibold text-gray-500">#</th>
              <th className="text-left py-3 px-4 font-semibold text-gray-500">Job Title</th>
              <th className="text-right py-3 px-4 font-semibold text-gray-500">National Median</th>
              <th className="text-right py-3 px-4 font-semibold text-gray-500 hidden sm:table-cell">H1B Records</th>
              <th className="text-left py-3 px-4 font-semibold text-gray-500 hidden md:table-cell">Category</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job, i) => (
              <tr
                key={job.slug}
                className="border-b border-gray-50 hover:bg-blue-50/30 transition-colors"
              >
                <td className="py-3 px-4 text-gray-400 font-mono text-xs">{i + 1}</td>
                <td className="py-3 px-4">
                  <Link
                    href={`/job/${job.slug}`}
                    className="font-medium text-gray-900 hover:text-blue-600 transition-colors"
                  >
                    {job.display_name}
                  </Link>
                </td>
                <td className="py-3 px-4 text-right font-semibold text-blue-700">
                  {formatSalary(job.median_national_salary)}
                </td>
                <td className="py-3 px-4 text-right text-gray-500 hidden sm:table-cell">
                  {formatCount(job.total_count)}
                </td>
                <td className="py-3 px-4 text-gray-500 hidden md:table-cell text-xs">
                  {job.soc_category ?? '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
