"""Initialize a NEW disposable acceptance database; never reset existing inputs."""

import os
from pathlib import Path

import psycopg


def main():
    root = Path(__file__).resolve().parents[1]
    with psycopg.connect(os.environ["TEST_DATABASE_URL"], autocommit=True) as conn:
        if conn.execute("SELECT to_regnamespace('operational_fixture')").fetchone()[0]:
            raise RuntimeError("Use a fresh acceptance database; bootstrap refuses existing source schemas")
        conn.execute((root / "sql/schema.sql").read_text())
        conn.execute((root / "sql/planning_schema.sql").read_text())


if __name__ == "__main__":
    main()
