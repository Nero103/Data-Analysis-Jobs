---
name: data-jobs-dataset
description: Everything learned about the data_jobs.duckdb job-postings database (Data Analyst / Data Engineer / Data Scientist postings with salaries and skills) and the skill pay-vs-popularity dashboard it feeds. Use this whenever you query, clean, explore, chart or build a dashboard from data_jobs.duckdb, job_postings_fact, skills_dim, skills_job_dim or company_dim, or whenever the user asks which data skills pay best or are most in demand, which tools a data analyst should learn, or about salary or skill counts from job postings in this repo, even if they don't name the database.
---

# Data jobs dataset

This skill holds what is already known about `data_jobs.duckdb`, so you don't have to re-run discovery. It also records the goals of the dashboard it feeds and the decisions the user has made. Numbers below come from an EDA run in Nov 2026. If the database changes, re-check them with `scripts/inspect.py`.

## The dashboard this data serves

The user is an aspiring data analyst choosing which skills to learn. They care about **pay** and **popularity**. The decisions they made, in order:

| Area | Decision |
|---|---|
| Main question | Is this tool worth learning? (look up a skill and judge it) |
| How it answers | Pay and popularity side by side, with no combined score; the user makes the call |
| Jobs counted | Data Analyst titles only, at any seniority level |
| Location | Several places, with a location filter. **For now, US only**, to avoid mixed currencies |
| Popularity | Raw count of postings that mention the skill |
| Pay | Average yearly salary of postings that mention the skill |
| Skills covered | Technical tools only (SQL, Python, Excel, Tableau, Power BI, etc.) |
| Layout | One sortable table of tools, with posting count and average pay as columns |
| Audience | The user, and also a portfolio piece for employers, so polish and a short method note matter |

Respect these. If an analysis seems to need a different choice, such as the median instead of the average, propose it and let the user decide, rather than switching silently. The user likes questions asked one at a time.

## Getting the data

The database lives on the **`main` branch** as `data_jobs.duckdb` (about 47 MB, not the 30 MB once mentioned). Feature branches may not have it. Copy it out without touching the working branch, and always open it read-only:

```bash
bash .claude/skills/data-jobs-dataset/scripts/get_db.sh <dest_dir>   # writes <dest_dir>/data_jobs.duckdb
```

Python's `duckdb` may not be installed (`pip install duckdb pandas`). With duckdb 2.x, a relation has no `.fetchone()`: use `.fetchall()[0][0]`, or `.df()`.

## Shape of the data

Four tables in a star schema: one fact table of postings, a skills bridge, and two dimension tables. Full column lists are in `references/schema.md`.

- `job_postings_fact` has 491,140 postings. It holds title, `job_title_short` (one of Data Analyst, Data Engineer or Data Scientist), location, country, a remote flag, posted date, `salary_rate`, `salary_year_avg` and `salary_hour_avg`.
- `skills_job_dim` has 3.16M (job_id, skill_id) pairs, with no duplicates and no orphans.
- `skills_dim` has 960 skills, each with a `type`: Programming Languages, Analytics, Infrastructure, Applications, Machine Learning & AI, Data Sources & APIs, or Data & AI Consulting.
- `company_dim` has 65,970 companies.
- Postings run from 2025-07-01 to 2026-06-30, cover 171 countries, and are steady month to month.

US Data Analyst slice (source category = Data Analyst, country = United States):

| Figure | Value |
|---|---|
| Postings | 64,268 |
| With at least one skill linked | 48,515 (75%) |
| With yearly salary | 12,567 (20%) |
| With hourly salary only | 3,604 |
| Remote (work-from-home flag) | 1,591 |
| Skills mentioned | 620 |
| Top skills by postings | SQL 28,210 · Excel 19,946 · Python 17,131 · Power BI · Tableau |

## Data-quality issues and how to handle them

Each item says what's wrong, why it matters, and what to do about it. "Decided" means the user agreed. "Proposed" means it's recommended but not yet confirmed, so confirm with the user before relying on it in anything final.

1. **Currencies (decided: US only).** Outside the US there are almost no salaries: the UK has 16, Spain 3. Values that do exist are a mix. So filter `job_country = 'United States'` for pay. A location filter should mean US states plus Remote, not countries.
2. **Who counts as a Data Analyst (open decision).** The source's `job_title_short = 'Data Analyst'` category is broad: about half its US postings are titled Business Analyst, BI Analyst, plain "Analyst" or even Data Scientist. The stricter rule, `job_title ILIKE '%data analyst%'` across all categories, gives 39,519 US postings with 7,986 yearly salaries, versus 64,268 and 12,567 for the category. The user asked for "Data Analyst titles only", which points to the title rule, but they haven't explicitly confirmed it. Show the effect or ask before you pick one.
3. **False skill matches (proposed: exclude).** Skills were extracted by text matching. So `Go`, `C`, `Ada` and `Narrative` fire on ordinary words ("go", "C-level", "ADA compliance", "narrative"). They appear on unrelated postings such as "Senior Business Analyst", and would otherwise rank in the top 15. Also, four names appear twice under different ids (Red Hat, IBM Watson, Hugging Face, IBM Db2), so group by name, not id.
4. **Which types are "technical tools" (proposed).** Keep Programming Languages, Analytics and Infrastructure. Applications mixes real tools (PowerPoint, Jira, SharePoint, Confluence, Visio, Smartsheet, Power Automate) with noise (Zoom, Outlook, Outreach, Momentum, Microsoft Teams), so hand-pick from it. ML & AI, Data Sources and Consulting are mostly noise for this role.
5. **Salary outliers (proposed: keep $25k–$300k, both ends inclusive).** The spread of `salary_year_avg` depends on the population, so always name it:

   | Population | Yearly salaries | Min | Max | Middle 50% | Below $25k | Above $300k |
   |---|---|---|---|---|---|---|
   | All countries, all postings | 60,848 | $15,360 | $900,000 | $105k–$170k | 167 | 437 |
   | US, source category (`job_title_short = 'Data Analyst'`) | 12,567 | $16,000 | $900,000 | $80k–$125k | 41 | 36 |
   | US, title rule (`job_title ILIKE '%data analyst%'`) | 7,986 | $16,000 | $800,000 | $77.5k–$120k | 37 | 12 |

   So 77 yearly salaries fall outside the range for the US source category, and 49 for the US title rule. The title rule is the currently implemented default in `scripts/clean_views.sql` and the main dashboard, but its methodological status is still an open decision (see issue 2). The range is inclusive: `salary_year_avg BETWEEN 25000 AND 300000` keeps exactly $25,000 (5 postings under the title rule, 7 in the category) and exactly $300,000 (none at present). There are $900k "PowerBI Developer" and "Team Lead" postings, which are clearly entry errors, and averages are sensitive to them.
