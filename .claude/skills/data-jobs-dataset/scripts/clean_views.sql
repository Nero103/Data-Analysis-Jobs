-- Cleaned views for the Data Analyst skills dashboard.
-- Load into a READ-ONLY connection; everything here is a TEMP view.
-- Each choice is marked DECIDED (user agreed) or PROPOSED (confirm with the user). Flip as needed.

-- Postings in scope.
create or replace temp view da_us as
select j.*,
       case when j.job_location = 'Anywhere' or j.job_work_from_home then 'Remote'
            when regexp_matches(j.job_location, ', [A-Z]{2}$') then right(j.job_location, 2)
            else 'Other / unknown' end as us_state,
       -- PROPOSED: keep yearly salaries in a sensible range; outliers become NULL, posting stays.
       case when j.salary_year_avg between 25000 and 300000 then j.salary_year_avg end as salary_clean
from job_postings_fact j
where j.job_country = 'United States'                -- DECIDED: US only (currency)
  and j.job_title ilike '%data analyst%';            -- OPEN: title rule. Category alternative:
                                                      --   j.job_title_short = 'Data Analyst'

-- Posting x clean technical skill (deduplicated by skill name).
create or replace temp view da_skills as
select distinct p.job_id, d.skills as skill, d.type
from da_us p
join skills_job_dim s using (job_id)
join skills_dim d using (skill_id)
where d.skills not in ('Go', 'C', 'Ada', 'Narrative')            -- PROPOSED: text-match false positives
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
