-- Cleaned views for the Data Analyst skills dashboard.
-- Load into a READ-ONLY connection; everything here is a TEMP view.
-- Each choice is marked with a status (same labels as CLAUDE.md and SKILL.md). Flip as needed.
--   DECIDED         explicitly approved methodological choice
--   WORKING DEFAULT currently implemented, but subject to review
--   PROPOSED        suggested, not approved or not necessarily implemented
--   OPEN            unresolved methodological question; may have a working default

-- Postings in scope.
create or replace temp view da_us as
select j.*,
       case when j.job_location = 'Anywhere' or j.job_work_from_home then 'Remote'
            when regexp_matches(j.job_location, ', [A-Z]{2}$') then right(j.job_location, 2)
            else 'Other / unknown' end as us_state,
       -- WORKING DEFAULT: keep yearly salaries $25k-$300k, both ends inclusive; outliers become NULL, posting stays.
       case when j.salary_year_avg between 25000 and 300000 then j.salary_year_avg end as salary_clean
from job_postings_fact j
where j.job_country = 'United States'                -- DECIDED: US only (currency)
  and j.job_title ilike '%data analyst%';            -- OPEN; WORKING DEFAULT: title rule. Category alternative:
                                                      --   j.job_title_short = 'Data Analyst'

-- Posting x clean technical skill (deduplicated by skill name).
create or replace temp view da_skills as
select distinct p.job_id, d.skills as skill, d.type
from da_us p
join skills_job_dim s using (job_id)
join skills_dim d using (skill_id)
where d.skills not in ('Go', 'C', 'Ada', 'Narrative')            -- WORKING DEFAULT: text-match false positives
  and (d.type in ('Programming Languages', 'Analytics', 'Infrastructure')
       or d.skills in ('PowerPoint', 'Jira', 'SharePoint', 'Confluence', 'Visio',
                       'Smartsheet', 'Microsoft Power Automate + Copilot'));  -- PROPOSED: hand-picked Applications

-- Per-skill pay and popularity.
create or replace temp view skill_stats as
select k.skill, any_value(k.type) as type,
       count(*) as postings,                                  -- DECIDED: popularity = raw posting count
       count(p.salary_clean) as salaries,
       round(avg(p.salary_clean)) as avg_salary,              -- DECIDED: pay = average yearly salary
       round(median(p.salary_clean)) as median_salary,
       count(p.salary_clean) >= 30 as enough_salaries         -- PROPOSED: show pay only when n >= 30
from da_skills k join da_us p using (job_id)
group by k.skill;

-- Dashboard metrics 1-4 (see references/metrics.md), plus share of postings and remote % per skill.
create or replace temp view skill_metrics as
with base as (
  select count(*) as all_postings, avg(salary_clean) as all_avg_salary from da_us
)
select s.skill, s.type,
       s.postings,                                                        -- 1. skill demand
       round(s.postings / b.all_postings, 4) as share_of_postings,
       s.avg_salary,                                                      -- 2. average salary
       round(s.avg_salary - b.all_avg_salary) as pay_premium,             -- 3. pay premium ($)
       round((s.avg_salary - b.all_avg_salary) / b.all_avg_salary, 4) as pay_premium_pct,
       s.salaries as salary_sample_size,                                  -- 4. salary sample size
       s.enough_salaries,
       r.remote_pct as remote_pct_skill                                   -- optional: remote % per skill
from skill_stats s
cross join base b
join (select k.skill, round(avg(p.job_work_from_home::int), 4) as remote_pct
      from da_skills k join da_us p using (job_id) group by k.skill) r using (skill);

-- Dashboard metric 5: remote % per company. PROPOSED minimum: 20 postings.
create or replace temp view company_remote as
select c.name as company, count(*) as postings,
       sum(p.job_work_from_home::int) as remote_postings,
       round(avg(p.job_work_from_home::int), 4) as remote_pct,
       round(avg(p.job_work_from_home::int) - (select avg(job_work_from_home::int) from da_us), 4) as vs_overall
from da_us p join company_dim c using (company_id)
group by c.name
having count(*) >= 20;
