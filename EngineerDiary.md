# Engineer Diary

Chronological record of decisions, trade-offs and lessons for this build.
Written for a future reader (recruiter, judge, or future me) who wants to
understand *why*, not just *what*.

## Decision: which of the four case studies to build

Considered all four AI BuildFest 2026 case studies (Customer Support
Assistant, Sales Assistant, HR/Recruitment Bot, Business Intelligence
Assistant). Chose Case Study 4 (Business Intelligence Assistant) because it
combines the strongest data/analytics depth with the clearest "AI must not
just be a wrapper" constraint — and because the judging panel includes a
data-analytics firm (10Alytics), where a superficial "LLM makes up numbers"
implementation would be spotted immediately rather than rewarded.

## Decision: no dataset was provided, so we built one — with a twist

The case study says "the provided business dataset," but no dataset was
actually distributed with the brief. Rather than build a generic/random
dataset, we constructed a synthetic-but-relationally-consistent NexaSphere
dataset with intentionally planted business conditions (margin pressure from
discounting, an elevated Audio return rate, a deteriorating delivery
partner, TV stockouts alongside AC excess stock, one standout marketing
campaign) and independently pre-computed a ground-truth reference file. This
let the analytics engine be validated against known-correct answers instead
of "it looks right to me."

## Decision: AI narrates, never calculates — enforced structurally

The single most important architectural decision in this project. It would
have been faster to hand the LLM the raw CSVs (or even the joined
dataframes) and ask it to answer questions directly. We rejected that
approach even though it's the "obvious" AI-first design, specifically
because it can't be trusted or tested the same way. Instead: pandas
computes everything, and the LLM only ever rephrases an already-verified
result — with a post-generation numeric check that discards ungrounded
output. This took longer to build than a naive LLM-does-everything version,
but it's the difference between "an AI demo" and "a system a business could
actually rely on."

## Bug found during testing: column-name collision in the sales/products join

`sales.csv` and `products.csv` both contain a `category` column (the data
dictionary documents this). A naive merge produced `category_x`/`category_y`
instead of a single `category` column, silently breaking every
category-grouped analytic with a `KeyError`. Fixed by dropping the sales
table's own `category` column before merging, keeping `products.csv` as the
single source of truth for the category dimension. Caught by the test suite
(`test_breakdown_by_category_sums_to_total_revenue`), not by manual
inspection — a good argument for why the tests were written before the UI.

## Bug found during testing: date strings misread as negative numbers

The numeric-grounding regex (`-?\d[\d,]*\.?\d*`) matched the "-06" in a date
string like `"2026-06"` as the number *-6*, which then failed the grounding
check because no evidence value was close to -6. Fixed with a negative
lookbehind so a leading `-` is only treated as a sign when it isn't
immediately preceded by a digit (dates keep their hyphen; genuine negative
percentages like "-4.6%" still parse correctly). Also extended the grounding
check to scan numbers embedded in evidence *strings* (not just numeric
values), since a month like `"2026-06"` is legitimate grounding for a
narration that mentions June 2026.

## Trade-off: rule-based intent detection instead of an LLM router

Considered routing "what does this question want?" through the LLM too.
Decided against it: the case study specifies a closed set of required
questions, a keyword router covers all nine of them with 100% test coverage
and zero dependency on a model being installed, and its worst-case failure
(an honest "I couldn't map that question") is strictly safer than an LLM
router occasionally picking the wrong analysis with high confidence.

## Trade-off: Streamlit over a custom React/FastAPI stack

The original strategy discussion (before the case study was finalized)
considered Next.js + FastAPI + Postgres + pgvector for a more elaborate
multi-agent product. Once Case Study 4 was locked in and the solo-builder,
zero-budget, tight-deadline constraints were made explicit, that stack was
deliberately downsized to Streamlit + pandas + Ollama: it's the fastest path
to a genuinely functional, testable prototype that still demonstrates real
engineering discipline (layered architecture, deterministic core, tested
guardrails) rather than a large amount of unfinished scaffolding.

## What I'd build next (v2, not required for this submission)

