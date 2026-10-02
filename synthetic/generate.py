"""Load a named synthetic scenario without modifying any existing inputs."""

import argparse
from datetime import datetime, timedelta, timezone
import json
import os

from psycopg import sql
from psycopg.pq import TransactionStatus

SCENARIOS = (
    "clean", "quantity_mismatch", "duplicate_movement", "unknown_reference",
    "invalid_transfer", "stale_snapshot", "missing_snapshot", "combined",
)
BASELINE = datetime(2026, 1, 1, tzinfo=timezone.utc)
AS_OF = BASELINE + timedelta(days=1)
WATERMARK = 10
# Manually specified independent physical counts; never derived from movements.
BALANCES = (
    ("tee-m", "harbor", 20, 24),
    ("tee-m", "upland", 5, 9),
    ("hoodie-l", "harbor", 12, 16),
    ("tee-l", "harbor", 0, 0),
    ("jacket-m", "harbor", 30, 25),
)


def _scenario_data(scenario_name):
    if scenario_name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_name!r}")
    prefix = f"{scenario_name}:"

    def ident(value):
        return prefix + value

    ledger, snapshot = ident("ledger"), ident("snapshot")
    observed = AS_OF + timedelta(minutes=90)
    data = {name: [] for name in (
        "styles", "skus", "warehouses", "batches", "coverage",
        "opening_balances", "movements", "snapshots",
    )}
    for style, name in (
        ("tee", "Northwind Everyday Tee"), ("hoodie", "Northwind Trail Hoodie"),
        ("jacket", "Northwind Light Jacket"),
    ):
        data["styles"].append(dict(style_id=ident(style), style_code=ident(style.upper()), name=name))
    for sku, style, color, size in (
        ("tee-m", "tee", "navy", "M"), ("tee-l", "tee", "navy", "L"),
        ("hoodie-l", "hoodie", "forest", "L"), ("jacket-m", "jacket", "stone", "M"),
    ):
        data["skus"].append(dict(sku_id=ident(sku), style_id=ident(style),
                                 sku_code=ident(sku.upper()), color=color, size=size, base_uom="each"))
    for warehouse in ("harbor", "upland"):
        data["warehouses"].append(dict(warehouse_id=ident(warehouse),
                                       warehouse_code=ident(warehouse.upper()),
                                       name=f"Northwind {warehouse.title()} Warehouse"))
    for sku, warehouse, opening, counted in BALANCES:
        bucket = f"{sku}:{warehouse}"
        for batch, kind in ((ledger, "ledger"), (snapshot, "snapshot")):
            data["coverage"].append(dict(row_id=ident(f"coverage:{kind}:{bucket}"),
                                          batch_id=batch, sku_id=ident(sku), warehouse_id=ident(warehouse)))
        data["opening_balances"].append(dict(
            row_id=ident(f"opening:{bucket}"), batch_id=ledger,
            sku_id=ident(sku), warehouse_id=ident(warehouse), quantity=opening,
            as_of=BASELINE, baseline_ref=ident("opening-count-20260101"),
        ))
        data["snapshots"].append(dict(
            row_id=ident(f"snapshot:{bucket}"), batch_id=snapshot,
            sku_id=ident(sku), warehouse_id=ident(warehouse), on_hand_qty=counted,
            as_of=AS_OF, watermark=WATERMARK, observed_at=observed,
        ))

    def movement(label, sku, warehouse, quantity, kind, sequence, hours, *,
                 event=None, document=None, line="1", leg="1", posting="posted",
                 transfer=None, reversal=None, reason=None):
        effective = BASELINE + timedelta(hours=hours)
        recorded = effective + timedelta(minutes=5)
        data["movements"].append(dict(
            row_id=ident(f"movement:{label}"), batch_id=ledger,
            source_system="fictional-erp", event_id=ident(event or label),
            document_id=ident(document or label), document_line_id=ident(line),
            leg_id=ident(leg), sku_id=ident(sku), warehouse_id=ident(warehouse),
            quantity=quantity, movement_type=kind, posting_status=posting,
            effective_at=effective, source_recorded_at=recorded, source_seq=sequence,
            observed_at=recorded + timedelta(minutes=5),
            transfer_id=ident(transfer) if transfer else None,
            reversal_of_row_id=ident(f"movement:{reversal}") if reversal else None,
            reason=reason,
        ))

    movement("receipt-tee", "tee-m", "harbor", 10, "receipt", 1, 1,
             event="receipt-001", document="receipt-001", line="1")
    movement("receipt-hoodie", "hoodie-l", "harbor", 4, "receipt", 1, 1,
             event="receipt-001", document="receipt-001", line="2")
    movement("shipment-tee", "tee-m", "harbor", -3, "shipment", 2, 2)
    movement("transfer-out", "tee-m", "harbor", -4, "transfer", 3, 3,
             event="transfer-001", document="transfer-001", leg="out", transfer="transfer-001")
    movement("transfer-in", "tee-m", "upland", 4, "transfer", 3, 3,
             event="transfer-001", document="transfer-001", leg="in", transfer="transfer-001")
    movement("shipment-hoodie", "hoodie-l", "harbor", -2, "shipment", 4, 4)
    movement("reversal-hoodie", "hoodie-l", "harbor", 2, "reversal", 5, 5,
             reversal="shipment-hoodie", reason="Shipment cancelled")
    movement("adjustment-jacket", "jacket-m", "harbor", -5, "adjustment", 6, 6,
             reason="Independent physical count correction")
    movement("at-baseline", "tee-m", "harbor", 99, "receipt", 0, 0)
    movement("pending", "tee-m", "harbor", 50, "receipt", 7, 7, posting="pending")
    movement("after-cutoff", "tee-m", "harbor", 80, "receipt", 9, 25)
    movement("late-higher-sequence", "tee-m", "harbor", 70, "receipt", 11, 23)
    data["movements"][-1].update(source_recorded_at=AS_OF + timedelta(minutes=25),
                                 observed_at=AS_OF + timedelta(minutes=30))
    movement("at-cutoff", "tee-m", "harbor", 1, "return", 10, 24)

    if scenario_name in ("duplicate_movement", "combined"):
        duplicate = data["movements"][1].copy()
        duplicate["row_id"] = ident("movement:receipt-hoodie-copy")
        data["movements"].append(duplicate)
    if scenario_name == "unknown_reference":
        movement("unknown-sku", "unknown-sku", "harbor", 3, "receipt", 8, 8)
    if scenario_name in ("invalid_transfer", "combined"):
        data["movements"][4]["quantity"] = 3
    if scenario_name in ("quantity_mismatch", "combined"):
        data["snapshots"][4]["on_hand_qty"] = 26
    if scenario_name == "missing_snapshot":
        del data["snapshots"][3]  # Explicitly covered zero stock is still required.

    for batch, kind, count in (
        (ledger, "ledger", len(data["movements"])),
        (snapshot, "snapshot", len(data["snapshots"])),
    ):
        data["batches"].append(dict(
            batch_id=batch, kind=kind, status="complete",
            baseline_at=BASELINE if kind == "ledger" else None,
            as_of=AS_OF, watermark=WATERMARK, observed_at=observed, expected_row_count=count,
        ))
    age = timedelta(hours=24, seconds=1) if scenario_name == "stale_snapshot" else timedelta(hours=2)
    context = dict(ledger_batch_id=ledger, snapshot_batch_id=snapshot,
                   as_of=AS_OF, evaluated_at=AS_OF + age)
    return data, context


