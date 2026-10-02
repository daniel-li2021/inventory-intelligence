# Milestone 1 contract — v1

Frozen 2026-10-02 for the first reconciliation milestone. This is the normative interface shared by the three agents. Research and the broader Stage 1 roadmap are context. This document is a specification, not implemented functionality.

## Scope and invariants

- Python 3.12, PostgreSQL 17, Docker Compose, Psycopg 3; standard-library CLI/JSON/unittest. Pin reviewed dependency versions and image versions/digests during implementation.
- One fictional business, finished garments in integer pieces, `(sku_id, warehouse_id)` balance grain. Styles group color/size SKUs; they do not hold inventory.
- Synthetic data only. Checker reads operational inputs and writes reliability results only. No upload/form layer, ERP, ORM, scheduler, dashboard, forecasting, or LLM.
- Ledger and snapshot are independent observations. Missing data is never zero. Ambiguous input blocks quantity conclusions for affected buckets.
- Source batches/rows used by existing runs must remain available. Repeated checking creates a new run without rewriting previous findings.

## Database interface

Table/column names below are fixed. IDs/codes/statuses/references are `text`, quantities and source sequences are `bigint`, instants are `timestamptz`, counts are `integer`. `?` marks nullable columns; others are required. Fixture row IDs are primary keys. No business-reference foreign keys or business-key uniqueness constraints on movement/opening/snapshot rows: they must admit the seeded bad records.

```text
operational_fixture.styles
  style_id, style_code, name
operational_fixture.skus
  sku_id, style_id, sku_code, color, size, base_uom
operational_fixture.warehouses
  warehouse_id, warehouse_code, name
operational_fixture.batches
  batch_id, kind, status, baseline_at?, as_of, watermark?, observed_at,
  expected_row_count
operational_fixture.coverage
  row_id, batch_id, sku_id, warehouse_id
operational_fixture.opening_balances
  row_id, batch_id, sku_id, warehouse_id, quantity, as_of, baseline_ref
operational_fixture.movements
  row_id, batch_id, source_system, event_id, document_id, document_line_id,
  leg_id, sku_id, warehouse_id, quantity, movement_type, posting_status,
  effective_at, source_recorded_at, source_seq, observed_at,
  transfer_id?, reversal_of_row_id?, reason?
operational_fixture.snapshots
  row_id, batch_id, sku_id, warehouse_id, on_hand_qty, as_of, watermark?,
  observed_at
```

`base_uom=each`. Batch `kind=ledger|snapshot`, `status=complete|incomplete`; ledger baseline is required, snapshot baseline is null. Ledger expected row count counts all raw movement rows in that batch; snapshot count counts all raw snapshot rows. Opening balances/coverage are checked separately. Coverage explicitly lists expected SKU/warehouse keys, including zero stock; no sparse-zero convention in v1.

Movement `posting_status=posted|pending`; types are `receipt|shipment|return|adjustment|transfer|reversal`. Posted signed quantities supply the arithmetic. Posted reversal legs negate their original effects; never also remove the original from the sum. Multi-line documents and distinct transfer legs are legitimate, not duplicates.

Natural movement-leg key: `(source_system, event_id, document_line_id, leg_id)`, scoped to the selected ledger batch. `source_seq` is the upstream event sequence, not a local row ID or event-time timestamp; an immediate transfer's two legs share that sequence. Preserve recording/observation times separately from effective time.

Agent 1 also creates these storage tables, using report field types below:

```text
reliability.runs
  run_id uuid PK, contract_version, code_version, ledger_batch_id,
  snapshot_batch_id, as_of, evaluated_at, overall_status
reliability.check_results
  run_id uuid, rule_id, status; PK(run_id, rule_id)
reliability.findings
  run_id uuid, finding_id, rule_id, severity, reason, sku_id?, warehouse_id?,
  source_row_ids jsonb, expected_qty?, observed_qty?, delta_qty?, evidence jsonb;
  PK(run_id, finding_id)
```

Use foreign keys from reliability child tables to runs. Bootstrap creates a local `ii_runner` role with SELECT/USAGE on operational tables/schema and SELECT/INSERT/USAGE on reliability tables/schema, without operational write privileges. Password/configuration is synthetic local configuration, documented by Agent 1; never use real credentials. Runtime must not require schema creation privileges.

## Cutoff and checks

Both selected batch manifests must be complete, cover the same declared keys, and agree with requested cutoff `T` and watermark `W`. Each snapshot row must agree with its manifest. Opening balances match ledger baseline `t0`. Freshness uses `evaluated_at - snapshot.as_of`; v1 default is 24 hours, and exactly 24 hours is fresh. A future snapshot cutoff is invalid metadata.

Eligible movements belong to the selected ledger batch, are posted, and satisfy `t0 < effective_at <= T` and `source_seq <= W`. Higher-sequence late arrivals, pending movements, and movements after `T` do not affect this comparison. Check identity/transfers for eligible movements. Read/check/persist in one Repeatable Read transaction; retain the selected batch IDs and cutoff in the run.

```text
expected_qty = opening.quantity + sum(eligible signed quantities)
delta_qty = snapshot.on_hand_qty - expected_qty
```

Fixed rule IDs and reasons:

