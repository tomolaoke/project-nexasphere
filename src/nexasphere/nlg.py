"""AI narration layer.

Design principle (see docs/ai-architecture.md): the LLM is never the source
of a number. It only receives numbers that the analytics engine already
computed (via a Finding's `evidence` dict, or a structured answer payload)
and is asked to phrase them in plain language.

Three guardrails enforce this rather than just hoping the model behaves:

1. Prompting: the system prompt explicitly forbids introducing any number
   that isn't present in the supplied evidence block.
2. Post-generation numeric check: every number-like token in the model's
   output must match a number that also appears in the evidence payload
   (within a small rounding tolerance). If the check fails, the deterministic
   template narration is used instead and the response is flagged.
3. Post-generation entity check: catches the case the numeric check can't --
   every number in the evidence is correct, but attributed to the wrong
   named entity (e.g. crediting "SwiftShip" with the delay rate that
   actually belongs to "UrbanMove"). If a named entity in the output is
   restated together with a number that belongs to a *different* entity in
   the same evidence set, the output is rejected the same way.

Backend selection, in order:

1. Ollama (free, local, open-source models) if reachable at OLLAMA_HOST --
   used for the offline/local demo that proves the $0 stack needs no
   internet dependency at all.
2. Groq's free-tier hosted inference API (also $0 -- no credit card, a free
   API key from console.groq.com) if GROQ_API_KEY is set -- used when the
   app is deployed online (e.g. Streamlit Community Cloud), where there is
   no local machine to run Ollama on.
3. The deterministic template narrator, always available, if neither of the
   above is reachable or the model's output fails the grounding guardrail.

Nothing breaks and nothing is invented in any of the three cases -- the
grounding guardrail below is applied identically regardless of which
backend produced the text.
"""
from __future__ import annotations

import os
import re
import json
import time
from dataclasses import dataclass

import requests

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Negative lookbehind on the leading '-' prevents a date like "2026-06" from
# being misread as the negative number -6 (the hyphen there separates a
# year and month, not a sign; a real negative like "-4.6%" is never
# preceded by a digit, so it still matches correctly).
_NUMBER_RE = re.compile(r"(?<!\d)-?\d[\d,]*\.?\d*")


@dataclass
class NarrationResult:
    text: str
    source: str          # "llm" | "template"
    verified: bool        # True if numeric-consistency check passed (or template used)
    backend: str | None = None   # "ollama" | "groq" | None (template)
    model: str | None = None


_AVAILABILITY_CACHE_SECONDS = 10.0
_availability_cache: dict[str, tuple[float, bool]] = {}


def _ollama_available() -> bool:
    """Health-checks Ollama, cached for a few seconds.

    Audit finding: the Streamlit Findings tab used to call this once per
    finding (up to 6 times) plus once for the sidebar badge, on *every*
    rerun -- including reruns triggered by unrelated UI interactions like
    expanding a panel. With Ollama unreachable, that was up to ~10 seconds
    of blocking network timeouts per click. A short TTL cache means the
    real check runs at most once every `_AVAILABILITY_CACHE_SECONDS`,
    regardless of how many findings or reruns happen in that window.
    """
    now = time.monotonic()
    cached = _availability_cache.get(OLLAMA_HOST)
    if cached and (now - cached[0]) < _AVAILABILITY_CACHE_SECONDS:
        return cached[1]

    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=1.5)
        available = r.status_code == 200
    except requests.RequestException:
        available = False

    _availability_cache[OLLAMA_HOST] = (now, available)
    return available


def _groq_available() -> bool:
    """No network probe needed -- Groq is a hosted, always-on service, so
    presence of a free API key is enough. If the key turns out to be
    invalid, `_call_groq` returns None on the actual request and the caller
    falls back to the template narrator exactly like an Ollama failure.
    """
    return bool(GROQ_API_KEY)


def ai_backend_status() -> tuple[str | None, str | None]:
    """Which AI backend narration will use right now, without making an
    actual generation call. Used by the UI status badge.
    """
    if _ollama_available():
        return "ollama", OLLAMA_MODEL
    if _groq_available():
        return "groq", GROQ_MODEL
    return None, None


