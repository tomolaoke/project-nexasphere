# Solution

## Concept

An AI Business Intelligence copilot that turns NexaSphere's disconnected
retail data into prioritized, evidence-backed findings and plain-language
answers, without ever letting an AI model invent a metric.

## Two modes

**Discover** — the manager opens the app and immediately sees a ranked list
of findings generated fresh from the current data: is revenue growth
outpacing profit growth, which product category has an outlier return
rate, which delivery partner is underperforming, where inventory is
mismatched (stockouts vs. excess), which marketing campaign has the best
ROI, and which stores are missing targets. Each finding states its evidence
and a recommended focus area.

**Ask** — the manager types a business question in plain English. The
question is matched to one of the analyses the case study requires, that
analysis is computed live from the data, and the result is phrased in plain
language. If a question can't be matched to a supported analysis, the system
says so honestly and offers a general snapshot instead of guessing.

## How it satisfies every item in "The Challenge"

| Requirement | How it's met |
|---|---|
| Analyse the dataset and calculate KPIs | `analytics.py` — revenue, gross profit, margin, orders, AOV, all deterministic |
| Answer management questions in plain language | `qa.py` intent router + `nlg.py` narration |
| Identify trends, unusual results, risks, gaps | `analytics.monthly_revenue_trend`, `zscore_outliers`, `insights.py` findings |
| Compare across products/stores/regions/employees/campaigns/segments | `analytics.breakdown_by`, `employee_store_performance`, `customer_segment_value`, `campaign_roi` |
| Present via charts, dashboards, summaries | Streamlit Dashboards tab (Plotly) |
| Explain possible reasons behind changes | Finding summaries trace evidence (e.g. return reasons, discount patterns) |
| Recommend practical actions | Every Finding carries a `recommendation` field |

## What we deliberately did not build

- **Autonomous execution.** The system recommends what to investigate; it
  never sends an email, changes a price, or reallocates stock on its own.
  This is a judgement call, not a limitation we ran out of time to fix — see
  [responsible-ai.md](responsible-ai.md).
- **A generic natural-language-to-SQL engine.** The case study enumerates
  the exact business questions the assistant must answer. A rule-based
  intent router covers all of them precisely and stays fully testable,
  rather than depending on a general-purpose NL2SQL model whose failure
  mode is a wrong query that still returns a confident-looking number.
- **Per-employee sales attribution.** The dataset records sales per store,
  not per employee. Rather than fabricate an individual-level number the
  data doesn't support, `employee_store_performance()` reports store-level
  performance plus headcount, and says so explicitly.

---

## Update — solution workflow (current)

### Demo workspace
```
data/*.csv → data_loader (cached) → analytics (pandas) → insights (Finding + evidence)
          → nlg (AI narration) → grounding validation → UI
```

### Business workspace
```
uploaded files → ingestion (DATA vs CONTEXT) → primary table selection
              → profiling → semantic mapping → user confirmation
              → capability matrix → generic analytics → evidence
              → nlg (same layer) → grounding validation → UI
```

Both paths share the AI narration and grounding layer. The model is a narrator
in both; the analytics engine is authoritative in both.

### Pages
**Overview** — KPIs with change and real sparklines, hero revenue-vs-profit
chart, category breakdown, top three findings.
**Findings** — six ranked findings with severity, confidence, possible drivers,
evidence and recommendation.
**Ask NexaSphere** — streaming chat with persisted history and suggestion chips;
formal English, casual English or Pidgin.
**Dashboards** — nine charts across products, regions, returns, delivery,
employees, segments, campaigns and targets.
**Analyze My Business** — upload, profile, data-quality score, mapping,
capability matrix, then a dashboard generated from the user's own columns.

### Chart selection
Chart type follows the shape of the question: area for trend, line for margin
over time, bars for period change, horizontal bars for ranking, donut for share,
treemap for nested composition, box for spread, histogram for distribution, and
scatter for the revenue-vs-margin trade-off — which no ranked bar chart can
express.
