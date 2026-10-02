# Milestone 1 data foundation

Implements [contract v1](CONTRACT_V1.md): PostgreSQL source/result storage,
local Compose bootstrap, and deterministic fictional Northwind Apparel fixtures.
Loading never runs the checker or changes source rows already present. All
quantities are signed integer garment pieces (`bigint`, `base_uom=each`).

## Fresh local bootstrap

Requirements: Docker Desktop/Engine with Compose, Python 3.12, and Psycopg 3.
Run from this branch's repository/worktree root. The reviewed pins are
[`postgres:17.9`](https://hub.docker.com/_/postgres/tags?name=17.9) and
[`psycopg[binary]==3.2.10`](https://pypi.org/project/psycopg/3.2.10/).
Compose also locks the tested image manifest digest
`sha256:2a0d0fe14825b0939f78a8cad5cd4e6aa68bf94d0e5dd96e24b6d23af4315545`.
The foundation does not own the shared `pyproject.toml`; these commands install
only the database driver in a local environment.

```sh
cp .env.example .env
# Before starting, edit project name and port if another worktree is running.
set -a
. ./.env
set +a
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install 'psycopg[binary]==3.2.10'
docker compose config --quiet
docker compose up -d --wait
```

The default project is `ii-stage1-data`, database `inventory_intelligence`, and
host port `55432`, bound only to `127.0.0.1`. Parallel worktrees must use distinct
`COMPOSE_PROJECT_NAME` and `POSTGRES_PORT`; change both connection URLs to match
that port. Docker uses `.env` automatically; Python requires the exported variables.
If Docker's bundled CLI is outside your shell PATH on macOS, first run:

```sh
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
docker desktop start
```

Compose mounts `sql/schema.sql` into the official image's initialization directory.
On a **fresh** volume it atomically creates `operational_fixture`, `reliability`,
and the local `ii_runner` login. Bootstrap is intentionally not a migration and
refuses existing schemas. Restarting an existing volume does not reload SQL or data.
Stop this project's containers without deleting their retained data:

```sh
docker compose down
```

For a separately created empty PostgreSQL 17 database, apply the same bootstrap
using an owner connection (the database must not already contain these schemas):

```sh
psql "$FIXTURE_DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/schema.sql
```

## Connection roles

`.env.example` contains synthetic, local-only credentials:

- Owner/loader: `ii_owner`, password `ii_owner_local`, via `FIXTURE_DATABASE_URL`.
- Checker: `ii_runner`, password `ii_runner_local`, via `DATABASE_URL`.

The owner creates schema and loads scenarios. `ii_runner` has schema USAGE and
SELECT on operational inputs, plus SELECT/INSERT on reliability results. It cannot
INSERT/UPDATE/DELETE/TRUNCATE operational tables, create tables in either schema,
or UPDATE/DELETE results. Runtime does not need schema-creation privileges.
Reliability child tables reference their run through foreign keys.
An existing cluster-wide `ii_runner` must be unprivileged and have no role
memberships; bootstrap refuses elevated roles and leaves existing passwords alone.
The Compose database gets the documented password when the role is first created.

Operational rows enforce primary-key row identity and required field types only.
They deliberately have no business-reference foreign keys, business-key uniqueness,
or enum checks that would reject raw defect evidence. Duplicate movement identities,
unknown references, duplicate opening/snapshot buckets, and broken manifests can
therefore be inspected by the checker. No source repair occurs in this layer.

## Load and reuse scenarios

```sh
python -m synthetic.generate clean
python -m synthetic.generate combined
# Or use --database-url with an explicit owner connection.
```

Each prints the two batch IDs and aware UTC cutoff/evaluation instants as JSON.
IDs for all catalogs, batches, coverage, opening, movement and snapshot rows are
prefixed `<scenario>:`. Namespaces coexist in the same database. A second load of
any existing namespace raises `ValueError` (CLI exit 2), without overwriting or
deleting inputs. The loader inserts all rows in one transaction and writes no
reliability results. Concurrent loads of the same namespace cannot overwrite data;
a primary-key conflict rolls back the losing load.

```python
import os
import psycopg
from synthetic.generate import load_scenario

with psycopg.connect(os.environ["FIXTURE_DATABASE_URL"], autocommit=True) as conn:
    context = load_scenario(conn, "quantity_mismatch")
# context: ledger_batch_id, snapshot_batch_id, as_of, evaluated_at
# Pass context to the engine separately using an ii_runner connection.
```

The connection must be idle with `autocommit=True`; the loader owns its transaction.
No table creation happens inside `load_scenario`.

| Scenario | Deliberate source change |
| --- | --- |
| `clean` | Complete controls, no corruption |
| `quantity_mismatch` | Jacket/harbor snapshot 26 instead of independently expected 25; delta +1 |
| `duplicate_movement` | Duplicate hoodie receipt natural key, separate raw row ID |
| `unknown_reference` | Extra posted row referring to `unknown-sku` |
| `invalid_transfer` | Tee inbound transfer +3 against outbound -4 |
| `stale_snapshot` | Evaluation is 24 hours and 1 second after snapshot cutoff |
| `missing_snapshot` | Zero-stock tee-L/harbor snapshot absent despite explicit coverage |
| `combined` | Duplicate hoodie receipt, broken tee transfer, jacket quantity mismatch on separate buckets |

All raw movement and snapshot counts match their manifests, including fault
scenarios; missing snapshot coverage is distinct from a raw count mismatch.
There are five declared buckets per batch and five opening balances per scenario.
Each scenario has 13 movements (14 for duplicate, unknown-reference and combined),
and five snapshot rows (four for missing-snapshot).

Independent clean snapshot observations at `2026-01-02T00:00:00+00:00` are:

| SKU / warehouse | Opening | Posted effects in comparison | Independent snapshot |
| --- | ---: | --- | ---: |
| tee-M / harbor | 20 | +10 receipt -3 shipment -4 transfer +1 cutoff return | 24 |
| tee-M / upland | 5 | +4 transfer | 9 |
| hoodie-L / harbor | 12 | +4 receipt -2 shipment +2 posted reversal | 16 |
| tee-L / harbor | 0 | No movement | 0 |
| jacket-M / harbor | 30 | -5 adjustment | 25 |

Baseline is `2026-01-01T00:00:00+00:00`, watermark 10. A baseline-time receipt,
pending receipt, after-cutoff receipt, and higher-sequence late observation remain
raw evidence but do not contribute. The immediate transfer shares one event and
sequence across distinct legs. The two receipt lines share one event/document.
The reversal links to the original shipment; both quantities remain in arithmetic.
Default evaluation is two hours after cutoff. Observation/recording instants are
preserved separately; manifest observation is 90 minutes after cutoff.

## Focused foundation validation

With the owner URL exported, run:

```sh
python -m synthetic.check_foundation
```

This creates a uniquely named disposable database in the same PostgreSQL cluster,
bootstraps the schema, loads all eight namespaces, checks manual clean quantities
and controls, exact seeded fault evidence, manifest counts and reload refusal,
and connects as `ii_runner` to verify actual operational-write and schema-create
denials, result insertion/reading, and child foreign keys. It drops only its own
disposable database when done. The owner connection needs CREATEDB privileges
(the Compose owner has them). It does not alter your scenario database.

This validates the foundation, not reconciliation findings, report ordering,
or repeated checker runs. Those remain the engine and independent validation
owners' integration work.