def load_scenario(conn, scenario_name: str) -> dict:
    """Insert one scenario atomically using an idle autocommit owner connection.

    Re-loading a scenario raises ValueError; no source or result rows are deleted.
    """
    data, context = _scenario_data(scenario_name)
    if not conn.autocommit or conn.info.transaction_status != TransactionStatus.IDLE:
        raise ValueError("load_scenario requires an idle autocommit=True connection")
    with conn.transaction():
        for table in data:
            key = {"styles": "style_id", "skus": "sku_id", "warehouses": "warehouse_id",
                   "batches": "batch_id"}.get(table, "row_id")
            exists = conn.execute(sql.SQL(
                "SELECT 1 FROM operational_fixture.{} WHERE starts_with({}, %s) LIMIT 1"
            ).format(sql.Identifier(table), sql.Identifier(key)), (f"{scenario_name}:",)).fetchone()
            if exists:
                raise ValueError(f"Scenario {scenario_name!r} already has inputs; refusing to overwrite")
        for table, rows in data.items():
            columns = list(rows[0])
            query = sql.SQL("INSERT INTO operational_fixture.{} ({}) VALUES ({})").format(
                sql.Identifier(table), sql.SQL(", ").join(map(sql.Identifier, columns)),
                sql.SQL(", ").join(sql.Placeholder() for _ in columns),
            )
            with conn.cursor() as cursor:
                cursor.executemany(query, [tuple(row[column] for column in columns) for row in rows])
    return context


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=SCENARIOS)
    parser.add_argument("--database-url", default=os.environ.get("FIXTURE_DATABASE_URL"))
    args = parser.parse_args()
    if not args.database_url:
        parser.error("Set FIXTURE_DATABASE_URL to an owner connection, or use --database-url")
    import psycopg
    try:
        with psycopg.connect(args.database_url, autocommit=True) as conn:
            context = load_scenario(conn, args.scenario)
    except (ValueError, psycopg.Error) as error:
        parser.exit(2, f"{error}\n")
    print(json.dumps({key: value.isoformat() if isinstance(value, datetime) else value
                      for key, value in context.items()}, sort_keys=True))


if __name__ == "__main__":
    main()
