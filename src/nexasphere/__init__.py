"""NexaSphere AI Business Intelligence Assistant -- core package.

Layering (see docs/architecture.md):
    data_loader  -> load & join raw CSVs (source of truth)
    analytics    -> deterministic KPI / trend / anomaly / comparison functions
    insights     -> ranks analytics output into cited business Findings
    nlg          -> LLM (Ollama) narration of Findings/answers, with a
                    grounded, template-based fallback and a numeric guard
    qa           -> natural-language question -> intent -> analytics -> nlg
"""
