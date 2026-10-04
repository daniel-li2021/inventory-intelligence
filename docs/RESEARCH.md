# Open-source investigation

Checked 2026-10-02. This investigation uses maintainers' repositories, source files, license files, and official documentation. GitHub searches covered inventory/stock systems and SQL/data-quality tooling beyond the supplied references. Small tutorial repositories were not used as design authorities.

This is the original reliability/tooling investigation. All three bounded
synthetic stages are now integrated on main; [current status](STATE.md).
The historical [next-round investigation](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/NEXT_ROUND_RESEARCH.md) covers decision metrics,
backlog/lost-sales costs, lead-time risk, SBA/TSB/aggregation/LightGBM, M5 provenance
and minimal lifecycle. It proposes evaluation work; no new dependency or public
real-data import was performed.

[Repository metadata](research/repositories.json) records exact star counts, archived status, last push, licenses reported by GitHub, and source revision snapshots. Stars are adoption proxies, not a guarantee of correctness or production suitability. All shortlisted active repositories showed recent pushes around September 30–October 2, 2026; pushes can include bots and non-release branches. This was a reference investigation, not a deployment, security audit, or performance benchmark of those systems.

## Highest-value design references

**ERPNext — approximately 39.7k stars; GPL-3.0; study, do not install.**

The most useful contrast is Stock Ledger Entry versus Bin: movement history has item/warehouse identity, signed `actual_qty`, posting time, source voucher and line references, and resulting quantity; Bin separately stores current actual/reserved/projected quantities. Borrow traceable movement provenance and the separation of transactions from balances, without importing accounting/valuation workflows. The inspected ledger also contains cancellation and adjustment indicators, so cancellation semantics cannot be inferred from a signed quantity alone.

