# Decision Lab validation

Independent validation, 2026-10-03. Tests use the immutable synthetic replay
exported from the real persisted reliability/forecast/planning path. Expected
quantities below were calculated independently of the adapter output.

## Numerical acceptance

- Baseline: stock 10, prior reservation 3, confirmed inbound 5 on day 1,
  demand 4/day, lead 2, review 3, safety 2, pack 6, MOQ 10. Prefix balances
  without order are `[3, 4, 0, -4, -8]`; raw requirement 10 rounds to 12;
  with-order balances are `[3, 4, 12, 8, 4]`.
- The separate periodic simulation fulfills 112 new pieces and 3 prior pieces,
  with 10 orders of 12. Scored holding 219 plus setup 20 is 239; runoff 88
  makes total synthetic cost 327. Average stock is exactly `219/28`, terminal
  stock 20, and all 9 complete review cycles are shortage free.
- Demand 150% produces 6/day and order 24; 50% produces 2/day and order 0;
  101% rounds each historical/future daily quantity up to 5 and orders 18.
  Source quantities remain 4 and baseline remains identical.
- Lead, reservation, safety, MOQ, pack and late-inbound cases have independent
  prefix-balance oracles. Late inbound exposes a shortage before order arrival.
- Hidden supplier delay 3 preserves the planner and first simulation review.
  It causes 17 scored shortage days, 100 backlog piece-days, immediate fill
  `11/28`, scored cost 1027, runoff cost 144 and total cost 1171.
- Every day in baseline and extreme valid scenarios conserves both supply and
  obligations. Costs reconcile exactly to declared rates 1/10/2. Zero demand
  preserves null fill and WAPE denominators and a null service-target result.

## Evidence and API acceptance

Tests verify immutable scenario pairing, deterministic content identifiers,
ordered structured trace nodes, nested comparison deltas, incomplete-supply
suppression, corrupt transport hashes and semantically altered archives.
HTTP tests cover inclusive control bounds; booleans, floats, strings, nulls,
out-of-range values, extra fields and malformed bodies return 422. Invalid
injected archives return 503. The app owns a copy of injected evidence.

Commands:

```sh
python -m unittest tests.test_lab tests.test_lab_api
python -m unittest tests.test_decision tests.test_forecasting
```

Final combined integration: **18/18 lab/API tests pass**, including packaged
frontend assets. The full existing-plus-lab suite passes **124/124** tests against
a fresh isolated local PostgreSQL 17.6 database on Python 3.12.14. The final trace
reference correction was rechecked with the 18 lab/API tests: derived values
cite their lab calculation hash and saved planning UUIDs refer to input reports.

Installed-wheel assets and offline HTTP routes pass from outside the checkout.
Real browser demand, supplier-delay, incomplete-supply and zero-demand scenarios,
stale inputs, rounding trace and downloaded JSON were verified; the export was
parsed to confirm baseline preservation and blocked nulls. [Integration evidence
and screenshot](DECISION_LAB.md). No production inventory, calibrated risk, live
service, remote PostgreSQL 17.9 CI, cloud deployment or performance claim is
implied by these local synthetic checks.
