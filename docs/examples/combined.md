# Combined synthetic fault report

Curated JSON excerpt from the CLI command in the [quickstart](../../README.md#quickstart), executed on PostgreSQL 17.9. Exit code: **1**, as expected for intentional dirty data. Run/finding identifiers and verbose source/manifests evidence are omitted here; the CLI returns the complete persisted report.

The jacket count is independently expected to be `30 - 5 = 25`; the supplied physical snapshot is 26, so delta is +1. Duplicate hoodie receipts and invalid tee transfer legs suppress quantity conclusions for their affected buckets. Other complete controls remain assessable.

```json
{
  "contract_version": "1",
  "code_version": "stage1-demo",
  "ledger_batch_id": "combined:ledger",
  "snapshot_batch_id": "combined:snapshot",
  "as_of": "2026-01-02T00:00:00+00:00",
  "evaluated_at": "2026-01-02T02:00:00+00:00",
  "overall_status": "fail",
  "checks": [
    {
      "rule_id": "R001",
      "status": "fail"
    },
    {
      "rule_id": "R002",
      "status": "fail"
    },
    {
      "rule_id": "R003",
      "status": "pass"
    },
    {
      "rule_id": "R004",
      "status": "fail"
    },
    {
      "rule_id": "R005",
      "status": "pass"
    }
  ],
  "findings": [
    {
      "rule_id": "R001",
      "reason": "quantity_mismatch",
      "severity": "error",
      "sku_id": "combined:jacket-m",
      "warehouse_id": "combined:harbor",
      "source_row_ids": [
        "combined:movement:adjustment-jacket",
        "combined:opening:jacket-m:harbor",
        "combined:snapshot:jacket-m:harbor"
      ],
      "expected_qty": 25,
      "observed_qty": 26,
      "delta_qty": 1
    },
    {
      "rule_id": "R002",
      "reason": "duplicate_movement_key",
      "severity": "error",
      "sku_id": null,
      "warehouse_id": null,
      "source_row_ids": [
        "combined:movement:receipt-hoodie",
        "combined:movement:receipt-hoodie-copy"
      ],
      "expected_qty": null,
      "observed_qty": null,
      "delta_qty": null
    },
    {
      "rule_id": "R004",
      "reason": "invalid_transfer",
      "severity": "error",
      "sku_id": null,
      "warehouse_id": null,
      "source_row_ids": [
        "combined:movement:transfer-in",
        "combined:movement:transfer-out"
      ],
      "expected_qty": null,
      "observed_qty": null,
      "delta_qty": null
    }
  ]
}
```
