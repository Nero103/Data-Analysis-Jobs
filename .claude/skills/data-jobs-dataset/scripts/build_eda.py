# Builds the US-only EDA aggregates for the Data Analyst jobs dashboard.
# Input: data_jobs.duckdb (opened read-only). Output: one JSON file per dataset.
import duckdb, json, sys, os, math
db, out = sys.argv[1], sys.argv[2]
con = duckdb.connect(db, read_only=True)
SRC = open(__file__).read()

# Scope: US postings in the source's "Data Analyst" category.
con.sql("""create temp view da as select * from job_postings_fact
           where job_title_short = 'Data Analyst' and job_country = 'United States'""")
SUSPECT = ['Go', 'C', 'Ada', 'Narrative']  # likely text-match errors (e.g. "go", "C-level", "ADA compliance")

def rows(sql):
    r = con.sql(sql)
    cols = r.columns
    return [{c: (None if isinstance(v, float) and math.isnan(v) else (str(v) if hasattr(v, 'isoformat') else v))
             for c, v in zip(cols, t)} for t in r.fetchall()]

def save(name, data, note):
    meta = [{"label": "build_eda.py", "value": SRC, "type": "code", "lang": "python"},
            {"label": "Input", "value": "data_jobs.duckdb (main branch of the Data-Analysis-Jobs repo), opened read-only"},
            {"label": "Scope", "value": note}]
    with open(os.path.join(out, name + ".json"), "w") as f:
        json.dump({"rows": data, "meta": meta}, f)

US_DA = "US postings where job_title_short = 'Data Analyst'"

save("overview", rows("""
  select count(*) as postings,
         count(*) filter (where job_id in (select job_id from skills_job_dim)) as with_skills,
         count(salary_year_avg) as yearly_salary,
         count(salary_hour_avg) as hourly_salary,
         count(salary_rate) as any_salary_rate,
         count(*) filter (where job_work_from_home) as remote_postings,
         count(*) filter (where salary_year_avg < 25000 or salary_year_avg > 300000) as yearly_outside_range,
         min(job_posted_date) as first_date, max(job_posted_date) as last_date
  from da"""), US_DA)

save("salary_rate", rows("""
  select coalesce(salary_rate, 'not listed') as rate, count(*) as postings,
         count(coalesce(salary_year_avg, salary_hour_avg)) as with_amount
  from da group by 1 order by postings desc"""), US_DA)

save("salary_hist", rows("""
  select least(floor(salary_year_avg / 20000) * 20000, 400000)::int as bin_start,
         count(*) as postings
  from da where salary_year_avg is not null group by 1 order by 1"""),
  US_DA + "; yearly salaries in $20k bins, the last bin holds everything from $400k up")

save("skills", rows(f"""
  select d.skills as skill, d.type,
         count(*) as postings,
         count(salary_year_avg) as salaries,
         round(avg(salary_year_avg)) as avg_salary,
         round(median(salary_year_avg)) as median_salary,
         d.skills in ({",".join("'"+s+"'" for s in SUSPECT)}) as suspect
  from skills_job_dim s join da using (job_id) join skills_dim d using (skill_id)
  group by d.skills, d.type order by postings desc"""),
  US_DA + "; one row per skill, salary = salary_year_avg; suspect = likely text-match error")

save("states", rows("""
  select case when job_location in ('Anywhere') or job_work_from_home then 'Remote'
              when regexp_matches(job_location, ', [A-Z]{2}$') then right(job_location, 2)
              else 'Other / unknown' end as state,
         count(*) as postings, count(salary_year_avg) as salaries, round(avg(salary_year_avg)) as avg_salary
  from da group by 1 order by postings desc"""),
  US_DA + "; state parsed from job_location ending in ', XX'; remote = work-from-home flag or 'Anywhere'")

save("monthly", rows("""
  select strftime(job_posted_date, '%Y-%m') as month, count(*) as postings,
         count(salary_year_avg) as with_salary
  from da group by 1 order by 1"""), US_DA)

save("title_rule", rows("""
  select 'Source category is Data Analyst' as rule, count(*) as postings, count(salary_year_avg) as yearly_salary
    from da
  union all
  select 'Title contains \"data analyst\"', count(*), count(salary_year_avg)
    from job_postings_fact where job_country = 'United States' and job_title ilike '%data analyst%'
  union all
  select 'Category only (title lacks it)', count(*), count(salary_year_avg)
    from da where job_title not ilike '%data analyst%'
"""), "US postings; compares the source's role category with a title-text rule")
print("ok")
