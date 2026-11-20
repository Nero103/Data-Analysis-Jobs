# Builds the data files for the Data Analyst Skill Explorer dashboard.
# Metrics follow references/metrics.md; cleaning rules follow clean_views.sql, computed here for
# both "Data Analyst" definitions (scope = title | category) and every location with enough postings.
# Usage: python3 -I build_dashboard.py <data_jobs.duckdb> <out_dir>
import duckdb, json, math, os, sys

db, out = sys.argv[1], sys.argv[2]
con = duckdb.connect(db, read_only=True)
SRC = open(__file__).read()
MIN_LOCATION_POSTINGS = 300   # locations below this are left out of the filter
MIN_SALARIES = 30             # PROPOSED: show pay only with >= 30 salaries
MIN_COMPANY_POSTINGS = 20     # PROPOSED: remote % only for companies with >= 20 postings

con.execute("""
create temp view p as
select s.scope, j.job_id, j.company_id, j.job_work_from_home::int as remote,
       case when j.job_location = 'Anywhere' or j.job_work_from_home then 'Remote'
            when regexp_matches(j.job_location, ', [A-Z]{2}$') then right(j.job_location, 2)
            else 'Other / unknown' end as state,
       case when j.salary_year_avg between 25000 and 300000 then j.salary_year_avg end as salary
from job_postings_fact j, (values ('title'), ('category')) s(scope)
where j.job_country = 'United States'
  and ((s.scope = 'title' and j.job_title ilike '%data analyst%')
    or (s.scope = 'category' and j.job_title_short = 'Data Analyst'));

-- every posting counted under 'All US' and under its own state
create temp view pl as
select *, 'All US' as location from p
union all select *, state as location from p where state <> 'Other / unknown';

create temp view k as
select distinct s.job_id, d.skills as skill, d.type
from skills_job_dim s join skills_dim d using (skill_id)
where d.skills not in ('Go', 'C', 'Ada', 'Narrative')
  and (d.type in ('Programming Languages', 'Analytics', 'Infrastructure')
       or d.skills in ('PowerPoint', 'Jira', 'SharePoint', 'Confluence', 'Visio',
                       'Smartsheet', 'Microsoft Power Automate + Copilot'));

create temp table base as
select scope, location, count(*) as postings, count(salary) as salaries,
       round(avg(salary)) as avg_salary, round(avg(remote), 4) as remote_pct
from pl group by all having count(*) >= MIN_LOCATION_POSTINGS;
""".replace("MIN_LOCATION_POSTINGS", str(MIN_LOCATION_POSTINGS)))

def rows(sql):
    r = con.sql(sql)
    return [{c: (None if isinstance(v, float) and math.isnan(v) else v) for c, v in zip(r.columns, t)}
            for t in r.fetchall()]

def save(name, data, scope_note):
    meta = [{"label": "build_dashboard.py", "value": SRC, "type": "code", "lang": "python"},
            {"label": "Input", "value": "data_jobs.duckdb (main branch of the Data-Analysis-Jobs repo), opened read-only"},
            {"label": "Scope", "value": scope_note}]
    with open(os.path.join(out, name + ".json"), "w") as f:
        json.dump({"rows": data, "meta": meta}, f, separators=(",", ":"))
    print(name, len(data), "rows", os.path.getsize(os.path.join(out, name + ".json")), "bytes")

COMMON = ("US postings only. scope 'title' = job title contains 'data analyst'; scope 'category' = source "
          "category Data Analyst. Yearly salaries kept between $25k and $300k. Technical tools only; "
          "Go, C, Ada and Narrative removed as text-matching errors.")

save("baseline", rows("select * from base order by scope, postings desc"),
     COMMON + f" One row per definition and location (locations with {MIN_LOCATION_POSTINGS}+ postings).")

save("skill_metrics", rows(f"""
  select pl.scope, pl.location, k.skill, any_value(k.type) as type,
         count(*) as postings,
         round(count(*) / any_value(b.postings), 4) as share_of_postings,
         round(avg(pl.salary)) as avg_salary,
         round(avg(pl.salary) - any_value(b.avg_salary)) as pay_premium,
         round((avg(pl.salary) - any_value(b.avg_salary)) / any_value(b.avg_salary), 4) as pay_premium_pct,
         count(pl.salary) as salaries,
         count(pl.salary) >= {MIN_SALARIES} as enough_salaries,
         round(avg(pl.remote), 4) as remote_pct
  from pl join k using (job_id) join base b using (scope, location)
  group by pl.scope, pl.location, k.skill
  order by pl.scope, pl.location, postings desc"""),
  COMMON + " Metrics 1-4 per tool: postings, share of postings, average salary, pay premium vs the "
  f"location's average, salary sample size (enough = {MIN_SALARIES}+), and remote % per tool.")

save("company_remote", rows(f"""
  select p.scope, c.name as company, count(*) as postings, sum(p.remote) as remote_postings,
         round(avg(p.remote), 4) as remote_pct,
         round(avg(p.remote) - any_value(b.remote_pct), 4) as vs_overall
  from p join company_dim c using (company_id)
  join base b on b.scope = p.scope and b.location = 'All US'
  group by p.scope, c.name having count(*) >= {MIN_COMPANY_POSTINGS}
  order by p.scope, remote_pct desc, postings desc"""),
  COMMON + f" Metric 5: remote % per company, companies with {MIN_COMPANY_POSTINGS}+ postings, all US locations.")
