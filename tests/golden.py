"""Manually calculated inputs: no generator or checker output feeds this oracle."""

from datetime import datetime, timedelta, timezone

from psycopg import sql

BASELINE = datetime(2026, 1, 1, tzinfo=timezone.utc)
CUTOFF = BASELINE + timedelta(days=1)
EXPECTED = {("shirt", "a"): 109, ("shirt", "b"): 25,
            ("coat", "a"): 15, ("zero", "a"): 0}


def insert(conn, table, **row):
    conn.execute(sql.SQL("INSERT INTO operational_fixture.{} ({}) VALUES ({})").format(
        sql.Identifier(table), sql.SQL(", ").join(map(sql.Identifier, row)),
        sql.SQL(", ").join(sql.Placeholder() for _ in row)), tuple(row.values()))


def load_golden(conn, prefix):
    """109 = 100 + 10 - 7 - 5 + 7 + 4; 25 = 20 + 5; 15 = 10 + 2 + 3."""
    key = lambda name: f"{prefix}:{name}"
    with conn.transaction():
        insert(conn, "styles", style_id=key("style"), style_code=key("style"),
               name="Fictional garments")
        for sku in ("shirt", "coat", "zero"):
            insert(conn, "skus", sku_id=key(sku), style_id=key("style"),
                   sku_code=key(sku), color="navy", size="M", base_uom="each")
        for wh in ("a", "b"):
            insert(conn, "warehouses", warehouse_id=key(wh), warehouse_code=key(wh),
                   name=f"Fictional warehouse {wh}")
        for kind, count in (("ledger", 12), ("snapshot", 4)):
            insert(conn, "batches", batch_id=key(kind), kind=kind, status="complete",
                   baseline_at=BASELINE if kind == "ledger" else None,
                   as_of=CUTOFF, watermark=10, observed_at=CUTOFF,
                   expected_row_count=count)
            for sku, wh in EXPECTED:
                insert(conn, "coverage", row_id=key(f"{kind}:coverage:{sku}:{wh}"),
                       batch_id=key(kind), sku_id=key(sku), warehouse_id=key(wh))
        for (sku, wh), opening in zip(EXPECTED, (100, 20, 10, 0)):
            insert(conn, "opening_balances", row_id=key(f"opening:{sku}:{wh}"),
                   batch_id=key("ledger"), sku_id=key(sku), warehouse_id=key(wh),
                   quantity=opening, as_of=BASELINE, baseline_ref="manual-baseline")
            insert(conn, "snapshots", row_id=key(f"snapshot:{sku}:{wh}"),
                   batch_id=key("snapshot"), sku_id=key(sku), warehouse_id=key(wh),
                   on_hand_qty=EXPECTED[sku, wh], as_of=CUTOFF,
                   watermark=10, observed_at=CUTOFF)
        movements = [
            ("receipt", "shirt", "a", 10, "receipt", 1),
            ("shipment", "shirt", "a", -7, "shipment", 2),
            ("transfer-out", "shirt", "a", -5, "transfer", 3),
            ("transfer-in", "shirt", "b", 5, "transfer", 3),
            ("reversal", "shirt", "a", 7, "reversal", 4),
            ("return", "shirt", "a", 4, "return", 6),
            ("line-1", "coat", "a", 2, "receipt", 5),
            ("line-2", "coat", "a", 3, "receipt", 5),
            ("pending", "shirt", "a", 999, "adjustment", 6),
            ("at-baseline", "shirt", "a", 1000, "receipt", 7),
            ("late", "coat", "a", 1000, "receipt", 11),
            ("after-cutoff", "coat", "a", 1000, "receipt", 8),
        ]
        for name, sku, wh, qty, kind, seq in movements:
            effective = BASELINE + timedelta(hours=seq)
            if name.startswith("line-"):
                effective = CUTOFF
            elif name == "at-baseline":
                effective = BASELINE
            elif name == "after-cutoff":
                effective = CUTOFF + timedelta(microseconds=1)
            insert(conn, "movements", row_id=key(name), batch_id=key("ledger"),
                   source_system="manual", event_id=key("multi-line" if name.startswith("line-")
                                                       else "transfer" if kind == "transfer" else name),
                   document_id=key("document"), document_line_id=name if kind != "transfer" else "transfer",
                   leg_id=wh, sku_id=key(sku), warehouse_id=key(wh), quantity=qty,
                   movement_type=kind, posting_status="pending" if name == "pending" else "posted",
                   effective_at=effective, source_recorded_at=effective,
                   source_seq=seq, observed_at=CUTOFF + timedelta(hours=2),
                   transfer_id=key("transfer") if kind == "transfer" else None,
                   reversal_of_row_id=key("shipment") if kind == "reversal" else None,
                   reason="synthetic manual acceptance fixture")
    return dict(ledger_batch_id=key("ledger"), snapshot_batch_id=key("snapshot"),
                as_of=CUTOFF, evaluated_at=CUTOFF + timedelta(hours=24))
