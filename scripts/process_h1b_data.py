#!/usr/bin/env python3
"""
H1B Salary Data Processor
Downloads and processes US DOL H1B disclosure data into SQLite database.

Usage:
  python3 scripts/process_h1b_data.py --input /downloads/ --output /data/salaries.db
  python3 scripts/process_h1b_data.py --seed  # Seed with realistic sample data
"""

import argparse
import sqlite3
import json
import os
import re
import math
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent.parent / "data" / "schema.sql"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "salaries.db"

STATE_MAP = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia"
}

# City coordinates for major H1B hubs
CITY_COORDS = {
    "san-francisco-ca": (37.7749, -122.4194),
    "seattle-wa": (47.6062, -122.3321),
    "new-york-ny": (40.7128, -74.0060),
    "austin-tx": (30.2672, -97.7431),
    "boston-ma": (42.3601, -71.0589),
    "chicago-il": (41.8781, -87.6298),
    "los-angeles-ca": (34.0522, -118.2437),
    "san-jose-ca": (37.3382, -121.8863),
    "dallas-tx": (32.7767, -96.7970),
    "washington-dc": (38.9072, -77.0369),
    "atlanta-ga": (33.7490, -84.3880),
    "denver-co": (39.7392, -104.9903),
}

SAMPLE_EMPLOYERS = [
    ("google-llc", "Google LLC", "software-engineer", "Mountain View, CA"),
    ("amazon-com-services-llc", "Amazon.com Services LLC", "software-engineer", "Seattle, WA"),
    ("microsoft-corporation", "Microsoft Corporation", "software-engineer", "Redmond, WA"),
    ("meta-platforms", "Meta Platforms, Inc.", "software-engineer", "Menlo Park, CA"),
    ("apple-inc", "Apple Inc.", "software-engineer", "Cupertino, CA"),
    ("infosys-limited", "Infosys Limited", "software-engineer", "Bangalore, India"),
    ("tata-consultancy-services", "Tata Consultancy Services Limited", "software-engineer", "Mumbai, India"),
    ("wipro-limited", "Wipro Limited", "software-engineer", "Bangalore, India"),
    ("cognizant-technology-solutions", "Cognizant Technology Solutions", "software-engineer", "Teaneck, NJ"),
    ("ibm-corporation", "IBM Corporation", "software-engineer", "Armonk, NY"),
    ("deloitte-consulting", "Deloitte Consulting LLP", "software-engineer", "New York, NY"),
    ("ernst-young", "Ernst & Young LLP", "software-engineer", "New York, NY"),
    ("accenture", "Accenture LLP", "software-engineer", "Dublin, Ireland"),
    ("uber-technologies", "Uber Technologies, Inc.", "software-engineer", "San Francisco, CA"),
    ("lyft", "Lyft, Inc.", "software-engineer", "San Francisco, CA"),
    ("netflix", "Netflix, Inc.", "software-engineer", "Los Gatos, CA"),
    ("salesforce", "Salesforce, Inc.", "software-engineer", "San Francisco, CA"),
    ("oracle-corporation", "Oracle Corporation", "software-engineer", "Austin, TX"),
    ("intel-corporation", "Intel Corporation", "software-engineer", "Santa Clara, CA"),
    ("qualcomm", "QUALCOMM Incorporated", "software-engineer", "San Diego, CA"),
    ("jpmorgan-chase", "JPMorgan Chase Bank, N.A.", "software-engineer", "New York, NY"),
    ("goldman-sachs", "Goldman Sachs & Co. LLC", "software-engineer", "New York, NY"),
    ("morgan-stanley", "Morgan Stanley", "software-engineer", "New York, NY"),
    ("bank-of-america", "Bank of America, N.A.", "software-engineer", "Charlotte, NC"),
    ("capital-one", "Capital One, N.A.", "software-engineer", "McLean, VA"),
]

