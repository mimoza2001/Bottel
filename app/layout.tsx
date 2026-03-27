import type { Metadata } from 'next';
import './globals.css';
import Link from 'next/link';

export const metadata: Metadata = {
  title: {
    default: 'H1B Salary Database — 2M+ Verified Records',
    template: '%s | H1B Salary Database',
  },
  description:
    'Search real H1B salary data from 2M+ US Department of Labor disclosures. See exact salaries for any company, job title, and city — free, no signup required.',
  keywords: ['H1B salary', 'visa salary data', 'DOL disclosure', 'tech salaries', 'software engineer salary'],
  openGraph: {
    type: 'website',
    siteName: 'H1B Salary Database',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased min-h-screen flex flex-col">
        <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
            <Link href="/" className="font-bold text-xl text-blue-700 tracking-tight">
              H1BSalary<span className="text-gray-900">.info</span>
            </Link>
            <nav className="hidden sm:flex items-center gap-6 text-sm font-medium text-gray-600">
              <Link href="/company" className="hover:text-blue-600 transition-colors">Companies</Link>
              <Link href="/job" className="hover:text-blue-600 transition-colors">Job Titles</Link>
              <Link href="/location" className="hover:text-blue-600 transition-colors">Cities</Link>
            </nav>
          </div>
        </header>

        <main className="flex-1">{children}</main>

        <footer className="bg-white border-t border-gray-200 mt-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-sm text-gray-600">
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">H1BSalary.info</h3>
                <p>Real salary data from US Department of Labor H1B visa disclosures. Public government data made readable.</p>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Explore</h3>
                <ul className="space-y-1">
                  <li><Link href="/company" className="hover:text-blue-600">Top Companies</Link></li>
                  <li><Link href="/job" className="hover:text-blue-600">Job Titles</Link></li>
                  <li><Link href="/location" className="hover:text-blue-600">Cities</Link></li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">About the Data</h3>
                <p>
                  Data sourced from{' '}
                  <a href="https://www.dol.gov/agencies/eta/foreign-labor/performance" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                    DOL OFLC Performance Data
                  </a>. All H1B disclosures are public record. Updated weekly.
                </p>
              </div>
            </div>
            <div className="mt-8 pt-6 border-t border-gray-100 text-center text-xs text-gray-400">
              Data sourced from public US government records. Not financial or legal advice.
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
