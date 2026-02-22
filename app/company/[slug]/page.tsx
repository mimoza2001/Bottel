import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import Breadcrumb from '@/components/Breadcrumb';
import SalaryBar from '@/components/SalaryBar';
import {
  getAllEmployers,
  getEmployer,
  getCompanyTopJobs,
  getCompanyTopLocations,
  formatSalary,
  formatCount,
} from '@/lib/db';

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateStaticParams() {
  return getAllEmployers().map((e) => ({ slug: e.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const emp = getEmployer(slug);
  if (!emp) return {};
  const median = formatSalary(emp.median_salary);
  return {
    title: `${emp.display_name} H1B Salaries 2024 — ${formatCount(emp.total_h1b_count)} Verified Records`,
    description: `${emp.display_name} pays a median of ${median} based on ${emp.total_h1b_count.toLocaleString()} H1B applications. See salaries by role and city.`,
    openGraph: {
      title: `${emp.display_name} H1B Salary Data`,
      description: `Median salary: ${median} across ${formatCount(emp.total_h1b_count)} H1B filings.`,
    },
  };
}

export default async function CompanyPage({ params }: Props) {
  const { slug } = await params;
  const emp = getEmployer(slug);
  if (!emp) notFound();

  const topJobs = getCompanyTopJobs(slug, 15);
  const topLocations = getCompanyTopLocations(slug, 10);

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: emp.display_name,
    description: `H1B salary data for ${emp.display_name}`,
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
            { label: 'Companies', href: '/company' },
            { label: emp.display_name },
          ]}
        />

        <div className="mb-8">
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2">
            {emp.display_name} H1B Salary Data 2024
          </h1>
          <p className="text-gray-500">
            Based on {emp.total_h1b_count.toLocaleString()} verified H1B
            applications
          </p>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-10">
          <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
            <div className="text-3xl font-bold text-blue-700">
              {formatSalary(emp.median_salary)}
            </div>
            <div className="text-sm text-gray-500 mt-1">Median Salary</div>
          </div>
          <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
            <div className="text-3xl font-bold text-blue-700">
              {formatCount(emp.total_h1b_count)}
            </div>
            <div className="text-sm text-gray-500 mt-1">H1B Applications</div>
          </div>
          <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm col-span-2 sm:col-span-1">
            <div className="text-3xl font-bold text-blue-700">
              {topJobs.length}
            </div>
            <div className="text-sm text-gray-500 mt-1">Job Categories</div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Jobs Table */}
          <div className="lg:col-span-2">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Salaries by Job Title
            </h2>
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="text-left py-3 px-4 font-semibold text-gray-500">Job Title</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-500">Median</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-500 hidden sm:table-cell">Range</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-500">Count</th>
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
                          href={`/salary/${slug}/${job.job_slug}`}
                          className="font-medium text-gray-900 hover:text-blue-600 transition-colors"
                        >
                          {job.job_name}
                        </Link>
                      </td>
                      <td className="py-3 px-4 text-right font-semibold text-blue-700">
                        {formatSalary(job.avg_salary)}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-400 text-xs hidden sm:table-cell">
                        {formatSalary(job.avg_p25)} – {formatSalary(job.avg_p75)}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-500">
                        {formatCount(job.total_count)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Locations Sidebar */}
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Hiring Locations
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

            {/* Internal Links */}
            <div className="mt-6 bg-blue-50 rounded-2xl p-4 border border-blue-100">
              <p className="text-sm font-semibold text-blue-800 mb-3">
                Compare {emp.display_name} roles
              </p>
              <div className="flex flex-wrap gap-2">
                {topJobs.slice(0, 5).map((job) => (
                  <Link
                    key={job.job_slug}
                    href={`/salary/${slug}/${job.job_slug}`}
                    className="text-xs bg-white border border-blue-200 text-blue-700 px-3 py-1.5 rounded-full hover:bg-blue-100 transition-colors"
                  >
                    {job.job_name}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* About data */}
        <div className="mt-10 bg-gray-50 rounded-2xl border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-2">
            About {emp.display_name} H1B Data
          </h3>
          <p className="text-sm text-gray-600 leading-relaxed">
            This data is sourced from US Department of Labor H1B Labor Condition
            Application (LCA) disclosures. Employers are legally required to
            file these applications and disclose exact wages before hiring H1B
            visa workers. The data covers FY2021–FY2024 and is refreshed weekly
            from{' '}
            <a
              href="https://www.dol.gov/agencies/eta/foreign-labor/performance"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              dol.gov
            </a>
            .
          </p>
        </div>
      </div>
    </>
  );
}
