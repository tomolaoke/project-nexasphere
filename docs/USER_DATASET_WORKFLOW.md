# Analyze My Business — Workflow

How an arbitrary business dataset becomes evidence-backed insight, without the
AI ever calculating a figure.

```
Business details (required)  →  Upload  →  Ingest  →  Profile  →  Map  →  Confirm
       →  Capability matrix  →  Deterministic analytics  →  Evidence
       →  AI explanation  →  Grounding validation  →  Recommendation
```

## 1. Business details (required)

Business name and industry are required before upload, so every page is
labelled with the business's own name. **Display only** — not persisted, not
transmitted, gone when the tab closes. Stated as such in-app.

## 2. Upload — multiple files, multiple formats

Handled by [`ingestion.py`](../src/ordino/ingestion.py), which sorts files
into two buckets:

| Bucket | Formats | Role |
|---|---|---|
| **DATA** | CSV, TSV, XLSX, JSON | Drives KPIs, findings and charts |
| **CONTEXT** | PDF, DOCX, TXT, MD | Business notes and targets — read, but **never counted as measured figures** |

The DATA/CONTEXT split matters: a PDF stating *"our revenue target is ₦10m"*
records a **target**, not revenue. Treating document text as measurement is how
BI tools invent numbers.

**Declined, deliberately:** images and video. Reliable OCR needs a system
Tesseract binary unavailable on free hosting, and there is no dependable free
path from video to trustworthy figures. Ordino explains why rather than
returning a plausible guess.

## 3. Primary table selection

Analytics run on **one** table — files are never auto-merged. Selection is
scored by analytical usefulness: a money column outranks everything (it unlocks
nearly every analysis), then a date column, with row count only breaking ties.

> This replaced "pick the largest file", which selected a 130k-row inventory
> snapshot with no money column over the sales table that answers business
> questions.

Related tables are surfaced as **candidate relationships** where they share an
identifier column, for the user to note — never auto-joined, since a
coincidental shared column name would fabricate combined figures.

## 4. Profiling

Per column: dtype, missing count and %, distinct values, numeric flag,
date-like flag. Per dataset: row/column counts, duplicate rows, and a
**data-quality score** penalising missingness and duplicates, expressed in
plain language.

## 5. Semantic mapping — proposed, never assumed

Column names are matched against synonym sets for thirteen canonical concepts
(`date`, `revenue`, `cost`, `profit`, `quantity`, `product`, `customer`,
`store`, `region`, `category`, `campaign`, `return_flag`, `employee`) —
`total_sales`, `amount`, `turnover` and `invoice_total` all propose `revenue`.

Every proposal is **shown and editable**, and each dropdown offers only
type-appropriate columns: dates for Date, numerics for Revenue/Cost, binary
columns for Return flag. Nothing is analysed until confirmed.

## 6. Capability matrix — honest limits

Ordino reports which of nine analyses the data supports and which it
doesn't, with the missing columns named:

```
✓ Revenue trend over time      ○ Returns analysis — needs return_flag
✓ Profitability                ○ Marketing / campaign ROI — needs campaign
✓ Product performance          ○ Employee performance — needs employee
```

Unsupported analyses are never fabricated. A restaurant's CSV cannot report
delivery-partner performance, and the app says so.

## 7. Analytics → evidence → AI

Identical to the demo pipeline: pandas computes, evidence is assembled, and the
AI receives only that evidence. The same numeric and entity grounding checks
apply — code path shared, not duplicated.

## 8. Isolation

The demo dataset is loaded from `/data` and cached; user data lives in session
state. They cannot overwrite each other, and the workspace switcher makes the
active one explicit.

## Tests

[`test_user_data.py`](../tests/test_user_data.py) and
[`test_ingestion.py`](../tests/test_ingestion.py) cover ingestion of every
supported format, declined formats, malformed and empty files, profiling, type
detection, mapping proposals and filters, capability detection, and honest
refusal — using schemas deliberately unlike the demo dataset's.
