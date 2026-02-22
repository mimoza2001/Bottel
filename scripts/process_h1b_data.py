#!/usr/bin/env python3
"""
H1B Salary Data Processor — Real DOL Data Edition
Processes actual US Department of Labor H1B LCA disclosure Excel files.

Usage:
  python3 scripts/process_h1b_data.py --input downloads/ --output data/salaries.db
  python3 scripts/process_h1b_data.py --seed   # sample data for dev
"""

import argparse
import sqlite3
import json
import re
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent.parent / "data" / "schema.sql"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "salaries.db"

# ---------------------------------------------------------------------------
# Job title → canonical slug mapping via keyword rules
# Order matters: more specific rules first
# ---------------------------------------------------------------------------
JOB_SLUG_RULES = [
    ("machine-learning-engineer",  ["machine learning", "ml engineer", "mlops"]),
    ("data-scientist",             ["data scientist", "data science"]),
    ("data-engineer",              ["data engineer", "etl engineer", "data pipeline"]),
    ("quantitative-analyst",       ["quantitative analyst", "quant analyst", "quantitative researcher"]),
    ("research-scientist",         ["research scientist", "applied scientist", "research engineer"]),
    ("cloud-architect",            ["cloud architect", "solutions architect"]),
    ("devops-engineer",            ["devops", "dev ops", "site reliability", " sre ", "platform engineer"]),
    ("security-engineer",          ["security engineer", "cybersecurity", "information security"]),
    ("database-administrator",     ["database administrator", " dba ", "database engineer"]),
    ("network-engineer",           ["network engineer", "network administrator"]),
    ("full-stack-engineer",        ["full stack", "fullstack", "full-stack"]),
    ("frontend-engineer",          ["front end", "frontend", "front-end", "ui engineer", "ui developer"]),
    ("backend-engineer",           ["back end", "backend", "back-end"]),
    ("software-engineer",          ["software engineer", "software developer", "software dev",
                                    "programmer analyst", " sde ", " swe ", "application developer",
                                    "application engineer", "computer engineer"]),
    ("product-manager",            ["product manager", "product management"]),
    ("it-project-manager",         ["project manager", "it manager"]),
    ("business-analyst",           ["business analyst", "business systems"]),
    ("financial-analyst",          ["financial analyst", "finance analyst"]),
    ("systems-engineer",           ["systems engineer", "systems analyst", "systems administrator"]),
]

SOC_CATEGORY_MAP = {
    "machine-learning-engineer":  "Computer and Information Technology",
    "data-scientist":             "Computer and Information Technology",
    "data-engineer":              "Computer and Information Technology",
    "quantitative-analyst":       "Business and Financial Operations",
    "research-scientist":         "Life, Physical, and Social Science",
    "cloud-architect":            "Computer and Information Technology",
    "devops-engineer":            "Computer and Information Technology",
    "security-engineer":          "Computer and Information Technology",
    "database-administrator":     "Computer and Information Technology",
    "network-engineer":           "Computer and Information Technology",
    "full-stack-engineer":        "Computer and Information Technology",
    "frontend-engineer":          "Computer and Information Technology",
    "backend-engineer":           "Computer and Information Technology",
    "software-engineer":          "Computer and Information Technology",
    "product-manager":            "Business and Financial Operations",
    "it-project-manager":         "Computer and Information Technology",
    "business-analyst":           "Business and Financial Operations",
    "financial-analyst":          "Business and Financial Operations",
    "systems-engineer":           "Architecture and Engineering",
}

JOB_DISPLAY_NAMES = {
    "machine-learning-engineer":  "Machine Learning Engineer",
    "data-scientist":             "Data Scientist",
    "data-engineer":              "Data Engineer",
    "quantitative-analyst":       "Quantitative Analyst",
    "research-scientist":         "Research Scientist",
    "cloud-architect":            "Cloud Architect",
    "devops-engineer":            "DevOps Engineer",
    "security-engineer":          "Security Engineer",
    "database-administrator":     "Database Administrator",
    "network-engineer":           "Network Engineer",
    "full-stack-engineer":        "Full Stack Engineer",
    "frontend-engineer":          "Frontend Engineer",
    "backend-engineer":           "Backend Engineer",
    "software-engineer":          "Software Engineer",
    "product-manager":            "Product Manager",
    "it-project-manager":         "IT Project Manager",
    "business-analyst":           "Business Analyst",
    "financial-analyst":          "Financial Analyst",
    "systems-engineer":           "Systems Engineer",
}

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
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}


