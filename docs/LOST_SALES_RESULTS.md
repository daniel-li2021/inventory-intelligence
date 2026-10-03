# Same attempted demand, different fulfillment obligations

The [research contract](CONTRACT_LOST_SALES_V1.md) was frozen at `7550cc4` before
implementation. Validated kernel, generator, independent oracles and saved-event
auditor were committed at `54ded62` before the first fresh experiment. This
research-only lost-sales kernel does not replace accepted-order backlog semantics,
operational planning or Lab behavior.

Both arms see the same completed **attempted demand**, including unfilled attempts,
and have identical forecasts/targets at each scored review. This is an explicitly
synthetic observation assumption. Ordinary observed sales do not reveal lost
attempts; censored-feedback decisions need a separate protocol. No public data,
database, model API or purchase execution is involved.

## Population, state and paid costs

18 family/seed labels contain 12 distinct demand paths; supplier profiles contain
19 distinct complete paths (18 variable plus the shared all-zero reference).
The fixed mean/seasonal-naive, safety0/6, lead2/5 and fixed/variable supply grid
produces **288 semantics pairs / 576 logical arms**, using480 exact-input cached
computations and376 distinct native physical trajectories. Deterministic demand
controls repeat across seeds; costs repriced at different tariffs are not new
physical simulations or independent statistical evidence.

Each arm has56 paid warmup dates,28 score dates and a common100-day accounting
window, including16 settlement dates. Initial10 pieces and every order cost2 per
piece. Ending stock is retained and charged through the common end, with no
salvage credit. Holding1 and setup2 are shared. Backlog costs10 per unit-day;
lost sales cost10 or40 **once per permanently lost unit**. These penalty units
represent different business obligations and are not interchangeable retailer
cost estimates. Warmup's lost units and owed debt remain in full costs.

| Lost-sales versus backlog | Count / 288 pairs |
|---|---:|
| Immediate score fill improves | 89 |
| Immediate score fill regresses | 10 |
| Equal immediate score fill | 93 |
| Undefined score fill | 96 |
| Different first order | 0 |
| Different total ordered pieces | 199 (all lower in this grid) |
| Full lost-sales cost lower / higher / equal, lost penalty10 | 171 / 31 / 86 |
| Full lost-sales cost lower / higher / equal, lost penalty40 | 25 / 177 / 86 |

The96 null comparisons come from zero-demand and score-period cessation controls;
they are preserved rather than assigned perfect fill. Score-cycle comparison
uses four complete cycles with **no newly unmet attempted demand** in either arm.
Native backlog shortage cycles also include persistent old debt; their counts
are retained separately. Neither immediate service nor buying fewer pieces makes
lost sales a valid replacement for an accepted customer obligation.

## A concrete timing/economics control

Constant demand3, seed9101, mean/safety0, lead5 and the shared variable supplier
path have84 score attempts over28 dates. Both arms first order26 pieces and use
identical forecast targets. Their policy-owned warmup boundary differs:

| Quantity | Backlog | Lost sales |
|---|---:|---:|
| Score-boundary stock / debt / pipeline | 0 / 6 / 22 | 7 / 0 / 14 |
| Total ordered pieces (warmup, score, settlement) | 258 | 226 |
| Score immediate units / 84 | 80 / 84 | 81 / 84 |
| Score eventually served units / 84 | 84 / 84 | 81 / 84 |
| New-demand shortage-free score cycles / 4 | 2 / 4 | 3 / 4 |
| Warmup permanently lost units | 0 | 29 |
| Score permanently lost units | 0 | 3 |
| Terminal paid stock | 16 | 16 |
| Full cost, lost penalty10 | 2200 | 1817 |
| Full cost, lost penalty40 | 2200 | 2777 |

Backlog's paid costs split into warmup1498, score446 and settlement256. Lost sales
at penalty10 splits1090/471/256. The latter's one extra immediate score unit does
not restore its32 permanently lost warmup/score units. Its eventual score fill
is27/28, while backlog eventually delivers all84 score obligations.

Lost-sales non-loss costs are1497. Conditional on backlog's fixed10/unit-day
valuation, its32 lost units make the algebraic break-even lost-unit penalty
`(2200-1497)/32 = 703/32` (about21.97). Penalty10 therefore costs383 less, while
penalty40 costs577 more. This is a finite synthetic counterfactual, not a claim a
retailer can reduce costs by abandoning accepted orders or a selected optimal rule.

## A negative service result is retained

Weekly/seed9101, seasonal-naive/safety0, lead2 and variable supply has backlog
immediate fill78/84 versus lost-sales77/84. Their new-demand cycle service is
2/4 in both arms. Lost-sales ordering is34 pieces lower, but immediate service
regresses by1/84; its77 served units never become84 through later receipts.
Full costs are1688 backlog versus1507/2587 lost sales at penalty10/40. Lower
purchases or one particular tariff cannot establish a general service winner.

The benchmark selects no model, policy or fulfillment contract. Viewed paths are
now consumed. Broader conclusions require a new question, protocol and fresh
traces; ordinary sales-only feedback would be a different realism experiment.

## Acceptance and reproducibility

24 focused tests pass on Python3.12.14 / Psycopg3.3.6: ten new lost-sales controls
plus existing decision and historical benchmark checks. Hand-calculated controls
cover lost-unit permanence, divergent later orders, initial inbound, exact paid
costs/break-even, fractional targets/pack/MOQ, phase/calendar delay after zero
orders, future observation, nulls and stock/attempt conservation. Six purposeful
rehashed receipt/identity/forecast/cost/loss/native-metric faults are rejected.

A separate saved-event audit reconciles all480 cached computations/288 pairs:
source bytes against their recorded code commit, receipts and FIFO, completed
attempt-only forecast arithmetic, origin actions, pipeline/stock/debt conservation,
permanent losses, paid warmup/score/common settlement, service denominators,
repricing and every aggregate count. It invokes no models and replays no kernel.
With the experiment function explicitly disabled, the benchmark reuses and audits
its accepted cache without changing archive/summary bytes.
[Acceptance receipt](review/lost-sales-acceptance.json).

The full synthetic input/trajectory artifact is a deterministic standard-library
[JSON gzip archive](review/lost-sales-v1.json.gz),1,301,214 bytes. The
[readable paired summary](review/lost-sales-v1-summary.json) retains all path inputs,
paired differences/denominators and the archive SHA-256. Compression preserves
complete exact evidence without committing a large repetitive plaintext trace.
Fractions use exact numerator/denominator objects.

```sh
PYTHONPATH=src python3.12 -m unittest tests.test_lost_sales tests.test_decision tests.test_decision_benchmark -q
PYTHONPATH=src python3.12 -m scripts.lost_sales_benchmark
PYTHONPATH=src python3.12 -m scripts.lost_sales_audit
```

The benchmark refuses changed source bytes or an uncommitted implementation and
never overwrites a consumed artifact. To reproduce first generation, use the
recorded implementation commit; default commands on the published branch reuse
and validate the retained outputs. Source/old accepted-order contract, old results
and operational planner/Lab files remain byte-for-byte unchanged against main.
No dependency, remote CI or hosted deployment was added. Main integration still
needs explicit owner approval after the earlier automatic review rejection.

Next independent work: physical-count truth/provenance with an additive synthetic
contract, then a concrete read-only hosting proposal. Censored lost-demand
feedback and broader closed-loop operational planning remain separately gated.
