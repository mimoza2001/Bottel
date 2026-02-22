import type { Metadata } from 'next';
import Link from 'next/link';
import SearchBox from '@/components/SearchBox';
import {
  getHomepageStats,
  getTopEmployers,
  getTopJobs,
  formatSalary,
  formatCount,
} from '@/lib/db';

export const metadata: Metadata = {
  title: 'H1B Salary Database — 2M+ Verified Records | Free Salary Lookup',
  description:
    'Search real H1B salary data for any company and job title. 2M+ verified records from US Department of Labor disclosures. Free, no signup. Google pays $195K median for Software Engineers.',
};

export default function HomePage() {
  const stats = getHomepageStats();
  const topEmployers = getTopEmployers(10);
  const topJobs = getTopJobs(10);

  return (
    <>
      {/* Hero */}
      <section className="bg-gradient-to-b from-blue-700 to-blue-600 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
          <div className="inline-block bg-blue-500/30 text-blue-100 text-sm font-medium px-3 py-1 rounded-full mb-5">
            Public Government Data — Free Forever
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-5 leading-tight">
            Real Salaries.{' '}
            <span className="text-blue-200">Real Data.</span>
            <br />
            From {formatCount(stats.totalRecords)}+ H1B Disclosures.
          </h1>
          <p className="text-blue-100 text-lg sm:text-xl mb-8 max-w-2xl mx-auto">
            The US Department of Labor publishes every H1B visa salary publicly.
            Search exact wages for any company, job title, and city — no signup,
            no paywall, ever.
          </p>

          <div className="max-w-2xl mx-auto">
            <SearchBox placeholder="Search Google, Software Engineer, Seattle..." size="lg" />
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-center">
            <div>
              <div className="text-3xl font-bold text-blue-700">
                {formatCount(stats.totalRecords)}+
              </div>
              <div className="text-sm text-gray-500 mt-1">Salary Records</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-700">
                {stats.totalCompanies.toLocaleString()}
              </div>
              <div className="text-sm text-gray-500 mt-1">Companies</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-700">
                {stats.totalJobs.toLocaleString()}
              </div>
              <div className="text-sm text-gray-500 mt-1">Job Titles</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-700">FY2024</div>
              <div className="text-sm text-gray-500 mt-1">Latest Data</div>
            </div>
          </div>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Top Companies */}
          <div>
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-xl font-bold text-gray-900">Top Companies</h2>
              <Link
                href="/company"
                className="text-sm text-blue-600 hover:underline font-medium"
              >
                View all →
              </Link>
            </div>
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="text-left py-3 px-4 font-semibold text-gray-500">Company</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-500">Median Salary</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-500">Applications</th>
                  </tr>
                </thead>
                <tbody>
                  {topEmployers.map((emp, i) => (
                    <tr
                      key={emp.slug}
                      className="border-b border-gray-50 hover:bg-blue-50/50 transition-colors"
                    >
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-3">
                          <span className="text-gray-400 font-mono text-xs w-4">{i + 1}</span>
                          <Link
                            href={`/company/${emp.slug}`}
                            className="font-medium text-gray-900 hover:text-blue-600 transition-colors"
                          >
                            {emp.display_name}
                          </Link>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right font-semibold text-blue-700">
                        {formatSalary(emp.median_salary)}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-500">
                        {formatCount(emp.total_h1b_count)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Top Job Titles */}
          <div>
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-xl font-bold text-gray-900">Top Job Titles</h2>
              <Link
                href="/job"
                className="text-sm text-blue-600 hover:underline font-medium"
              >
                View all →
              </Link>
            </div>
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="text-left py-3 px-4 font-semibold text-gray-500">Job Title</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-500">National Median</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-500">Records</th>
                  </tr>
                </thead>
                <tbody>
                  {topJobs.map((job, i) => (
                    <tr
                      key={job.slug}
                      className="border-b border-gray-50 hover:bg-blue-50/50 transition-colors"
                    >
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-3">
                          <span className="text-gray-400 font-mono text-xs w-4">{i + 1}</span>
                          <Link
                            href={`/job/${job.slug}`}
                            className="font-medium text-gray-900 hover:text-blue-600 transition-colors"
                          >
                            {job.display_name}
                          </Link>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right font-semibold text-blue-700">
                        {formatSalary(job.median_national_salary)}
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
        </div>

        {/* How it works */}
        <div className="mt-16">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-8">
            Why This Data Is Accurate
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                title: '1. Legally Required Disclosure',
                body: 'US employers must file an H1B Labor Condition Application with exact salary details before hiring a foreign worker. These are not estimates — they are legal commitments.',
              },
              {
                title: '2. Public Government Records',
                body: 'The Department of Labor publishes every filing as public data under FOIA. We download directly from dol.gov, clean it, and present it here.',
              },
              {
                title: '3. Updated Weekly',
                body: 'We process new disclosure data every Monday from DOL\'s public FTP. You\'re seeing salaries filed as recently as this year, not outdated surveys.',
              },
            ].map((item) => (
              <div
                key={item.title}
                className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm"
              >
                <h3 className="font-bold text-gray-900 mb-2">{item.title}</h3>
                <p className="text-sm text-gray-600 leading-relaxed">{item.body}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Popular Searches */}
        <div className="mt-16">
          <h2 className="text-xl font-bold text-gray-900 mb-5">
            Popular Salary Lookups
          </h2>
          <div className="flex flex-wrap gap-3">
            {[
              { label: 'Google Software Engineer', href: '/salary/google-llc/software-engineer' },
              { label: 'Amazon Data Scientist', href: '/salary/amazon-com-services-llc/data-scientist' },
              { label: 'Microsoft ML Engineer', href: '/salary/microsoft-corporation/machine-learning-engineer' },
              { label: 'Meta Software Engineer', href: '/salary/meta-platforms/software-engineer' },
              { label: 'Netflix Software Engineer', href: '/salary/netflix/software-engineer' },
              { label: 'Goldman Sachs Quant', href: '/salary/goldman-sachs/quantitative-analyst' },
              { label: 'Apple Software Engineer', href: '/salary/apple-inc/software-engineer' },
              { label: 'Uber Data Scientist', href: '/salary/uber-technologies/data-scientist' },
            ].map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="inline-flex items-center px-4 py-2 bg-white border border-gray-200 rounded-full text-sm font-medium text-gray-700 hover:border-blue-300 hover:text-blue-600 transition-colors shadow-sm"
              >
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
