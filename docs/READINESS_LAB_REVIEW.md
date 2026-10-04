# Decision Lab adversarial readiness review

> Historical assessment for the recorded source/environment. Use [STATE](STATE.md)
> for current phase, scope, integration mode and acceptance references.

Reviewed 2026-10-03 from `429cc71`, using the existing packaged synthetic
archive and Python 3.12.14. No database, model API, external data or benchmark
recomputation was required for this slice.

## Findings and fixes

The archive transport digest and persisted input digests checked content
integrity, but several contradictory archives passed after those hashes were
recomputed. This matters for accidental export corruption and changes to the
bundled evidence even though the public API has no upload endpoint.

- A snapshot with a future business cutoff or a missing observation timestamp
  remained trusted. An unreconciled *other* saved inventory key also retained
  the whole reliability run's pass. Bounded archive validation now requires
  opening/snapshot reconciliation for every retained key, coverage, row counts,
  cutoff/watermark agreement and unique row identities.
- A supply batch could have a different SKU, a false expected receipt count,
  missing or inverted observation clocks, or duplicate identities while still
  being treated as complete. A null receipt identity passed archive validation
  and then raised inside simulation. Invalid archives now suppress both sides
  in the offline adapter and return HTTP 503 from all evidence/scenario routes.
- Duplicate demand row/order identities and boolean revision/count metadata
  could enter an eligible training series. Unique observation/order-line
  lineage, exact integer metadata and acceptance/source clock order are now
  required. Saved plan horizons, policy versions, forecast/training copies,
  distinct run identities and incomplete-supply reasons also agree.
- The risk card now names the **prefix projection** separately from periodic
  simulation backlog. A hidden three-day supplier delay preserves the prefix
  proposal but creates 17 scored days with periodic backlog; both are visible.
- Cost comparisons now show each arm's scored and runoff lengths. Default
  baseline is 28 + 5 days, while hidden delay 3 uses 28 + 8 days. Existing total
  costs 327 and 1171 therefore include different accounting durations. Scored
  costs remain 239 and 1027. No simulator arithmetic changed.
- An initial API failure now replaces loading/evaluating placeholders with
  unavailable/not-assessable text while retaining the retry action.

## Validation

Focused offline acceptance passed **23/23 Lab/API tests**. The new semantic
regressions include 29 distinct malformed cases with independently rebuilt
hashes, plus an HTTP regression for the previously uncaught null receipt ID.
The original independent quantity, service, cost, immutable pairing, null
denominator and strict input-boundary oracles remain unchanged and pass.
JavaScript syntax and `git diff --check` pass.

```sh
PYTHONPATH=src python -m unittest discover -s tests -p 'test_lab*.py' -v
node --check src/inventory_intelligence/lab_static/lab.js
```

Fresh full-database acceptance and browser checks of the integrated changes
belong to the integration owner; this scoped result does not claim either.
The bounded archive checks assume this declared zero-movement synthetic fixture.
They are not a second general reliability engine or a cryptographic source
attestation.

## Readiness and next evidence

The offline, packaged, read-only Lab is strong enough to keep its current scope:
exact calculations, bounded controls, inspectable source/counterfactual evidence
and explicit incomplete-input blocking. Preserve the distinction between its
single prefix proposal and the separate periodic ordering policy. It does not
establish a current order recommendation, calibrated service or measured savings.

The most useful small evaluation follow-up is a **common accounting horizon**
sensitivity alongside existing per-arm runoff totals and terminal stock. It
would test whether policy conclusions survive equal exposure duration before
adding forecast complexity. The current Lab should disclose this limitation;
the review does not change the frozen simulator accounting contract.
