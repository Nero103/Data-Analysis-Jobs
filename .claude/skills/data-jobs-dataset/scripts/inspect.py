# List every table in a DuckDB file with its schema, row count and 5 sample rows.
# Usage: python3 -I inspect.py <db>
import sys
import duckdb
import pandas as pd

con = duckdb.connect(sys.argv[1], read_only=True)
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 50)
pd.set_option("display.max_colwidth", 40)
tables = con.sql("select table_schema, table_name from information_schema.tables order by 1, 2").fetchall()
for schema, name in tables:
    q = f'"{schema}"."{name}"'
    n = con.sql(f"select count(*) from {q}").fetchall()[0][0]
    print(f"\n===== {q} ({n:,} rows)")
    print(con.sql(f"describe {q}").df()[["column_name", "column_type", "null"]].to_string(index=False))
    print(con.sql(f"select * from {q} limit 5").df().to_string(index=False))
