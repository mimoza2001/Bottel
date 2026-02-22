# H1B Salary Database

A fast, beautiful, free H1B salary search tool built on US Department of Labor public disclosure data.

## What It Does

The US DOL publishes every H1B visa salary disclosure publicly. This site makes that data searchable and beautiful:

- 2M+ salary records from DOL H1B LCA filings (FY2021–FY2024)
- Search any company + job title + city combination
- No login, no paywall, updated weekly

## Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js (App Router, Static Generation) |
| Database | SQLite via `better-sqlite3` |
| Hosting | Vercel |
| Styling | Tailwind CSS |
| Automation | n8n workflows |
| Data source | [DOL OFLC Performance Data](https://www.dol.gov/agencies/eta/foreign-labor/performance) |

## URL Structure

```
/                              Homepage + search
/company/[slug]                All salaries for a company
/job/[slug]                    All salaries for a job title
/location/[slug]               All salaries in a city
/salary/[company]/[job]        The money pages — specific company+job combo
```

## Quick Start

```bash
# Install dependencies
npm install

# Seed sample data (for development)
python3 scripts/process_h1b_data.py --seed

# Run dev server
npm run dev

# Build static site
npm run build
```

## Processing Real DOL Data

1. Download H1B disclosure files from https://www.dol.gov/agencies/eta/foreign-labor/performance
2. Place Excel files in a directory (e.g., `/downloads/`)
3. Run: `python3 scripts/process_h1b_data.py --input /downloads/ --output data/salaries.db`
4. Rebuild the Next.js site

## n8n Automation Workflows

See `/n8n-workflows/` for importable workflow JSON files:

| File | Purpose |
|------|---------|
| `01-weekly-data-refresh.json` | Fetch new DOL data every Monday, process, trigger rebuild |
| `02-reddit-launch.json` | Launch day Reddit posting campaign |
| `03-twitter-launch.json` | Launch day Twitter thread |
| `05-seo-monitoring.json` | Weekly Google Search Console analysis |

### Required n8n Environment Variables

```
VERCEL_DEPLOY_HOOK_URL=https://api.vercel.com/v1/integrations/deploy/...
ADMIN_EMAIL=you@example.com
SITE_URL=https://h1bsalary.info
GSC_SITE_URL=https://h1bsalary.info
```

## Deployment (Vercel)

```bash
npm i -g vercel
vercel --prod
```

Set `NEXT_PUBLIC_SITE_URL=https://yourdomain.com` in the Vercel dashboard.

## Data Accuracy

All salary figures come from US Department of Labor H1B LCA filings. Employers are **legally required** to disclose exact wages in these applications — verified government data, not survey estimates.

Source: https://www.dol.gov/agencies/eta/foreign-labor/performance
