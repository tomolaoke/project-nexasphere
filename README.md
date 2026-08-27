# NexaSphere AI Business Intelligence Assistant

**AI BuildFest 2026 · Track 1 — AI for Business & Productivity · Case Study 4**

> Revenue can grow while profit quietly doesn't. NexaSphere turns disconnected
> retail data into a ranked list of what management should look at today —
> each finding backed by a number you can trace back to the raw dataset,
> explained in plain English, with a concrete next step.

## The one-sentence pitch

We built an AI decision-support copilot that connects a retailer's sales,
returns, delivery, inventory and marketing data, explains *why* a number
moved, and recommends what deserves investigation — without ever letting the
AI invent a number.

## Why this isn't "chat with your CSV"

Most AI-over-data demos wire an LLM directly to a database and hope it does
correct arithmetic. We don't. See [docs/ai-architecture.md](docs/ai-architecture.md)
for the full reasoning, but the short version:

```
Business data → deterministic analytics engine → verified metrics → AI narration
```

The analytics engine (plain pandas, unit-tested, validated against an
independent ground truth) owns every number. The AI layer — a local,
free, open-source model via [Ollama](https://ollama.com) — is only ever
allowed to *rephrase* numbers that already exist in a verified result. A
post-generation numeric check throws away any model output that introduces a
number not present in the evidence, and the app falls back to a
deterministic, plain-English template. Nothing about the app breaks, and
nothing gets invented, whether or not Ollama is installed.

## What it actually does (functional prototype)

- **Findings ("Discover" mode)** — six ranked business findings, generated
  every time from live data: profitability vs. revenue growth, category
  return-rate outliers, delivery-partner performance gaps, inventory
  stockout/excess imbalance, marketing ROI spread, and target attainment.
  Every finding card shows its supporting evidence JSON.
- **Ask a Question ("Ask" mode)** — a natural-language box that answers the
  nine business questions the case study specifies (revenue/profit leaders,
  growth vs. profitability, returns, marketing ROI, inventory, delivery,
  customer segments, store/employee performance, targets), computed live.
- **Dashboards** — monthly revenue/profit trend, category and regional
  revenue mix, return-rate and delivery-delay charts, campaign ROI table,
  target-vs-actual table.

## Try it in three commands

```bash
pip install -r requirements.txt
streamlit run app.py
```

That's it — no API keys, no signup, no paid service. Everything works with
the deterministic template narrator out of the box. To enable AI-phrased
narration:

```bash
# optional, free, runs locally
ollama pull llama3.2
ollama serve
```

The app auto-detects Ollama at `http://localhost:11434` and switches to LLM
narration; if it's not reachable, nothing errors — it just uses the
template narrator (which itself is the ground truth wording, not a lesser
experience).

## Repository layout

```
app.py                      Streamlit UI (three tabs: Findings, Ask, Dashboards)
src/nexasphere/
  data_loader.py             Loads & joins the CSVs (single source of truth)
  analytics.py                Deterministic KPI / trend / anomaly / comparison functions
  insights.py                  Ranks analytics output into cited Findings
  nlg.py                        LLM narration + numeric-grounding guardrail + template fallback
  qa.py                          Natural-language question → intent → analytics → nlg
data/                        NexaSphere BuildFest dataset (CSV)
internal_validation/       Ground-truth file used only by the test suite, never by the app
tests/test_analytics.py   22 tests: unit tests + ground-truth validation + grounding checks
docs/                          Competition deliverables (problem statement, architecture, etc.)
EngineerDiary.md            Chronological engineering decisions and trade-offs
FeatureIntegrations.md    Every integration used, and why
Non-technical-breakdown.md  What we built, explained with no jargon
ReviewerNotes.md            For judges/recruiters: what to look at first
```

## Dataset

The competition case study did not ship a dataset, so we constructed a
synthetic, relationally-consistent retail dataset (`/data`) matching the
NexaSphere scenario, and independently pre-computed a ground-truth
validation file (`internal_validation/GROUND_TRUTH_INTERNAL.json`, excluded
from the public app) so the analytics engine's output could be verified
rather than eyeballed. Details: [data/DATASET_README.md](data/DATASET_README.md).

## Responsible AI

No hallucinated numbers, explanations cite their evidence, recommendations
point at what to *investigate* rather than issuing an autonomous decision.
Full write-up: [docs/responsible-ai.md](docs/responsible-ai.md).

## Competition deliverables

- [docs/NexaSphere-Executive-Summary.pdf](docs/NexaSphere-Executive-Summary.pdf) — plain-English problem/use case/advantages/recommendations/value proposition
- [docs/pitch-deck/NexaSphere-Pitch-Deck.pptx](docs/pitch-deck/NexaSphere-Pitch-Deck.pptx) — 10-slide pitch deck
- [docs/demo-script.md](docs/demo-script.md) — 3-minute demo video flow
- [docs/problem-statement.md](docs/problem-statement.md), [solution.md](docs/solution.md), [architecture.md](docs/architecture.md), [ai-architecture.md](docs/ai-architecture.md), [responsible-ai.md](docs/responsible-ai.md), [evaluation.md](docs/evaluation.md), [testing.md](docs/testing.md), [business-impact.md](docs/business-impact.md)
- [EngineerDiary.md](EngineerDiary.md), [FeatureIntegrations.md](FeatureIntegrations.md), [Non-technical-breakdown.md](Non-technical-breakdown.md), [ReviewerNotes.md](ReviewerNotes.md)

## Testing

22 automated tests cover the analytics engine, the insight engine's
numeric-grounding guarantee, and all nine required business questions.
Full write-up: [docs/testing.md](docs/testing.md) and [docs/evaluation.md](docs/evaluation.md).

## Cost

$0. Python, pandas, Streamlit, Plotly and Ollama are all free and
open-source; the dataset is synthetic; there is no paid API in the critical
path.
