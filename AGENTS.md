# Project instructions

## Start here

Read [current state and integration mode](docs/STATE.md), then use the
[plan registry](docs/README.md#plans-and-work-status) to find the relevant plan.
The [knowledge index](docs/README.md) also routes to contracts, guides and evidence. Historical
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

After each material checkpoint or phase, update STATE and the affected plan's
completed work, remaining gaps and next action. Multiple short-term, long-term
or area plans are allowed; link each from the index with scope and status. Work
one assigned task at a time; multiple plans do not authorize parallel execution.
Keep useful completed plans linked with outcomes/gaps; archive only obsolete or
duplicated plans, and link replacements when superseded. Update affected guides
and enduring decisions; preserve original evidence. Avoid duplicate progress
files/instructions. See the [maintenance rules](docs/README.md).
