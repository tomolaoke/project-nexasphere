# Feature Integrations

Every meaningful integration used in this project, what it does, and why it
was chosen — all free/open-source, $0 total cost.

## AI model: Ollama + Llama 3.2 (local, optional)

- **What:** A local, open-source LLM runtime. The app calls
  `POST /api/chat` on `http://localhost:11434` (configurable via
  `OLLAMA_HOST` / `OLLAMA_MODEL` env vars).
- **Why:** Free, no API key, no per-token cost, no rate limit tied to money,
  works fully offline. Fits the hard zero-budget constraint without a
  "free tier that runs out" risk.
- **How it's used:** Only to rephrase already-computed evidence into plain
  English (`nlg.narrate_finding`, `nlg.narrate_answer`). Never given raw
  data access. See [docs/ai-architecture.md](docs/ai-architecture.md).
- **Graceful degradation:** A 1.5-second health check
  (`nlg._ollama_available`) detects whether Ollama is reachable; if not, the
  app automatically uses the deterministic template narrator with no error
  and no missing functionality.

## Data processing: pandas + numpy

- **What:** All CSV loading, joining, aggregation, and the z-score anomaly
  detector (`analytics.zscore_outliers`).
- **Why:** Standard, fast enough for this dataset size (30k+ sales rows
  processed in well under a second), and every operation is a plain,
  auditable pandas call rather than a black box.

## UI: Streamlit + Plotly

- **What:** The entire interactive frontend (`app.py`) — KPI cards,
  findings cards, the Q&A box, and charts.
- **Why:** Fastest path from a Python analytics engine to a real interactive
  product, with free deployment on Streamlit Community Cloud if a public
  demo link is needed. Plotly gives interactive charts (hover, zoom) at no
  extra integration cost inside Streamlit.

## Testing: pytest

- **What:** `tests/test_analytics.py`, 22 tests covering analytics
  correctness, ground-truth validation, insight ranking, the numeric
  grounding guarantee, and Q&A coverage of all required business questions.
- **Why:** Standard, fast, and lets the ground-truth validation run as part
  of normal CI rather than a manual spreadsheet comparison.

## Dataset: synthetic NexaSphere retail data (self-generated)

- **What:** 13 relationally-consistent CSVs (`sales`, `products`, `stores`,
  `customers`, `employees`, `returns`, `deliveries`, `delivery_partners`,
  `marketing`, `campaigns`, `inventory_daily`, `targets`, `hubs`) plus a data
  dictionary, built to match the NexaSphere scenario in the case study since
  no dataset was distributed with the brief.
- **Why:** Needed a dataset that actually contains the business signals the
  case study's "Suggested Business Questions" require (margin pressure,
  return outliers, delivery deterioration, inventory imbalance, marketing
  ROI spread) so the assistant has something real to discover, and an
  independently pre-computed ground-truth file so the analytics engine's
  correctness could be verified rather than assumed.

## Explicitly not integrated (and why)

| Considered | Why not used here |
|---|---|
| A paid/hosted LLM API (OpenAI, Anthropic, etc.) | Violates the zero-budget constraint; Ollama achieves the same narration role for free |
| Vector database / RAG (pgvector) | The case study's data is small, structured and tabular — retrieval-augmented generation over documents wasn't the right tool for tabular KPI question-answering |
| n8n / workflow automation | Considered in early strategy discussion for a different case study (autonomous action execution); out of scope once Case Study 4 was locked in, since this system deliberately stops at recommendation, not execution (see [docs/responsible-ai.md](docs/responsible-ai.md)) |
| A general NL2SQL / text-to-pandas model | The case study specifies a closed set of required questions; a tested, deterministic rule-based router covers all of them more reliably (see [docs/ai-architecture.md](docs/ai-architecture.md)) |
