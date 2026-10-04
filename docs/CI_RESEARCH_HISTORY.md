# Research provenance CI history requirement

CI must check out complete Git history in the PostgreSQL acceptance job. The
research lineage tests verify original source snapshots, retained delivery heads
and the frozen base by ancestry. A one-commit shallow checkout cannot prove those
requirements; the verifier must fail rather than skip or weaken evidence checks.

On 2026-10-03, PR 24 and integrated main failed at `ResearchLineageTests.setUpClass`:
`fatal: Not a valid commit name f6d3d160...`, then `ValueError: base not retained`.
The main run executed 236 tests without assertion failures, with this one setup
error preventing four lineage tests from running. Repository hygiene passed.
[Failure log](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37160187852/job/111311855286).

PR 16 had a separate older intermittent-report source-hash assertion failure.
The combined integration already corrected that assertion to use the preserved
original kernel; the integrated CI log confirms that test passes. Original report
bytes remain unchanged. PR 17-23 head workflows passed. Shared documentation
merge conflicts were resolved before integration; no code conflict was observed.

The fix changes only acceptance-job checkout depth to zero. Keep verifier logic,
source bindings, tests, Python/PostgreSQL pins and published reports unchanged.
A local shallow/full checkout reproduction and the new GitHub Actions result are
recorded separately from the earlier local 240-test candidate acceptance.
