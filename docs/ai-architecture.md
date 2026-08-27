# AI Architecture

## The one rule everything else follows

**The AI never calculates. It only narrates numbers that were already
computed deterministically, and a guardrail verifies it didn't add any.**

This decision was made specifically because the dataset judges include a
data-analytics team (10Alytics) who will notice immediately if "AI
analytics" is actually just an LLM making plausible-sounding numbers up. We
chose to make that structurally impossible rather than promise to be careful.

## Where AI is used

| Use | Model / method | Grounded? |
|---|---|---|
| Rephrasing a Finding's evidence into natural language | Ollama (local LLM, e.g. Llama 3.2) | Yes — numeric-grounding check, falls back to template |
| Rephrasing a Q&A answer into natural language | Ollama (local LLM) | Yes — same guard |
| Intent detection ("which analysis does this question need?") | Rule-based keyword matcher | N/A — deterministic by design |
| KPI calculation, trend detection, anomaly (z-score) detection | pandas / numpy | N/A — no AI involved at all |

## Why intent detection is rule-based, not model-based

It would be easy to route "understand the question" through an LLM too. We
chose not to, for two reasons specific to this case study:

1. The case study lists the exact business questions the assistant must
   answer. A closed set of nine required questions is a better fit for a
   fast, deterministic, 100%-testable router than for a general-purpose
   classifier that needs training data and can silently misroute.
2. If intent detection is wrong, the *worst case* with our design is an
   honest "I couldn't map that question" — never a wrong analysis presented
   as if it were correct.

## The numeric-grounding guardrail, in detail

`nlg._numbers_are_grounded(text, evidence)`:

1. Extracts every number-like token from the generated text.
2. Recursively walks the evidence payload (which can be nested
   dicts/lists/dataframically-derived records) and collects every number it
   contains — including numbers embedded in strings like `"2026-06"` or
   `"DP04"`, so the model is free to restate a date or ID that's genuinely
   present in the evidence.
3. For each generated number, checks it's within a small tolerance
   (`max(0.5, 1% of the evidence value)`) of some grounded number. Small
   integers (≤ 12, e.g. counts/ranks) and the universal percentage anchors
   0 and 100 are exempt, since they aren't factual claims about the
   business.
4. If any generated number fails this check, the LLM output is discarded
   entirely and the deterministic template sentence — which by construction
   only contains evidence numbers — is shown instead.

This is enforced by a unit test
(`test_every_finding_summary_number_is_grounded_in_evidence`) that runs the
check against every Finding's own template summary, proving the templates
themselves are grounded, not just the check's exemptions.

## Model choice and cost

Ollama running Llama 3.2 (3B) locally: $0, no API key, no rate limit tied to
money, works offline. If Ollama isn't installed or running (e.g. a judge's
machine), the app detects this via a lightweight `GET /api/tags` health
check and transparently falls back to the template narrator — the UI shows
which source produced each piece of text ("Narration source: template" or
"llm") so this is never hidden.

## Failure modes and what happens

| Failure | Behaviour |
|---|---|
| Ollama not running | Falls back to template narration automatically |
| Ollama returns malformed JSON / times out | Falls back to template narration |
| Model output contains an ungrounded number | Discarded; template narration shown instead |
| Question doesn't match any known intent | Honest "I couldn't map that question" + overall KPI snapshot, never a guess |
| Missing/malformed dataset file | `FileNotFoundError` raised at load time with the expected path, not a silent empty result |