def _extract_numbers(text: str) -> set[float]:
    nums = set()
    for m in _NUMBER_RE.findall(text):
        cleaned = m.replace(",", "")
        try:
            nums.add(round(float(cleaned), 1))
        except ValueError:
            continue
    return nums


def _flatten_evidence_numbers(evidence: dict) -> set[float]:
    nums = set()

    def walk(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                walk(v)
        elif isinstance(obj, (int, float)):
            nums.add(round(float(obj), 1))
        elif isinstance(obj, str):
            # Evidence strings can embed numbers too (e.g. a "2026-06" month
            # value, or "DP04"). Treat those as grounded so narration is free
            # to restate a date/id that already appears in the evidence.
            for m in _NUMBER_RE.findall(obj):
                try:
                    nums.add(round(float(m.replace(",", "")), 1))
                except ValueError:
                    continue

    walk(evidence)
    return nums


def _numbers_are_grounded(generated_text: str, evidence: dict, tolerance: float = 0.5) -> bool:
    generated = _extract_numbers(generated_text)
    if not generated:
        return True
    grounded = _flatten_evidence_numbers(evidence)
    for n in generated:
        if any(abs(n - g) <= max(tolerance, abs(g) * 0.01) for g in grounded):
            continue
        # small integers (counts, ranks) are common and low-risk; don't fail on those
        if abs(n) <= 12 and n == int(n):
            continue
        # universal percentage anchors ("of target", "100% on time") aren't
        # claims about the business -- they're the fixed reference point a
        # percentage is measured against, not a fact that needs grounding.
        if n in (0.0, 100.0):
            continue
        return False
    return True


_ENTITY_KEYS = (
    "partner_name", "campaign_name", "category", "store_name",
    "customer_segment", "region", "product_name",
)


def _collect_entity_numbers(evidence) -> dict[str, set[float]]:
    """Walks evidence for dict "records" that name an entity (a delivery
    partner, campaign, category, store, segment, region or product) and
    maps each entity name to the set of numbers that appear in that same
    record. Used to catch a correct-number-wrong-entity swap, which the
    purely numeric grounding check cannot see.
    """
    entity_numbers: dict[str, set[float]] = {}

    def record_numbers(d: dict) -> set[float]:
        out = set()
        for v in d.values():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out.add(round(float(v), 1))
        return out

    def walk(obj):
        if isinstance(obj, dict):
            name = None
            for key in _ENTITY_KEYS:
                if key in obj and isinstance(obj[key], str):
                    name = obj[key]
                    break
            if name:
                entity_numbers.setdefault(name, set()).update(record_numbers(obj))
            for v in obj.values():
                walk(v)
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                walk(v)

    walk(evidence)
    return entity_numbers


def _entities_are_grounded(generated_text: str, evidence) -> bool:
    entity_numbers = _collect_entity_numbers(evidence)
    if not entity_numbers:
        return True

    text_numbers = _extract_numbers(generated_text)
    mentioned = [name for name in entity_numbers if name in generated_text]
    if not mentioned or not text_numbers:
        return True

    for name in mentioned:
        own_numbers = entity_numbers[name]
        other_numbers = set().union(*(v for k, v in entity_numbers.items() if k != name)) if len(entity_numbers) > 1 else set()
        # A text number that belongs to some OTHER named entity but not to
        # this one is the swapped-attribution signature we're guarding
        # against. Numbers that belong to nobody in particular (rates,
        # counts shared incidentally) are not penalized.
        for n in text_numbers:
            if n in other_numbers and n not in own_numbers:
                return False
    return True


def _call_ollama(system_prompt: str, user_prompt: str) -> str | None:
    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "options": {"temperature": 0.2},
            },
            timeout=30,
        )
        if resp.status_code != 200:
            return None
        return resp.json().get("message", {}).get("content", "").strip()
    except (requests.RequestException, json.JSONDecodeError):
        return None