- A background job that periodically snapshots findings so the "Discover"
  view can show trend-over-time on findings themselves (e.g. "this return
  outlier has persisted for 3 weeks").
- Swap the CSV loader for Postgres so this can run against a live retailer's
  data rather than a static file.
- Add an evaluation harness that runs a larger battery of paraphrased
  questions against the intent router to measure and improve match rate
  before falling back.

---

## Phase 2 — Generalisation, UI rebuild, deployment readiness

### Bugs found and fixed (each now has a regression test)

**"What questions can I ask?" answered with a revenue dump.** The router ran
nine keyword matchers; a question containing no business keyword fell through to
`fallback_overview`, which printed the KPI snapshot. There was no concept of a
question *about the assistant*. Added `meta_capabilities` and `out_of_scope`
intents ahead of all topic matchers, and stopped the unmatched fallback from
emitting numbers at all — answering an unmatched question with unrelated totals
reads as bluffing.

**Capability matrix contradicted the KPI panel.** With `cost` but no `profit`
column, `kpi_summary` derived profit and displayed a margin, while
`capability_matrix` only checked for an explicit `profit` column — so the UI
showed "51.67% margin" beside "Profitability: not detected". Fixed by deriving
`profit` once in `build_canonical_frame` so every downstream function agrees.

**Groq narration silently fell back to templates.** The default model name had
been retired by Groq (404). Fixed by moving to a currently listed model; the
symptom is documented in DEPLOYMENT.md because it will recur.

**Streamlit header covered the navigation.** `stHeader` is a 60px opaque bar at
z-index 999990; content padding was 22px, so it painted over the navbar and pill
tabs. Made transparent and click-through with padding below. Also reverted an
earlier over-correction that hid the whole toolbar: the running/connecting
indicator is real feedback and hiding it makes a slow AI call look like a freeze.
Only the Deploy button is hidden.

**Indented HTML rendered as code blocks.** Streamlit runs markdown through a
Markdown renderer, which treats 4+ space indentation as code. `textwrap.dedent`
was insufficient because interpolated SVG already sits at column 0, zeroing the
common prefix. Strip every line instead — safe for HTML.

**Charts stayed Plotly-blue.** `layout.colorway` was set, but Plotly Express
assigns each trace an explicit colour at creation, which wins. Fixed by setting
`px.defaults` once at startup.

**Navigation assignment raised StreamlitAPIException.** "Confirm & Analyze"
wrote to `nx_active_page` — the nav radio's own key — after the widget was
instantiated, so it silently did nothing. Requested pages are now staged in
`nx_pending_page` and applied before the widget is built.

**Stale mapping selections overrode fresh suggestions.** A keyed Streamlit
widget takes its value from session state and *ignores* the `index` argument, so
the previous file's mapping persisted into the next upload — which is how a
correctly detected `snapshot_date` was reported as "no date column mapped".
`ud_map_*` keys are now cleared whenever the upload set changes.

**Primary table chosen by row count.** Uploading a business folder selected
`inventory_daily.csv` (130k rows, no money column) over `sales.csv`. Selection
is now scored by analytical usefulness — money column first, then date, size
only breaking ties.

**Sidebar conflated two states.** "Not analyzed yet" and "analyzed, but no date
column" shared one message, making a pre-analysis workspace look like a mapping
failure. Now distinct.

### Judgement calls

**Declined images/video rather than faking support.** Reliable OCR needs a
system Tesseract binary unavailable on free hosting, and there's no dependable
free path from video to trustworthy figures. A broken feature is worse than an
explained absence — and it is the one area where a judge could dismantle the
trust story in thirty seconds.

**Streamed verified text, not raw model tokens.** Streaming live would put
numbers on screen before the grounding check has run. A figure that has been
read has already misinformed the reader even if retracted.

**Corrected an earlier wrong claim.** I had told the user bespoke layouts were
impossible in Streamlit. That was wrong — the DOM-order constraint applies only
to interactive widgets; `unsafe_allow_html` content lands in the main document,
so CSS Grid, layering and inline SVG were available throughout. The rebuilt UI
depends on that, and the correction is recorded in `theme.py`.

**Kept `analytics.py` untouched.** Generalising it would have risked the
competition demo. `user_data.py` is a separate, smaller engine; the two share
the narration and grounding layer, which was already dataset-agnostic.
