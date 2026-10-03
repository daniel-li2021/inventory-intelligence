# Readiness and the next useful investigation

Assessed 2026-10-03 from main `429cc71`. This investigation reused the saved
decision/intermittent artifacts and checked primary external sources. No new
experiment, model fit, public-data acquisition or deployment was performed.
The operational portfolio remains synthetic-only. This document updates the
priority judgment in [earlier research](NEXT_ROUND_RESEARCH.md); it does not
authorize its proposed implementations or change a frozen contract.

## What the current evidence supports

The strongest portfolio claim is an auditable, fail-closed path from inventory
evidence to an advisory proposal and deterministic explanation, with a local
[Decision Lab](DECISION_LAB.md) that exposes assumptions and negative results.
Freeze the existing operational methods, exact quantities, evidence identities,
historical decoding and read-only Copilot boundary after review fixes. Research
SBA/TSB should remain separate: there is no measured general champion, calibrated
service guarantee, real inventory performance or business-savings result.

The [saved intermittent artifact](review/intermittent-benchmark.json) records
5,544 candidate/split results in 84 cells, with 18 cells lacking an eligible
overall selection. Four dual-reference passes come from **one** declining-demand
path, seed101, repriced under two costs and evaluated under two supplier regimes.
They are not four independent successes. The ten new-method-versus-baseline
passes likewise do not establish general superiority.

Two independently inspected examples make policy evidence the immediate gap:

- Declining/211 has demand `[0,20]` before the first possible day2 receipt,
  initial stock10 and total demand39. At least ten units inevitably miss immediate
  fill, giving an upper bound of `29/39`, below the 90% floor, whatever forecast
  is used. Full cumulative target coverage cannot repair this timing constraint.
- Obsolescence/307 selects TSB with empirical 90% safety, sees only eight holdout
  units, retains safety quantities 23–40 and ends with 54 pieces. Synthetic cost
  is 3464 versus the selected baseline's 3340 and fixed mean's 1870. Forecast
  decay alone does not remove safety stock or already owned inventory.

These are replay facts and arithmetic deductions under the frozen assumptions,
not claims about an external retailer. Details remain in
[the recorded benchmark](INTERMITTENT_BENCHMARK.md).

## Ranked options

Scope estimates below describe focused engineering work, not delivery promises.

| Priority | Direction | New evidence or capability | Rough scope | Main decision or risk |
| --- | --- | --- | --- | --- |
| 1 | Feasibility and evaluation attribution | Separates unavoidable startup shortages from forecast/policy failures; tests whether conclusions survive fresh demand and supply paths | Small: separate protocol, independent timing oracles, bounded offline report | Cold-start and steady-state answer different questions; never discard infeasible cases to improve a score |
| 2 | Safety retention under decline | Tests whether a bounded recent-history calibration policy improves cost without sacrificing service after temporary pauses and permanent decline | Medium: one challenger, calibration oracles, fresh held-out counterfactual | A short zero run is not evidence of retirement; smaller safety cannot liquidate existing stock |
| 3 | Public observed-sales benchmark | Challenges synthetic generators with real transaction sparsity and seasonal behavior | Medium: governed adapter, provenance/exclusion tests, bounded baseline evaluation | Requires a separate public-data boundary; sales remain censored observations, not verified demand |
| 4 | Easier demo access | Lets an interviewer inspect the working story quickly | Small for guided local walkthrough; medium for hosted API operations | Hosting adds recurring ownership/cost and no new forecast evidence; choose it only if setup friction is observed |
| 5 | Additional forecasting models | Can test a demonstrated cumulative-demand weakness across diverse series | Medium to large depending on features and dependencies | Present evidence does not justify widening the model grid or promoting ML |

