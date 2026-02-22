import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import Breadcrumb from '@/components/Breadcrumb';
import {
  getAllLocations,
  getLocation,
  getLocationTopEmployers,
  getLocationTopJobs,
  formatSalary,
  formatCount,
} from '@/lib/db';

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateStaticParams() {
  return getAllLocations().map((l) => ({ slug: l.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const loc = getLocation(slug);
  if (!loc) return {};
  const median = formatSalary(loc.median_salary);
  return {
    title: `H1B Salaries in ${loc.city}, ${loc.state} 2024 — Median ${median}`,
    description: `H1B salary data for ${loc.city}, ${loc.state}. Median salary ${median} based on ${loc.total_count.toLocaleString()} applications. See top employers and roles.`,
  };
}

export default async function LocationPage({ params }: Props) {
  const { slug } = await params;
  const loc = getLocation(slug);
  if (!loc) notFound();

  const topEmployers = getLocationTopEmployers(slug, 15);
  const topJobs = getLocationTopJobs(slug, 15);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <Breadcrumb
        crumbs={[
          { label: 'Home', href: '/' },
          { label: 'Cities', href: '/location' },
          { label: `${loc.city}, ${loc.state}` },
        ]}
      />

      <div className="mb-8">
        <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2">
          H1B Salaries in {loc.city}, {loc.state_full ?? loc.state} (2024)
        </h1>
        <p className="text-gray-500">
          Based on {loc.total_count.toLocaleString()} verified H1B applications
          {loc.metro_area && ` · ${loc.metro_area}`}
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-10">
        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
          <div className="text-3xl font-bold text-blue-700">
            {formatSalary(loc.median_salary)}
          </div>
          <div className="text-sm text-gray-500 mt-1">Median Salary</div>
        </div>
        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
          <div className="text-3xl font-bold text-blue-700">
            {formatCount(loc.total_count)}
          </div>
          <div className="text-sm text-gray-500 mt-1">H1B Applications</div>
        </div>
        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm col-span-2 sm:col-span-1">
          <div className="text-3xl font-bold text-blue-700">{topEmployers.length}+</div>
          <div className="text-sm text-gray-500 mt-1">Employers</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Top Employers */}
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            Top Paying Companies in {loc.city}
          </h2>
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50">
                  <th className="text-left py-3 px-4 font-semibold text-gray-500">Company</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-500">Median</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-500 hidden sm:table-cell">Count</th>
                </tr>
              </thead>
              <tbody>
                {topEmployers.map((emp) => (
                  <tr
                    key={emp.employer_slug}
                    className="border-b border-gray-50 hover:bg-blue-50/30 transition-colors"
                  >
                    <td className="py-3 px-4">
                      <Link
                        href={`/company/${emp.employer_slug}`}
                        className="font-medium text-gray-900 hover:text-blue-600 transition-colors"
                      >
                        {emp.employer_name}
                      </Link>
                    </td>
                    <td className="py-3 px-4 text-right font-semibold text-blue-700">
                      {formatSalary(emp.avg_salary)}
                    </td>
                    <td className="py-3 px-4 text-right text-gray-500 hidden sm:table-cell">
                      {formatCount(emp.total_count)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top Jobs */}
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            Top Paying Roles in {loc.city}
          </h2>
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50">
                  <th className="text-left py-3 px-4 font-semibold text-gray-500">Job Title</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-500">Median</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-500 hidden sm:table-cell">Count</th>
                </tr>
              </thead>
              <tbody>
                {topJobs.map((job) => (
                  <tr
                    key={job.job_slug}
                    className="border-b border-gray-50 hover:bg-blue-50/30 transition-colors"
                  >
                    <td className="py-3 px-4">
                      <Link
                        href={`/job/${job.job_slug}`}
                        className="font-medium text-gray-900 hover:text-blue-600 transition-colors"
                      >
                        {job.job_name}
                      </Link>
                    </td>
                    <td className="py-3 px-4 text-right font-semibold text-blue-700">
                      {formatSalary(job.avg_salary)}
                    </td>
                    <td className="py-3 px-4 text-right text-gray-500 hidden sm:table-cell">
                      {formatCount(job.total_count)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="mt-10 bg-gray-50 rounded-2xl border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-900 mb-2">
          About H1B Salaries in {loc.city}, {loc.state}
        </h3>
        <p className="text-sm text-gray-600 leading-relaxed">
          Salary data for {loc.city} is sourced from US Department of Labor H1B
          LCA filings. These represent exact wages disclosed by employers to
          federal regulators for each visa application. The median salary of{' '}
          {formatSalary(loc.median_salary)} reflects H1B applications filed in{' '}
          {loc.city} during FY2021–FY2024.
        </p>
      </div>
    </div>
  );
}
