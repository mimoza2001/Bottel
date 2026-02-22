import Database from 'better-sqlite3';
import path from 'path';

const DB_PATH = path.join(process.cwd(), 'data', 'salaries.db');

let _db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!_db) {
    _db = new Database(DB_PATH, { readonly: true });
    // cache_size is safe to set on readonly connections
    _db.pragma('cache_size = 10000');
  }
  return _db;
}

// ---- Types ----

export interface Employer {
  slug: string;
  display_name: string;
  total_h1b_count: number;
  top_job_category: string | null;
  hq_city: string | null;
  median_salary: number | null;
}

export interface Job {
  slug: string;
  display_name: string;
  soc_category: string | null;
  median_national_salary: number | null;
  total_count: number;
}

export interface Location {
  slug: string;
  city: string;
  state: string;
  state_full: string | null;
  lat: number | null;
  lng: number | null;
  metro_area: string | null;
  median_salary: number | null;
  total_count: number;
}

export interface SalaryRecord {
  employer_slug: string;
  job_slug: string;
  location_slug: string;
  median_salary: number;
  p25_salary: number | null;
  p75_salary: number | null;
  sample_count: number;
  soc_category: string | null;
  fiscal_year: number | null;
  last_updated: string;
}

export interface SalaryWithNames extends SalaryRecord {
  employer_name: string;
  job_name: string;
  city: string;
  state: string;
}

// ---- Query Functions ----

export function getAllEmployers(): Employer[] {
  return getDb()
    .prepare('SELECT * FROM employers ORDER BY total_h1b_count DESC')
    .all() as Employer[];
}

export function getEmployer(slug: string): Employer | null {
  return (
    (getDb()
      .prepare('SELECT * FROM employers WHERE slug = ?')
      .get(slug) as Employer) ?? null
  );
}

export function getCompanySalaries(
  companySlug: string
): (SalaryRecord & { job_name: string })[] {
  return getDb()
    .prepare(
      `SELECT s.*, j.display_name as job_name
       FROM salaries s
       JOIN jobs j ON s.job_slug = j.slug
       WHERE s.employer_slug = ?
       ORDER BY s.sample_count DESC`
    )
    .all(companySlug) as (SalaryRecord & { job_name: string })[];
}

export function getCompanyTopJobs(companySlug: string, limit = 10) {
  return getDb()
    .prepare(
      `SELECT s.job_slug, j.display_name as job_name,
              SUM(s.sample_count) as total_count,
              CAST(AVG(s.median_salary) AS INTEGER) as avg_salary,
              CAST(AVG(s.p25_salary) AS INTEGER) as avg_p25,
              CAST(AVG(s.p75_salary) AS INTEGER) as avg_p75
       FROM salaries s
       JOIN jobs j ON s.job_slug = j.slug
       WHERE s.employer_slug = ?
       GROUP BY s.job_slug
       ORDER BY total_count DESC
       LIMIT ?`
    )
    .all(companySlug, limit) as {
    job_slug: string;
    job_name: string;
    total_count: number;
    avg_salary: number;
    avg_p25: number;
    avg_p75: number;
  }[];
}

export function getCompanyTopLocations(companySlug: string, limit = 10) {
  return getDb()
    .prepare(
      `SELECT s.location_slug, l.city, l.state,
              SUM(s.sample_count) as total_count,
              CAST(AVG(s.median_salary) AS INTEGER) as avg_salary
       FROM salaries s
       JOIN locations l ON s.location_slug = l.slug
       WHERE s.employer_slug = ?
       GROUP BY s.location_slug
       ORDER BY total_count DESC
       LIMIT ?`
    )
    .all(companySlug, limit) as {
    location_slug: string;
    city: string;
    state: string;
    total_count: number;
    avg_salary: number;
  }[];
}

export function getAllJobs(): Job[] {
  return getDb()
    .prepare('SELECT * FROM jobs ORDER BY total_count DESC')
    .all() as Job[];
}

export function getJob(slug: string): Job | null {
  return (
    (getDb()
      .prepare('SELECT * FROM jobs WHERE slug = ?')
      .get(slug) as Job) ?? null
  );
}

export function getJobSalaries(jobSlug: string) {
  return getDb()
    .prepare(
      `SELECT s.*, e.display_name as employer_name
       FROM salaries s
       JOIN employers e ON s.employer_slug = e.slug
       WHERE s.job_slug = ?
       ORDER BY s.median_salary DESC`
    )
    .all(jobSlug) as (SalaryRecord & { employer_name: string })[];
}

export function getJobTopEmployers(jobSlug: string, limit = 15) {
  return getDb()
    .prepare(
      `SELECT s.employer_slug, e.display_name as employer_name,
              SUM(s.sample_count) as total_count,
              CAST(AVG(s.median_salary) AS INTEGER) as avg_salary,
              CAST(AVG(s.p25_salary) AS INTEGER) as avg_p25,
              CAST(AVG(s.p75_salary) AS INTEGER) as avg_p75
       FROM salaries s
       JOIN employers e ON s.employer_slug = e.slug
       WHERE s.job_slug = ?
       GROUP BY s.employer_slug
       ORDER BY avg_salary DESC
       LIMIT ?`
    )
    .all(jobSlug, limit) as {
    employer_slug: string;
    employer_name: string;
    total_count: number;
    avg_salary: number;
    avg_p25: number;
    avg_p75: number;
  }[];
}

