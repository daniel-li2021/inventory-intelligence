# Inventory Intelligence

A public portfolio project exploring trustworthy inventory data for an apparel business.

The intended progression is **Inventory Reliability → Forecasting & Planning → Inventory Copilot**. Contract v1 is frozen for the first implementation milestone. Three implementation handoffs are prepared; the inventory engine is not implemented yet.

## First milestone

Use synthetic operational data in PostgreSQL to reconcile inventory movements with independently supplied inventory snapshots at a shared cutoff. Detect deliberately injected failures and explain each finding through source records and quantity evidence.

The proposed stack is Python, PostgreSQL, SQL checks, and Docker Compose. Start with a command-line report and real database tests. Operational uploads/forms, forecasting, and agent features are outside the first milestone.

## Contract and implementation paths

- [Frozen milestone 1 contract](docs/CONTRACT_V1.md)
- [Three parallel agent handoffs](docs/PARALLEL_WORK.md)
- [Stage 1 design, first milestone, and roadmap](docs/STAGE1_PLAN.md)
- [Open-source investigation and reading guide](docs/RESEARCH.md)
- [Dated repository metadata and source revisions](docs/research/repositories.json)
- [Development and GitHub workflow](CONTRIBUTING.md)
- [Shared agent instructions](AGENTS.md)

## Current validation

The committed GitHub Actions workflow checks change whitespace and research JSON syntax. It does **not** establish inventory correctness. The first implementation PR must add PostgreSQL integration tests and exact assertions for seeded failures before its milestone is complete.

## Public-data boundary

All business examples and future fixtures must be synthetic. Do not include company code, data, screenshots, documents, credentials, or confidential schemas. Open-source projects are attributed references; no upstream implementation code has been copied into this repository.

Original project material is available under the [MIT license](LICENSE). Dependencies retain their own licenses.
