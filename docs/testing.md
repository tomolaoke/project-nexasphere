# Testing

## Suite overview (88 tests total, `pytest tests/ -q`)

| File | Count | What it proves |
|---|---|---|
| `tests/test_analytics.py` | 30 | Analytics correctness, ground-truth validation, insight ranking, numeric/entity-grounding guarantees, and exact-intent routing for all 9 case-study questions + 4 paraphrases |
| `tests/test_data_integrity.py` | 17 | The raw dataset itself: no duplicate keys, no orphaned foreign keys, no impossible values, derived flags (`stockout_flag`/`excess_stock_flag`) 100% consistent with the raw numbers they describe |
| `tests/test_evaluation_suite.py` | 41 | The 40-question AI evaluation suite (factual/analytical/comparison/anomaly/recommendation/unsupported) + 1 distribution check |

### `test_analytics.py` breakdown

| Group | What it proves |
|---|---|
| KPI shape & manual reconciliation | `kpi_for_window` matches a hand-computed subtotal for a narrow, easy-to-verify one-day window |
| Ground-truth validation (7 tests) | Revenue/profit/orders for the last-30/previous-30-day comparison, the top return category, the worst delivery partner, the top campaign ROI, and stockout scale all match an independently pre-computed reference file the analytics engine never sees |
| Margin-pressure detection | The engine correctly flags the intentionally planted "revenue growing faster than profit" condition |
| Dimensional integrity | `breakdown_by` rejects unknown dimensions; category-level revenue sums back to total revenue (no double-counting from the products/sales join) |
| Insight engine ranking | `generate_findings()` returns findings sorted by severity (critical → warning → watch → info) |
| Numeric-grounding guarantee (positive case) | Every Finding's own template summary passes the same grounding check used to gate LLM output |
| Numeric-grounding guarantee (adversarial) | The guard actually **rejects** a fabricated percentage and a fabricated currency value -- not just "the real templates happen to pass" |
| Entity-grounding guarantee (adversarial) | The guard **rejects** a correct-numbers-wrong-entity swap (crediting the wrong delivery partner with UrbanMove's delay rate) and accepts the correctly attributed version |
| Q&A exact-intent routing | All 9 case-study questions + 4 hero-question paraphrases route to the *correct* intent, not just "not the fallback" -- this is what caught the marketing-ROI/returns routing bug (see `docs/evaluation.md`) |
| Honest fallback | An unrelated question ("What is the meaning of life?") correctly falls back to the honest "couldn't map that question" response rather than guessing |

## How ground truth was used without leaking it into the product

The dataset generation process (documented in `docs/DATASET_METHODOLOGY.md`)
independently pre-computed expected values for period comparison, top
return category, delivery partner performance, campaign ROI ranking and
stockout scale, and stored them in
`internal_validation/GROUND_TRUTH_INTERNAL.json` -- explicitly outside
`/data` so the running application never reads it. The test suite reads it
directly from `internal_validation/` to check the analytics engine's
*independently written* calculation logic against that reference, which is
what makes the match meaningful rather than circular.

## Running the tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

If `internal_validation/GROUND_TRUTH_INTERNAL.json` isn't present (e.g. a
judge cloning only the public repo), the ground-truth-dependent tests are
skipped rather than failing -- the rest of the suite (manual reconciliation,
ranking, grounding, data integrity, Q&A coverage) still runs and still
proves correctness independent of that internal file.

## Manual UI verification performed

The Streamlit app was run end-to-end in a browser during development, both
before and after the post-audit hardening pass:

- **Findings tab** -- confirmed all six findings render, match the planted
  story (Audio returns, UrbanMove delays, revenue/profit growth gap), show
  the new confidence label and possible-drivers list, and each evidence
  panel expands correctly.
- **Ask tab** -- confirmed a suggested question and multiple hero-question
  paraphrases all return the correct grounded answer, including the intent
  label and narration source; confirmed the previously-broken marketing-ROI
  question now returns marketing data, not return-rate data.
- **Dashboards tab** -- confirmed all charts and tables render without
  console errors, including the newly added employee-performance and
  customer-segment panels.

## What isn't covered yet (known gap, not hidden)

- No automated UI/end-to-end tests (e.g. Playwright) -- verified manually
  instead, given the solo-builder time constraint. Documented as a P2 item
  for a post-competition iteration.
- No load/performance testing -- the dataset size (30k+ sales rows) loads
  and computes in well under a second locally, which was sufficient for the
  prototype's scope.
- The AI evaluation suite tests *routing correctness*, which is fully
  deterministic and therefore fully testable. It does not (and cannot,
  without a live Ollama instance running during CI) automatically grade the
  *quality* of live LLM-generated prose -- that path is instead protected by
  the numeric/entity grounding guards, which run on every real generation
  and were separately verified with adversarial inputs.

---

## Update — current test inventory

**140 tests, all passing.**

```bash
python -m pytest tests/ -q
```

| File | Coverage |
|---|---|
| `test_analytics.py` | KPI correctness vs. independently computed ground truth; finding grounding; intent routing for all nine case-study questions and paraphrases; meta/out-of-scope intents; Pidgin routing; adversarial grounding (wrong number, wrong entity) |
| `test_data_integrity.py` | Referential integrity, valid ranges, date validity, flag consistency |
| `test_evaluation_suite.py` | The 40-question evaluation suite |
| `test_user_data.py` | CSV loading, empty/malformed files, profiling, date/numeric detection, mapping proposals and type-filtered options, capability detection, derived profit, dataset window, generic analytics, honest refusal |
| `test_ingestion.py` | CSV/TSV/JSON/XLSX/DOCX/TXT/MD ingestion, DATA vs CONTEXT classification, declined images/video, malformed and empty files, multi-file handling, candidate relationships (and that they are *not* auto-joined), primary-table selection |

### Regression tests written from real defects

Each of these encodes a bug found during development, so it cannot silently
return:

- **Marketing ROI mis-routed to returns** — "return on investment" contains "return".
- **Ungrounded number accepted** — adversarial narration must be rejected.
- **Correct number, wrong entity** — crediting one partner with another's rate must be rejected.
- **Meta question answered with a KPI dump** — "What can I ask?" must list capabilities and must not contain business figures.
- **Unsupported question answered with numbers** — declined answers must contain no business figures.
- **Capability matrix contradicting the KPI panel** — revenue+cost must report Profitability as supported.
- **Primary table chosen by size** — a large inventory snapshot with no money column must lose to a smaller sales table.
- **Dataset window falling back to demo dates** — must return `None` when no date column is mapped, never another dataset's range.

### Manual verification

Browser-driven QA on each release: landing page, both CTAs, all five pages in
both workspaces, upload → profile → map → confirm, light and dark themes,
mobile (375px), and console/server error checks.
