import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import Breadcrumb from '@/components/Breadcrumb';
import SalaryBar from '@/components/SalaryBar';
import SalaryCard from '@/components/SalaryCard';
import {
  getDb,
  getEmployer,
  getJob,
  getSalaryRecord,
  getSalaryByLocation,
  getCompanyComparison,
  getCompanyTopJobs,
  formatSalary,
  formatCount,
} from '@/lib/db';

interface Props {
  params: Promise<{ company: string; job: string }>;
}

export async function generateStaticParams() {
  // Only generate pages for combinations that actually exist in the database
  return getDb()
    .prepare(
      `SELECT DISTINCT employer_slug as company, job_slug as job
       FROM salaries ORDER BY sample_count DESC LIMIT 10000`
    )
    .all() as { company: string; job: string }[];
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { company, job } = await params;
  const emp = getEmployer(company);
  const jobData = getJob(job);
  if (!emp || !jobData) return {};

  const salary = getSalaryRecord(company, job);
  const median = salary ? formatSalary(salary.median_salary) : 'N/A';
  const p25 = salary ? formatSalary(salary.p25_salary) : '';
  const p75 = salary ? formatSalary(salary.p75_salary) : '';

  return {
    title: `${emp.display_name} ${jobData.display_name} Salary — ${median} Median (2024 H1B Data)`,
    description: `${emp.display_name} paid a median salary of ${median} to ${jobData.display_name}s based on ${(salary?.sample_count ?? 0).toLocaleString()} H1B visa applications. Salary range: ${p25}–${p75}.`,
    openGraph: {
      title: `${emp.display_name} ${jobData.display_name} Salary — ${median}`,
      description: `Verified from ${(salary?.sample_count ?? 0).toLocaleString()} H1B applications. Range: ${p25}–${p75}.`,
    },
  };
}

