# Internal Linking Strategy

## Rules

### Company Pages (`/company/[slug]`)
- Link to top 10 job titles at that company (by sample count) → `/salary/[company]/[job]`
- Link to top 5 cities where that company hires → `/location/[slug]`

### Job Pages (`/job/[slug]`)
- Link to top 10 companies hiring for that role (by sample count) → `/salary/[company]/[job]`
- Link to top 5 cities for that role → `/location/[slug]`

### Salary Pages (`/salary/[company]/[job]`)
- Link to 5 similar companies for the same role → `/salary/[otherCompany]/[job]`
- Link to 3 other roles at the same company → `/salary/[company]/[otherJob]`
- Link to city breakdown pages → `/location/[slug]`
- Breadcrumb: Home → Company → Job

### Location Pages (`/location/[slug]`)
- Link to top 10 employers in city → `/company/[slug]`
- Link to top 10 job titles in city → `/job/[slug]`

## SEO Content Formula (Salary Pages)

```
H1: "[Company] [Job Title] Salary — H1B Data [Year]"
Subhead: "Based on [N] verified H1B applications"
Big number: $[median] (huge font, first above fold)
Salary range: p25 – median – p75 visual bar
Stats box: Median, Range, Applications, Latest Data, Cities
Comparison table: Same job, top 10 companies by sample count
City breakdown table: Top cities sorted by median
About data explainer (2 paragraphs)
CTA: LinkedIn Jobs affiliate link
Internal links panel
```

## Anchor Text Rules
- Avoid generic anchors like "click here" or "read more"
- Use descriptive anchors: "[Company] [Job Title] salary", "[City] H1B data"
- Include the salary amount in anchor when possible
