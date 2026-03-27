import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import Breadcrumb from '@/components/Breadcrumb';
import SalaryBar from '@/components/SalaryBar';
import {
  getAllJobs,
  getJob,
  getJobTopEmployers,
  getJobTopLocations,
  formatSalary,
  formatCount,
} from '@/lib/db';

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateStaticParams() {
  return getAllJobs().map((j) => ({ slug: j.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const job = getJob(slug);
  if (!job) return {};
  const median = formatSalary(job.median_national_salary);
  return {
    title: `${job.display_name} H1B Salary 2024 — National Median ${median}`,
    description: `${job.display_name} median salary is ${median} based on ${job.total_count.toLocaleString()} H1B applications. See salaries by company and city.`,
    openGraph: {
      title: `${job.display_name} Salary Data — ${median} Median`,
      description: `National median salary for ${job.display_name}: ${median}`,
    },
  };
}

export default async function JobPage({ params }: Props) {
  const { slug } = await params;
  const job = getJob(slug);
  if (!job) notFound();

  const topEmployers = getJobTopEmployers(slug, 15);
  const topLocations = getJobTopLocations(slug, 10);

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Occupation',
    name: job.display_name,
    occupationalCategory: job.soc_category,
    estimatedSalary: {
      '@type': 'MonetaryAmountDistribution',
      name: 'Median',
      currency: 'USD',
      median: job.median_national_salary,
    },
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <Breadcrumb
          crumbs={[
            { label: 'Home', href: '/' },
            { label: 'Job Titles', href: '/job' },
            { label: job.display_name },
          ]}
        />

        <div className="mb-8">
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2">
            {job.display_name} H1B Salary Data 2024
          </h1>
          <p className="text-gray-500">
            Based on {job.total_count.toLocaleString()} verified H1B applications
          </p>
        </div>

        {/* National Median Hero */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl p-8 text-white mb-10">
          <div className="text-sm text-blue-200 mb-1">National Median Salary</div>
          <div className="text-5xl font-bold mb-2">
            {formatSalary(job.median_national_salary)}
          </div>
          <div className="text-blue-200 text-sm">
            {job.total_count.toLocaleString()} H1B applications ·{' '}
            {job.soc_category}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Top Employers */}
          <div className="lg:col-span-2">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Salary by Company
            </h2>
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="text-left py-3 px-4 font-semibold text-gray-500">Company</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-500">Median</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-500 hidden sm:table-cell">Range</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-500">Count</th>
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
                          href={`/salary/${emp.employer_slug}/${slug}`}
                          className="font-medium text-gray-900 hover:text-blue-600 transition-colors"
                        >
                          {emp.employer_name}
                        </Link>
                      </td>
                      <td className="py-3 px-4 text-right font-semibold text-blue-700">
                        {formatSalary(emp.avg_salary)}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-400 text-xs hidden sm:table-cell">
                        {formatSalary(emp.avg_p25)} – {formatSalary(emp.avg_p75)}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-500">
                        {formatCount(emp.total_count)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Top Cities */}
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Salary by City
            </h2>
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="text-left py-3 px-4 font-semibold text-gray-500">City</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-500">Median</th>
                  </tr>
                </thead>
                <tbody>
                  {topLocations.map((loc) => (
                    <tr
                      key={loc.location_slug}
                      className="border-b border-gray-50 hover:bg-blue-50/30 transition-colors"
                    >
                      <td className="py-3 px-4">
                        <Link
                          href={`/location/${loc.location_slug}`}
                          className="text-gray-700 hover:text-blue-600 transition-colors"
                        >
                          {loc.city}, {loc.state}
                        </Link>
                      </td>
                      <td className="py-3 px-4 text-right font-semibold text-blue-700">
                        {formatSalary(loc.avg_salary)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-6 bg-blue-50 rounded-2xl p-4 border border-blue-100">
              <p className="text-sm font-semibold text-blue-800 mb-3">
                Compare companies for {job.display_name}
              </p>
              <div className="flex flex-wrap gap-2">
                {topEmployers.slice(0, 5).map((emp) => (
                  <Link
                    key={emp.employer_slug}
                    href={`/salary/${emp.employer_slug}/${slug}`}
                    className="text-xs bg-white border border-blue-200 text-blue-700 px-3 py-1.5 rounded-full hover:bg-blue-100 transition-colors"
                  >
                    {emp.employer_name.split(' ')[0]}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="mt-10 bg-gray-50 rounded-2xl border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-2">
            About {job.display_name} H1B Salary Data
          </h3>
          <p className="text-sm text-gray-600 leading-relaxed">
            These figures come from US Department of Labor H1B LCA disclosures —
            exact wages that employers are legally required to report. Unlike
            salary surveys, this data cannot be gamed or anonymized away. The
            national median of {formatSalary(job.median_national_salary)} is
            calculated across all companies and cities in the DOL database for
            FY2021–FY2024.
          </p>
        </div>
      </div>
    </>
  );
}