export default async function SalaryPage({ params }: Props) {
  const { company, job } = await params;

  const emp = getEmployer(company);
  const jobData = getJob(job);

  if (!emp || !jobData) notFound();

  const salary = getSalaryRecord(company, job);
  if (!salary || !salary.median_salary) notFound();

  const salaryByLocation = getSalaryByLocation(company, job);
  const companyComparison = getCompanyComparison(job, 8);
  const otherJobsAtCompany = getCompanyTopJobs(company, 5);

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'JobPosting',
    title: jobData.display_name,
    hiringOrganization: {
      '@type': 'Organization',
      name: emp.display_name,
    },
    baseSalary: {
      '@type': 'MonetaryAmount',
      currency: 'USD',
      value: {
        '@type': 'QuantitativeValue',
        value: salary.median_salary,
        minValue: salary.p25_salary,
        maxValue: salary.p75_salary,
        unitText: 'YEAR',
      },
    },
    datePosted: salary.last_updated,
    description: `H1B salary data for ${jobData.display_name} at ${emp.display_name}`,
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
            { label: emp.display_name, href: `/company/${company}` },
            { label: jobData.display_name },
          ]}
        />

        <div className="mb-8">
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2">
            {emp.display_name} {jobData.display_name} Salary — H1B Data 2024
          </h1>
          <p className="text-gray-500">
            Based on {(salary.sample_count ?? 0).toLocaleString()} verified H1B applications
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-10">
          {/* Salary Card */}
          <div>
            <SalaryCard
              median={salary.median_salary}
              p25={salary.p25_salary}
              p75={salary.p75_salary}
              sampleCount={salary.sample_count}
              fiscalYear={salary.fiscal_year ?? 2024}
              locationCount={salaryByLocation.length}
            />

            {/* Find jobs CTA */}
            <div className="mt-4 bg-blue-600 rounded-2xl p-5 text-white">
              <p className="font-semibold mb-1">
                Find {jobData.display_name} Jobs
              </p>
              <p className="text-blue-200 text-sm mb-3">
                See open roles at {emp.display_name} and similar companies.
              </p>
              <a
                href={`https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(jobData.display_name)}&company=${encodeURIComponent(emp.display_name)}`}
                target="_blank"
                rel="noopener noreferrer nofollow"
                className="inline-flex items-center bg-white text-blue-700 font-semibold text-sm px-4 py-2 rounded-lg hover:bg-blue-50 transition-colors"
              >
                View on LinkedIn →
              </a>
            </div>
          </div>

          {/* Salary Bar Visual */}
          <div className="lg:col-span-2 space-y-6">
            {/* Main salary bar */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <h2 className="font-bold text-gray-900 mb-5">Salary Distribution</h2>
              {salary.p25_salary && salary.p75_salary ? (
                <SalaryBar
                  p25={salary.p25_salary}
                  median={salary.median_salary}
                  p75={salary.p75_salary}
                />
              ) : (
                <p className="text-gray-500 text-sm">Range data not available</p>
              )}
            </div>

            {/* Company comparison */}
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100">
                <h2 className="font-bold text-gray-900">
                  How {emp.display_name} Compares — {jobData.display_name}
                </h2>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="text-left py-2.5 px-4 font-semibold text-gray-500">Company</th>
                    <th className="text-right py-2.5 px-4 font-semibold text-gray-500">Median</th>
                    <th className="text-right py-2.5 px-4 font-semibold text-gray-500 hidden sm:table-cell">Applications</th>
                  </tr>
                </thead>
                <tbody>
                  {companyComparison.map((c) => (
                    <tr
                      key={c.employer_slug}
                      className={`border-b border-gray-50 transition-colors ${
                        c.employer_slug === company
                          ? 'bg-blue-50 font-semibold'
                          : 'hover:bg-gray-50'
                      }`}
                    >
                      <td className="py-2.5 px-4">
                        <Link
                          href={`/salary/${c.employer_slug}/${job}`}
                          className={`hover:text-blue-600 transition-colors ${
                            c.employer_slug === company ? 'text-blue-700' : 'text-gray-900'
                          }`}
                        >
                          {c.employer_name}
                          {c.employer_slug === company && (
                            <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
                              This company
                            </span>
                          )}
                        </Link>
                      </td>
                      <td
                        className={`py-2.5 px-4 text-right font-semibold ${
                          c.employer_slug === company ? 'text-blue-700' : 'text-gray-900'
                        }`}
                      >
                        {formatSalary(c.avg_salary)}
                      </td>
                      <td className="py-2.5 px-4 text-right text-gray-500 hidden sm:table-cell">
                        {formatCount(c.total_count)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Salary by Location */}
        {salaryByLocation.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              {emp.display_name} {jobData.display_name} Salary by City
            </h2>
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="text-left py-3 px-4 font-semibold text-gray-500">City</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-500">Median</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-500 hidden sm:table-cell">25th – 75th</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-500">Applications</th>
                  </tr>
                </thead>
                <tbody>
                  {salaryByLocation.map((row) => (
                    <tr
                      key={row.location_slug}
                      className="border-b border-gray-50 hover:bg-blue-50/30 transition-colors"
                    >
                      <td className="py-3 px-4">
                        <Link
                          href={`/location/${row.location_slug}`}
                          className="text-gray-700 hover:text-blue-600 transition-colors"
                        >
                          {row.city}, {row.state}
                        </Link>
                      </td>
                      <td className="py-3 px-4 text-right font-semibold text-blue-700">
                        {formatSalary(row.median_salary)}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-400 text-xs hidden sm:table-cell">
                        {formatSalary(row.p25_salary)} – {formatSalary(row.p75_salary)}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-500">
                        {(row.sample_count ?? 0).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Other roles at this company */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div>
            <h2 className="text-lg font-bold text-gray-900 mb-3">
              Other Roles at {emp.display_name}
            </h2>
            <div className="flex flex-wrap gap-2">
              {otherJobsAtCompany
                .filter((j) => j.job_slug !== job)
                .map((j) => (
                  <Link
                    key={j.job_slug}
                    href={`/salary/${company}/${j.job_slug}`}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:border-blue-300 hover:text-blue-600 transition-colors shadow-sm"
                  >
                    {j.job_name}
                    <span className="text-gray-400 text-xs">
                      {formatSalary(j.avg_salary)}
                    </span>
                  </Link>
                ))}
            </div>
          </div>

          <div>
            <h2 className="text-lg font-bold text-gray-900 mb-3">
              Explore More
            </h2>
            <div className="flex flex-wrap gap-2">
              <Link
                href={`/company/${company}`}
                className="px-3 py-1.5 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:border-blue-300 hover:text-blue-600 transition-colors shadow-sm"
              >
                All {emp.display_name} salaries →
              </Link>
              <Link
                href={`/job/${job}`}
                className="px-3 py-1.5 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:border-blue-300 hover:text-blue-600 transition-colors shadow-sm"
              >
                All {jobData.display_name} salaries →
              </Link>
            </div>
          </div>
        </div>

        {/* About data explainer */}
        <div className="bg-gray-50 rounded-2xl border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-2">
            Is This Salary Data Accurate?
          </h3>
          <p className="text-sm text-gray-600 leading-relaxed">
            Yes. This data comes directly from the US Department of Labor H1B
            Labor Condition Application (LCA) database. Employers are{' '}
            <strong>legally required</strong> to disclose the exact prevailing
            wage and offered wage for every H1B position before filing. Unlike
            salary surveys or crowdsourced data, these are official government
            filings that cannot be gamed or omitted. Data is sourced from{' '}
            <a
              href="https://www.dol.gov/agencies/eta/foreign-labor/performance"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              dol.gov
            </a>{' '}
            and refreshed weekly. Last updated: {salary.last_updated}.
          </p>
        </div>
      </div>
    </>
  );
}
