# Supply reliability and service interventions — v1

Frozen before outcomes on 2026-10-03. Identifier `supply-sensitivity-v1`.
Research-only, new RNG namespaces, no operational policy/schema changes.

Fresh seeds5301/5709/6027, constant/lumpy/declining families, 420-day lifecycle
shape reused from fresh-warmup-v1 under a distinct demand namespace. Score
origin308 for56 days, warmup56 days beforehand; prior history ends before warmup.
Use identical cold/warm information and per-policy owned warm state. Mean/fixed0,
TSB/fixed0 and TSB/expanding-q90 remain frozen; no new model or safety refit.
The extra TSB/fixed0 control is required to compare forecasts without changing
safety at the same time; it was added before examining any outcome values.

Cross nominal lead2/5/10 with low/medium/high hidden supplier variability. Each
path has one daily uniform six-valued latent shock shared by every intervention.
Map shocks to low=[1,1,1,1,1,1], medium=[0,0,1,1,2,2], high=[0,0,0,0,2,4]. All
distributions have expected delay1, but empirical means may differ. This is an
expected-mean-controlled variability study; retain actual review-slot means and
maximums. Neither supplier shocks nor future demand enter policy decisions.

Reference intervention: L5/medium/R7/on-hand10/pack2/MOQ4. Add four one-factor
controls: on-hand0, on-hand40, R1, and pack1/MOQ1. Review changes the protection
period as well as review frequency; report this joint policy effect honestly.
Quantities and constraints are fixed before outcomes, never repaired based on
observed shortage. Initial stock and all warmup/score/runoff purchases cost2;
h1/b10/setup2, no salvage. Common final calendar tail is21 days for every cell
(maximum L10 + maximum hidden delay4 + maximum review7).

There are13 physical interventions * three forecast/safety configurations * nine
family/seed labels * two start arms =702 logical simulations. Constant demand is repeated, so these
are not nine distinct independent demand paths. Cache exact identical inputs;
report unique physical computations, paired outcomes and all null denominators.

Measure score fill/cycle, startup-unfillable cold units, later missed fill,
warm carryover, target coverage, forecasts and full costs. For each one-factor
control report signed differences against the reference, separately by forecast
and start arm. Do not sum those differences into an invented causal shortage
partition: stock, review, forecast, constraints and supplier effects interact.
Initial feasibility is an independent evaluation bound; later residual misses
are not exclusively forecast error. Delay-tail quantiles are not used by safety.

Compare lowering supply variance at fixed nominal lead with changing forecast
at fixed supply and fixed zero safety. The separate q90 arm measures a different
forecast/safety combination. Report path-level gains/losses and denominators rather than a
universal forecast-versus-supplier claim. Conservation, common settlement,
equal-expected-delay profiles, absolute-calendar pairing and intervention-cost
oracles precede the bounded CLI. No new champion or population confidence.