def slugify(text: str) -> str:
    text = str(text).lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def clean_employer_slug(name: str) -> str:
    name = str(name).strip()
    name = re.sub(
        r"\b(LLC|LLP|LP|INC\.?|CORP\.?|LTD\.?|CO\.?|PLLC|PC|NA|N\.A\.|PLC)\b\.?",
        "", name, flags=re.IGNORECASE,
    )
    name = re.sub(r",\s*$", "", name)
    return slugify(name)


def clean_employer_display(name: str) -> str:
    name = str(name).strip()
    if not name.isupper():
        return name
    result = name.title()
    for old, new in [("Llc", "LLC"), ("Llp", "LLP"), ("Na", "N.A.")]:
        result = result.replace(old, new)
    return result


def map_job_title(title: str):
    title_lower = " " + title.lower() + " "
    for slug, keywords in JOB_SLUG_RULES:
        for kw in keywords:
            if kw in title_lower:
                return slug
    return None


def percentile(values: list, p: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    idx = (len(values) - 1) * p / 100
    lo = int(idx)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] * (1 - (idx - lo)) + values[hi] * (idx - lo)


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    return conn


# ---------------------------------------------------------------------------
# Real DOL processor
# ---------------------------------------------------------------------------
def process_dol_files(input_dir: str, output_db: str):
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas required.  pip3 install pandas openpyxl")
        return

    input_path = Path(input_dir)
    files = sorted(input_path.glob("*.xlsx")) + sorted(input_path.glob("*.csv"))
    if not files:
        print(f"No files found in {input_dir}")
        return

    print(f"\nReading {len(files)} file(s)...")
    frames = []
    for f in files:
        print(f"  {f.name}  ({f.stat().st_size // 1_000_000} MB)...")
        try:
            if f.suffix == ".xlsx":
                chunk = pd.read_excel(f, dtype=str, engine="openpyxl",
                                      usecols=["CASE_STATUS", "EMPLOYER_NAME",
                                               "JOB_TITLE", "WORKSITE_CITY",
                                               "WORKSITE_STATE", "WAGE_RATE_OF_PAY_FROM",
                                               "WAGE_UNIT_OF_PAY", "BEGIN_DATE"])
            else:
                chunk = pd.read_csv(f, dtype=str, encoding="latin1", low_memory=False,
                                    usecols=lambda c: c.upper() in {
                                        "CASE_STATUS", "EMPLOYER_NAME", "JOB_TITLE",
                                        "WORKSITE_CITY", "WORKSITE_STATE",
                                        "WAGE_RATE_OF_PAY_FROM", "WAGE_UNIT_OF_PAY", "BEGIN_DATE"})
                chunk.columns = [c.upper() for c in chunk.columns]
            frames.append(chunk)
            print(f"    {len(chunk):,} rows")
        except Exception as e:
            print(f"    ERROR: {e}")

    if not frames:
        print("No data loaded.")
        return

    df = pd.concat(frames, ignore_index=True)
    print(f"\nTotal: {len(df):,} rows")

    # Filter
    df = df[df["CASE_STATUS"].str.strip().str.lower() == "certified"]
    df = df[df["WAGE_UNIT_OF_PAY"].str.strip().str.lower() == "year"]
    df["WAGE"] = pd.to_numeric(df["WAGE_RATE_OF_PAY_FROM"], errors="coerce")
    df = df[(df["WAGE"] >= 30_000) & (df["WAGE"] <= 800_000)]
    print(f"After filters: {len(df):,} certified year-wage rows")

    df["FISCAL_YEAR"] = pd.to_datetime(df["BEGIN_DATE"], errors="coerce").dt.year.fillna(2024).astype(int)
    df["EMP_SLUG"]   = df["EMPLOYER_NAME"].fillna("").apply(clean_employer_slug)
    df["EMP_DISP"]   = df["EMPLOYER_NAME"].fillna("").apply(clean_employer_display)
    df["JOB_SLUG"]   = df["JOB_TITLE"].fillna("").apply(map_job_title)
    df = df[df["JOB_SLUG"].notna()]
    df["CITY"]       = df["WORKSITE_CITY"].fillna("").str.strip().str.title()
    df["STATE"]      = df["WORKSITE_STATE"].fillna("").str.strip().str.upper()
    df["LOC_SLUG"]   = (df["CITY"] + "-" + df["STATE"]).apply(slugify)
    df = df[df["LOC_SLUG"].str.len() > 3]
    print(f"After job mapping: {len(df):,} rows")

    # Aggregate
    print("Aggregating...")
    salary_rows   = []
    employer_meta = {}
    location_meta = {}

    for (emp_slug, job_slug, loc_slug), grp in df.groupby(["EMP_SLUG", "JOB_SLUG", "LOC_SLUG"]):
        wages = grp["WAGE"].tolist()
        if len(wages) < 2:
            continue
        median = int(percentile(wages, 50))
        p25    = int(percentile(wages, 25))
        p75    = int(percentile(wages, 75))
        year   = int(grp["FISCAL_YEAR"].max())
        salary_rows.append((emp_slug, job_slug, loc_slug, median, p25, p75,
                             len(wages), SOC_CATEGORY_MAP.get(job_slug), year))

        if emp_slug not in employer_meta:
            r = grp.iloc[0]
            employer_meta[emp_slug] = r["EMP_DISP"]
        if loc_slug not in location_meta:
            r = grp.iloc[0]
            location_meta[loc_slug] = (r["CITY"], r["STATE"])

    print(f"Combinations: {len(salary_rows):,}  |  Employers: {len(employer_meta):,}  |  Cities: {len(location_meta):,}")

    # Write DB
    db_path = Path(output_db)
    if db_path.exists():
        db_path.unlink()
    conn = init_db(output_db)
    cur  = conn.cursor()

    for slug, display in employer_meta.items():
        cur.execute("INSERT OR IGNORE INTO employers (slug, display_name) VALUES (?,?)", (slug, display))
    for slug, display in JOB_DISPLAY_NAMES.items():
        cur.execute("INSERT OR IGNORE INTO jobs (slug, display_name, soc_category) VALUES (?,?,?)",
                    (slug, display, SOC_CATEGORY_MAP.get(slug)))
    for slug, (city, state) in location_meta.items():
        cur.execute("INSERT OR IGNORE INTO locations (slug, city, state, state_full) VALUES (?,?,?,?)",
                    (slug, city, state, STATE_MAP.get(state, state)))

    cur.executemany(
        "INSERT INTO salaries (employer_slug,job_slug,location_slug,median_salary,"
        "p25_salary,p75_salary,sample_count,soc_category,fiscal_year) VALUES (?,?,?,?,?,?,?,?,?)",
        salary_rows,
    )
    conn.commit()

    # Aggregates
    cur.execute("""UPDATE employers SET
        total_h1b_count=(SELECT SUM(sample_count) FROM salaries WHERE employer_slug=employers.slug),
        median_salary=(SELECT CAST(AVG(median_salary) AS INTEGER) FROM salaries WHERE employer_slug=employers.slug),
        top_job_category=(SELECT j.display_name FROM salaries s JOIN jobs j ON s.job_slug=j.slug
                          WHERE s.employer_slug=employers.slug ORDER BY s.sample_count DESC LIMIT 1)""")
    cur.execute("""UPDATE jobs SET
        total_count=(SELECT SUM(sample_count) FROM salaries WHERE job_slug=jobs.slug),
        median_national_salary=(SELECT CAST(AVG(median_salary) AS INTEGER) FROM salaries WHERE job_slug=jobs.slug)""")
    cur.execute("""UPDATE locations SET
        total_count=(SELECT SUM(sample_count) FROM salaries WHERE location_slug=locations.slug),
        median_salary=(SELECT CAST(AVG(median_salary) AS INTEGER) FROM salaries WHERE location_slug=locations.slug)""")
    cur.execute("DELETE FROM employers WHERE total_h1b_count IS NULL OR total_h1b_count=0")
    cur.execute("DELETE FROM locations WHERE total_count IS NULL OR total_count=0")
    conn.commit()

    n_emp  = cur.execute("SELECT COUNT(*) FROM employers").fetchone()[0]
    n_loc  = cur.execute("SELECT COUNT(*) FROM locations").fetchone()[0]
    n_sal  = cur.execute("SELECT COUNT(*) FROM salaries").fetchone()[0]
    n_recs = cur.execute("SELECT SUM(sample_count) FROM salaries").fetchone()[0]
    conn.close()

    print(f"\nDone! {output_db}")
    print(f"  Employers: {n_emp:,}  |  Cities: {n_loc:,}  |  Salary combos: {n_sal:,}  |  Records: {n_recs:,}")
    export_json(output_db)


