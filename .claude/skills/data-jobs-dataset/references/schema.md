# data_jobs.duckdb schema

All columns are nullable. Joins: `job_postings_fact.job_id = skills_job_dim.job_id`, `skills_job_dim.skill_id = skills_dim.skill_id`, `job_postings_fact.company_id = company_dim.company_id`.

## job_postings_fact (491,140 rows, one per posting)

| Column | Type | Notes |
|---|---|---|
| job_id | INTEGER | Unique, no duplicates |
| company_id | INTEGER | → company_dim |
| job_title_short | VARCHAR | Data Engineer 298,184 · Data Analyst 123,655 · Data Scientist 69,301. A broad category, not the title |
| job_title | VARCHAR | Free text as posted |
| job_location | VARCHAR | "Austin, TX", "Anywhere", "United States", or foreign city strings; null for ~1% |
| job_via | VARCHAR | Job board (BeBee, Snagajob, Built In, ...) |
| job_schedule_type | VARCHAR | Full-time, Part-time, Contractor, combos |
| job_work_from_home | BOOLEAN | Remote flag; in US DA postings it equals location "Anywhere" |
| search_location | VARCHAR | Where the scraper searched; not the job's location |
| job_posted_date | DATE | 2025-07-01 to 2026-06-30 |
| job_no_degree_mention | BOOLEAN | |
| job_health_insurance | BOOLEAN | |
| job_country | VARCHAR | Always filled for DA; 171 distinct |
| salary_rate | VARCHAR | year / hour / month / week / day / NULL |
| salary_year_avg | DOUBLE | Only when salary_rate = 'year' |
| salary_hour_avg | DOUBLE | Only when salary_rate = 'hour' |

## skills_job_dim (3,159,600 rows)

`job_id`, `skill_id`. One row per skill mentioned in a posting. No duplicate pairs, no orphan skill ids. US DA postings average 4.3 skills (median 4, max 40).

## skills_dim (960 rows)

`skill_id`, `skills` (name), `type`.

| type | skills |
|---|---|
| Infrastructure | 315 |
| Machine Learning & Artificial Intelligence | 224 |
| Applications | 201 |
| Programming Languages | 87 |
| Analytics | 69 |
| Data Sources & APIs | 46 |
| Data & AI Consulting | 18 |

Duplicate names under two ids: Red Hat, IBM Watson, Hugging Face, IBM Db2 (case-insensitive).

## company_dim (65,970 rows)

`company_id`, `name`. Some names carry literal quotes or start with "#".

## Salary coverage by country (DA category, yearly salaries)

United States 12,567 · UAE 202 · Zimbabwe 104 · Canada 80 · Puerto Rico 63 · India 48 · Malaysia 44 · Philippines 36 · everyone else fewer. The UK has 9,165 DA postings but only 16 salaries.
