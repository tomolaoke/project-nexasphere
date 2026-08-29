# What Ordino Deliberately Won't Do

Each limit below is a choice. The alternative in every case is producing a
plausible-looking number that isn't backed by evidence, which is the exact
failure this project is built to avoid.

## Won't analyse images or video
Reliable OCR needs a system Tesseract binary that free hosting doesn't provide,
and there is no dependable free path from video to trustworthy business
figures. Ordino declines and explains, rather than guessing at numbers in a
picture.

## Won't auto-join related tables
Shared identifier columns are surfaced as *candidates* for the user to note. A
coincidental shared column name (`id`, `name`) would silently produce combined
figures the business never had.

## Won't analyse multiple tables at once
One table at a time, chosen by analytical usefulness and shown explicitly.
Merging files on assumptions fabricates data.

## Won't treat document text as measurement
PDF/DOCX/TXT content is CONTEXT, never DATA. A document stating *"our revenue
target is ₦10m"* records a target, not revenue.

## Won't claim causation
Findings use "consistent with", "may indicate", "worth investigating".
Correlation in a business dataset rarely establishes cause, and asserting it
would send managers after the wrong problem.

## Won't fabricate unsupported analyses
The capability matrix reports what your data supports and names what's missing
for the rest. No delivery columns means no delivery analysis — not an estimate.

## Won't answer non-business questions
Out-of-scope questions are declined without numbers. Answering "what's the
weather?" with a revenue total is a bug, not a graceful fallback.

## Won't let the model calculate
The LLM never sees raw data and never produces an authoritative figure. Any
number in its output not present in the evidence rejects the response.

## Won't persist your data
Session-scoped only. No disk writes, no database. Closing the tab ends it.

## Scale limits
pandas, single process, 500,000-row upload ceiling — appropriate for a
prototype and typical SME exports, not a warehouse replacement. Scaling means
swapping the compute layer; the evidence contract and guardrails are unchanged,
which is why they are a separate layer.
