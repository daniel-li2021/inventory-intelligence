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

## Verified corrected main baseline

PR 25 is merged at main `9d7c55f8e30c9b885e14c450632de18efe413693`.
[Main run 37164884160](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37164884160)
passes both PostgreSQL acceptance and repository hygiene. The acceptance log
records 240 tests / OK / 19.495 seconds with full history, Python 3.12.12,
PostgreSQL 17.9 and Psycopg 3.3.6. This resolves the CI-history incident; it
is not a performance benchmark or proof of repeated CI reliability. The older
236-test/error run and local candidate receipts remain unchanged historical
evidence. See [current engineering readiness](ENGINEERING_READINESS.md) and the
[separate baseline inspection receipt](review/engineering-readiness-baseline.json).

## PR 26: documentation drift exposed a fixed-count oracle

[PR 26 run 37166377305](https://github.com/daniel-li2021/inventory-intelligence/actions/runs/37166377305)
executed 240 tests with one failure: the lineage test expected exactly 13 current
source-drift bindings, but correctly observed 14. Repository hygiene passed.
The new binding is `docs/HOSTED_LAB_PLAN.md` referenced by the immutable original
hosted acceptance receipt. Updating current status legitimately changes that
document's hash; it does not invalidate the report's original source snapshot.
This differs from PR 25's shallow-history setup error. No merge conflict or
inventory arithmetic failure caused this run to fail.

The test now independently enumerates exact drift rows from saved source maps
and current file bytes, checking artifact/source identity, both hashes, missing
files and the summary denominator. Existing historical-kernel, artifact-byte,
ancestry and graph corruption checks remain. A regression exercises the document
at its original bytes and updated bytes; omitting its real drift row, even with a
matching reduced count, must fail. Do not replace the old 13 with another fixed
total, suppress documentation drift or rewrite saved reports to pass CI.

Documentation changes to source-bound files must run the focused lineage tests
before pushing. Green CI is required on the exact PR head before automatic merge;
then verify the resulting main run separately. Feature and benchmark development
remain paused during this CI repair.
