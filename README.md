# H1B Salary Database

A fast, beautiful, free H1B salary search tool built on US Department of Labor public disclosure data.

## What It Does

The US DOL publishes every H1B visa salary disclosure publicly. This site makes that data searchable and beautiful:

- 2M+ salary records from DOL H1B LCA filings (FY2021–FY2024)
- Search any company + job title + city combination
- No login, no paywall, updated weekly

---

## Step 1 — Prerequisites (install once)

You need two free programs:

1. **Node.js** — download from https://nodejs.org (click "LTS" version)
2. **Python 3** — download from https://python.org/downloads

After installing, open your terminal (Mac: press Cmd+Space, type "Terminal"; Windows: press Win+R, type "cmd") and verify:

```
node --version    # should print v18 or higher
python3 --version # should print 3.8 or higher
```

---

## Step 2 — First-time setup

Open terminal in this project folder and run one command:

```bash
bash setup.sh
```

This installs all code dependencies and seeds the database with sample data. Takes about 2 minutes. You only need to do this once.

---

## Step 3 — Preview the site locally

```bash
npm run dev
```

Then open http://localhost:3000 in your browser. You'll see the full site with sample data.

Press Ctrl+C in the terminal to stop the server.

---

## Step 4 — Load real DOL data (2 million records)

```bash
# Download the actual government files
python3 scripts/download_dol_data.py

# Process them into the database
python3 scripts/process_h1b_data.py --input downloads/ --output data/salaries.db

# Rebuild the site with real data
npm run build
```

Each Excel file from DOL is ~100MB and contains 500,000+ salary records.

---

## Step 5 — Deploy to the internet (free)

1. Create a free account at https://vercel.com
2. Install the Vercel tool: `npm i -g vercel`
3. Run: `vercel --prod`
4. Follow the prompts — it will give you a live URL

Your site will be live at something like `your-project.vercel.app`.

To use a custom domain: buy one (e.g., from Namecheap), add it in the Vercel dashboard under Project → Settings → Domains.

---

## Step 6 — Set up automated weekly data refresh (n8n)

1. Create a free account at https://n8n.io (cloud version)
2. In n8n: click "Import workflow" and upload each file from the `n8n-workflows/` folder
3. Set these environment variables in your n8n instance:

```
VERCEL_DEPLOY_HOOK_URL   → get from Vercel: Project → Settings → Git → Deploy Hooks
ADMIN_EMAIL              → your email address
SITE_URL                 → your live domain
```

4. Activate the "H1B Weekly Data Refresh" workflow — it will now run every Monday at 3am automatically

---

## URL Structure

Every page type is auto-generated:

```
/                              Homepage with search
/company/google-llc            Google's salary data
/job/software-engineer         Software Engineer salaries everywhere
/location/seattle-wa           All salaries in Seattle
/salary/google-llc/software-engineer   The money page — Google SWE salary
```

---

## n8n Automation Workflows

| File | What it does |
|------|-------------|
| `01-weekly-data-refresh.json` | Downloads new DOL data every Monday, updates site |
| `02-reddit-launch.json` | Posts to r/cscareerquestions, r/dataisbeautiful, r/personalfinance on launch day |
| `03-twitter-launch.json` | Posts a salary data thread on Twitter/X on launch day |
| `05-seo-monitoring.json` | Sends weekly Google Search Console report to your email |

---

## Data Accuracy

All salary figures come from US Department of Labor H1B LCA filings. Employers are **legally required** to disclose exact wages in these applications — verified government data, not survey estimates.

Source: https://www.dol.gov/agencies/eta/foreign-labor/performance
