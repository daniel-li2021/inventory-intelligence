-- Read-only projections, composed with checks.sql in a single parameterized query.
-- These are CTEs, not installed views: ii_runner needs no DDL privileges.
WITH
p AS (
    SELECT %(ledger_batch_id)s::text AS ledger_id,
           %(snapshot_batch_id)s::text AS snapshot_id,
           %(as_of)s::timestamptz AS cutoff,
           %(evaluated_at)s::timestamptz AS evaluated_at,
           %(max_snapshot_age_hours)s::integer * interval '1 hour' AS max_age
),
selected AS (
    SELECT 'ledger'::text AS kind, ledger_id AS batch_id FROM p
    UNION ALL SELECT 'snapshot', snapshot_id FROM p
),
manifests AS (
    SELECT s.kind AS selected_kind, s.batch_id AS selected_id, b.*
    FROM selected s LEFT JOIN operational_fixture.batches b USING (batch_id)
),
ledger AS (SELECT * FROM manifests WHERE selected_kind = 'ledger'),
snapshot AS (SELECT * FROM manifests WHERE selected_kind = 'snapshot'),
coverage AS (
    SELECT c.*, s.kind FROM operational_fixture.coverage c
    JOIN selected s USING (batch_id)
),
ledger_keys AS (SELECT DISTINCT sku_id, warehouse_id FROM coverage WHERE kind = 'ledger'),
snapshot_keys AS (SELECT DISTINCT sku_id, warehouse_id FROM coverage WHERE kind = 'snapshot'),
keys AS (SELECT * FROM ledger_keys UNION SELECT * FROM snapshot_keys),
openings AS (
    SELECT o.* FROM operational_fixture.opening_balances o, p
    WHERE o.batch_id = p.ledger_id
),
movements AS (
    SELECT m.* FROM operational_fixture.movements m, p WHERE m.batch_id = p.ledger_id
),
snapshots AS (
    SELECT s.* FROM operational_fixture.snapshots s, p WHERE s.batch_id = p.snapshot_id
),
eligible AS (
    SELECT m.* FROM movements m, ledger l, p
    WHERE m.posting_status = 'posted'
      AND l.baseline_at < m.effective_at AND m.effective_at <= p.cutoff
      AND m.source_seq <= l.watermark
),
source_rows AS (
    SELECT 'movement'::text AS source, row_id, sku_id, warehouse_id, to_jsonb(m) AS record FROM movements m
    UNION ALL SELECT 'opening', row_id, sku_id, warehouse_id, to_jsonb(o) FROM openings o
    UNION ALL SELECT 'snapshot', row_id, sku_id, warehouse_id, to_jsonb(s) FROM snapshots s
),
unknown_rows AS (
    SELECT r.*, array_remove(ARRAY[
        CASE WHEN s.sku_id IS NULL THEN 'sku_id' END,
        CASE WHEN w.warehouse_id IS NULL THEN 'warehouse_id' END,
        CASE WHEN s.sku_id IS NOT NULL AND st.style_id IS NULL THEN 'style_id' END,
        CASE WHEN r.source = 'movement' AND r.record->>'reversal_of_row_id' IS NOT NULL
                  AND NOT EXISTS (SELECT 1 FROM operational_fixture.movements original
                                  WHERE original.row_id = r.record->>'reversal_of_row_id')
             THEN 'reversal_of_row_id' END
    ], NULL) AS unknown_fields
    FROM source_rows r
    LEFT JOIN operational_fixture.skus s USING (sku_id)
    LEFT JOIN operational_fixture.styles st USING (style_id)
    LEFT JOIN operational_fixture.warehouses w USING (warehouse_id)
    WHERE s.sku_id IS NULL OR w.warehouse_id IS NULL OR st.style_id IS NULL
       OR r.source = 'movement' AND r.record->>'reversal_of_row_id' IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM operational_fixture.movements original
                          WHERE original.row_id = r.record->>'reversal_of_row_id')
),
duplicate_keys AS (
    SELECT source_system, event_id, document_line_id, leg_id,
           array_agg(row_id ORDER BY row_id) AS row_ids
    FROM eligible GROUP BY source_system, event_id, document_line_id, leg_id
    HAVING count(*) > 1
),
opening_groups AS (
    SELECT k.sku_id, k.warehouse_id, count(o.row_id) AS row_count,
           array_remove(array_agg(o.row_id ORDER BY o.row_id), NULL) AS row_ids,
           bool_or(o.as_of IS DISTINCT FROM l.baseline_at)
               FILTER (WHERE o.row_id IS NOT NULL AND l.baseline_at IS NOT NULL) AS wrong_cutoff
    FROM keys k LEFT JOIN openings o USING (sku_id, warehouse_id)
    CROSS JOIN ledger l GROUP BY k.sku_id, k.warehouse_id
),
snapshot_groups AS (
    SELECT k.sku_id, k.warehouse_id, count(s.row_id) AS row_count,
           array_remove(array_agg(s.row_id ORDER BY s.row_id), NULL) AS row_ids
    FROM keys k LEFT JOIN snapshots s USING (sku_id, warehouse_id)
    GROUP BY k.sku_id, k.warehouse_id
),
transfer_groups AS (
    SELECT transfer_id, array_agg(row_id ORDER BY row_id) AS row_ids,
           array_remove(ARRAY[
               CASE WHEN transfer_id IS NULL THEN 'missing_transfer_id' END,
               CASE WHEN count(*) <> 2 THEN 'leg_count' END,
               CASE WHEN count(DISTINCT sku_id) <> 1 THEN 'same_sku' END,
               CASE WHEN count(DISTINCT effective_at) <> 1 THEN 'same_effective_at' END,
               CASE WHEN count(DISTINCT source_seq) <> 1 THEN 'same_source_seq' END,
               CASE WHEN count(DISTINCT warehouse_id) <> 2 THEN 'different_warehouses' END,
               CASE WHEN count(*) <> 2 OR min(abs(quantity::numeric)) = 0
                          OR sum(quantity::numeric) <> 0 THEN 'equal_opposite_nonzero' END
           ], NULL) AS broken_conditions
    FROM eligible, ledger l, p
    WHERE movement_type = 'transfer' AND l.status = 'complete'
      AND l.kind = 'ledger' AND l.as_of = p.cutoff AND l.baseline_at <= p.cutoff
      AND l.watermark IS NOT NULL AND l.expected_row_count = (SELECT count(*) FROM movements)
    GROUP BY transfer_id
),
