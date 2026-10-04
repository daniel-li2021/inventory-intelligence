# Project instructions

Read [STATE](docs/STATE.md) for current focus and integration mode, then the
relevant plan or guide in the [index](docs/README.md).

- Inspect the smallest relevant surface and trace callers before shared changes.
  Read once when practical; preserve unrelated work and reuse valid saved outputs.
- Prefer focused validation and SQL/stdlib/native features. Avoid full pipelines,
  suites, builds and external/model calls unless needed for correctness.
- Preserve versioned interface semantics, source identities, business/knowledge clocks and
  original evidence. Missing data is not zero/pass; quantities are exact pieces.
  Read operational inputs and write results separately; never silently repair them.
- Keep planner projection separate from simulation. Copilot explains saved evidence;
  language routing cannot invent evidence or business arithmetic. Check independent
  expected quantities and clean controls, not just counts.
- Operational inputs are synthetic. The [approved UCI exception](docs/KB.md#public-data-boundary)
  is offline research with ignored raw/reconstructable data and attributed aggregates.
  Never import company code, data, screenshots, credentials or confidential schema.
- Follow [CONTRIBUTING](CONTRIBUTING.md). AUTO merges validated authorized work;
  REVIEW stops before merge. Read the current mode before integrating. Neither mode
  resumes paused work or approves new benchmark programs or paid deployments.
- After merging, verify remote main, return the primary checkout to current main,
  delete the completed local task branch and retire its clean temporary worktree.
  Preserve active/dirty/unmerged work; never force-push or discard it.
- Update STATE and the affected indexed plan after material progress. Plans may
  cover different areas/horizons; record outcomes, gaps and next action. Extract
  durable knowledge/results before deleting completed or superseded task documents;
  retain only plans needed for pending execution. Historical originals live in Git;
  do not retain completed plans, compatibility stubs or duplicate narratives.
- Stop when the scoped work is validated. Keep progress and final summaries concise.
