# Startup attribution: retained Lab replay

Measured 2026-10-03 after freezing [protocol v1](FEASIBILITY_DIAGNOSTIC.md) in
commit `5e2ec8e`. [Exact reproducible artifact](review/feasibility-diagnostic.json)
retains source hashes, archive digest/UUIDs, calculation IDs, counterfactual
inputs, startup trajectories, service denominators and original/common costs.
These are five controls on one existing synthetic demand path, not five
independent experiments or new held-out evidence.

## Findings

The hidden three-day supplier delay misses **68 of 112** new demand units.
Before the earliest possible new receipt on day 5, initial stock 10 plus known
inbound 5 minus prior commitments 3 can fill only 12 of the first 20 new units.
**Eight misses are inevitable at startup; 60 happen later** among 92 later units.
The startup-only immediate-fill ceiling is `104/112 = 13/14`; actual immediate
fill is `44/112 = 11/28`. Startup infeasibility alone does not explain this
scenario's poor service. Later shortages do not uniquely identify forecast error;
hidden supply delays and periodic policy timing still matter.

The common accounting window is 36 days for every assessable control, including
28 scored days and eight no-demand runoff days. All obligations/pipeline have
already settled before any extension. Exact synthetic penalties are:

- Baseline: original 327 over 33 days; terminal 20 pieces incur 60 extra holding;
  common total 387, including scored 239 and common runoff 148.
- Delay3: original/common 1171 over 36 days, including scored 1027 and runoff 144;
  terminal 20. Cost delta versus baseline falls from 844 to **784**. The direction
  survives equal exposure duration; original totals remain intact.
- Demand125%: original 351 becomes 417 after 66 extra holding on 22 terminal pieces;
  delta versus baseline 30, with all 140 new units immediately filled. Different
  demand quantities prevent interpreting this delta as policy savings.
- Zero new demand: original 391 becomes 427 after 36 extra holding on 12 terminal
  pieces. Fill and its ceiling stay null; disjoint prior commitments remain due.
- Incomplete supply: feasibility, realized outcomes, accounting and deltas all
  stay null with explicit `not_assessable` reasons. It is retained in the report.

## Reproduce and validate

Use the existing project Python environment; no database or model API is needed:

```sh
PYTHONPATH=src python scripts/feasibility_diagnostic.py --output /tmp/feasibility.json
PYTHONPATH=src python -m unittest tests.test_decision tests.test_decision_diagnostics tests.test_lab tests.test_lab_api -v
```

Focused acceptance passes **48/48 tests**, including 15 new diagnostics tests,
on Python 3.12.14 / Psycopg 3.3.6. Independent hand calculations cover priority,
timed inbound, later reviews arriving earlier, the exact receipt boundary,
possible versus actual ordering, null demand and rational holding costs.
The CLI reproduces the in-process exact report. Invalid archives, truncation,
unsettled terminal state and inexact rates fail instead of yielding cheap costs.
The original simulator and Lab/API regressions pass unchanged. No full database
suite, browser rerun, remote CI or statistical generalization is claimed here.

## Next decision

This slice makes accounting exposure and startup limits explicit without adding
a forecasting model. A new forecast grid remains unjustified. The next valuable
study is the already ranked **fresh demand/supplier paths and costed warmup**:
carry each policy's stock/backlog/pipeline into scoring, count warmup costs and
retain infeasible/null controls. Later service failure is material on this saved
delay case, but it does not justify promoting a safety challenger from one
consumed path. Fresh independent evaluation must precede that decision.
