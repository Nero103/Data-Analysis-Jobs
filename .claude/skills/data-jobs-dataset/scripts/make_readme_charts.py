# Draws the README charts from data_jobs.duckdb, using the cleaned views in clean_views.sql.
# Usage: python3 -I make_readme_charts.py <data_jobs.duckdb> <out_dir>
# Scope: US postings whose title contains "data analyst"; salaries $25k-$300k; technical tools only.
import os, sys
import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

db, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
here = os.path.dirname(os.path.abspath(__file__))
con = duckdb.connect(db, read_only=True)
con.execute(open(os.path.join(here, "clean_views.sql")).read())

# Palette: validated categorical slots and chart chrome (light surface).
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, RED = "#2a78d6", "#e34948"
TYPE_STYLE = {  # color + marker shape, so category never relies on color alone
    "Programming Languages": ("#2a78d6", "o"),
    "Analytics": ("#eda100", "s"),
    "Infrastructure": ("#008300", "^"),
    "Applications": ("#e87ba4", "D"),
}
LINE_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]

plt.rcParams.update({
    "text.usetex": False, "axes.formatter.use_mathtext": False,
    "font.family": "DejaVu Sans", "font.size": 11, "text.color": INK, "axes.labelcolor": INK2,
    "axes.edgecolor": AXIS, "xtick.color": MUTED, "ytick.color": INK2, "axes.facecolor": SURFACE,
    "figure.facecolor": SURFACE, "savefig.facecolor": SURFACE, "axes.spines.top": False,
    "axes.spines.right": False, "axes.titleweight": "bold", "axes.titlesize": 14, "axes.titlelocation": "left",
})
money_k = FuncFormatter(lambda v, _: f"${v/1000:,.0f}k")

def finish(fig, name, note):
    fig.text(0.01, -0.04, note, fontsize=9, color=MUTED, ha="left", va="top")
    fig.savefig(os.path.join(out, name), dpi=200, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("wrote", name)

NOTE = "US Data Analyst postings (title contains \"data analyst\"), Jul 2025 – Jun 2026."
base = con.sql("select count(*) n, avg(salary_clean) avg from da_us").fetchall()[0]

# 1. Horizontal bar: most requested tools.
rows = con.sql("select skill, postings, share_of_postings from skill_metrics order by postings desc limit 15").fetchall()[::-1]
fig, ax = plt.subplots(figsize=(9, 6.2))
ax.barh([r[0] for r in rows], [r[1] for r in rows], color=BLUE, height=0.7)
for i, (_, n, s) in enumerate(rows):
    ax.text(n + max(r[1] for r in rows) * 0.01, i, f"{n:,}  ({s:.0%})", va="center", fontsize=10, color=INK2)
ax.set_title("Most requested tools in Data Analyst postings")
ax.set_xlabel("Postings that mention the tool")
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.grid(axis="x", color=GRID, linewidth=0.8); ax.set_axisbelow(True)
ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False)
ax.set_xlim(0, max(r[1] for r in rows) * 1.18)
finish(fig, "top_tools.png", NOTE + f" Share = of all {base[0]:,} postings.")

# 2. Diverging horizontal bar: pay premium of the 15 most requested tools.
rows = con.sql("""select skill, pay_premium, salary_sample_size from skill_metrics
                  where enough_salaries order by postings desc limit 15""").fetchall()
rows.sort(key=lambda r: r[1])
fig, ax = plt.subplots(figsize=(9, 6.2))
ax.barh([r[0] for r in rows], [r[1] for r in rows], color=[BLUE if r[1] >= 0 else RED for r in rows], height=0.7)
span = max(abs(r[1]) for r in rows)
for i, (_, p, _) in enumerate(rows):
    sign = "+" if p >= 0 else "−"
    ax.text(p + (span * 0.02 if p >= 0 else -span * 0.02), i, f"{sign}${abs(p):,.0f}",
            va="center", ha="left" if p >= 0 else "right", fontsize=10, color=INK2)
ax.axvline(0, color=AXIS, linewidth=1)
ax.set_xlim(-span * 1.35, span * 1.35)
ax.set_title("Pay premium of the 15 most requested tools")
ax.set_xlabel(f"Average salary minus the all-postings average (${base[1]:,.0f})")
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{'+' if v > 0 else '−' if v < 0 else ''}${abs(v)/1000:,.0f}k"))
ax.grid(axis="x", color=GRID, linewidth=0.8); ax.set_axisbelow(True)
ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False)
finish(fig, "pay_premium.png", NOTE + " Tools with 30+ salaries; salaries \\$25k–\\$300k.")

# 3. Scatter: pay against popularity.
pts = con.sql("""select skill, type, postings, avg_salary from skill_metrics
                 where enough_salaries and type in ('Programming Languages','Analytics','Infrastructure','Applications')""").fetchall()
fig, ax = plt.subplots(figsize=(9.5, 6.5))
for t, (color, marker) in TYPE_STYLE.items():
    sel = [p for p in pts if p[1] == t]
    ax.scatter([p[2] for p in sel], [p[3] for p in sel], s=56, color=color, marker=marker,
               edgecolor=SURFACE, linewidth=1.2, label=t, zorder=3)
