-- H1B Salary Database Schema
-- Source: US Department of Labor H1B Disclosure Data

CREATE TABLE IF NOT EXISTS employers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT UNIQUE NOT NULL,
  display_name TEXT NOT NULL,
  total_h1b_count INTEGER DEFAULT 0,
  top_job_category TEXT,
  hq_city TEXT,
  median_salary INTEGER
);

CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT UNIQUE NOT NULL,
  display_name TEXT NOT NULL,
  soc_category TEXT,
  median_national_salary INTEGER,
  total_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS locations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT UNIQUE NOT NULL,
  city TEXT NOT NULL,
  state TEXT NOT NULL,
  state_full TEXT,
  lat REAL,
  lng REAL,
  metro_area TEXT,
  median_salary INTEGER,
  total_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS salaries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employer_slug TEXT NOT NULL,
  job_slug TEXT NOT NULL,
  location_slug TEXT NOT NULL,
  median_salary INTEGER NOT NULL,
  p25_salary INTEGER,
  p75_salary INTEGER,
  sample_count INTEGER NOT NULL DEFAULT 1,
  soc_category TEXT,
  fiscal_year INTEGER,
  last_updated TEXT DEFAULT (date('now')),
  FOREIGN KEY (employer_slug) REFERENCES employers(slug),
  FOREIGN KEY (job_slug) REFERENCES jobs(slug),
  FOREIGN KEY (location_slug) REFERENCES locations(slug)
);

CREATE INDEX IF NOT EXISTS idx_salaries_employer ON salaries(employer_slug);
CREATE INDEX IF NOT EXISTS idx_salaries_job ON salaries(job_slug);
CREATE INDEX IF NOT EXISTS idx_salaries_location ON salaries(location_slug);
CREATE INDEX IF NOT EXISTS idx_salaries_employer_job ON salaries(employer_slug, job_slug);
CREATE INDEX IF NOT EXISTS idx_salaries_median ON salaries(median_salary DESC);
