-- Additive bootstrap; Stage 1 schema and privileges stay frozen.
BEGIN;
CREATE SCHEMA planning_input;
CREATE SCHEMA planning;
CREATE TABLE planning_input.demand_batches (
    batch_id text PRIMARY KEY, version_id text NOT NULL,
    business_timezone text NOT NULL, start_day date NOT NULL, end_day date NOT NULL,
    assembled_at timestamptz NOT NULL, status text NOT NULL,
    expected_orders integer NOT NULL, expected_days integer NOT NULL
);
CREATE TABLE planning_input.order_versions (
    row_id text PRIMARY KEY, batch_id text NOT NULL,
    source_system text NOT NULL, order_id text NOT NULL, line_id text NOT NULL,
    revision integer NOT NULL, sku_id text NOT NULL, warehouse_id text NOT NULL,
    accepted_at timestamptz NOT NULL, source_recorded_at timestamptz NOT NULL,
    observed_at timestamptz NOT NULL, accepted_qty bigint NOT NULL, status text NOT NULL
);
CREATE TABLE planning_input.day_observations (
    row_id text PRIMARY KEY, batch_id text NOT NULL, sku_id text NOT NULL,
    warehouse_id text NOT NULL, business_day date NOT NULL, revision integer NOT NULL,
    source_recorded_at timestamptz NOT NULL, observed_at timestamptz NOT NULL,
    coverage text NOT NULL, availability text NOT NULL, expected_lines integer NOT NULL
);
REVOKE ALL ON SCHEMA planning_input, planning FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA planning_input FROM PUBLIC, ii_runner;
GRANT USAGE ON SCHEMA planning_input, planning TO ii_runner;
GRANT SELECT ON ALL TABLES IN SCHEMA planning_input TO ii_runner;
COMMIT;
