# Project instructions

## Start here

Read [current state and integration mode](docs/STATE.md), then the relevant part
of [the active plan](docs/PLAN.md). Use [the knowledge index](docs/README.md) to
find the responsible contract, operator guide or saved evidence. Historical
reviews and retired handoffs are evidence, not active instructions. A proposal
or AUTO mode does not authorize work outside the user's assigned scope.

## Work narrowly and correctly

- Inspect the responsible file/function first; trace callers before shared changes.
- Read files once when practical; use targeted searches/ranges afterward.
- Preserve unrelated dirty work. Use isolation when needed, not by default.
- Reuse valid caches, outputs and saved scores. Avoid full pipelines, suites,
  builds or external API/model calls unless correctness requires them.
- Prefer focused edits and validation, SQL/stdlib/native features over abstractions.
- Independently check quantities, identities and clean controls; counts alone fail.
- Once the requested work is sufficiently validated, stop; keep narration concise.

## Project boundaries

- Preserve frozen/versioned contracts and historical decoding. Stage 1 follows
  [CONTRACT_V1](docs/CONTRACT_V1.md); change shared interfaces through an explicit
  new contract/handoff, never by silently rewriting an accepted version.
- Operational portfolio inputs are synthetic. The approved UCI research exception
  follows [PUBLIC_SALES_PROTOCOL_V1](docs/PUBLIC_SALES_PROTOCOL_V1.md), stays offline,
  keeps raw/reconstructable data ignored and publishes aggregates with attribution.
  Never import company code/data/screenshots/credentials/confidential schema.
- Read source inputs; write results separately. Never silently repair inventory.
- Preserve source identity, business/knowledge clocks and append-only evidence.
  Missing/incomplete data must not become zero or pass; physical pieces are exact.
- Keep planner projection and periodic simulation distinct. Copilot explains saved
  evidence; language routing must not invent evidence or business arithmetic.

## Delivery and knowledge

Follow [CONTRIBUTING](CONTRIBUTING.md) for Git, validation and integration. The
persistent mode lives only in `docs/STATE.md`: AUTO integrates validated authorized
work; REVIEW stops before merge for the user's review. Re-read it before merging.
An explicit mode-switch instruction updates that line and persists across tasks.
Never force-push, discard work or retire unmerged/dirty/active branches.

After each material checkpoint or phase, update STATE in place and the active
PLAN's relevant task/gate. Update affected operator/contract docs with the change.
Record a new enduring decision or supersession in DECISIONS; leave old reasoning
and saved reports intact. Retire completed plans through the knowledge index and
Git history before replacing PLAN. Do not create new progress/status diaries,
per-agent documentation or duplicate instructions. See the [maintenance rules](docs/README.md).
