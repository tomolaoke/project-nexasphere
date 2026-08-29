# System Architecture

## Layered design

```
                    ┌─────────────────────────┐
                    │        data/*.csv        │   raw Ordino dataset
                    └────────────┬─────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │     data_loader.py        │   load, type, join (cached)
                    └────────────┬─────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │      analytics.py          │   deterministic KPIs, trends,
                    │  (no LLM calls, ever)      │   comparisons, z-score anomalies
                    └────────────┬─────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │      insights.py            │   ranks analytics output into
                    │                              │   cited Findings (severity-sorted)
                    └────────────┬─────────────┘
                                 ▼
              ┌──────────────────┴───────────────────┐
              ▼                                        ▼
   ┌─────────────────────┐                  ┌─────────────────────┐
   │        qa.py           │                  │       nlg.py           │
   │ question → intent →     │ ───────────────▶ │ LLM narration (Ollama) │
   │ analytics function       │                  │ + numeric-grounding    │
   └─────────────────────┘                  │   guard + template     │
                                              │   fallback              │
                                              └────────────┬────────────┘
                                                            ▼
                                              ┌─────────────────────┐
                                              │       app.py            │
                                              │   Streamlit UI            │
                                              └─────────────────────┘
```

## Why this layering, specifically

**Analytics never imports nlg, and nlg never imports data_loader.** This
isn't incidental — it's the enforcement mechanism for "AI doesn't calculate."
The AI layer physically cannot query the raw data; it can only receive
already-computed evidence dictionaries and phrase them. There is no code
path by which the language model sees the CSVs.

**Findings carry their own evidence.** A `Finding` (see `insights.py`) is a
dataclass with a `summary` string and an `evidence` dict. The `nlg` module's
grounding check (`_numbers_are_grounded`) walks the evidence recursively and
verifies every number in the generated narration exists in that evidence,
before showing it. If the check fails, the pre-written template sentence is
shown instead. This is tested directly in
`tests/test_analytics.py::test_every_finding_summary_number_is_grounded_in_evidence`.

**The intent router is rule-based, not model-based.** The case study lists
nine required business questions verbatim. A keyword-matched router against
that fixed list is more reliable, more testable, and zero-cost compared to a
general NL2SQL model, and its failure mode is honest ("I couldn't map that
question...") rather than a wrong answer delivered with false confidence.

## Data flow for a single Ask-mode question

1. User types a question in the Streamlit text box.
2. `qa.answer_question()` lower-cases it and runs it through an ordered list
   of intent matchers (`_intent_*` functions), each a simple keyword check.
3. The first matching intent calls the corresponding `analytics` function
   and builds a `result` dict (the verified computed answer) plus a
   deterministic `template_answer` string built only from that dict.
4. `nlg.narrate_answer()` is called with the question, the result, and the
   template. If Ollama is reachable, it asks the model to *rephrase* the
   template using only numbers present in `result`; the numeric-grounding
   check runs on the output. If Ollama is unreachable, or the check fails,
   the template is returned as-is.
5. The Streamlit UI renders the narration text, its source (`llm` or
   `template`), and the raw `result` JSON in an expander for full
   transparency.

## Tech stack (100% free / open-source)

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11 | Data/AI ecosystem, single runtime for analytics + AI + UI |
| Data | pandas / numpy | Standard, fast, testable |
| UI | Streamlit | Fastest path to a real interactive prototype, free hosting on Streamlit Community Cloud |
| Charts | Plotly | Interactive, works natively inside Streamlit |
| LLM | Ollama + Llama 3.2 (or any local model) | Free, local, open-source, no API key, no usage cap |
| Tests | pytest | Standard, CI-friendly |

## Known gotcha: `sales.csv` and `products.csv` both have a `category` column

`sales.csv` carries its own `category` column (a denormalized copy), and so
does `products.csv`. A naive `sales.merge(products, on="product_id")`
produces `category_x`/`category_y` instead of a single `category` column,
which silently breaks every category-grouped analytic with a `KeyError`.
Fixed by dropping `sales`'s own `category` column before any merge with
`products` (see `data_loader.sales_enriched` and `analytics.return_analysis`)
so `products.category` remains the single source of truth. Documented here
because it's the kind of thing that reappears if a new analytics function
merges the two tables without knowing this.

## What would change for a multi-tenant production version

This prototype reads CSVs directly for simplicity and demo speed. A
production version would swap `data_loader.py`'s file reads for a Postgres
connection (the rest of the architecture — analytics → insights → nlg → qa
— is storage-agnostic and would not need to change), add authentication and
per-business data isolation, and move the Ollama call behind a queue so
narration doesn't block the request thread under load. See
[FeatureIntegrations.md](../FeatureIntegrations.md) for the full list of
what's in-scope for the prototype vs. deferred.

---

## Update — modules added since the initial architecture

| Module | Responsibility |
|---|---|
| `ingestion.py` | Multi-file, multi-format upload. Sorts files into DATA (CSV/TSV/XLSX/JSON) and CONTEXT (PDF/DOCX/TXT/MD); declines images/video with an explanation; selects one primary table by analytical usefulness; surfaces candidate relationships without joining. |
| `user_data.py` | Schema-agnostic pipeline for uploaded data: profiling, semantic mapping, capability matrix, generic analytics, findings and a capability-aware question router. |
| `theme.py` | Presentation only — design system (light/dark via CSS custom properties), landing page, app chrome, generated inline SVG, Plotly theming. Imports no analytics module. |

### Why `user_data.py` is separate from `analytics.py`

`analytics.py` and `insights.py` are deliberately coupled to the Ordino
schema — specific joins (`sales.merge(products, on="product_id")`) and specific
column names. Generalising them would risk the competition demo. `user_data.py`
is a smaller, schema-agnostic engine that only computes what the mapped columns
support. The two share the AI narration and grounding layer, which was already
dataset-agnostic and needed no change.

### Workspaces

```
Landing
 ├── Explore Demo        → demo workspace   (data/*.csv, cached, read-only)
 └── Analyze My Business → business workspace (session state, isolated)
```

Both render the same five pages (Overview, Findings, Ask, Dashboards, Data)
against different engines. User uploads cannot overwrite the demo dataset; the
active workspace is always named in the header and sidebar.

### Request flow

```
main()
 ├── theme.inject_css()            palette by session theme
 ├── theme.apply_chart_defaults()  Plotly colour defaults
 ├── landing gate                  → render_landing()
 ├── business setup gate           → required details before upload
 ├── render_sidebar()              backend status, dataset window, privacy
 ├── theme.app_shell()             logo/home, workspace, theme toggle, pill nav
 └── page dispatch                 demo engine or user engine
```

Navigation is staged through `nx_pending_page` and applied *before* the nav
widget is instantiated — Streamlit raises if a widget's key is written after
the widget exists.
