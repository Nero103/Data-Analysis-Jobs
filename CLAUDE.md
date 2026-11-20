# Data-Analysis-Jobs

A portfolio project by an aspiring data analyst: a dashboard showing which technical tools are worth learning for Data Analyst jobs, judged by **pay** and **popularity**.

## Where things are

- `data_jobs.duckdb` is on the **`main` branch** (about 47 MB). Open it read-only.
- `.claude/skills/data-jobs-dataset/` holds everything learned about the data: schema, data-quality issues, metric definitions, and scripts to fetch, clean and rebuild the dashboard data. Use that skill for any work on this data; it has the details this file leaves out.
- Dashboards (claude.ai artifacts):
  - Data Analyst Skill Explorer, the main dashboard: https://claude.ai/artifact/W4cww43zqM99szxejNtejn
  - Data Analyst Jobs EDA, the exploratory analysis: https://claude.ai/artifact/KfqGK9sVaNTogVm4ftJ9hY

## Decisions made

- Scope is **US postings only**, because other countries have almost no salaries and mixed currencies.
- "Data Analyst" means the job title contains "data analyst", at any seniority. The dashboard can also switch to the source's broader category.
- Popularity is the number of postings mentioning a tool. Pay is the average yearly salary of those postings, with salaries kept only between $25k and $300k.
- Only technical tools are counted. Go, C, Ada and Narrative are removed as text-matching errors.
- Pay and popularity are shown side by side. Don't combine them into a single score.
- Company-level views leave out recruiters, staffing firms, job boards, survey panels and gig platforms.

## Working with the user

- Ask questions one at a time.
- Propose changes to a decided rule rather than switching silently.
- When reporting numbers, say which scope and rules were used, so the method can be defended in a portfolio.
