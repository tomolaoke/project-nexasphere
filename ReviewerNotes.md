# Reviewer Notes

For judges and recruiters short on time. Five minutes gets you the whole
picture.

## 60-second version

Run `pip install -r requirements.txt && streamlit run app.py`. Open the
**Findings** tab first — six business findings render immediately, computed
live from the dataset, each with an evidence panel. Then try the **Ask**
tab with one of the suggested questions. Everything you see is backed by
`pytest tests/` (22 passing tests), including a test that verifies findings
against an independently pre-computed ground-truth file.

## What to look at, in order of what proves the most

1. **[src/ordino/nlg.py](src/ordino/nlg.py)** — the numeric-grounding
   guardrail (`_numbers_are_grounded`). This is the mechanism that makes "no
   hallucinated numbers" an enforced property of the code, not a claim in a
   README.
2. **[tests/test_analytics.py](tests/test_analytics.py)** — specifically
   `test_every_finding_summary_number_is_grounded_in_evidence` and the
   ground-truth comparison tests. Run it yourself: `pytest tests/ -v`.
3. **[src/ordino/insights.py](src/ordino/insights.py)** — see how a
   `Finding` always carries its own `evidence` dict alongside its `summary`
   text; this is what the UI's evidence panels and the grounding check both
   read from.
4. **[src/ordino/qa.py](src/ordino/qa.py)** — the intent router
   covering all nine business questions the case study requires.
5. **[app.py](app.py)** — three tabs, ~200 lines, no business logic lives
   here; it only calls into `analytics`/`insights`/`qa`/`nlg` and renders
   the result. That separation is deliberate.

## Where the "story" in the data comes from

Since no dataset was provided with the case study brief, we built a
synthetic one and intentionally planted realistic business conditions
(margin pressure, an Audio return-rate outlier, a deteriorating delivery
partner, an inventory imbalance, one standout marketing campaign) so the
assistant would have real signals to discover. This is disclosed openly in
[README.md](README.md) and [data/DATASET_README.md](data/DATASET_README.md)
— we're not claiming the AI "magically" found something we didn't already
know was there; we're proving the analytics engine correctly *discovers*
signals we can independently verify, which is the harder and more honest
claim.

## Common questions we anticipate

**"Isn't a rule-based Q&A router just... not AI?"** The router is
intentionally simple and deterministic — see
[docs/ai-architecture.md](docs/ai-architecture.md) for why that's a design
choice, not a shortcut. The AI is used where it adds real value (turning
verified numbers into natural language) and avoided where it would introduce
risk without benefit (deciding what a number is).

**"What if Ollama isn't installed when I run this?"** Nothing breaks. The
app detects this and uses the deterministic template narrator, which is
shown in the UI as "Narration source: template." Every number and every
finding is identical either way; only the sentence phrasing differs.

**"Where's the ground truth file — is it in the repo?"** No, by design.
`internal_validation/GROUND_TRUTH_INTERNAL.json` is excluded from `/data`
and from git per the dataset README's own instruction not to expose it
publicly. The test suite reads it directly from that folder for validation
only.

## Scope honesty

This is a solo-built, zero-budget competition prototype, not a finished SaaS
product. Known gaps (multi-tenant auth, a real database instead of CSVs, a
larger evaluation harness for the intent router) are listed explicitly in
[docs/testing.md](docs/testing.md) and
[EngineerDiary.md](EngineerDiary.md) rather than glossed over.
