# Dashboard metrics

Five metrics proposed for the dashboard (Nov 2026). Metrics 1 and 2 are the two columns the user decided on. Metrics 3 to 5 were suggested and the user asked for them to be recorded. Their place on the dashboard isn't settled, so check with the user before featuring them.

Example values use the scope in `scripts/clean_views.sql`: title rule, US only, salaries $25k–$300k, technical tools only, false matches removed. In that scope there are 39,519 postings and 7,937 usable salaries, with an overall average of $102,782 and an overall remote rate of 2.3%. Re-run before quoting them, and always name the scope you used.

The views `skill_metrics` and `company_remote` in `scripts/clean_views.sql` compute all five.

## 1. Skill demand (popularity column, decided)

- **Definition:** the number of Data Analyst postings that mention the tool.
- **Formula:** `COUNT(DISTINCT job_id)` over postings linked to the skill.
- **Comparisons:**
  - Rank among tools.
  - Share of postings = postings mentioning the tool ÷ all postings in scope. Label the denominator: 25% of postings name no skill, so shares understate how often skills are named.
- **Examples:** SQL 18,590 (47%), Excel 12,116 (31%), Python 11,762 (30%).

## 2. Average salary (pay column, decided)

- **Definition:** the average yearly salary of postings that mention the tool and list one.
- **Formula:** `AVG(salary_year_avg)` over those postings, keeping only salaries between $25k and $300k.
- **Comparison:** the overall average for all postings in scope (see metric 3). Offer the median as an alternative only if the user asks, because they chose the average.
- **Examples:** Snowflake $117,023, Python $113,321, SQL $108,645, Excel $91,956.

## 3. Pay premium

- **Definition:** how far a tool's average salary sits above or below the average for all Data Analyst postings.
- **Formula:** tool average salary − overall average salary. The percentage version is that difference ÷ the overall average.
- **Comparison:** a positive premium means postings asking for the tool pay above the typical analyst posting.
- **Examples:** Snowflake +$14.2k, Python +$10.5k, R +$8.4k, SQL +$5.9k, Power BI −$0.9k, Excel −$10.8k.
- **Caveat:** a premium shows correlation, not cause. Senior roles list more and rarer tools. Keep it as a separate column and never fold it into a combined score, because the user wants pay and popularity side by side.

## 4. Salary sample size

- **Definition:** how many salaries a tool's average is based on.
- **Formula:** `COUNT(salary_year_avg)` over postings mentioning the tool, after the $25k–$300k filter.
- **Comparison:** a threshold of at least 30 salaries to show the average. Grey out or hide it below that. 71 of 313 tools meet the threshold.
- **Examples:** SQL 3,545; Snowflake 435.

## 5. Remote % per company

- **Definition:** the share of a company's Data Analyst postings flagged as remote.
- **Formula:** `SUM(job_work_from_home::int) ÷ COUNT(*)` per company.
- **Comparisons:**
  - The overall remote rate (2.3%).
  - Show only companies with at least 20 postings. 9,200 companies have fewer than 5 postings, where one posting swings the rate between 0% and 100%.
- **Caveats:**
  - The flag covers only fully remote "Anywhere" postings, so hybrid roles are missed.
  - 133 of the 181 companies with 20+ postings are at 0%, so the median company is 0%.
  - The top of the list is job platforms and recruiters (Upwork 100%, vmysmartpros, remotepromsp), not employers. Consider labelling or excluding them.
  - It describes companies, not skills. **Remote % per skill** (remote postings mentioning the tool ÷ all postings mentioning it) fits the main question better. Offer it as an extra table column.

## Added KPIs (Nov 2026, requested by the user)

The KPI cards are: postings, postings per week, average salary, remote share and hybrid share. The "tools with 30+ salaries" card was removed at the user's request; the table still greys out averages from fewer than 30 salaries.

### Postings per week
- **Definition:** average number of Data Analyst postings per week.
- **Formula:** postings ÷ weeks the data covers. Weeks = (last − first US posting date + 1) ÷ 7, which is about 52.1 for 2025-07-01 to 2026-06-30.
- **Example:** 757.9 per week under the title rule, all US.

### Hybrid share
- **Definition:** the share of postings whose job title says "hybrid".
- **Formula:** `AVG((job_title ILIKE '%hybrid%')::int)`.
- **Caveat:** the data has no hybrid field (not in the location, schedule type or work-from-home flag). Only titles carry the word, so this is a floor, not a full count. It comes to 1.3% (905 of about 67,700 US postings). Label it "job title says hybrid".
- **Related:** the remote flag also undercounts. 2,637 US postings say "remote" in the title but aren't flagged.

## Excluding recruiters and job platforms (decided)

The user asked for recruiters and job platforms to be removed from company-level views. `scripts/build_dashboard.py` holds a hand-reviewed `INTERMEDIARIES` list, plus every name starting with "beBee", and adds an `intermediary` flag to each company row. The list covers job boards and aggregators (Dice, Lensa, VirtualVocations), survey panels and gig or data-annotation platforms (Online Surveys, Focus Group Panel, Upwork, DataAnnotation, Outlier AI), and recruiters and staffing firms (Robert Half, Insight Global, TEKsystems, Harnham). Of 181 companies with 20+ postings under the title rule, 99 are intermediaries and 82 are employers; 62 of those employers post no remote roles. The list was reviewed only for companies with 20 or more postings, so extend it if you lower that threshold.