6. **Salary periods.** `salary_rate` is year, hour, month, week, day or NULL, and NULL is about 74% of US postings. Only year (`salary_year_avg`) and hour (`salary_hour_avg`) carry amounts; month, week and day rows have none. The proposal is to convert hourly × 2,080 to yearly, which adds about 30% more salary data. That isn't decided, so keep hourly separate unless the user agrees.
7. **Thin salary samples (proposed: show n, hide below 30).** Of 620 skills, about 130 have 30 or more yearly salaries and about 63 have 100 or more. Always show how many salaries sit behind an average, and grey out or hide skills below the minimum.
8. **Missing skills.** 25% of postings link to no skill. Count popularity as postings that mention the skill. Don't use share of all postings unless you say what the denominator is.
9. **Location parsing.** `job_location` ending in `, XX` gives a US state for 93% of US postings. "Anywhere", "United States" and blanks don't parse; route "Anywhere" and `job_work_from_home` to Remote.

`scripts/clean_views.sql` creates temp views that apply all of the above, with each choice clearly marked so you can flip it. Use it as the starting point for any analysis, and tell the user which choices were applied. With every proposed choice applied (title rule, US only, $25k–$300k, technical tools, no false matches), you get 39,519 postings, 7,937 usable salaries and 313 skills, of which 71 have 30 or more salaries. The top six are SQL, Excel, Python, Power BI, Tableau and R.

## Metrics

Five metric definitions are recorded in `references/metrics.md`, each with its formula, the comparisons to show and caveats. Read that file before computing, charting or explaining any of them.

| Metric | Formula, in short | Status |
|---|---|---|
| Skill demand | postings mentioning the tool | Decided (popularity column) |
| Average salary | `AVG(salary_year_avg)` of those postings, $25k–$300k | Decided (pay column) |
| Pay premium | tool average − overall average | Proposed |
| Salary sample size | count of salaries behind the average; show the average only at 30 or more | Proposed |
| Remote % per company | remote postings ÷ company postings, employers with 20+ postings, recruiters and job platforms excluded | Requested; see caveats |
| Postings per week | postings ÷ weeks covered (~52.1) | Requested (KPI card) |
| Hybrid share | share of job titles saying "hybrid"; a floor, since there is no hybrid field | Requested (KPI card) |

## Working with it

- **Quick look at what's there**: `python3 -I scripts/inspect.py <db>` lists tables, schemas, row counts and 5 sample rows each.
- **Cleaned base for analysis**: load `scripts/clean_views.sql` into a read-only connection. It defines `da_us` (US postings in scope), `da_skills` (posting × clean technical skill), `skill_stats` (per-skill postings, salary count, average and median pay), `skill_metrics` (metrics 1–4 plus share of postings and remote % per skill) and `company_remote` (metric 5).
- **EDA aggregates for a dashboard**: `python3 -I scripts/build_eda.py <db> <out_dir>` writes one JSON per dataset (overview, salary_rate, salary_hist, skills, states, monthly, title_rule). Each file is `{rows, meta}`, with the script's own source embedded in `meta`, so a dashboard's Sources panel shows how every number was made. These files fed the existing EDA dashboard (claude.ai artifact "Data Analyst Jobs EDA"). Re-run the script and re-upload the files to refresh it.
- **Data for the main dashboard**: `python3 -I scripts/build_dashboard.py <db> <out_dir>` writes `baseline.json`, `skill_metrics.json` and `company_remote.json`. They hold all five metrics, precomputed for both Data Analyst definitions (`scope` = title or category) and every location with 300 or more postings, so the page can filter without a query. They feed the claude.ai dashboard "Data Analyst Skill Explorer" (https://claude.ai/artifact/W4cww43zqM99szxejNtejn). Its filters are `scope` and `location`; the default is title rule, All US. To refresh it, re-run the script and re-upload the files.

When you report numbers, say which scope you used: category vs. title rule, US only, the salary range, and whether suspect skills were excluded. These choices change rankings, and the user is learning to defend their method in a portfolio.
