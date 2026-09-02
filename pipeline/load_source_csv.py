import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from pg_loader import DB_DSN


def load_csv(path: str) -> int:
    df = pd.read_csv(path)
    sub = df[["num", "start_datetime", "current_datetime", "status_name", "status_comment", "region"]].copy()

    rows = [
        tuple(None if pd.isna(v) else v for v in row)
        for row in sub.itertuples(index=False, name=None)
    ]

    conn = psycopg2.connect(**DB_DSN)
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO source_application_status
                (num, start_datetime, current_datetime, status_name, status_comment, region)
            VALUES %s
            ON CONFLICT (num, current_datetime) DO NOTHING
        """, rows)
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM source_application_status")
        total = cur.fetchone()[0]
    conn.close()
    return total


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python3 load_source_csv.py <путь_к_csv>")
        sys.exit(1)
    total = load_csv(sys.argv[1])
    print(f"Готово. Всего строк в source_application_status: {total}")
