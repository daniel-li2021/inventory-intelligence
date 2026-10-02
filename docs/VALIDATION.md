# Independent milestone 1 validation

The standard-library `unittest` suite uses real PostgreSQL 17 and the frozen [contract](CONTRACT_V1.md). Neither SQLite nor SQL mocks provide milestone evidence. `TEST_DATABASE_URL` must select a disposable fixture-owner connection, and `DATABASE_URL` must select `ii_runner` in the same database. Missing modules, URLs, schema, or database are errors; tests are never skipped to manufacture a pass.

## Independent arithmetic and evidence

`tests/golden.py` inserts its own fixture without using the scenario generator or checker SQL. Four snapshot observations are manually supplied:

| SKU / warehouse | Opening | Eligible signed movements | Expected |
| --- | ---: | --- | ---: |
| shirt / a | 100 | +10 −7 −5 +7 +4 | 109 |
| shirt / b | 20 | +5 | 25 |
| coat / a | 10 | +2 +3 | 15 |
| zero / a | 0 | no movements | 0 |

The −7 shipment and +7 posted reversal both remain in arithmetic. The two coat rows share an event/document but have distinct lines. The transfer's two legs share the upstream sequence. Pending rows, events exactly at the opening baseline, events after the cutoff, and rows above the selected watermark are excluded. Both coat receipts occur exactly at the inclusive cutoff; the higher-sequence late observation is excluded despite an effective time before it. Snapshot age exactly 24 hours passes; one microsecond older fails.

Tests deliberately change observations by +1 to prove all four expected quantities are actually evaluated; a checker that returns an empty report cannot pass. Fault assertions cover rule/reason multiplicity, source IDs, affected buckets, exact quantities and signed deltas, and null quantities outside R001. Duplicate groups may span buckets, so their nullable top-level bucket fields are supplemented by source evidence.

Additional cases cover identical/conflicting duplicate natural keys, missing/duplicate/wrong-cutoff opening balances, references in movements/openings/snapshots, invalid/missing transfer legs, absent/incomplete/count-mismatched manifests, manifest and row metadata, missing/duplicate snapshots, and coverage discrepancies. Blocked buckets cannot receive invented deltas; assessable controls remain independently checked. The eight generator scenarios have separately written expected findings, including the combined jacket delta `26 − 25 = +1`.

Repeat checks assert semantic equality excluding only `run_id`, distinct persisted runs, exact stored check/findings values, and complete operational row equality before/after. A forced child-result constraint failure proves that a partially inserted run rolls back completely. Quantities above floating-point precision remain exact integer pieces. Runtime role tests execute prohibited writes/DDL against PostgreSQL and require permission-denied errors. CLI assertions require exit 0 for clean data, 1 for dirty data, and 2 for configuration errors, with JSON/Markdown output checks.

## Run locally

Install the pinned environment and start a **fresh**, separate Compose project using the [README](../README.md#independent-acceptance). Compose initializes the source and reliability schemas. Run:

```sh
python -m unittest discover -s tests -v
```

The suite retains its generated source inputs and run history; it does not truncate or reset schemas. Named scenarios must be absent at the first suite execution. For another complete suite execution, use a new disposable database/project rather than overwriting existing evidence. Individual golden-fixture tests generate separate namespaced inputs and can be rerun in the existing acceptance database.

On a fresh PostgreSQL database without Compose's initialization mount, initialize explicitly before testing:

```sh
python -m tests.bootstrap
python -m unittest discover -s tests -v
```

`tests.bootstrap` reads `sql/schema.sql` and refuses an existing operational schema. It never resets existing source inputs.

## CI

`PostgreSQL acceptance` uses a service with PostgreSQL 17.9 pinned by manifest digest, a pinned Python setup action, Python 3.12.12, and pinned pip/setuptools/wheel/typing-extensions. Installing the engine's `pyproject.toml` supplies its exact Psycopg binary dependency. The job bootstraps a new database and runs the same acceptance command. Repository hygiene remains a separate job. Service-container networking follows [GitHub's PostgreSQL service guidance](https://docs.github.com/en/actions/tutorials/use-containerized-services/create-postgresql-service-containers).

There are no secrets, external operational data, deployment jobs, or schedules. Configure branch protection to require `PostgreSQL acceptance` after its first successful remote execution; adding the workflow alone does not change repository settings.

## Integration evidence

Final local acceptance on 2026-10-02 uses Python 3.12.12, Psycopg 3.3.6, and PostgreSQL 17.9. The validation branch integrates:

- Data foundation: `f6115547a39f9d9eb714145c8a55129b3c552002`.
- Original engine: `0502c2f`.
- Engine corrections found by independent acceptance: `a90d7a167c66ee6ddc61c83fb511a703c3160f45`.

The corrections preserve local reference blocking, avoid comparison against an unavailable ledger watermark, and assess freshness at the manifest cutoff while reporting disagreeing row metadata separately. No independent oracle was weakened to accept those defects.

Executed in the combined checkout against a fresh dedicated database (`validation_final`, local port 55433):

```sh
python -m pip install --no-build-isolation .
python -m tests.bootstrap
python -m unittest discover -s tests -v
```

Result: **21 tests passed**, zero failures/errors/skips. Compose fresh-volume initialization was separately verified with `COMPOSE_PROJECT_NAME=ii_validation_demo POSTGRES_PORT=55434 docker compose up -d --wait`. Both `combined` and `clean` were loaded through the documented generator command. Combined CLI returned exit 1 with exactly R001/R002/R004 (jacket expected 25, observed 26, delta +1); clean returned exit 0 without findings. The installed final report's retained fields exactly match [the curated example](examples/combined.md).

CI YAML parsing, Compose configuration validation, Python compilation, research JSON parsing, and whitespace checks also passed. Remote workflow verification is recorded below after the branch is published. `main` integration/merging and branch-protection configuration remain the coordinator's responsibility.
