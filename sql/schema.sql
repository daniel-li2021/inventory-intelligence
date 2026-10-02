-- Fresh-database bootstrap, run as the local database owner.
BEGIN;
CREATE SCHEMA operational_fixture;
CREATE SCHEMA reliability;

CREATE TABLE operational_fixture.styles (
    style_id text PRIMARY KEY, style_code text NOT NULL, name text NOT NULL
);
CREATE TABLE operational_fixture.skus (
    sku_id text PRIMARY KEY, style_id text NOT NULL, sku_code text NOT NULL,
    color text NOT NULL, size text NOT NULL, base_uom text NOT NULL
);
CREATE TABLE operational_fixture.warehouses (
    warehouse_id text PRIMARY KEY, warehouse_code text NOT NULL, name text NOT NULL
);
CREATE TABLE operational_fixture.batches (
    batch_id text PRIMARY KEY, kind text NOT NULL, status text NOT NULL,
    baseline_at timestamptz, as_of timestamptz NOT NULL, watermark bigint,
    observed_at timestamptz NOT NULL, expected_row_count integer NOT NULL
);
CREATE TABLE operational_fixture.coverage (
    row_id text PRIMARY KEY, batch_id text NOT NULL, sku_id text NOT NULL,
    warehouse_id text NOT NULL
);
CREATE TABLE operational_fixture.opening_balances (
    row_id text PRIMARY KEY, batch_id text NOT NULL, sku_id text NOT NULL,
    warehouse_id text NOT NULL, quantity bigint NOT NULL,
    as_of timestamptz NOT NULL, baseline_ref text NOT NULL
);
CREATE TABLE operational_fixture.movements (
    row_id text PRIMARY KEY, batch_id text NOT NULL, source_system text NOT NULL,
    event_id text NOT NULL, document_id text NOT NULL, document_line_id text NOT NULL,
    leg_id text NOT NULL, sku_id text NOT NULL, warehouse_id text NOT NULL,
    quantity bigint NOT NULL, movement_type text NOT NULL, posting_status text NOT NULL,
    effective_at timestamptz NOT NULL, source_recorded_at timestamptz NOT NULL,
    source_seq bigint NOT NULL, observed_at timestamptz NOT NULL,
    transfer_id text, reversal_of_row_id text, reason text
);
CREATE TABLE operational_fixture.snapshots (
    row_id text PRIMARY KEY, batch_id text NOT NULL, sku_id text NOT NULL,
    warehouse_id text NOT NULL, on_hand_qty bigint NOT NULL,
    as_of timestamptz NOT NULL, watermark bigint, observed_at timestamptz NOT NULL
);

CREATE TABLE reliability.runs (
    run_id uuid PRIMARY KEY, contract_version text NOT NULL, code_version text NOT NULL,
    ledger_batch_id text NOT NULL, snapshot_batch_id text NOT NULL,
    as_of timestamptz NOT NULL, evaluated_at timestamptz NOT NULL,
    overall_status text NOT NULL
);
CREATE TABLE reliability.check_results (
    run_id uuid NOT NULL REFERENCES reliability.runs(run_id),
    rule_id text NOT NULL, status text NOT NULL, PRIMARY KEY (run_id, rule_id)
);
CREATE TABLE reliability.findings (
    run_id uuid NOT NULL REFERENCES reliability.runs(run_id),
    finding_id text NOT NULL, rule_id text NOT NULL, severity text NOT NULL,
    reason text NOT NULL, sku_id text, warehouse_id text,
    source_row_ids jsonb NOT NULL, expected_qty bigint, observed_qty bigint,
    delta_qty bigint, evidence jsonb NOT NULL, PRIMARY KEY (run_id, finding_id)
);

-- Synthetic local credentials only. A role may already exist in this cluster.
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ii_runner') THEN
        CREATE ROLE ii_runner LOGIN PASSWORD 'ii_runner_local'
            NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
    END IF;
    IF EXISTS (
        SELECT FROM pg_roles WHERE rolname = 'ii_runner'
        AND (NOT rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolinherit OR rolreplication OR rolbypassrls)
    ) OR EXISTS (
        SELECT FROM pg_auth_members WHERE member = 'ii_runner'::regrole
    ) THEN
        RAISE EXCEPTION 'ii_runner must be an unprivileged role without memberships';
    END IF;
END $$;
REVOKE ALL ON SCHEMA operational_fixture, reliability FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA operational_fixture, reliability FROM PUBLIC;
REVOKE ALL ON SCHEMA operational_fixture, reliability FROM ii_runner;
REVOKE ALL ON ALL TABLES IN SCHEMA operational_fixture, reliability FROM ii_runner;
GRANT USAGE ON SCHEMA operational_fixture, reliability TO ii_runner;
GRANT SELECT ON ALL TABLES IN SCHEMA operational_fixture TO ii_runner;
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA reliability TO ii_runner;
COMMIT;
