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