- `R001` quantity: `quantity_mismatch`, one finding per assessable mismatched bucket, with exact expected/observed/delta quantities.
- `R002` identity: `duplicate_movement_key`, one finding per duplicate natural-key group with all offending row IDs. Conflicting and identical duplicates both block their affected buckets; do not silently deduplicate.
- `R003` references/baseline: `unknown_reference` per offending movement/opening/snapshot row (evidence names unknown fields); `missing_opening_balance`, `duplicate_opening_balance`, or `opening_cutoff_mismatch` per affected covered bucket.
- `R004` transfers: `invalid_transfer` per eligible transfer ID. Require two posted transfer legs, same SKU/effective time/source sequence, different warehouses, and equal-and-opposite nonzero quantities. Evidence names broken conditions. Incomplete ledger extraction cannot prove a missing transfer leg; mark this check not assessable when the ledger batch is incomplete/missing.
- `R005` coverage/freshness: `missing_batch`, `incomplete_batch`, `count_mismatch`, `metadata_mismatch`, `stale_snapshot`, `coverage_mismatch` per affected batch; `missing_snapshot` or `duplicate_snapshot` per covered bucket. Check both manifests and unexpected snapshot keys, not just snapshot rows that happen to exist.

All v1 findings have `severity=error`. Quantity fields are null outside R001. Global manifest/cutoff/freshness failures block R001 for all buckets; local source/reference/opening/transfer/snapshot defects block affected buckets. Continue checks that can still establish defects from available evidence. Never emit a manufactured quantity delta for blocked buckets.

Exactly five check-result entries appear per successful execution. A rule is `fail` if it emitted findings, otherwise `not_assessable` if required comparisons were blocked, otherwise `pass`. R001 with some comparable and some blocked buckets is not fully passed. Overall: `fail` if any rule fails, else `not_assessable` if any rule is not assessable, else `pass`. Execution errors roll back that transaction and are separately reported; they must not become passes.

## Python and CLI interfaces

All connection arguments are idle Psycopg connections opened with `autocommit=True`; each function owns its transaction. Datetime arguments/context values are aware UTC `datetime` objects.

```python
# Agent 1: importable module, no dependency on the checker
synthetic.generate.load_scenario(conn, scenario_name: str) -> dict
# returns ledger_batch_id, snapshot_batch_id, as_of, evaluated_at

# Agent 2: owns the checker and persistence
inventory_intelligence.reliability.run_checks(
    conn, *, ledger_batch_id: str, snapshot_batch_id: str,
    as_of, evaluated_at, code_version: str = "dev",
    max_snapshot_age_hours: int = 24,
) -> dict
```

Fixture loading inserts deterministic, scenario-namespaced batches/rows in one transaction; refuse to overwrite an existing scenario. Tests load once and can check repeatedly. Source schemas are created beforehand with `sql/schema.sql`; the checker never initializes or reloads them.

Report dict fields: `run_id` (UUID string), `contract_version` (`"1"`), `code_version`, `ledger_batch_id`, `snapshot_batch_id`, `as_of`, `evaluated_at`, `overall_status`, `checks` (list of `{rule_id,status}`), and `findings` (list of storage fields above except `run_id`). Serialize timestamps as UTC ISO 8601. `finding_id` is a deterministic string; source row ID arrays are sorted, check entries sort by rule ID, findings sort by rule/reason/bucket/source IDs. Run IDs are the only required volatile report field.

CLI: `python -m inventory_intelligence --ledger-batch ID --snapshot-batch ID --as-of ISO --evaluated-at ISO --format json|markdown`, using `DATABASE_URL` for an `ii_runner` connection. Optional `--max-snapshot-age-hours` and `--code-version` match the library. Exit 0 pass, 1 fail/not-assessable, 2 execution/configuration error. Output goes to stdout; diagnostic errors to stderr. No automatic source repair or fixture loading in this command.

## Scenario and acceptance interface

Agent 1 supplies names `clean`, `quantity_mismatch`, `duplicate_movement`, `unknown_reference`, `invalid_transfer`, `stale_snapshot`, `missing_snapshot`, `combined`. Each isolated scenario changes only the relevant source evidence; its manifests should remain internally consistent unless manifest inconsistency is the fault. Combined includes duplicate, transfer, and quantity faults on separate buckets. Snapshot quantities are independent of checker SQL.

Agent 3 owns independent assertions and a manually calculated golden fixture. Assert exact rules/reasons/row IDs/buckets and deltas; counts alone are insufficient. Cover clean multi-line documents, zero stock, immediate transfer, posted reversal, pending rows, cutoff boundaries, higher-watermark late observations, missing/incomplete manifests, and conflicting duplicates. It may construct additional scenarios directly in its own fixtures using this schema.

Milestone acceptance requires real PostgreSQL tests, reproducible fresh-database setup, semantic stability on repeated checks, persisted run history, and proof that the runtime role cannot modify operational inputs. Demo corruption must cause the expected checker findings; integration tests pass only when those findings match their independent oracle.

Any change to table names, public signatures, rule/reason IDs, report shape, or temporal semantics requires a coordinated contract amendment. Do not privately change v1 in one branch. Internal implementation details remain each agent's choice.
