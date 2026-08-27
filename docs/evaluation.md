# Evaluation

## Post-audit update (read this first)

A senior-engineering audit of this repository (full report preserved in
`EngineerDiary.md`) found that the original test for "does the router cover
the 9 required business questions" only asserted `intent != "fallback_overview"`
-- it never checked that the *correct* intent was chosen. That gap let a
real bug ship silently: **"Which marketing campaigns generate the best
return on investment?" was being answered with product return-rate data**,
because the string "return on investment" contains the substring "return",
and the returns-analysis matcher ran before the marketing-ROI matcher. The
old version of this very document quoted the *intended* correct answer for
that exact question without the code actually producing it -- a direct
example of documentation getting ahead of what was verified.

Both are fixed now (see `qa.py`'s intent-ordering rewrite and
`EngineerDiary.md` for the fix rationale), and the regression is now
impossible to reintroduce silently: `tests/test_analytics.py` and
`tests/test_evaluation_suite.py` assert the *exact expected intent* for
every case, not just "something answered."

## How we know the analytics are correct

Every KPI, trend and comparison function in `analytics.py` is validated
against an independently pre-computed ground-truth reference
(`internal_validation/GROUND_TRUTH_INTERNAL.json`) generated separately from
the analytics code. Because the two were written independently and still
agree, the match is meaningful evidence of correctness rather than a
tautology. See [testing.md](testing.md) for the full breakdown.

## How we know the dataset itself is sound

`tests/test_data_integrity.py` (17 tests) codifies a manual audit of the raw
CSVs: zero duplicate keys, zero orphaned foreign keys, no negative/impossible
values, and the `stockout_flag`/`excess_stock_flag` derived columns verified
100% consistent with the raw stock numbers they describe. Full methodology
and the one non-obvious finding (an intentional, now-documented arithmetic
quirk in `inventory_daily.csv`) are in
[DATASET_METHODOLOGY.md](DATASET_METHODOLOGY.md).

## How we know the AI narration doesn't hallucinate

Two independent guards, tested independently:

1. **Numeric grounding** (`_numbers_are_grounded`) -- every number in
   generated text must trace to the evidence payload. Tested three ways:
   the positive case (every Finding's own template passes, proving the
   templates are grounded), and two adversarial cases proving the guard
   actually *rejects* a fabricated percentage and a fabricated currency
   value (`test_grounding_rejects_a_fabricated_percentage`,
   `test_grounding_rejects_a_fabricated_currency_value`).
