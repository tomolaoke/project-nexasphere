# Anticipated Judge Questions

**Why does this need AI at all? Pandas already computes the numbers.**
It doesn't need AI to *calculate* — that's the point. A manager looking at a
23.84% margin still has to work out that it matters because revenue grew 63.2%
while profit grew 53.8%. The AI turns verified evidence into an explanation a
non-technical decision-maker can act on. Analytics answers *what*; the AI
answers *why it matters and what to check next*.

**Why not just use Power BI or Tableau?**
Those tell you *what happened* — you still interpret it. NexaSphere ranks what
deserves attention, explains it in plain language, cites the evidence, and
recommends what to investigate. It also answers questions typed in your own
words, including Pidgin.

**How do you prevent hallucination?**
Three layers. (1) The model never sees raw data — only computed evidence.
(2) Every number in its output is checked against that evidence within
tolerance; unmatched numbers reject the whole response. (3) An entity check
catches correct-number-wrong-entity attribution — crediting SwiftShip with
UrbanMove's 34% delay rate is rejected even though 34% is a real figure. On
rejection the deterministic template is shown and labelled. Adversarial tests
cover all three.

**What if the AI is unavailable?**
The app works. Template narration is used and labelled; the numbers are
identical. Local Ollama is preferred, hosted Groq is the fallback, templates are
the final fallback. The active backend is always visible in the sidebar.

**Can I upload my own data?**
Yes — multiple files at once. CSV, TSV, XLSX and JSON are analysed; PDF, DOCX,
TXT and MD are read as business context but never counted as measurements.

**What if my data doesn't have a required field?**
NexaSphere tells you. The capability matrix reports which of nine analyses your
data supports and names the missing columns for the rest. Ask an unsupported
question and it declines and explains what would be needed — it does not
approximate.

**Does the AI see my raw dataset?**
No. It receives an aggregated evidence dict. Raw rows are never placed in a
prompt. With Ollama the data never leaves the machine at all.

**How accurate are the calculations?**
Validated against a ground truth computed independently when the dataset was
generated, plus a 40-question evaluation suite and data-integrity tests. 140
tests currently pass.

**How was the dataset created?**
Synthetically, with documented business logic and deliberately planted signals
(margin compression, one underperforming delivery partner, one high-return
category). See DATASET_METHODOLOGY.md. No real people or businesses.

**Why a rule-based question router rather than an LLM one?**
The case study enumerates the questions the system must answer, so rules cover
100% of required scope while remaining explainable, instant, testable and free.
An LLM router adds a failure mode — misrouting into a *plausible but wrong*
analysis — without adding coverage. The trade-off is documented, not hidden.

**How much does it cost?**
$0. Streamlit, pandas, Plotly, pypdf, openpyxl, python-docx are open-source;
Ollama is free and local; Groq's free tier needs no card. No paid API, database
or hosting.

**Can this scale?**
The analytics engine is pandas and single-process — appropriate for a prototype
and for typical SME exports. Scaling means swapping the compute layer for a
warehouse; the evidence contract and grounding guardrail are unchanged, which is
precisely why they're a separate layer.

**What are its limits?**
It won't do OCR or video. It won't auto-join related tables. It analyses one
table at a time. It won't claim causation — findings say "consistent with" and
"worth investigating". Every one of these is a deliberate choice to avoid
fabricating confidence.

**What would you build next?**
Confirmed multi-table joins, scheduled monitoring with alerting, and
warehouse-backed compute for larger datasets.
