# Independent checkpoint — 2026-10-02

Reviewed fetched `origin/main` at `dacdc8f`, independently of PR titles and delivery
speed. Stage 1 implementation, SQL, schema, and acceptance tests are byte-for-byte
unchanged since `83e8457`. The 22 database tests still assert exact independent
balances/evidence, clean and explicit zero-stock controls, empty-coverage refusal,
temporal boundaries, atomic history, and restricted operational permissions.

All **27 tests passed**, zero failures/errors/skips, against a newly initialized
PostgreSQL **17.6** cluster and fresh `checkpoint` database, Python **3.12.14**,
Psycopg **3.3.6**. Local binaries differ from pinned CI (17.9 / 3.12.12); remote
acceptance is required on the new PRs. No Stage 1 correctness defect was found.
Stage 1 remains frozen within its bounded contract.

The forecasting kernel correctly excludes future observations from training,
repeats the last seasonal cycle across multi-season horizons, and retains exact
rational estimates. MAE is absolute error per origin/lead pair, bias is forecast
minus actual, and WAPE is aggregate absolute error divided by actual volume,
null for all-zero truth. Overlapping folds intentionally count repeated targets.
An additional independent overlapping-horizon oracle guards these definitions.

The kernel validates integer values, not source eligibility or knowledge time.
Its positional leakage test cannot establish absence of leakage from late order
revisions. This limitation is documented and must be resolved by the Stage 2
adapter. No model is selected from the toy weekly demonstration. Stage 2 currently
contains only this first slice and is **not complete**.

Stage 3's other checkout currently adds an evidence reader over existing outputs.
Its uncommitted files are preserved; Stage 2 uses a separate worktree and adds
its own contracts/results without changing Stage 1 report interfaces.