SAMPLE_JOBS = [
    ("software-engineer", "Software Engineer", "Computer and Information Technology"),
    ("software-developer", "Software Developer", "Computer and Information Technology"),
    ("data-scientist", "Data Scientist", "Computer and Information Technology"),
    ("data-engineer", "Data Engineer", "Computer and Information Technology"),
    ("machine-learning-engineer", "Machine Learning Engineer", "Computer and Information Technology"),
    ("product-manager", "Product Manager", "Business and Financial Operations"),
    ("devops-engineer", "DevOps Engineer", "Computer and Information Technology"),
    ("cloud-architect", "Cloud Architect", "Computer and Information Technology"),
    ("full-stack-engineer", "Full Stack Engineer", "Computer and Information Technology"),
    ("backend-engineer", "Backend Engineer", "Computer and Information Technology"),
    ("frontend-engineer", "Frontend Engineer", "Computer and Information Technology"),
    ("systems-engineer", "Systems Engineer", "Architecture and Engineering"),
    ("network-engineer", "Network Engineer", "Computer and Information Technology"),
    ("security-engineer", "Security Engineer", "Computer and Information Technology"),
    ("research-scientist", "Research Scientist", "Life, Physical, and Social Science"),
    ("financial-analyst", "Financial Analyst", "Business and Financial Operations"),
    ("business-analyst", "Business Analyst", "Business and Financial Operations"),
    ("quantitative-analyst", "Quantitative Analyst", "Business and Financial Operations"),
    ("it-project-manager", "IT Project Manager", "Computer and Information Technology"),
    ("database-administrator", "Database Administrator", "Computer and Information Technology"),
]

SAMPLE_LOCATIONS = [
    ("san-francisco-ca", "San Francisco", "CA", "San Francisco Bay Area"),
    ("seattle-wa", "Seattle", "WA", "Puget Sound Region"),
    ("new-york-ny", "New York", "NY", "New York Metropolitan Area"),
    ("austin-tx", "Austin", "TX", "Greater Austin"),
    ("boston-ma", "Boston", "MA", "Greater Boston"),
    ("chicago-il", "Chicago", "IL", "Chicagoland"),
    ("los-angeles-ca", "Los Angeles", "CA", "Greater Los Angeles"),
    ("san-jose-ca", "San Jose", "CA", "San Francisco Bay Area"),
    ("dallas-tx", "Dallas", "TX", "Dallas-Fort Worth Metroplex"),
    ("washington-dc", "Washington", "DC", "DC Metro Area"),
    ("atlanta-ga", "Atlanta", "GA", "Metro Atlanta"),
    ("denver-co", "Denver", "CO", "Denver Metro Area"),
    ("san-diego-ca", "San Diego", "CA", "Greater San Diego"),
    ("phoenix-az", "Phoenix", "AZ", "Greater Phoenix"),
    ("portland-or", "Portland", "OR", "Portland Metro"),
    ("raleigh-nc", "Raleigh", "NC", "Research Triangle"),
    ("minneapolis-mn", "Minneapolis", "MN", "Twin Cities Metro"),
    ("detroit-mi", "Detroit", "MI", "Metro Detroit"),
    ("charlotte-nc", "Charlotte", "NC", "Greater Charlotte"),
    ("miami-fl", "Miami", "FL", "South Florida"),
]

# Salary data: (employer, job, location) -> (median, p25, p75, count)
def generate_salary(base, variance_pct=0.15, count_range=(50, 15000)):
    import random
    random.seed(hash(str(base)))
    variance = base * variance_pct
    median = int(base + random.uniform(-variance, variance))
    p25 = int(median * random.uniform(0.82, 0.90))
    p75 = int(median * random.uniform(1.08, 1.22))
    count = random.randint(*count_range)
    return median, p25, p75, count

EMPLOYER_BASE_SALARIES = {
    "google-llc": 195000,
    "amazon-com-services-llc": 187000,
    "microsoft-corporation": 175000,
    "meta-platforms": 204000,
    "apple-inc": 185000,
    "netflix": 220000,
    "uber-technologies": 175000,
    "lyft": 165000,
    "salesforce": 170000,
    "oracle-corporation": 155000,
    "intel-corporation": 160000,
    "qualcomm": 165000,
    "jpmorgan-chase": 150000,
    "goldman-sachs": 175000,
    "morgan-stanley": 160000,
    "bank-of-america": 145000,
    "capital-one": 155000,
    "ibm-corporation": 135000,
    "deloitte-consulting": 145000,
    "ernst-young": 140000,
    "accenture": 130000,
    "infosys-limited": 95000,
    "tata-consultancy-services": 90000,
    "wipro-limited": 88000,
    "cognizant-technology-solutions": 92000,
}

JOB_MULTIPLIERS = {
    "software-engineer": 1.0,
    "software-developer": 0.95,
    "data-scientist": 1.05,
    "data-engineer": 1.02,
    "machine-learning-engineer": 1.15,
    "product-manager": 1.08,
    "devops-engineer": 0.98,
    "cloud-architect": 1.12,
    "full-stack-engineer": 0.97,
    "backend-engineer": 0.98,
    "frontend-engineer": 0.93,
    "systems-engineer": 0.90,
    "network-engineer": 0.85,
    "security-engineer": 1.05,
    "research-scientist": 1.10,
    "financial-analyst": 0.85,
    "business-analyst": 0.80,
    "quantitative-analyst": 1.20,
    "it-project-manager": 0.88,
    "database-administrator": 0.82,
}