ax.set_xscale("log")
ax.axhline(base[1], color=MUTED, linestyle=(0, (4, 4)), linewidth=1, zorder=2)
ax.text(ax.get_xlim()[0] * 1.08, base[1] + 900, f"All postings ${base[1]/1000:,.1f}k", color=INK2, fontsize=9)
label = sorted(pts, key=lambda p: -p[2])[:6] + sorted(pts, key=lambda p: -p[3])[:3]
offsets = {"Scala": (8, 9), "Teradata": (8, -13), "SQL": (-8, 8), "Excel": (-8, -4), "Python": (8, 6), "Power BI": (8, -12), "Tableau": (8, 4), "R": (8, 4)}
for p in {p[0]: p for p in label}.values():
    dx, dy = offsets.get(p[0], (8, 4))
    ax.annotate(p[0], (p[2], p[3]), xytext=(dx, dy), textcoords="offset points", fontsize=10, color=INK,
                ha="right" if dx < 0 else "left")
ax.yaxis.set_major_formatter(money_k)
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.grid(color=GRID, linewidth=0.8); ax.set_axisbelow(True)
ax.set_title("Pay against popularity, by tool")
ax.set_xlabel("Postings that mention the tool (log scale)")
ax.set_ylabel("Average yearly salary")
ax.legend(frameon=False, loc="upper right", fontsize=10, labelcolor=INK2)
finish(fig, "pay_vs_popularity.png", NOTE + " Tools with 30+ salaries; dashed line = average of all postings.")

# 4. Trend: postings per month, all and with a yearly salary.
rows = con.sql("""select date_trunc('month', job_posted_date) m, count(*) n, count(salary_clean) s
                  from da_us group by 1 order by 1""").fetchall()
months = [r[0] for r in rows]
fig, ax = plt.subplots(figsize=(9.5, 5))
ax.plot(months, [r[1] for r in rows], color=BLUE, linewidth=2, marker="o", markersize=5)
ax.plot(months, [r[2] for r in rows], color=LINE_COLORS[1], linewidth=2, marker="o", markersize=5)
ax.annotate("All postings", (months[-1], rows[-1][1]), xytext=(8, 0), textcoords="offset points", va="center", color=INK2)
ax.annotate("With a yearly salary", (months[-1], rows[-1][2]), xytext=(8, 0), textcoords="offset points", va="center", color=INK2)
ax.set_ylim(0, max(r[1] for r in rows) * 1.12)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.set_xticks(months); ax.set_xticklabels([m.strftime("%b\n%Y") if m.month in (7, 1) else m.strftime("%b") for m in months])
ax.grid(axis="y", color=GRID, linewidth=0.8); ax.set_axisbelow(True)
ax.set_title("Data Analyst postings per month")
ax.set_ylabel("Postings")
finish(fig, "monthly_postings.png", NOTE)

# 5. Trend: share of postings mentioning the top five tools, by month.
top5 = [r[0] for r in con.sql("select skill from skill_metrics order by postings desc limit 5").fetchall()]
rows = con.sql(f"""
  with m as (select date_trunc('month', job_posted_date) m, count(*) n from da_us group by 1)
  select date_trunc('month', p.job_posted_date) m, k.skill, count(*) / any_value(m.n) share
  from da_skills k join da_us p using (job_id) join m on m.m = date_trunc('month', p.job_posted_date)
  where k.skill in ({",".join("'" + s + "'" for s in top5)})
  group by 1, 2 order by 1""").fetchall()
fig, ax = plt.subplots(figsize=(9.5, 5.5))
ends = []
for skill, color in zip(top5, LINE_COLORS):
    sel = [r for r in rows if r[1] == skill]
    ax.plot([r[0] for r in sel], [r[2] for r in sel], color=color, linewidth=2, label=skill)
    ends.append([skill, sel[-1][0], sel[-1][2]])
ends.sort(key=lambda e: e[2])
for i in range(1, len(ends)):  # keep end labels at least 3 points apart
    ends[i][2] = max(ends[i][2], ends[i - 1][2] + 0.03)
for skill, m, y in ends:
    ax.annotate(skill, (m, y), xytext=(8, 0), textcoords="offset points", va="center", color=INK2, fontsize=10)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}"))
ax.set_ylim(0, max(r[2] for r in rows) * 1.15)
ax.set_xticks(months); ax.set_xticklabels([m.strftime("%b\n%Y") if m.month in (7, 1) else m.strftime("%b") for m in months])
ax.grid(axis="y", color=GRID, linewidth=0.8); ax.set_axisbelow(True)
ax.set_title("Share of postings mentioning each top tool, by month")
ax.set_ylabel("Share of that month's postings")
ax.legend(frameon=False, loc="lower left", ncol=5, fontsize=10, labelcolor=INK2)
finish(fig, "tool_share_trend.png", NOTE)
