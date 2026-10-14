# Forecast accuracy and actual decision quality

The fresh `forecast-decision-study-v1` protocol freezes eight families, two
independently generated paths per family, and all three existing operational
baselines before execution. There are 48 real planner loops and 144 restricted
PostgreSQL reviews. No new method, parameter tuning, or policy promotion follows.

The selection path chooses lowest exact forecast MAE with a frozen method-order
tie break. That choice is carried unchanged into evaluation. All evaluation arms,
including losing policies, remain in the immutable archive. The decision gate
requires lower complete paid cost than mean, no immediate-fill regression, and
no additional blocked reviews. Undefined service cannot pass. The gate compares
a selected policy with mean; it does not claim that policy is globally best.

The eight families are steady, weekly, intermittent, upward demand shift, downward
shift/obsolescence, notified disruption, hidden disruption, and blocked recovery.
The independent saved auditor recalculates each baseline formula, projection,
pack/MOQ proposal, FIFO shipment, exact conservation, source clocks/bindings and
purchase/holding/backlog/setup costs without calling the forecast or planner.
The same immutable source controls are used by the actual restricted runner.

## Measured outcomes

PostgreSQL 17.9 ARM64 Linux with Python 3.12.14 executed all 48 loops and 144
reviews; 39 reviews remained blocked. Two of eight selected methods passed the
paired decision gate: naive on the upward-shift evaluation path reduced paid cost
by 3260 synthetic units and improved immediate fill from 2/7 to 16/21; seasonal
naive on the steady path reduced cost by 32 with fill 1 in both arms. These are
finite synthetic outcomes, not estimated commercial savings or efficacy rates.

Six families did not pass. On downward demand shift the accuracy-selected naive
arm cost 170 more, and zero-demand fill remained undefined. On weekly demand the
accuracy-selected seasonal arm had the same cost as mean while naive cost less.
Intermittent and disrupted paths retained ties and method-ranking disagreements.
Blocked recovery produced null proposals at all three review dates in every arm;
no forecast method repaired missing evidence, stockout history or overdue debt.
There is no global winner or promoted policy; mean remains the operational default.

Each forecast cell scores 15 overlapping origin/lead pairs across three reviews.
Forecast quality uses the complete synthetic demand path, while executable plans
retain their own stockout/completeness gates. MAE, bias and WAPE use exact rational
strings; all-zero WAPE is null. Existing point baselines provide no predictive
intervals, so probabilistic calibration is explicitly unavailable. Seven saved
arithmetic/split/tamper tests and the two historical saved-loop tests pass.

## Reproduce and inspect

The frozen inputs are [protocol](examples/forecast-decision-study-v1.json), and
all actual reports, original source archives, and paid trajectories are retained
in [saved study](review/forecast-decision-study-v1.json.gz). Original consumed
studies remain untouched. The artifact binds exact working-source hashes; its
`parent_commit` records ancestry and does not claim new sources existed there.
A later change is reported as current source drift, never silently rebinds history.
The [workbench summary](review/forecast-decision-summary-v1.json) retains every
evaluation arm and binds its original archive SHA256; a separate test compares
its exact service/cost/forecast quantities with the original report.

With the normal project environment:

```sh
PYTHONPATH=src python scripts/forecast_decision_study.py --audit --output docs/review/forecast-decision-study-v1.json.gz
PYTHONPATH=src python -m unittest tests.test_forecast_decision_study tests.test_planner_loop_saved -v
```

For a fresh diagnostic replication, bootstrap a **new disposable PostgreSQL 17**
database using [VALIDATION](VALIDATION.md), configure owner `TEST_DATABASE_URL`
and restricted `DATABASE_URL`, then choose a previously nonexistent output:

```sh
PYTHONPATH=src python scripts/forecast_decision_study.py --output output/fresh-diagnostic-study.json.gz
```

The exporter refuses to overwrite any consumed artifact. Reproduction of these
published paths is a diagnostic check, not another independent evaluation. New
forecast claims require a different predeclared study, with fresh selection and
evaluation namespaces. Human usability, x86 timing/reference hardware, sustained
HTTP, operational producer authentication and public deployment remain separate.