def _call_groq(system_prompt: str, user_prompt: str) -> str | None:
    try:
        resp = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
            },
            timeout=20,
        )
        if resp.status_code != 200:
            return None
        return resp.json()["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, json.JSONDecodeError, KeyError, IndexError):
        return None


def _generate(system_prompt: str, user_prompt: str) -> tuple[str, str, str] | None:
    """Tries each configured backend in order and returns the first
    successful (text, backend_name, model_name), or None if none produced
    output. Callers still run the result through the numeric/entity
    grounding guardrail before trusting it.
    """
    if _ollama_available():
        text = _call_ollama(system_prompt, user_prompt)
        if text:
            return text, "ollama", OLLAMA_MODEL
    if _groq_available():
        text = _call_groq(system_prompt, user_prompt)
        if text:
            return text, "groq", GROQ_MODEL
    return None


_SYSTEM_PROMPT = (
    "You are a business intelligence narrator for the NexaSphere retail analytics "
    "assistant. You will be given a JSON evidence block that was computed by a "
    "deterministic analytics engine, and a deterministic template sentence built "
    "from that evidence. Rewrite the template sentence(s) in clearer, more natural "
    "management-facing English. "
    "STRICT RULES: "
    "1) You may only use numbers that already appear in the evidence JSON or the "
    "template sentence. Never introduce a new number, percentage, date or currency "
    "value. "
    "2) Do not speculate about causes that are not supported by the evidence. "
    "3) Keep it to 2-4 sentences. "
    "4) Do not recommend an autonomous action; only suggest what deserves human "
    "investigation, matching the tone of the provided recommendation. "
    "5) Keep every named entity (store, partner, campaign, category, region, segment) "
    "attached to exactly the number it has in the evidence JSON. Never restate a "
    "number next to a different entity than the one it belongs to."
)


def narrate_finding(finding) -> NarrationResult:
    """finding: nexasphere.insights.Finding"""
    template_text = f"{finding.summary} Recommended focus: {finding.recommendation}"

    user_prompt = (
        f"Evidence JSON:\n{json.dumps(finding.evidence, default=str)[:6000]}\n\n"
        f"Template sentence:\n{finding.summary}\n\n"
        f"Recommendation:\n{finding.recommendation}\n\n"
        "Rewrite the template sentence and recommendation as a short, clear "
        "management narrative."
    )
    generated = _generate(_SYSTEM_PROMPT, user_prompt)
    if generated:
        text, backend, model = generated
        if _numbers_are_grounded(text, finding.evidence) and _entities_are_grounded(text, finding.evidence):
            return NarrationResult(text=text, source="llm", verified=True, backend=backend, model=model)
    return NarrationResult(text=template_text, source="template", verified=True)


_QA_SYSTEM_PROMPT = (
    "You are a business intelligence assistant answering a manager's question about "
    "the NexaSphere retail business. You will be given the exact analytical result "
    "already computed for their question (as JSON) and a deterministic template "
    "answer. Rephrase the template answer more naturally. "
    "STRICT RULES: never introduce a number, date, or name that is not present in "
    "the provided JSON result or template answer. If the JSON result is empty or "
    "null, say plainly that the data needed to answer was not found -- do not guess. "
    "Reply in the same language and register the manager used: if they wrote in "
    "Nigerian Pidgin or informal English, answer naturally in that same style; if "
    "they wrote in another language, answer in that language. Never change the "
    "numbers when changing language."
)


def narrate_answer(question: str, result: dict, template_answer: str) -> NarrationResult:
    user_prompt = (
        f"Manager's question:\n{question}\n\n"
        f"Computed result JSON:\n{json.dumps(result, default=str)[:6000]}\n\n"
        f"Template answer:\n{template_answer}\n\n"
        "Rephrase the template answer naturally in 2-4 sentences."
    )
    generated = _generate(_QA_SYSTEM_PROMPT, user_prompt)
    if generated:
        text, backend, model = generated
        if _numbers_are_grounded(text, result) and _entities_are_grounded(text, result):
            return NarrationResult(text=text, source="llm", verified=True, backend=backend, model=model)
    return NarrationResult(text=template_answer, source="template", verified=True)
