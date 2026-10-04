-- Continuation of views.sql. All operational relations are read-only.
manifest_metadata AS (
    SELECT m.selected_kind, m.selected_id, array_remove(ARRAY[
        CASE WHEN m.kind IS DISTINCT FROM m.selected_kind THEN 'kind' END,
        CASE WHEN m.status NOT IN ('complete', 'incomplete') THEN 'status' END,
        CASE WHEN m.as_of IS DISTINCT FROM p.cutoff THEN 'as_of' END,
        CASE WHEN m.watermark IS NULL OR
                       (l.watermark IS NOT NULL AND m.watermark IS DISTINCT FROM l.watermark)
             THEN 'watermark' END,
        CASE WHEN m.selected_kind = 'ledger' AND
                       (m.baseline_at IS NULL OR m.baseline_at > p.cutoff)
                  OR m.selected_kind = 'snapshot' AND m.baseline_at IS NOT NULL
             THEN 'baseline_at' END,
        CASE WHEN m.as_of > p.evaluated_at THEN 'future_cutoff' END,
        CASE WHEN m.expected_row_count < 0 THEN 'expected_row_count' END
    ], NULL) AS broken_conditions
    FROM manifests m, ledger l, p WHERE m.batch_id IS NOT NULL
),
coverage_problems AS (
    SELECT m.selected_kind AS kind, NULL::text AS row_id, NULL::text AS sku_id,
           NULL::text AS warehouse_id, 'empty_coverage' AS problem
    FROM manifests m WHERE m.batch_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM coverage c WHERE c.kind = m.selected_kind
    )
    UNION ALL
    SELECT c.kind, c.row_id, c.sku_id, c.warehouse_id, 'unknown_coverage_reference' AS problem
    FROM coverage c LEFT JOIN operational_fixture.skus s USING (sku_id)
    LEFT JOIN operational_fixture.warehouses w USING (warehouse_id)
    WHERE s.sku_id IS NULL OR w.warehouse_id IS NULL
    UNION ALL
    SELECT c.kind, c.row_id, c.sku_id, c.warehouse_id, 'duplicate_coverage'
    FROM coverage c JOIN (
        SELECT kind, sku_id, warehouse_id FROM coverage GROUP BY kind, sku_id, warehouse_id
        HAVING count(*) > 1
    ) d USING (kind, sku_id, warehouse_id)
    UNION ALL
    SELECT 'ledger', NULL, sku_id, warehouse_id, 'keys_disagree'
    FROM (SELECT * FROM snapshot_keys EXCEPT SELECT * FROM ledger_keys) d
    UNION ALL
    SELECT 'snapshot', NULL, sku_id, warehouse_id, 'keys_disagree'
    FROM (SELECT * FROM ledger_keys EXCEPT SELECT * FROM snapshot_keys) d
    UNION ALL
    SELECT 'snapshot', s.row_id, s.sku_id, s.warehouse_id, 'unexpected_snapshot_key'
    FROM snapshots s WHERE NOT EXISTS (
        SELECT 1 FROM snapshot_keys k WHERE (k.sku_id, k.warehouse_id) = (s.sku_id, s.warehouse_id)
    )
    UNION ALL
    SELECT 'ledger', o.row_id, o.sku_id, o.warehouse_id, 'unexpected_opening_key'
    FROM openings o WHERE NOT EXISTS (
        SELECT 1 FROM ledger_keys k WHERE (k.sku_id, k.warehouse_id) = (o.sku_id, o.warehouse_id)
    )
    UNION ALL
    SELECT 'ledger', m.row_id, m.sku_id, m.warehouse_id, 'unexpected_movement_key'
    FROM movements m WHERE NOT EXISTS (
        SELECT 1 FROM unknown_rows r WHERE r.source = 'movement' AND r.row_id = m.row_id
    ) AND NOT EXISTS (
        SELECT 1 FROM ledger_keys k WHERE (k.sku_id, k.warehouse_id) = (m.sku_id, m.warehouse_id)
    )
),
row_metadata AS (
    SELECT 'snapshot' AS kind, s.row_id, jsonb_build_object(
        'row_id', s.row_id, 'as_of', s.as_of, 'watermark', s.watermark,
        'conditions', array_remove(ARRAY[
            CASE WHEN b.batch_id IS NOT NULL AND s.as_of IS DISTINCT FROM b.as_of THEN 'as_of' END,
            CASE WHEN b.batch_id IS NOT NULL AND s.watermark IS DISTINCT FROM b.watermark THEN 'watermark' END,
            CASE WHEN s.as_of > p.evaluated_at THEN 'future_cutoff' END
        ], NULL)) AS detail
    FROM snapshots s, snapshot b, p
    WHERE b.batch_id IS NOT NULL AND (s.as_of IS DISTINCT FROM b.as_of OR s.watermark IS DISTINCT FROM b.watermark)
       OR s.as_of > p.evaluated_at
    UNION ALL
    SELECT 'ledger', m.row_id, jsonb_build_object('row_id', m.row_id, 'conditions', 'invalid_movement_enum')
    FROM movements m WHERE m.posting_status NOT IN ('posted', 'pending')
       OR m.movement_type NOT IN ('receipt', 'shipment', 'return', 'adjustment', 'transfer', 'reversal')
    UNION ALL
    SELECT CASE r.source WHEN 'snapshot' THEN 'snapshot' ELSE 'ledger' END, r.row_id,
           jsonb_build_object('row_id', r.row_id, 'conditions', 'base_uom', 'base_uom', s.base_uom)
    FROM source_rows r JOIN operational_fixture.skus s USING (sku_id) WHERE s.base_uom <> 'each'
),
defects(rule_id, reason, sku_id, warehouse_id, row_ids, evidence) AS (
    SELECT 'R002'::text, 'duplicate_movement_key'::text, NULL::text, NULL::text, d.row_ids,
           jsonb_build_object('source_system', d.source_system, 'event_id', d.event_id,
                              'document_line_id', d.document_line_id, 'leg_id', d.leg_id)
    FROM duplicate_keys d
    UNION ALL
    SELECT 'R003', 'unknown_reference', sku_id, warehouse_id, ARRAY[row_id],
           jsonb_build_object('source', source, 'unknown_fields', unknown_fields)
    FROM unknown_rows
    UNION ALL
    SELECT 'R003', CASE WHEN row_count = 0 THEN 'missing_opening_balance' ELSE 'duplicate_opening_balance' END,
           sku_id, warehouse_id, row_ids, jsonb_build_object('row_count', row_count)
    FROM opening_groups WHERE row_count <> 1
    UNION ALL
    SELECT 'R003', 'opening_cutoff_mismatch', sku_id, warehouse_id, row_ids,
           jsonb_build_object('baseline_at', l.baseline_at)
    FROM opening_groups, ledger l WHERE wrong_cutoff
    UNION ALL
    SELECT 'R004', 'invalid_transfer', NULL, NULL, row_ids,
           jsonb_build_object('transfer_id', transfer_id, 'broken_conditions', broken_conditions)
    FROM transfer_groups WHERE cardinality(broken_conditions) > 0
    UNION ALL
    SELECT 'R005', 'missing_batch', NULL, NULL, ARRAY[]::text[],
           jsonb_build_object('batch_id', selected_id, 'kind', selected_kind)
    FROM manifests WHERE batch_id IS NULL
    UNION ALL
    SELECT 'R005', 'incomplete_batch', NULL, NULL, ARRAY[]::text[],
           jsonb_build_object('batch_id', selected_id, 'kind', selected_kind)
    FROM manifests WHERE status = 'incomplete'
    UNION ALL
    SELECT 'R005', 'count_mismatch', NULL, NULL, ARRAY[]::text[],
           jsonb_build_object('batch_id', selected_id, 'kind', selected_kind,
                              'expected_row_count', expected_row_count, 'actual_row_count', actual)
    FROM manifests m CROSS JOIN LATERAL (
        SELECT CASE m.selected_kind WHEN 'ledger' THEN (SELECT count(*) FROM movements)
                    ELSE (SELECT count(*) FROM snapshots) END AS actual
    ) n WHERE m.batch_id IS NOT NULL AND expected_row_count <> actual
    UNION ALL
    SELECT 'R005', 'metadata_mismatch', NULL, NULL,
           ARRAY(SELECT DISTINCT r.row_id FROM row_metadata r
                 WHERE r.kind = m.selected_kind ORDER BY r.row_id),
           jsonb_build_object('batch_id', m.selected_id, 'kind', m.selected_kind,
               'broken_conditions', m.broken_conditions,
               'row_metadata', COALESCE((SELECT jsonb_agg(r.detail ORDER BY r.row_id, r.detail::text)
                                        FROM row_metadata r WHERE r.kind = m.selected_kind), '[]'::jsonb))
    FROM manifest_metadata m WHERE cardinality(m.broken_conditions) > 0
       OR EXISTS (SELECT 1 FROM row_metadata r WHERE r.kind = m.selected_kind)
    UNION ALL
    SELECT 'R005', 'metadata_mismatch', NULL, NULL,
           ARRAY(SELECT DISTINCT r.row_id FROM row_metadata r
                 WHERE r.kind = m.selected_kind ORDER BY r.row_id),
           jsonb_build_object('batch_id', m.selected_id, 'kind', m.selected_kind,
               'row_metadata', (SELECT jsonb_agg(r.detail ORDER BY r.row_id, r.detail::text)
                               FROM row_metadata r WHERE r.kind = m.selected_kind))
    FROM manifests m WHERE m.batch_id IS NULL
       AND EXISTS (SELECT 1 FROM row_metadata r WHERE r.kind = m.selected_kind)
    UNION ALL
    SELECT 'R005', 'stale_snapshot', NULL, NULL,
           ARRAY(SELECT row_id FROM snapshots r WHERE p.evaluated_at - r.as_of > p.max_age ORDER BY row_id),
           jsonb_build_object('batch_id', s.selected_id, 'as_of', s.as_of,
                              'evaluated_at', p.evaluated_at, 'max_age_hours', %(max_snapshot_age_hours)s::integer)
    FROM snapshot s, p WHERE p.evaluated_at - s.as_of > p.max_age
    UNION ALL
    SELECT 'R005', 'coverage_mismatch', NULL, NULL,
           array_remove(array_agg(DISTINCT c.row_id ORDER BY c.row_id), NULL),
           jsonb_build_object('batch_id', m.selected_id, 'kind', m.selected_kind,
               'problems', jsonb_agg(jsonb_build_object('sku_id', c.sku_id, 'warehouse_id', c.warehouse_id,
                   'row_id', c.row_id, 'problem', c.problem) ORDER BY c.sku_id, c.warehouse_id, c.problem, c.row_id))
    FROM coverage_problems c JOIN manifests m ON m.selected_kind = c.kind
    GROUP BY m.selected_id, m.selected_kind
    UNION ALL
    SELECT 'R005', CASE WHEN row_count = 0 THEN 'missing_snapshot' ELSE 'duplicate_snapshot' END,
           sku_id, warehouse_id, row_ids, jsonb_build_object('row_count', row_count)
    FROM snapshot_groups WHERE row_count <> 1
),
blocked_keys AS (
    SELECT sku_id, warehouse_id FROM defects WHERE sku_id IS NOT NULL AND warehouse_id IS NOT NULL
    UNION
    SELECT m.sku_id, m.warehouse_id FROM eligible m
    JOIN defects d ON d.rule_id IN ('R002', 'R004') AND m.row_id = ANY(d.row_ids)
),
global_block AS (
    SELECT EXISTS (SELECT 1 FROM defects WHERE rule_id = 'R005'
                  AND reason NOT IN ('missing_snapshot', 'duplicate_snapshot')) AS blocked
),
comparable AS (
    SELECT k.* FROM keys k, global_block g WHERE NOT g.blocked
    AND NOT EXISTS (SELECT 1 FROM blocked_keys b
                    WHERE (b.sku_id, b.warehouse_id) = (k.sku_id, k.warehouse_id))
),
movement_totals AS (
    SELECT sku_id, warehouse_id, sum(quantity::numeric) AS quantity,
           array_agg(row_id) AS row_ids
    FROM eligible GROUP BY sku_id, warehouse_id
),
quantities AS (
    SELECT k.sku_id, k.warehouse_id,
           (o.quantity::numeric + COALESCE(m.quantity, 0))::bigint AS expected_qty,
           s.on_hand_qty AS observed_qty,
           ARRAY(SELECT row_id FROM unnest(
               ARRAY[o.row_id, s.row_id] || COALESCE(m.row_ids, ARRAY[]::text[])
           ) r(row_id) ORDER BY row_id) AS row_ids
    FROM comparable k JOIN openings o USING (sku_id, warehouse_id)
    JOIN snapshots s USING (sku_id, warehouse_id)
    LEFT JOIN movement_totals m USING (sku_id, warehouse_id)
),
findings AS (
    SELECT rule_id, reason, sku_id, warehouse_id, row_ids AS source_row_ids,
           NULL::bigint AS expected_qty, NULL::bigint AS observed_qty, NULL::bigint AS delta_qty, evidence
    FROM defects
    UNION ALL
    SELECT 'R001', 'quantity_mismatch', q.sku_id, q.warehouse_id, q.row_ids,
           q.expected_qty, q.observed_qty, (q.observed_qty::numeric - q.expected_qty)::bigint,
           jsonb_build_object('baseline_at', l.baseline_at, 'watermark', l.watermark)
    FROM quantities q, ledger l WHERE q.expected_qty <> q.observed_qty
),
ledger_scope AS (
    SELECT COALESCE(l.status = 'complete' AND l.kind = 'ledger' AND l.as_of = p.cutoff
        AND l.baseline_at <= p.cutoff AND l.watermark IS NOT NULL
        AND l.expected_row_count = (SELECT count(*) FROM movements), false) AS assessable
    FROM ledger l, p
),
rule_blocks(rule_id, blocked) AS (
    SELECT 'R001'::text, g.blocked OR EXISTS (SELECT 1 FROM blocked_keys)
    FROM global_block g
    UNION ALL SELECT 'R002', NOT assessable FROM ledger_scope
    UNION ALL SELECT 'R003', NOT ls.assessable OR COALESCE(s.status <> 'complete', true)
    FROM ledger_scope ls, snapshot s
    UNION ALL SELECT 'R004', NOT assessable FROM ledger_scope
    UNION ALL SELECT 'R005', false
)
SELECT jsonb_build_object(
    'checks', (SELECT jsonb_agg(jsonb_build_object('rule_id', b.rule_id, 'status',
        CASE WHEN EXISTS (SELECT 1 FROM findings f WHERE f.rule_id = b.rule_id) THEN 'fail'
             WHEN b.blocked THEN 'not_assessable' ELSE 'pass' END) ORDER BY b.rule_id) FROM rule_blocks b),
    'findings', COALESCE((SELECT jsonb_agg(to_jsonb(f) || jsonb_build_object('evidence',
        f.evidence || jsonb_build_object(
            'source_records', COALESCE((SELECT jsonb_agg(jsonb_build_object('source', r.source, 'record', r.record)
                                                       ORDER BY r.source, r.row_id)
                                       FROM source_rows r WHERE r.row_id = ANY(f.source_row_ids)), '[]'::jsonb),
            'manifests', (SELECT jsonb_agg(to_jsonb(m) ORDER BY selected_kind) FROM manifests m)
        )) ORDER BY rule_id, reason, sku_id, warehouse_id, source_row_ids, evidence::text)
        FROM findings f), '[]'::jsonb)
);
