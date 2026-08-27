# Responsible AI

## Principles applied

**1. No hallucinated numbers.** Enforced structurally (see
[ai-architecture.md](ai-architecture.md)), not just prompted for. The AI
layer physically has no access to raw data — only to already-computed
evidence dicts — and a post-generation check discards any output that
introduces an unsupported number.

**2. Explanations cite metrics.** Every Finding and every Q&A answer is
displayed with an "Evidence" panel showing the exact computed values the
narration is based on. Nothing is asserted without a visible number behind
it.

**3. Recommendations are traceable and non-autonomous.** Every
recommendation names the metric that triggered it (e.g. "Audio has a return
rate 2.28 standard deviations above the category average → investigate
Audio quality and the 'Not as Expected' return reason"). The system never
executes an action — it surfaces what deserves human investigation, and a
human decides.

**4. Transparency about AI vs. template source.** The UI labels every piece
of narration with its source (`llm` or `template`) and shows a sidebar
status indicating whether a local LLM is even connected. Nothing pretends to
be smarter than it is.

**5. Honesty over confident guessing.** If a question doesn't match a
supported analysis, the system says so explicitly rather than forcing an
answer. If a business signal (e.g. inventory imbalance) isn't actually
present in the data, the corresponding finding says "no material imbalance
detected" instead of manufacturing a story.

**6. No individual-level fabrication.** The dataset records sales at the
store level, not per employee. Rather than infer or estimate an
individual's contribution, `employee_store_performance()` explicitly
reports store-level results and states the limitation in its docstring and
in the UI's answer template.

## What we deliberately excluded from autonomy

The original Buildfest strategy discussion (see project history) considered
an "approve and execute" action loop (e.g. auto-sending customer messages).
We scoped that out of this build entirely for Case Study 4: a Business
Intelligence assistant's job is decision *support*, and letting an
unsupervised model take actions on live business operations (pricing,
inventory transfers, customer communication) introduces exactly the kind of
risk a judge from an insurance/enterprise background (one of our named
judges) would flag. Every recommendation in this system ends at "investigate
X" or "review Y" — never "we already did Z."

## Data privacy

The dataset is entirely synthetic (see [data/DATASET_README.md](../data/DATASET_README.md)).
No real customer, employee or transaction data is used anywhere in this
prototype. The one file marked internal
(`internal_validation/GROUND_TRUTH_INTERNAL.json`) is used only by the
automated test suite and is excluded from the shipped application (`/data`)
and from version control (`.gitignore`).

## Bias considerations

Store, region and employee comparisons are reported as raw computed
performance metrics (revenue, margin, attainment) without an editorializing
layer — the system doesn't rank "best" or "worst" employees by name; it
reports store-level aggregates and lets a manager apply local context before
drawing conclusions about people.
