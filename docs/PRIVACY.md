# Privacy and Data Handling

## What happens to an uploaded file

1. It is read **in memory** by `nexasphere.ingestion` (pandas / openpyxl / pypdf / python-docx).
2. It is held in **Streamlit session state** — scoped to one browser session.
3. Deterministic analytics compute aggregates from it.
4. **Only those aggregates** are passed to the AI narration layer.
5. When the session ends, it is gone.

## What we never do

- **Never write uploads to disk.** No file is saved to the server filesystem.
- **Never persist to a database.** There is no database.
- **Never send raw files to a model.** The AI receives a small evidence dict of already-computed values — never rows, never the file.
- **Never share across sessions.** Session state is per-browser-session; one user's upload is unreachable from another's.
- **Never train on your data.**

## What the AI layer actually receives

For a finding, the prompt contains only a truncated evidence JSON of computed
values plus the deterministic sentence built from them. For example:

```json
{"by_partner": [{"partner_name": "UrbanMove", "delayed_rate_pct": 34.0, "avg_rating": 4.38}]}
```

Aggregates, not records. Where a dimension is a customer identifier, only the
identifier as it appears in the grouped result is included.

## Third-party processing

If `GROQ_API_KEY` is set, evidence dicts are sent to Groq's API for rephrasing.
This is the only outbound call the app makes. To avoid third-party processing
entirely, either run Ollama locally (fully offline) or set no key at all, in
which case narration is generated locally from templates and every number is
still computed.

The active backend is always shown in the sidebar.

## Guidance to users

> Only upload business data you are authorised to analyse. Avoid uploading
> unnecessary personal or confidential information — NexaSphere does not need
> names, contact details or payment data to analyse business performance.

This notice is shown in-app on the upload screen.

## Demo dataset

The BuildFest dataset is entirely synthetic. It contains no real people or
businesses. See [DATASET_METHODOLOGY.md](DATASET_METHODOLOGY.md).