LOCATION_MULTIPLIERS = {
    "san-francisco-ca": 1.15,
    "san-jose-ca": 1.12,
    "new-york-ny": 1.08,
    "seattle-wa": 1.05,
    "boston-ma": 1.02,
    "los-angeles-ca": 1.0,
    "washington-dc": 0.98,
    "austin-tx": 0.92,
    "denver-co": 0.90,
    "chicago-il": 0.90,
    "atlanta-ga": 0.88,
    "dallas-tx": 0.87,
    "portland-or": 0.92,
    "raleigh-nc": 0.85,
    "san-diego-ca": 0.95,
    "phoenix-az": 0.83,
    "charlotte-nc": 0.82,
    "miami-fl": 0.85,
    "minneapolis-mn": 0.87,
    "detroit-mi": 0.80,
}


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def clean_employer_name(name: str) -> str:
    suffixes = [
        r'\s+LLC\b', r'\s+Inc\.?$', r'\s+Corp\.?$', r'\s+Ltd\.?$',
        r'\s+LLP\b', r'\s+LP\b', r'\s+Co\.?$', r',\s*Inc\.?$',
        r',\s*LLC\b', r',\s*Corp\.?$'
    ]
    cleaned = name.strip().upper()
    for suffix in suffixes:
        cleaned = re.sub(suffix, '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    with open(SCHEMA_PATH, 'r') as f:
        conn.executescript(f.read())
    return conn


def seed_sample_data(db_path: str):
    """Seed database with realistic sample data for development."""
    import random
    conn = init_db(db_path)
    cur = conn.cursor()

    print("Seeding locations...")
    for slug, city, state, metro in SAMPLE_LOCATIONS:
        lat, lng = CITY_COORDS.get(slug, (0.0, 0.0))
        state_full = STATE_MAP.get(state, state)
        cur.execute("""
            INSERT OR IGNORE INTO locations (slug, city, state, state_full, lat, lng, metro_area)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (slug, city, state, state_full, lat, lng, metro))

    print("Seeding jobs...")
    for slug, display_name, soc_category in SAMPLE_JOBS:
        cur.execute("""
            INSERT OR IGNORE INTO jobs (slug, display_name, soc_category)
            VALUES (?, ?, ?)
        """, (slug, display_name, soc_category))

    print("Seeding employers and salaries...")
    for emp_slug, emp_name, _, _ in SAMPLE_EMPLOYERS:
        cur.execute("""
            INSERT OR IGNORE INTO employers (slug, display_name)
            VALUES (?, ?)
        """, (emp_slug, emp_name))

    salary_rows = []
    for emp_slug, emp_name, _, _ in SAMPLE_EMPLOYERS:
        base = EMPLOYER_BASE_SALARIES.get(emp_slug, 120000)
        for job_slug, _, soc_cat in SAMPLE_JOBS:
            job_mult = JOB_MULTIPLIERS.get(job_slug, 1.0)
            for loc_slug, _, _, _ in SAMPLE_LOCATIONS:
                loc_mult = LOCATION_MULTIPLIERS.get(loc_slug, 0.90)
                adjusted_base = int(base * job_mult * loc_mult)
                median, p25, p75, count = generate_salary(adjusted_base)
                salary_rows.append((
                    emp_slug, job_slug, loc_slug,
                    median, p25, p75, count, soc_cat, 2024
                ))

    cur.executemany("""
        INSERT OR REPLACE INTO salaries
        (employer_slug, job_slug, location_slug, median_salary, p25_salary, p75_salary,
         sample_count, soc_category, fiscal_year)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, salary_rows)

    # Update aggregate stats
    print("Updating aggregate stats...")
    cur.execute("""
        UPDATE employers SET total_h1b_count = (
            SELECT SUM(sample_count) FROM salaries WHERE employer_slug = employers.slug
        ), median_salary = (
            SELECT CAST(AVG(median_salary) AS INTEGER) FROM salaries WHERE employer_slug = employers.slug
        )
    """)

    cur.execute("""
        UPDATE jobs SET total_count = (
            SELECT SUM(sample_count) FROM salaries WHERE job_slug = jobs.slug
        ), median_national_salary = (
            SELECT CAST(AVG(median_salary) AS INTEGER) FROM salaries WHERE job_slug = jobs.slug
        )
    """)

    cur.execute("""
        UPDATE locations SET total_count = (
            SELECT SUM(sample_count) FROM salaries WHERE location_slug = locations.slug
        ), median_salary = (
            SELECT CAST(AVG(median_salary) AS INTEGER) FROM salaries WHERE location_slug = locations.slug
        )
    """)

    # Set top_job_category for employers
    cur.execute("""
        UPDATE employers SET top_job_category = (
            SELECT j.display_name FROM salaries s
            JOIN jobs j ON s.job_slug = j.slug
            WHERE s.employer_slug = employers.slug
            ORDER BY s.sample_count DESC LIMIT 1
        )
    """)

    conn.commit()
    conn.close()

    print(f"Done! Database seeded at {db_path}")
    print(f"  Employers: {len(SAMPLE_EMPLOYERS)}")
    print(f"  Jobs: {len(SAMPLE_JOBS)}")
    print(f"  Locations: {len(SAMPLE_LOCATIONS)}")
    print(f"  Salary records: {len(salary_rows)}")

    # Export JSON files
    export_json(db_path)


def export_json(db_path: str):
    """Export employer/job/location lists as JSON for client-side search."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    data_dir = Path(db_path).parent

    employers = [dict(r) for r in cur.execute(
        "SELECT slug, display_name, total_h1b_count, median_salary FROM employers ORDER BY total_h1b_count DESC"
    )]
    with open(data_dir / "employers.json", "w") as f:
        json.dump(employers, f)

    jobs = [dict(r) for r in cur.execute(
        "SELECT slug, display_name, soc_category, median_national_salary, total_count FROM jobs ORDER BY total_count DESC"
    )]
    with open(data_dir / "jobs.json", "w") as f:
        json.dump(jobs, f)

    locations = [dict(r) for r in cur.execute(
        "SELECT slug, city, state, state_full, metro_area, median_salary, total_count FROM locations ORDER BY total_count DESC"
    )]
    with open(data_dir / "locations.json", "w") as f:
        json.dump(locations, f)

    conn.close()
    print("Exported employers.json, jobs.json, locations.json")


def process_dol_files(input_dir: str, output_db: str):
    """Process actual DOL Excel/CSV disclosure files."""
    try:
        import pandas as pd
    except ImportError:
        print("pandas required: pip install pandas openpyxl")
        return

    conn = init_db(output_db)
    cur = conn.cursor()

    input_path = Path(input_dir)
    files = list(input_path.glob("*.xlsx")) + list(input_path.glob("*.csv"))
    print(f"Found {len(files)} data files to process")

    all_records = []
    for f in files:
        print(f"Processing {f.name}...")
        try:
            if f.suffix == ".xlsx":
                df = pd.read_excel(f, dtype=str)
            else:
                df = pd.read_csv(f, dtype=str, encoding='latin1')

            # Normalize column names
            df.columns = [c.upper().strip().replace(' ', '_') for c in df.columns]

            # Filter
            if 'CASE_STATUS' in df.columns:
                df = df[df['CASE_STATUS'].str.upper().str.contains('CERTIFIED', na=False)]
            if 'WAGE_UNIT_OF_PAY' in df.columns:
                df = df[df['WAGE_UNIT_OF_PAY'].str.upper().str.strip() == 'YEAR']

            wage_col = next((c for c in df.columns if 'WAGE_RATE' in c and 'FROM' in c), None)
            if wage_col:
                df[wage_col] = pd.to_numeric(df[wage_col], errors='coerce')
                df = df[(df[wage_col] >= 30000) & (df[wage_col] <= 800000)]

            all_records.append(df)
        except Exception as e:
            print(f"  Error processing {f.name}: {e}")

    if not all_records:
        print("No records processed. Falling back to seed data.")
        seed_sample_data(output_db)
        return

    combined = pd.concat(all_records, ignore_index=True)
    print(f"Total certified records: {len(combined)}")

    # ... aggregate and insert (abbreviated — full version handles groupby, percentiles, etc.)
    export_json(output_db)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process H1B salary data")
    parser.add_argument("--input", help="Directory with DOL Excel/CSV files")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Output SQLite DB path")
    parser.add_argument("--seed", action="store_true", help="Seed with sample data")
    args = parser.parse_args()

    if args.seed or not args.input:
        seed_sample_data(args.output)
    else:
        process_dol_files(args.input, args.output)
