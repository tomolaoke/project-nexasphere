# Ordino — AI Business Intelligence Assistant

**Turn business data into decisions.**

10Alytics Hack-AI-thon & BuildFest 2026 · Case Study 4 — AI Business
Intelligence Assistant · Track: AI for Business & Productivity

---

## The problem

NexaSphere Retail Ltd. collects sales, customer, inventory, marketing,
employee and delivery data across stores, hubs and digital channels. Reports
exist, but managers still can't quickly see *what is driving performance*.
Revenue can rise while margin, delivery reliability, returns and satisfaction
quietly deteriorate — and finding that out means cross-referencing several
spreadsheets by hand.

## The solution

Ordino answers business questions in plain language, **but never lets an
AI model produce the numbers**:

```
Business data
   → Deterministic analytics   (pandas — the numbers are computed here)
   → Verified evidence         (a structured dict of real values)
   → AI explanation            (rephrases the evidence, nothing more)
   → Grounding validation      (rejects any number or entity not in evidence)
   → Recommendation → human decision
```

The language model is a *narrator*, not a calculator. Every sentence it
produces is checked against the evidence that produced it, and rejected if it
contains a figure or an entity attribution that isn't there. If no model is
reachable, the deterministic template narration is used and the app keeps
working — the numbers are identical either way.

> **The data calculates. The AI explains. The evidence builds trust. The
> human decides.**

## Two workspaces

| Workspace | Purpose |
|---|---|
| **NexaSphere Retail (Demo)** | The BuildFest retail dataset and its hero story. Always available, never overwritten. |
| **Analyze My Business** | Any business uploads their own files; Ordino profiles them, reports what they *can* answer, and runs the same pipeline. |

## Features

- **KPIs** — revenue, gross profit, margin, orders, with period-on-period change and real sparklines
- **Findings** — six ranked findings with severity, confidence, possible drivers (never stated as causes), evidence and a recommendation
- **Ask Ordino** — streaming chat; formal English, casual English, or Nigerian Pidgin
- **Dashboards** — revenue/profit trend, category, region, returns, delivery, employee, segment, campaign ROI, target attainment
- **Analyze My Business** — multi-file upload (CSV/TSV/XLSX/JSON as data; PDF/DOCX/TXT/MD as context), profiling, data-quality score, type-filtered column mapping, capability matrix, and a dashboard generated from *their* columns
- **Light and dark themes**

## Quick start

```bash
pip install -r requirements.txt
```

```bash
streamlit run app.py
```

Open http://localhost:8501. **No API key is required** — without one the app
uses verified template narration and every number is still fully computed.

### Optional: enable AI narration (free)

Either backend works; both are $0.

**Hosted (works anywhere, including Streamlit Cloud):** get a free key at
[console.groq.com/keys](https://console.groq.com/keys), then create
`.streamlit/secrets.toml` (gitignored):

```toml
GROQ_API_KEY = "gsk_your_key_here"
```

**Local (fully offline):** install [Ollama](https://ollama.com), then:

```bash
ollama pull llama3.2
```

Ollama is preferred when reachable; Groq is the fallback; template narration
is the final fallback. The active backend is shown in the sidebar.

## Tests

```bash
python -m pytest tests/ -q
```

140 tests: analytics correctness against an independently computed ground
truth, data integrity, a 40-question evaluation suite, adversarial grounding
tests, ingestion, profiling and column mapping. See
[docs/testing.md](docs/testing.md).

## Tech stack — all free and open-source

| Layer | Tool |
|---|---|
| UI | Streamlit |
| Analytics | pandas, NumPy |
| Charts | Plotly |
| Ingestion | pandas, openpyxl (XLSX), pypdf (PDF), python-docx (DOCX) |
| AI narration | Ollama (local, open-source models) or Groq free tier |
| Tests | pytest |
| Design | hand-written CSS + generated inline SVG (no image assets, no icon package) |

**Total cost: $0.** No paid API, database, hosting or asset is used.

## Documentation

| Document | Contents |
|---|---|
| [problem-statement.md](docs/problem-statement.md) | The business problem |
| [solution.md](docs/solution.md) | Solution and workflow |
| [architecture.md](docs/architecture.md) | System architecture |
| [ai-architecture.md](docs/ai-architecture.md) | AI layer and grounding guardrails |
| [responsible-ai.md](docs/responsible-ai.md) | Responsible AI position |
| [evaluation.md](docs/evaluation.md) | Evaluation suite and results |
| [testing.md](docs/testing.md) | Test strategy and evidence |
| [business-impact.md](docs/business-impact.md) | Expected business value |
| [SAMPLE_IO.md](docs/SAMPLE_IO.md) | Sample inputs and outputs |
| [USER_DATASET_WORKFLOW.md](docs/USER_DATASET_WORKFLOW.md) | Upload → analysis pipeline |
| [PRIVACY.md](docs/PRIVACY.md) | Data handling |
| [USER_DATA_LIMITATIONS.md](docs/USER_DATA_LIMITATIONS.md) | What it deliberately won't do |
| [UI_UX_AUDIT.md](docs/UI_UX_AUDIT.md) | UI audit |
| [JUDGE_QA.md](docs/JUDGE_QA.md) | Anticipated judge questions |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Deploying for free |
| [FINAL_SUBMISSION_CHECKLIST.md](docs/FINAL_SUBMISSION_CHECKLIST.md) | Pre-submission QA |
| [DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) · [DATASET_METHODOLOGY.md](docs/DATASET_METHODOLOGY.md) | Dataset reference |

## Repository layout

```
Project-Ordino/
├── app.py                     Streamlit application
├── src/ordino/
│   ├── data_loader.py         Cached CSV loading (demo dataset)
│   ├── analytics.py           Deterministic analytics engine
│   ├── insights.py            Findings + evidence model
│   ├── qa.py                  Question router (demo workspace)
│   ├── nlg.py                 AI narration + grounding guardrails
│   ├── ingestion.py           Multi-file, multi-format ingestion
│   ├── user_data.py           Schema-agnostic profiling and analytics
│   └── theme.py               Design system, landing page, chrome
├── data/                      Demo dataset (12 CSVs)
├── tests/                     140 tests
└── docs/                      Documentation
```

## Responsible AI

- The model never calculates an authoritative business figure.
- Numeric and entity grounding checks reject unsupported output.
- Findings say "consistent with" and "worth investigating" — never "caused by".
- Uploaded data is session-scoped and never persisted; raw files are never sent to any model.
- Unsupported questions are declined honestly instead of answered with unrelated numbers.

## Licence

Built by Tomola Oke - ID-BF-0260 for 10Alytics BuildFest 2026. The demo dataset is synthetic — see
[DATASET_METHODOLOGY.md](docs/DATASET_METHODOLOGY.md).
