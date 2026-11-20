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

# Recruiters, staffing firms, job boards, survey panels and gig platforms post on behalf of others,
# so they are flagged (intermediary = true) and the dashboard leaves them out of the company chart.
# Reviewed by hand from every company with 20+ US Data Analyst postings (Nov 2026).
# Names starting with "beBee" are job-board feeds and are matched by prefix.
INTERMEDIARIES = [
    # job boards and aggregators
    "Jobs via Dice", "Jobs via eFinancialCareers", "VirtualVocations", "Virtual Vocations Inc", "Lensa",
    "Jobright.ai", "Jobgether", "ExecutivePlacements.com", "TalentAlly", "TradeJobsWorkforce", "Cosmoquick",
    "Inside Higher Ed", "InsideHigherEd", "ClearanceJobs", "Clearance Jobs", "WhatJobs Direct", "Whatjobs",
    "Mediabistro", "WayUp", "RippleMatch", "TieTalent", "buscojobs España", "Career.zycto", "Various Employers",
    "Confidential", "SoTalent", "The Elite Job", "vmysmartpros", "remotepromsp", "Earn Haus",
    # survey panels and gig / data-annotation marketplaces
    "Online Surveys", "Focus Group Panel", "FocusGroupPanel", "PartTime Panel", "Apex Focus Group",
    "Surprise Insights", "Maxion Research", "Upwork", "Data Annotation", "DataAnnotation", "Outlier AI",
    "Alignerr", "AfterQuery", "Clerk Crew",
    # recruiters and staffing firms
    "Robert Half", "Insight Global", "SynergisticIT", "Synergisticit", "Quality Talent Group", "Diverse Lynx",
    "Staffmark", "Kforce Inc", "Brooksource", "Two95 International Inc.", "Apex Systems", "Eliassen Group",
    "Trigyn", "Harnham", "Kelly Services", "Yoh, A Day & Zimmermann Company", "Dexian", "Net2Source (N2S)",
    "US Tech Solutions", "IT Resource Solutions", "Experis", "TEKsystems", "Talent Groups", "Motion Recruitment",
    "Compunnel Inc.", "Trident Consulting", "Jobsultant Solutions", "Mindlance", "INSPYR Solutions", "PTR Global",
    "Asta CRS Inc.", "Akkodis", "RIT Solutions, Inc.", "KellyMitchell Group", "Aditi Consulting",
    "Rose International", "Strategic Staffing Solutions", "Russell Tobin", "Global Channel Management, Inc.",
    "The Judge Group", "Aston Carter", "Tech Consulting", "New York Technology Partners", "Upen Group Inc",
    "My3Tech", "Harvey Nash", "Cypress HCM", "IDR, Inc.", "Addison Group", "Ampstek", "BCforward", "SPECTRAFORCE",
    "The Dignify Solutions, LLC", "Smart IT Frame LLC", "Pyramid Consulting, Inc", "System One", "Stellent IT LLC",
    "eTeam", "Randstad Digital Americas", "Vaco by Highspring", "Horizontal Talent", "ApTask",
    "DivIHN Integration Inc", "LHH", "Swoon", "Lorven Technologies", "Aquent Talent", "Aquent", "Jobot",
    "Staffing the Universe",
]
con.execute("create temp table intermediaries (name varchar)")
con.executemany("insert into intermediaries values (?)", [[n] for n in INTERMEDIARIES])

con.execute("""
-- weeks covered by the data, from the first to the last US posting date
create temp table span as
select (date_diff('day', min(job_posted_date), max(job_posted_date)) + 1) / 7.0 as weeks
from job_postings_fact where job_country = 'United States';

create temp view p as
select s.scope, j.job_id, j.company_id, j.job_work_from_home::int as remote,
       (j.job_title ilike '%hybrid%')::int as hybrid,   -- no hybrid field exists; the title is the only signal
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
select scope, location, count(*) as postings,
       round(count(*) / any_value(span.weeks), 1) as weekly_postings,
       count(salary) as salaries,
       round(avg(salary)) as avg_salary,
       round(avg(remote), 4) as remote_pct,
       round(avg(hybrid), 4) as hybrid_pct
from pl, span group by scope, location having count(*) >= MIN_LOCATION_POSTINGS;
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
     COMMON + f" One row per definition and location (locations with {MIN_LOCATION_POSTINGS}+ postings). "
     "weekly_postings = postings / weeks covered by the data. remote_pct = share flagged work-from-home. "
     "hybrid_pct = share whose job title says 'hybrid' (the data has no hybrid field, so this undercounts).")

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
  select p.scope, c.name as company,
         (c.name like 'beBee%' or c.name in (select name from intermediaries)) as intermediary,
         count(*) as postings, sum(p.remote) as remote_postings,
         round(avg(p.remote), 4) as remote_pct,
         round(avg(p.remote) - any_value(b.remote_pct), 4) as vs_overall
  from p join company_dim c using (company_id)
  join base b on b.scope = p.scope and b.location = 'All US'
  group by p.scope, c.name having count(*) >= {MIN_COMPANY_POSTINGS}
  order by p.scope, remote_pct desc, postings desc"""),
  COMMON + f" Metric 5: remote % per company, companies with {MIN_COMPANY_POSTINGS}+ postings, all US locations. "
  "intermediary = recruiter, staffing firm, job board, survey panel or gig platform (hand-reviewed list in "
  "the code); the dashboard leaves these out.")
