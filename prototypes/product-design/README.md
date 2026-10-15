# Inventory Intelligence: two product directions

Preserved frontend exploration. The owner chose Desk for the main workbench;
Brief remains runnable here as a future alternative. This app is separate from
the implemented frontend and does not replace its working lifecycle controls.
Research, visual evaluation and selection tradeoffs: [Product design](../../docs/PRODUCT_DESIGN.md).

From the repository root, use the project's installed `.[lab]` Python environment:

```sh
PYTHONPATH=src python prototypes/product-design/run_api.py
```

In a second terminal:

```sh
cd prototypes/product-design
npm ci
npm run build
npm run preview
```

Open [A — Brief](http://127.0.0.1:5176/?direction=brief) or
[B — Desk](http://127.0.0.1:5176/?direction=desk). `npm run dev` serves the same
routes during editing. Both API and frontend bind only to loopback. No database,
model key, paid calls, journal or new study is required. `npm test` runs focused
state/exactness checks. The preview API uses the existing saved Coast catalog at
`docs/review/generalization-v1/generalization-two-site-v1.json.gz`.

Review the complete journey in either direction:

1. Overview: risk, opportunity and evidence problem; select an item/location.
2. Explore: search, filter category/location, sort, clear filters and inspect an item.
3. Investigate: read the finding, select original plan/training/supply sections,
   page through records and inspect original identities/clocks.
4. Compare: inspect saved proposal versus no action; explicitly compare whole-piece
   alternatives/delay, supplier capacity or donor-safe transfer. Changed assumptions
   hide old results. Capacity five withholds the six-piece purchase; no action stays
   inspectable. These are synthetic scenarios, not observed supplier terms.
5. Decide: review the advisory proposal, return to evidence/comparisons, export the
   exact decision context. No order or synthetic journal admission is submitted.
6. History: inspect exact per-key cutoffs/deltas and reopen a prior snapshot.
7. Execution: inspect saved actual-planner controls, transfer partial receipts and
   subsequent saved feedback. This separate study does not modify the current catalog.
8. Evaluation: inspect independent paths, blocked reviews, losses/ties and exact
   policy outcomes. No policy is promoted.

URLs retain the current cutoff/item/filter selection and browser Back restores it.
Use COAST-1 at coast site1 for incomplete evidence: its proposal remains Unknown and
comparison is withheld. Supplier/transfer terms and all cost units are synthetic.

Dependencies match current React/Vite versions; `lucide-react`0.577.0 (ISC) adds
consistent icons. Local fonts retain their original OFL licenses in `public/fonts`.
No competitor source, premium template, external dataset or runtime CDN is required.