2. **Entity grounding** (`_entities_are_grounded`, added in this hardening
   pass) -- catches the case numeric grounding can't: every number correct,
   attributed to the wrong named entity (e.g. crediting a different
   delivery partner with UrbanMove's delay rate). Tested with
   `test_entity_grounding_rejects_wrong_partner_name`, which constructs
   exactly that swap and confirms it's rejected while the correctly
   attributed version passes.

Both guards run on every narration call before it's shown; failing either
one discards the LLM output and shows the deterministic template instead
(verified, not just claimed -- see `narrate_finding`/`narrate_answer` in
`nlg.py`).

## How we know the Q&A router covers the required scope

All nine business questions listed in the case study's "Suggested Business
Questions" are exercised as parametrized tests
(`test_questions_route_to_the_correct_intent`) and now assert the *correct*
intent, not just "not fallback." 9/9 pass, plus 4 known paraphrases of the
hero question that previously failed (see below).

## The 40-question evaluation suite

`tests/eval_cases.py` + `tests/test_evaluation_suite.py`, added in the
post-audit hardening pass, per the requested distribution:

| Category | Count | Result |
|---|---|---|
| Factual | 10 | 10/10 pass |
| Analytical | 10 | 10/10 pass |
| Comparison | 5 | 5/5 pass |
| Anomaly | 5 | 5/5 pass |
| Recommendation-oriented | 5 | 5/5 pass |
| Unsupported (must honestly fall back) | 5 | 5/5 pass |
| **Total** | **40** | **40/40 pass** |

One case in the anomaly set ("Is there anything unusual about our margins?")
initially failed during this pass -- it fell back to the honest overview
instead of routing to the profitability intent, because the matcher required
a companion revenue/comparison word alongside "margin." Fixed by recognizing
"margin", "profitability" and "bottom line" as unambiguous on their own
(nothing else in this domain means those words), while keeping bare "profit"
requiring a companion signal since it can appear in ranking phrasing that a
different, more specific intent should claim first. This is reported here
rather than quietly re-running the suite until it was green, because the
point of an eval suite is to surface exactly this kind of gap.

Two categories of paraphrase were specifically tested because they were
flagged as likely failure points before this pass: "Are we making more
money?", "Is our profit keeping pace with revenue?", "Sales are up. Did
profitability improve?", and "Has our margin improved despite sales growth?"
all now correctly route to the same profitability-trend intent as the
literal suggested question. All four previously failed (3 fell back to the
generic overview, 1 happened to work by accident).

### Known limitations surfaced by the eval suite (not fixed in this pass)

- A raw headcount question ("how many employees work here?") routes to the
  correct intent *family* (`employee_store_performance`) but the analytics
  function behind it answers a different, case-study-required question
  (revenue-per-employee ranking) -- so the intent is "right" but the answer
  wouldn't satisfy a literal headcount ask. Not fixed because the underlying
  analytics function was built for the case study's actual required
  question, not a headcount lookup, and inventing a new function for a
  question the case study doesn't ask isn't in scope for this pass.
- Comparison questions without a ranking word ("compare revenue across
  regions" vs. "which region has the most revenue") fall back to the honest
  overview rather than matching `revenue_profit_leaders`. Tracked as a v2
  router-coverage improvement, not silently special-cased.

## Sample inputs and outputs

**Input (Ask mode):** *"Is revenue growth leading to stronger
profitability?"*
**Output:** *"No. Revenue grew 63.2% over the last 30 days but gross profit
grew only 53.8%, and gross margin moved -1.45 percentage points. Revenue
growth is currently outpacing profit growth."*
(Matches ground truth: latest revenue 11,758,774.82 vs. previous
7,203,600.40 → +63.2%; latest margin 23.84% vs. previous 25.29% → -1.45pp.)

**Input (Ask mode):** *"Which marketing campaigns generate the best return
on investment?"* -- **the exact question that was misrouted before this
hardening pass.**
**Output (verified after the fix):** *"Summer Cooling generates the best
marketing ROI at 5.71x (spend 38,000.00, attributed revenue 255,000.00)."*
(Matches ground truth top campaign exactly; intent is `marketing_roi`, not
`returns_by_category`.)

**Input (Discover mode, automatic):** Delivery Partner Performance Gap
finding.
**Output:** *"UrbanMove (DP04) has a 34.0% delayed-delivery rate and an
average customer rating of 4.38/5, compared with an average of 7.8% delayed
across the other 4 delivery partners."*
(Matches ground truth: DP04 delayed_rate 33.99%, avg_rating 4.38, vs. other
four partners averaging ~7.8%. Confidence: medium -- see
`insights._CONFIDENCE_NOTES` on small-sample z-scoring.)

**Input (Ask mode, unsupported):** *"What is the meaning of life?"*
**Output:** *"I couldn't map that question to one of the supported business
analyses... Here is the overall business snapshot instead: total revenue
..., gross profit ... (...% margin) across ... orders."*
(Demonstrates the honest-fallback path rather than a fabricated answer.)

## Known limitations

- The Q&A router's keyword matching means a sufficiently unusual phrasing of
  a supported question could still fail to match and trigger the fallback.
  This is a deliberate trade-off (see [ai-architecture.md](ai-architecture.md))
  -- the failure mode is an honest "I don't know how to answer that" rather
  than a wrong answer, which is exactly what the eval suite's unsupported
  category verifies.
- Employee-level performance is reported at the store level because the
  dataset doesn't attribute individual sales to individual employees; this
  is disclosed in the answer itself rather than papered over.
- Return-rate and delivery-partner outlier findings are statistically
  "medium" confidence, not "high" -- they're z-scored over 8 categories and
  5 partners respectively, small enough samples that a single data point
  meaningfully shifts the mean/std. The underlying numbers are exact; the
  *outlier judgment* is what carries the caveat, and this is now surfaced
  explicitly via the `confidence` field on every Finding.
- Ollama's output quality depends on the local model chosen; smaller models
  (3B) occasionally produce narration that fails a grounding check and falls
  back to the template -- this is treated as correct, safe behaviour, not a
  bug, and is now visible in the UI ("Verified analysis" notice) rather than
  a quiet caption.