Read the [ledger schema](https://github.com/frappe/erpnext/blob/d607837e80fa731e2b3b285c9873f3f1185653bc/erpnext/stock/doctype/stock_ledger_entry/stock_ledger_entry.json), [Bin schema](https://github.com/frappe/erpnext/blob/d607837e80fa731e2b3b285c9873f3f1185653bc/erpnext/stock/doctype/bin/bin.json), and [immutable-ledger documentation](https://docs.frappe.io/erpnext/immutable-ledger-in-erpnext). The current documentation describes traceable reversals and controlled reposting for permitted backdated entries; do not repeat the outdated assumption that every backdated stock posting is prohibited. Our project should preserve observations and reversal evidence, not reproduce FIFO costing or ERP repost infrastructure.

**Odoo — approximately 54.8k stars; Community core LGPLv3, with component exceptions; study, do not install.**

The 19.0 source separates `stock.move` from `stock.quant`. Moves identify source/destination locations, product variant, unit, document origin, and workflow state. Quants distinguish on-hand, reserved, and available quantity; physical-count adjustments create stock movements instead of only replacing a displayed balance. Borrow these distinctions and the difference between planned and completed movement. Apparel variants should be stockkeeping SKUs beneath a style, not one quantity on a product template.

Read [stock_move.py](https://github.com/odoo/odoo/blob/c9bd6ea5e343a5a3ff279ed0911808268e17f1e6/addons/stock/models/stock_move.py), [stock_quant.py](https://github.com/odoo/odoo/blob/c9bd6ea5e343a5a3ff279ed0911808268e17f1e6/addons/stock/models/stock_quant.py), and the [license](https://github.com/odoo/odoo/blob/c9bd6ea5e343a5a3ff279ed0911808268e17f1e6/LICENSE). Inventory counting is operational business behavior; our initial checker only explains mismatches. Odoo's current default branch was 20.0, but the source study deliberately used 19.0.

**InvenTree — approximately 7.7k stars; MIT; additional priority reference.**

This is a narrower stock system than a full ERP and a useful Python implementation to study. It models part quantities at locations and records typed history with actor, time, notes, and deltas. In the inspected implementation, deleting a stock item can retain its history through a nullable reference, while deleting the part can remove that history; this is not an absolute immutability guarantee. Borrow concise evidence records and provenance. Do not adopt its Django/admin/API/plugin stack just to reconcile an existing database.

Read [stock concepts](https://docs.inventree.org/en/stable/stock/) and [StockItemTracking/add_tracking_entry in models.py](https://github.com/inventree/InvenTree/blob/9478c25a70696feddafbff139e6f41d3b0abe78d/src/backend/InvenTree/stock/models.py).

**SQLMesh — approximately 3.3k stars; Apache-2.0; study now, strongest later transformation candidate.**

Borrow the distinction between tests on known inputs and audits of actual model output, SQL queries that return violating rows, and explicit blocking/nonblocking policy. It also provides versioned models, plans, restatements, environments, and [PostgreSQL support](https://sqlmesh.readthedocs.io/en/stable/integrations/engines/postgres/). Those become valuable when many derived models and historical recomputation need coordination; they are extra machinery for five checks over one tiny database.

Read [audits](https://sqlmesh.readthedocs.io/en/stable/concepts/audits/) and [overview](https://github.com/SQLMesh/sqlmesh/blob/271b855b70cebfff35d9f2c247c32876d12cff77/docs/concepts/overview.md). An important limitation: a failed audit during `run` can occur after a production model was updated. Blocking downstream execution is not synonymous with rolling back already-written bad data. Incremental audit coverage also follows processed intervals. Our proposal explicitly persists evidence and separates input validity from assessable balances.

## Useful reliability/ingestion references; defer dependency adoption

**Great Expectations — approximately 11.9k stars; Apache-2.0.** The user-supplied [fivetran/great_expectations](https://github.com/fivetran/great_expectations) is the current repository, consistent with [Fivetran's stewardship announcement](https://www.fivetran.com/press/fivetran-to-become-steward-of-the-great-expectations-open-source-community-and-gx-core-project). Borrow named expectations, persisted validation outcomes, and evidence-oriented documentation. Its [custom SQL expectation](https://docs.greatexpectations.io/docs/core/customize_expectations/use_sql_to_define_a_custom_expectation/) succeeds when the query returns no unexpected rows, closely matching our SQL checks. Suites, contexts, batches, checkpoints, and result stores are justified when many reusable validations or data backends need them. They do not supply inventory semantics. Beware confusing a sampled validation result with every failed record: [unexpected-row retrieval](https://docs.greatexpectations.io/docs/core/run_validations/retrieve_all_unexpected_rows/) documents the supported complete retrieval path.

**Elementary — approximately 2.4k stars; Apache-2.0.** [Elementary OSS](https://github.com/elementary-data/elementary) is a reporting/alerting CLI that consumes artifacts collected by its separate [dbt package](https://github.com/elementary-data/dbt-data-reliability). Borrow run history, failed-test evidence, freshness/volume distinctions, and drill-down from symptoms to upstream models. Adding it now also introduces a dbt ecosystem we otherwise do not need. Distinguish OSS capabilities from the Cloud features advertised in the same README; do not assume every screenshot or automated monitor is freely self-hostable.

**dlt — approximately 5.9k stars; Apache-2.0.** [dlt](https://github.com/dlt-hub/dlt) is a sensible direct dependency later if operational databases/APIs actually need extraction into a separate analytical store. Its [SQL source configuration](https://dlthub.com/docs/dlt-ecosystem/verified-sources/sql_database/configuration) exposes primary keys and incremental cursors. Borrow stable source identity, load batches, and explicit schema policy. A cursor on event time can miss late/backdated updates; an update/recording cursor or another completeness strategy is required. An ingestion framework does not establish aligned ledger/snapshot cutoffs. There is no copying problem to solve in our one-database synthetic MVP.

**dbt — approximately 14.0k stars; Apache-2.0 repository source.** [dbt](https://github.com/dbt-labs/dbt) is the mature alternative if a future environment already uses dbt models and tests. Current `dbt-core` URLs redirect to `dbt-labs/dbt`; its default source is the newer Rust v2 implementation and the Python v1 code is on `1.latest`. The README also distinguishes Apache source from the customized product distribution. Check adapter, package, distribution/license, and Elementary compatibility for the specific version before adopting it. Do not run dbt and SQLMesh together simply to demonstrate both tools.

**OpenLineage — approximately 2.7k stars; Apache-2.0.** [Its job/run/dataset object model](https://openlineage.io/docs/spec/object-model/) is useful vocabulary for linking a reliability run to its inputs and outputs. Defer a collector/backend until jobs span multiple systems. Dataset lineage alone does not identify the particular bad inventory document; retain business record references in findings.

**Bruin — approximately 1.8k stars; Apache-2.0.** [Bruin](https://github.com/bruin-data/bruin) surfaced in broader GitHub searches as an integrated SQL/Python ingestion, transformation, and quality tool. It is worth awareness as an alternative later, but overlaps several already considered tools and expands the orchestration surface without a present need. No integration/source-code evaluation was done, so it is not a dependency recommendation.

**Carbon — approximately 2.7k stars; AGPLv3 core with commercially licensed enterprise exceptions.** [Carbon](https://github.com/crbnos/carbon) offers a PostgreSQL-based manufacturing system, traceability, and planning concepts that may be useful in Stage 2. It is less directly relevant than the stock references above and a much broader product than this reliability layer. The [license file](https://github.com/crbnos/carbon/blob/main/LICENSE) was checked independently because GitHub reports `NOASSERTION`; source visibility does not make all enterprise files open source. This was a README/license assessment, not an endorsement of its operational claims or a code audit.

## Explicitly excluded or reserved for later

- **Soda Core — approximately 2.4k stars, active, but current `main` uses [Elastic License 2.0](https://github.com/sodadata/soda-core/blob/8f652f4832d5534d5e0d8584cdb76d45fa087a7e/LICENSE).** Its declarative quality/contracts approach is relevant, but do not classify the current code as an unrestricted Apache-licensed OSS dependency from older recommendations. Exclude it from this project's initial dependency set.
- **Datafold data-diff — approximately 3.0k stars, [archived since May 2024](https://github.com/datafold/data-diff).** Dataset diffing is relevant to reconciliation, but this is not a maintained dependency choice. An ordinary keyed SQL join meets the first milestone's comparison need.
- **StatsForecast — approximately 4.9k stars; Apache-2.0; future challenger option.** [The project](https://github.com/Nixtla/statsforecast) supplies statistical baselines and intermittent-demand methods. Stage 2 now has a separate synthetic demand series and stdlib baselines. Dependency adoption is still deferred until the decision benchmark demonstrates a need; see [model investigation](https://github.com/daniel-li2021/inventory-intelligence/blob/208d5b3e1a9f2beb78ea94258800dfe4407150c8/docs/NEXT_ROUND_RESEARCH.md#models-test-the-weakness-before-increasing-complexity).
- Home inventory, cloud-asset inventory, scanner tools, and narrow material trackers appeared in searches but have different business grains and workflows. Small reconciliation demos were not promoted over mature systems just because their names matched.

## Direct-use decision

Use PostgreSQL itself, Docker Compose for its local environment, and [Psycopg 3](https://github.com/psycopg/psycopg) for Python database access. Psycopg is an established maintained adapter (approximately 2.5k stars; LGPL-3.0 metadata). Review/pin the selected package and binary distribution versions when implementation starts. The CLI, JSON output, deterministic fixture support, and initial tests can use Python's standard library.

The project's original work is the inventory contract, meaningful SQL reconciliation rules, provenance, and independent failure tests. Rebuilding generic ingestion, ERP operations, orchestration, or an expectation framework would obscure that contribution.