export function getJobTopLocations(jobSlug: string, limit = 15) {
  return getDb()
    .prepare(
      `SELECT s.location_slug, l.city, l.state,
              SUM(s.sample_count) as total_count,
              CAST(AVG(s.median_salary) AS INTEGER) as avg_salary
       FROM salaries s
       JOIN locations l ON s.location_slug = l.slug
       WHERE s.job_slug = ?
       GROUP BY s.location_slug
       ORDER BY avg_salary DESC
       LIMIT ?`
    )
    .all(jobSlug, limit) as {
    location_slug: string;
    city: string;
    state: string;
    total_count: number;
    avg_salary: number;
  }[];
}

export function getAllLocations(): Location[] {
  return getDb()
    .prepare('SELECT * FROM locations ORDER BY total_count DESC')
    .all() as Location[];
}

export function getLocation(slug: string): Location | null {
  return (
    (getDb()
      .prepare('SELECT * FROM locations WHERE slug = ?')
      .get(slug) as Location) ?? null
  );
}

export function getLocationTopEmployers(locationSlug: string, limit = 15) {
  return getDb()
    .prepare(
      `SELECT s.employer_slug, e.display_name as employer_name,
              SUM(s.sample_count) as total_count,
              CAST(AVG(s.median_salary) AS INTEGER) as avg_salary
       FROM salaries s
       JOIN employers e ON s.employer_slug = e.slug
       WHERE s.location_slug = ?
       GROUP BY s.employer_slug
       ORDER BY avg_salary DESC
       LIMIT ?`
    )
    .all(locationSlug, limit) as {
    employer_slug: string;
    employer_name: string;
    total_count: number;
    avg_salary: number;
  }[];
}

export function getLocationTopJobs(locationSlug: string, limit = 15) {
  return getDb()
    .prepare(
      `SELECT s.job_slug, j.display_name as job_name,
              SUM(s.sample_count) as total_count,
              CAST(AVG(s.median_salary) AS INTEGER) as avg_salary
       FROM salaries s
       JOIN jobs j ON s.job_slug = j.slug
       WHERE s.location_slug = ?
       GROUP BY s.job_slug
       ORDER BY avg_salary DESC
       LIMIT ?`
    )
    .all(locationSlug, limit) as {
    job_slug: string;
    job_name: string;
    total_count: number;
    avg_salary: number;
  }[];
}

export function getSalaryRecord(
  companySlug: string,
  jobSlug: string
): SalaryRecord | null {
  // Aggregate across all locations for the main salary page
  const row = getDb()
    .prepare(
      `SELECT employer_slug, job_slug,
              CAST(AVG(median_salary) AS INTEGER) as median_salary,
              CAST(AVG(p25_salary) AS INTEGER) as p25_salary,
              CAST(AVG(p75_salary) AS INTEGER) as p75_salary,
              SUM(sample_count) as sample_count,
              soc_category, fiscal_year, last_updated,
              '' as location_slug
       FROM salaries
       WHERE employer_slug = ? AND job_slug = ?`
    )
    .get(companySlug, jobSlug) as SalaryRecord | null;
  return row ?? null;
}

export function getSalaryByLocation(companySlug: string, jobSlug: string) {
  return getDb()
    .prepare(
      `SELECT s.location_slug, l.city, l.state,
              s.median_salary, s.p25_salary, s.p75_salary, s.sample_count
       FROM salaries s
       JOIN locations l ON s.location_slug = l.slug
       WHERE s.employer_slug = ? AND s.job_slug = ?
       ORDER BY s.sample_count DESC`
    )
    .all(companySlug, jobSlug) as {
    location_slug: string;
    city: string;
    state: string;
    median_salary: number;
    p25_salary: number;
    p75_salary: number;
    sample_count: number;
  }[];
}

export function getCompanyComparison(jobSlug: string, limit = 10) {
  return getDb()
    .prepare(
      `SELECT s.employer_slug, e.display_name as employer_name,
              CAST(AVG(s.median_salary) AS INTEGER) as avg_salary,
              SUM(s.sample_count) as total_count
       FROM salaries s
       JOIN employers e ON s.employer_slug = e.slug
       WHERE s.job_slug = ?
       GROUP BY s.employer_slug
       ORDER BY total_count DESC
       LIMIT ?`
    )
    .all(jobSlug, limit) as {
    employer_slug: string;
    employer_name: string;
    avg_salary: number;
    total_count: number;
  }[];
}

export function getHomepageStats() {
  const db = getDb();
  const totalRecords = (
    db.prepare('SELECT SUM(sample_count) as total FROM salaries').get() as {
      total: number;
    }
  ).total;
  const totalCompanies = (
    db
      .prepare('SELECT COUNT(*) as total FROM employers')
      .get() as { total: number }
  ).total;
  const totalJobs = (
    db
      .prepare('SELECT COUNT(*) as total FROM jobs')
      .get() as { total: number }
  ).total;
  const lastUpdated = (
    db
      .prepare(
        'SELECT MAX(last_updated) as last_updated FROM salaries'
      )
      .get() as { last_updated: string }
  ).last_updated;

  return { totalRecords, totalCompanies, totalJobs, lastUpdated };
}

export function getTopEmployers(limit = 10): Employer[] {
  return getDb()
    .prepare(
      'SELECT * FROM employers ORDER BY total_h1b_count DESC LIMIT ?'
    )
    .all(limit) as Employer[];
}

export function getTopJobs(limit = 10): Job[] {
  return getDb()
    .prepare('SELECT * FROM jobs ORDER BY total_count DESC LIMIT ?')
    .all(limit) as Job[];
}

export function formatSalary(n: number | null): string {
  if (!n) return 'N/A';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(n);
}

export function formatCount(n: number): string {
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return n.toString();
}
