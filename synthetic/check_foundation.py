"""Focused real-PostgreSQL foundation check in a disposable database."""

from datetime import timedelta
import os
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row

from .generate import AS_OF, BASELINE, SCENARIOS, load_scenario


def check(owner_url):
    database = "ii_foundation_" + uuid4().hex
    with psycopg.connect(owner_url, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
        try:
            scratch_url = make_conninfo(owner_url, dbname=database)
            with psycopg.connect(scratch_url, autocommit=True, row_factory=dict_row) as conn:
                conn.execute((Path(__file__).resolve().parents[1] / "sql/schema.sql").read_text())
                assert 170000 <= conn.info.server_version < 180000
                # Force a late insert failure and prove the complete load rolls back.
                conn.execute("""
                    CREATE FUNCTION reject_fixture() RETURNS trigger LANGUAGE plpgsql AS $$
                    BEGIN RAISE EXCEPTION 'foundation rollback probe'; END $$;
                    CREATE TRIGGER rollback_probe BEFORE INSERT ON operational_fixture.snapshots
                    FOR EACH ROW EXECUTE FUNCTION reject_fixture();
                """)
                try:
                    load_scenario(conn, "clean")
                except psycopg.errors.RaiseException:
                    pass
                else:
                    raise AssertionError("Forced insert failure did not propagate")
                conn.execute("DROP TRIGGER rollback_probe ON operational_fixture.snapshots; "
                             "DROP FUNCTION reject_fixture()")
                for table in ("styles", "skus", "warehouses", "batches", "coverage",
                              "opening_balances", "movements", "snapshots"):
                    assert conn.execute(sql.SQL("SELECT * FROM operational_fixture.{}").format(
                        sql.Identifier(table))).fetchall() == []
                contexts = {}
                for scenario in SCENARIOS:
                    context = contexts[scenario] = load_scenario(conn, scenario)
                    assert context["as_of"] == AS_OF
                    assert context["evaluated_at"].utcoffset() == timedelta(0)
                    batches = conn.execute(
                        "SELECT * FROM operational_fixture.batches WHERE batch_id IN (%s, %s)",
                        (context["ledger_batch_id"], context["snapshot_batch_id"]),
                    ).fetchall()
                    assert len(batches) == 2
                    for batch in batches:
                        table = "movements" if batch["kind"] == "ledger" else "snapshots"
                        rows = conn.execute(sql.SQL(
                            "SELECT * FROM operational_fixture.{} WHERE batch_id = %s ORDER BY row_id"
                        ).format(sql.Identifier(table)), (batch["batch_id"],)).fetchall()
                        expected_count = (14 if scenario in ("duplicate_movement", "unknown_reference", "combined")
                                          else 13) if table == "movements" else (4 if scenario == "missing_snapshot" else 5)
                        assert batch["expected_row_count"] == len(rows) == expected_count
                        assert all(row["row_id"].startswith(scenario + ":") for row in rows)
                    for table in ("styles", "skus", "warehouses", "coverage", "opening_balances"):
                        key = {"styles": "style_id", "skus": "sku_id", "warehouses": "warehouse_id"}.get(table, "row_id")
                        ids = conn.execute(sql.SQL(
                            "SELECT {} FROM operational_fixture.{} WHERE starts_with({}, %s)"
                        ).format(sql.Identifier(key), sql.Identifier(table), sql.Identifier(key)),
                            (scenario + ":",)).fetchall()
                        assert len(ids) == {"styles": 3, "skus": 4, "warehouses": 2,
                                            "coverage": 10, "opening_balances": 5}[table]
                    before = conn.execute(
                        "SELECT * FROM operational_fixture.movements ORDER BY row_id"
                    ).fetchall()
                    try:
                        load_scenario(conn, scenario)
                    except ValueError:
                        pass
                    else:
                        raise AssertionError("Loading existing scenario did not refuse")
                    assert conn.execute(
                        "SELECT * FROM operational_fixture.movements ORDER BY row_id"
                    ).fetchall() == before

                # Independent arithmetic oracle, including excluded boundary/status/sequence rows.
                quantities = conn.execute("""
                    SELECT o.sku_id, o.warehouse_id, o.quantity + COALESCE(sum(m.quantity), 0) AS qty
                    FROM operational_fixture.opening_balances o
                    LEFT JOIN operational_fixture.movements m ON m.batch_id = o.batch_id
                        AND m.sku_id = o.sku_id AND m.warehouse_id = o.warehouse_id
                        AND m.posting_status = 'posted' AND m.effective_at > o.as_of
                        AND m.effective_at <= %s AND m.source_seq <= 10
                    WHERE o.batch_id = 'clean:ledger'
                    GROUP BY o.row_id, o.sku_id, o.warehouse_id, o.quantity
                """, (AS_OF,)).fetchall()
                expected = {("clean:tee-m", "clean:harbor"): 24,
                            ("clean:tee-m", "clean:upland"): 9,
                            ("clean:hoodie-l", "clean:harbor"): 16,
                            ("clean:tee-l", "clean:harbor"): 0,
                            ("clean:jacket-m", "clean:harbor"): 25}
                assert {(r["sku_id"], r["warehouse_id"]): r["qty"] for r in quantities} == expected
                snapshots = conn.execute(
                    "SELECT * FROM operational_fixture.snapshots WHERE batch_id = 'clean:snapshot'"
                ).fetchall()
                assert {(r["sku_id"], r["warehouse_id"]): r["on_hand_qty"] for r in snapshots} == expected
                legs = conn.execute("""
                    SELECT * FROM operational_fixture.movements WHERE batch_id = 'clean:ledger'
                    AND transfer_id = 'clean:transfer-001' ORDER BY quantity
                """).fetchall()
                assert [r["quantity"] for r in legs] == [-4, 4]
                assert len({r["warehouse_id"] for r in legs}) == 2
                assert len({(r["sku_id"], r["effective_at"], r["source_seq"]) for r in legs}) == 1
                receipt = conn.execute("""
                    SELECT document_line_id FROM operational_fixture.movements
                    WHERE batch_id = 'clean:ledger' AND event_id = 'clean:receipt-001'
                """).fetchall()
                assert {r["document_line_id"] for r in receipt} == {"clean:1", "clean:2"}
                reversal = conn.execute("""
                    SELECT r.quantity, m.quantity AS original_qty, r.reversal_of_row_id
                    FROM operational_fixture.movements r
                    JOIN operational_fixture.movements m ON m.row_id = r.reversal_of_row_id
                    WHERE r.row_id = 'clean:movement:reversal-hoodie'
                """).fetchone()
                assert reversal == dict(quantity=2, original_qty=-2,
                                        reversal_of_row_id="clean:movement:shipment-hoodie")
                assert conn.execute("""
                    SELECT on_hand_qty FROM operational_fixture.snapshots
                    WHERE row_id = 'quantity_mismatch:snapshot:jacket-m:harbor'
                """).fetchone()["on_hand_qty"] == 26
                assert conn.execute("""
                    SELECT sku_id FROM operational_fixture.movements
                    WHERE row_id = 'unknown_reference:movement:unknown-sku'
                """).fetchone()["sku_id"] == "unknown_reference:unknown-sku"
                assert conn.execute("""
                    SELECT quantity FROM operational_fixture.movements
                    WHERE row_id = 'invalid_transfer:movement:transfer-in'
                """).fetchone()["quantity"] == 3
                assert contexts["stale_snapshot"]["evaluated_at"] - AS_OF == timedelta(hours=24, seconds=1)
                for scenario in ("duplicate_movement", "combined"):
                    duplicates = conn.execute(
                        "SELECT * FROM operational_fixture.movements WHERE row_id IN (%s, %s) ORDER BY row_id",
                        (scenario + ":movement:receipt-hoodie", scenario + ":movement:receipt-hoodie-copy"),
                    ).fetchall()
                    assert len(duplicates) == 2
                    assert {k: v for k, v in duplicates[0].items() if k != "row_id"} == {
                        k: v for k, v in duplicates[1].items() if k != "row_id"}
                assert conn.execute("SELECT quantity FROM operational_fixture.movements "
                                    "WHERE row_id = 'combined:movement:transfer-in'").fetchone()["quantity"] == 3
                assert conn.execute("SELECT on_hand_qty FROM operational_fixture.snapshots "
                                    "WHERE row_id = 'combined:snapshot:jacket-m:harbor'").fetchone()["on_hand_qty"] == 26
                assert conn.execute("SELECT * FROM operational_fixture.snapshots "
                                    "WHERE row_id = 'missing_snapshot:snapshot:tee-l:harbor'").fetchall() == []
                assert conn.execute("SELECT sku_id, warehouse_id FROM operational_fixture.coverage "
                                    "WHERE row_id = 'missing_snapshot:coverage:snapshot:tee-l:harbor'").fetchone() == {
                                        "sku_id": "missing_snapshot:tee-l", "warehouse_id": "missing_snapshot:harbor"}
                assert BASELINE < AS_OF
                assert conn.execute("SELECT count(*) AS n FROM reliability.runs").fetchone()["n"] == 0

            runner_url = make_conninfo(scratch_url, user="ii_runner", password="ii_runner_local")
            with psycopg.connect(runner_url, autocommit=True) as runner:
                assert runner.execute("SELECT current_user").fetchone()[0] == "ii_runner"
                assert runner.execute("SELECT count(*) FROM operational_fixture.movements").fetchone()[0] > 0
                for table in ("styles", "skus", "warehouses", "batches", "coverage",
                              "opening_balances", "movements", "snapshots"):
                    name = sql.Identifier("operational_fixture", table)
                    key = {"styles": "style_id", "skus": "sku_id", "warehouses": "warehouse_id",
                           "batches": "batch_id"}.get(table, "row_id")
                    for query in (sql.SQL("INSERT INTO {} SELECT * FROM {} WHERE false").format(name, name),
                                  sql.SQL("UPDATE {} SET {} = {} WHERE false").format(
                                      name, sql.Identifier(key), sql.Identifier(key)),
                                  sql.SQL("DELETE FROM {} WHERE false").format(name),
                                  sql.SQL("TRUNCATE {}").format(name)):
                        deny(runner, query)
                for schema in ("operational_fixture", "reliability"):
                    deny(runner, sql.SQL("CREATE TABLE {} (id text)").format(sql.Identifier(schema, "denied")))
                run = uuid4()
                runner.execute("INSERT INTO reliability.runs VALUES (%s, '1', 'foundation-check', "
                               "'clean:ledger', 'clean:snapshot', %s, %s, 'pass')", (run, AS_OF, AS_OF))
                runner.execute("INSERT INTO reliability.check_results VALUES (%s, 'R001', 'pass')", (run,))
                runner.execute("INSERT INTO reliability.findings VALUES "
                               "(%s, 'storage-probe', 'R001', 'error', 'quantity_mismatch', "
                               "NULL, NULL, '[]', 25, 26, 1, '{}')", (run,))
                assert runner.execute("SELECT expected_qty, observed_qty, delta_qty FROM reliability.findings "
                                      "WHERE run_id = %s", (run,)).fetchone() == (25, 26, 1)
                for table in ("runs", "check_results", "findings"):
                    deny(runner, sql.SQL("DELETE FROM {} WHERE false").format(sql.Identifier("reliability", table)))
                try:
                    runner.execute("INSERT INTO reliability.check_results VALUES (%s, 'R001', 'pass')", (uuid4(),))
                except psycopg.errors.ForeignKeyViolation:
                    pass
                else:
                    raise AssertionError("Reliability child foreign key missing")
        finally:
            admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(database)))
    print("PASS: eight scenarios, independent quantities/controls, reload refusal, PostgreSQL 17 and role grants")


def deny(conn, query):
    try:
        conn.execute(query)
    except psycopg.errors.InsufficientPrivilege:
        return
    raise AssertionError(f"Runtime role unexpectedly allowed: {query}")


if __name__ == "__main__":
    check(os.environ["FIXTURE_DATABASE_URL"])