For immediate portfolio polish, a short guided walkthrough of clean, blocked,
late-receipt and zero-demand cases is enough. A public service is optional.
Local wheel installation, packaged assets and browser replay are already
documented as validated; repeating packaging work adds little. A hosted demo is
a small reversible option, but requires a separately agreed public-exposure and
deployment scope before publication.
[FastAPI's deployment guidance](https://fastapi.tiangolo.com/deployment/concepts/)
requires explicit HTTPS, startup/restart and resource choices; local package
validation is not evidence those operations are ready.

## First investigation: distinguish feasibility from calibration

Freeze a new offline protocol before generating outcomes. Keep existing models
and safety grid; add an independent bound on units unfillable before the earliest
new receipt, retaining prior-commitment priority where present. Report those
units alongside actual shortages and service, without using future demand in
order decisions. This is an evaluation diagnostic, not an oracle policy.
Separate missed immediate fill before the first receipt from later missed fill.
The feasibility bound must pass hand-calculated oracles; actual immediate fill
must never exceed its applicable ceiling. Infeasibility stays in the denominator.

Compare the existing cold-start reset with a separately declared warmup in which
every candidate starts from the same earlier state, runs its own policy and
carries its resulting stock/backlog/pipeline into scoring. Warmup is not free
inventory: report its costs and starting state. Pair each candidate within a
scenario, but use **fresh supplier traces across selection and holdout**. The
current harness deliberately reuses the same ten-slot hidden delay trace across
both splits; it therefore does not test independent unseen supplier realizations.
This is a limitation of the counterfactual, not policy access to hidden delays.

Choose a small predeclared initial-stock/lead-time sensitivity grid. Use fresh
independent demand and supplier seed sets and independent manual controls. Extra
initial stock is a costed intervention fixed before outcomes, never a correction
chosen after seeing shortages. Write a separately versioned artifact; do not
overwrite the consumed benchmark. Evaluate selection choices on
several later origin blocks; all tuning stays inside earlier blocks. Report
paired deltas by demand path/family and collapse cost repricings and repeated
controls when counting independent evidence. Keep failures and null denominators.
Stop if attribution explains the negative results without needing a new model.
Advance to the second study only when later service failure or retained safety
cost remains material on the frozen grid. Its evaluation keeps the existing
service floors and 5% cost-improvement rule against both references, with paired
path-level results and no automatic operational promotion.
[Rolling-origin evaluation](https://otexts.com/fpp3/tscv.html) and
[selection/evaluation separation](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html)
support these boundaries; random K-fold splitting is inappropriate here.

Retain the old holdouts as regression data: their outcomes already influenced
these proposals. New tuning cannot produce a fresh generalization claim on them.
The simulator and Lab also use a periodic inventory-position policy, while the
operational recommendation uses prefix-stock-v1. Continue stating that distinction;
any future execution comparison needs an explicit policy/action adapter.
[Stockpyl](https://stockpyl.readthedocs.io/en/latest/tutorial/tutorial_sim.html)
is a useful independent reference for conservation and timing oracles, but its
default demand-before-order sequence differs. Translate lead conventions before
comparing; importing a second simulator is not required.

## Calibration and declining demand

Nearest-rank 90%/95% estimates from eight or nine calibration targets both pick
the maximum error. They do not identify two distinct tails or establish nominal
service. Current coverage uses seven complete nine-day targets; forecast windows,
inventory cycles and paths are dependent. Hidden delays are outside the nominal
`H=L+R` calibration target. Preserve the separation between pinball/coverage and
realized fill/cycle service, and report sample counts.
[Distribution evaluation](https://otexts.com/fpp3/distaccuracy.html).

After feasibility attribution, compare expanding-history safety with **one**
bounded recent-history challenger using completed targets only, an explicit
minimum sample count and fail-closed insufficient-calibration behavior. Test
temporary pauses/recovery as well as gradual decline and permanent cessation.
Freeze the window choice before a fresh holdout and include terminal inventory,
pipeline and horizon sensitivity. Do not add automatic product-retirement or
salvage rules without separate lifecycle evidence and cost semantics.
[TSB's original paper](https://doi.org/10.1016/j.ejor.2011.05.018)
addresses updating occurrence probability; it does not establish that this
project's retained safety policy controls obsolescence well.

## Public data: a useful complement with a different target

Metadata/license pages were rechecked; archives were not downloaded.

| Candidate | Verified value and rights | Semantics and evaluation limit | Judgment |
| --- | --- | --- | --- |
| [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online%2Bretail) | 541,909 transaction rows, Dec2010–Dec2011; CC BY 4.0 | Invoices include cancellation codes; customer country is not a warehouse; no availability, acceptance revisions or historical ingestion clock | Lowest-scope starting point; existing [protocol](PUBLIC_SALES_PROTOCOL_V1.md) remains pending |
| [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online%2Bretail%2Bii) | 1,067,371 rows, Dec2009–Dec2011; CC BY 4.0 | Same retailer/type of evidence, explicitly includes missing values; more repeated seasons but not an independent retailer | Consider only if a second seasonal cycle changes the research question; a separate protocol revision must establish overlap/schema handling |
| [M5](https://storage.googleapis.com/kaggle-forum-message-attachments/772349/15032/M5-Competitors-Guide-Final-10-March-2020.pdf) | 30,490 item/store series, daily sales, calendar and weekly average prices | No unconstrained-demand or stock-availability proof; weekly prices can use within-week information | Broader multiseries study later; [data](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data) and [rules](https://www.kaggle.com/competitions/m5-forecasting-accuracy/rules) returned no readable terms, so use/redistribution rights remain unverified |

For UCI, audit required identity/date/quantity fields independently of metadata
labels; retain raw row identities, cancellations and exclusion counts outside
Git. Gross positive non-cancelled invoiced sales is a declared target, not
reconstructed accepted-order demand. A complete extraction can justify an
observed-sales zero; it cannot prove product availability or zero lost demand.
Dates around the archive boundary may be partial. Do not treat Retail and
Retail II as independent datasets without checking their overlapping period.

Choose products, sparsity bins, scales, features and all forecast/calibration
labels using training prefixes only. Exclude labels crossing split boundaries.
Do not use future actual sales in recursive features, future dates from other
items in a global fit, or weekly-average prices as origin-known inputs without a
declared release assumption. Real acquisition time and simulated historical
release time stay separate. Any policy simulation uses sales as an explicit
proxy with synthetic stock, suppliers and penalties; it cannot measure historical
retailer shortages, profit or recover latent demand.

## Complexity gate and freeze decision

Keep existing baselines and SBA/TSB as the research references. Only investigate
ADIDA/IMAPA after a repeated cumulative-error weakness survives feasibility and
calibration controls. A global LightGBM challenger becomes reasonable after
diverse observed-sales histories and a frozen feature/evaluation protocol exist;
its [documented L1/L2/quantile objectives](https://lightgbm.readthedocs.io/en/stable/Parameters.html)
do not demonstrate inventory value. Any ML extension must explicitly represent
estimate precision and preserve exact physical quantities and historical decoding.

The first next deliverable should be the bounded feasibility/evaluation protocol,
not a larger application. It addresses demonstrated failures with existing
components, stays inside synthetic policy, and establishes whether calibration,
external data or additional modeling would answer the remaining question.