def export_json(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    data_dir = Path(db_path).parent

    json.dump([dict(r) for r in cur.execute(
        "SELECT slug,display_name,total_h1b_count,median_salary FROM employers ORDER BY total_h1b_count DESC")],
        open(data_dir / "employers.json", "w"))
    json.dump([dict(r) for r in cur.execute(
        "SELECT slug,display_name,soc_category,median_national_salary,total_count FROM jobs ORDER BY total_count DESC")],
        open(data_dir / "jobs.json", "w"))
    json.dump([dict(r) for r in cur.execute(
        "SELECT slug,city,state,state_full,metro_area,median_salary,total_count FROM locations ORDER BY total_count DESC")],
        open(data_dir / "locations.json", "w"))
    conn.close()
    print("Exported employers.json  jobs.json  locations.json")


# ---------------------------------------------------------------------------
# Sample data seeder
# ---------------------------------------------------------------------------
SAMPLE_EMPLOYERS = [
    ("google-llc",                   "Google LLC",                      "Mountain View, CA"),
    ("amazon-com-services-llc",      "Amazon.com Services LLC",         "Seattle, WA"),
    ("microsoft-corporation",        "Microsoft Corporation",           "Redmond, WA"),
    ("meta-platforms",               "Meta Platforms, Inc.",            "Menlo Park, CA"),
    ("apple-inc",                    "Apple Inc.",                      "Cupertino, CA"),
    ("netflix",                      "Netflix, Inc.",                   "Los Gatos, CA"),
    ("uber-technologies",            "Uber Technologies, Inc.",         "San Francisco, CA"),
    ("salesforce",                   "Salesforce, Inc.",                "San Francisco, CA"),
    ("oracle-corporation",           "Oracle Corporation",             "Austin, TX"),
    ("intel-corporation",            "Intel Corporation",               "Santa Clara, CA"),
    ("qualcomm",                     "QUALCOMM Incorporated",           "San Diego, CA"),
    ("jpmorgan-chase",               "JPMorgan Chase Bank, N.A.",       "New York, NY"),
    ("goldman-sachs",                "Goldman Sachs & Co. LLC",         "New York, NY"),
    ("ibm-corporation",              "IBM Corporation",                 "Armonk, NY"),
    ("accenture",                    "Accenture LLP",                   "New York, NY"),
    ("infosys-limited",              "Infosys Limited",                 "Bengaluru, India"),
    ("tata-consultancy-services",    "Tata Consultancy Services",       "Mumbai, India"),
    ("deloitte-consulting",          "Deloitte Consulting LLP",         "New York, NY"),
    ("cognizant-technology-solutions","Cognizant Technology Solutions", "Teaneck, NJ"),
    ("wipro-limited",                "Wipro Limited",                   "Bengaluru, India"),
]
EMPLOYER_BASE = {
    "google-llc": 195000, "amazon-com-services-llc": 187000,
    "microsoft-corporation": 175000, "meta-platforms": 204000,
    "apple-inc": 185000, "netflix": 220000, "uber-technologies": 175000,
    "salesforce": 170000, "oracle-corporation": 155000,
    "intel-corporation": 160000, "qualcomm": 165000,
    "jpmorgan-chase": 150000, "goldman-sachs": 175000,
    "ibm-corporation": 135000, "accenture": 130000,
    "infosys-limited": 95000, "tata-consultancy-services": 90000,
    "deloitte-consulting": 145000, "cognizant-technology-solutions": 92000,
    "wipro-limited": 88000,
}
SAMPLE_LOCS = [
    ("san-francisco-ca","San Francisco","CA",37.77,-122.42),
    ("seattle-wa","Seattle","WA",47.61,-122.33),
    ("new-york-ny","New York","NY",40.71,-74.01),
    ("austin-tx","Austin","TX",30.27,-97.74),
    ("boston-ma","Boston","MA",42.36,-71.06),
    ("chicago-il","Chicago","IL",41.88,-87.63),
    ("los-angeles-ca","Los Angeles","CA",34.05,-118.24),
    ("san-jose-ca","San Jose","CA",37.34,-121.89),
    ("dallas-tx","Dallas","TX",32.78,-96.80),
    ("washington-dc","Washington","DC",38.91,-77.04),
]
JOB_MULT = {
    "software-engineer":1.0,"software-developer":0.95,"data-scientist":1.05,
    "data-engineer":1.02,"machine-learning-engineer":1.15,"product-manager":1.08,
    "devops-engineer":0.98,"cloud-architect":1.12,"full-stack-engineer":0.97,
    "backend-engineer":0.98,"frontend-engineer":0.93,"systems-engineer":0.90,
    "network-engineer":0.85,"security-engineer":1.05,"research-scientist":1.10,
    "financial-analyst":0.85,"business-analyst":0.80,"quantitative-analyst":1.20,
    "it-project-manager":0.88,"database-administrator":0.82,
}
LOC_MULT = {
    "san-francisco-ca":1.15,"san-jose-ca":1.12,"new-york-ny":1.08,
    "seattle-wa":1.05,"boston-ma":1.02,"los-angeles-ca":1.0,
    "washington-dc":0.98,"austin-tx":0.92,"chicago-il":0.90,"dallas-tx":0.87,
}

def seed_sample_data(db_path: str):
    import random
    if Path(db_path).exists():
        Path(db_path).unlink()
    conn = init_db(db_path)
    cur  = conn.cursor()

    for slug, city, state, lat, lng in SAMPLE_LOCS:
        cur.execute("INSERT OR IGNORE INTO locations (slug,city,state,state_full,lat,lng) VALUES (?,?,?,?,?,?)",
                    (slug, city, state, STATE_MAP.get(state, state), lat, lng))
    for slug, display in JOB_DISPLAY_NAMES.items():
        cur.execute("INSERT OR IGNORE INTO jobs (slug,display_name,soc_category) VALUES (?,?,?)",
                    (slug, display, SOC_CATEGORY_MAP.get(slug)))
    for slug, name, hq in SAMPLE_EMPLOYERS:
        cur.execute("INSERT OR IGNORE INTO employers (slug,display_name,hq_city) VALUES (?,?,?)",
                    (slug, name, hq))

    rows = []
    for emp_slug, _, _ in SAMPLE_EMPLOYERS:
        base = EMPLOYER_BASE.get(emp_slug, 120000)
        for job_slug in JOB_DISPLAY_NAMES:
            jm = JOB_MULT.get(job_slug, 1.0)
            for loc_slug, *_ in SAMPLE_LOCS:
                lm = LOC_MULT.get(loc_slug, 0.90)
                rng = random.Random(hash(f"{emp_slug}{job_slug}{loc_slug}"))
                v = int(base * jm * lm * rng.uniform(0.88, 1.12))
                rows.append((emp_slug, job_slug, loc_slug, v,
                              int(v * rng.uniform(0.83, 0.90)),
                              int(v * rng.uniform(1.08, 1.20)),
                              rng.randint(50, 12000),
                              SOC_CATEGORY_MAP.get(job_slug), 2024))

    cur.executemany(
        "INSERT INTO salaries (employer_slug,job_slug,location_slug,median_salary,"
        "p25_salary,p75_salary,sample_count,soc_category,fiscal_year) VALUES (?,?,?,?,?,?,?,?,?)",
        rows)
    conn.commit()

    cur.execute("""UPDATE employers SET
        total_h1b_count=(SELECT SUM(sample_count) FROM salaries WHERE employer_slug=employers.slug),
        median_salary=(SELECT CAST(AVG(median_salary) AS INTEGER) FROM salaries WHERE employer_slug=employers.slug),
        top_job_category=(SELECT j.display_name FROM salaries s JOIN jobs j ON s.job_slug=j.slug
                          WHERE s.employer_slug=employers.slug ORDER BY s.sample_count DESC LIMIT 1)""")
    cur.execute("""UPDATE jobs SET
        total_count=(SELECT SUM(sample_count) FROM salaries WHERE job_slug=jobs.slug),
        median_national_salary=(SELECT CAST(AVG(median_salary) AS INTEGER) FROM salaries WHERE job_slug=jobs.slug)""")
    cur.execute("""UPDATE locations SET
        total_count=(SELECT SUM(sample_count) FROM salaries WHERE location_slug=locations.slug),
        median_salary=(SELECT CAST(AVG(median_salary) AS INTEGER) FROM salaries WHERE location_slug=locations.slug)""")
    conn.commit()
    conn.close()
    print(f"Seeded {len(rows)} salary records → {db_path}")
    export_json(db_path)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input",  help="Directory with DOL Excel/CSV files")
    p.add_argument("--output", default=str(OUTPUT_PATH))
    p.add_argument("--seed",   action="store_true")
    args = p.parse_args()
    if args.seed or not args.input:
        seed_sample_data(args.output)
    else:
        process_dol_files(args.input, args.output)
