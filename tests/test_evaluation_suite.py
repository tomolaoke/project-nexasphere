"""Runs the 40-question AI evaluation suite (tests/eval_cases.py) and
asserts routing correctness per case. See docs/evaluation.md for the
human-readable results summary and docs/testing.md for how this suite
differs from the unit/integration tests in test_analytics.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nexasphere import qa  # noqa: E402
from eval_cases import EVAL_CASES  # noqa: E402


@pytest.mark.parametrize("question,expected_intent,category,note", EVAL_CASES)
def test_eval_case_routes_correctly(question, expected_intent, category, note):
    result = qa.answer_question(question)
    assert result.intent == expected_intent, (
        f"[{category}] '{question}' -> got '{result.intent}', expected '{expected_intent}'"
    )
    assert result.template_answer, f"[{category}] '{question}' produced an empty answer"
    if expected_intent == "fallback_overview":
        assert "couldn't map" in result.template_answer


def test_eval_suite_has_required_category_distribution():
    from collections import Counter

    counts = Counter(c for _, _, c, _ in EVAL_CASES)
    assert counts == {
        "factual": 10,
        "analytical": 10,
        "comparison": 5,
        "anomaly": 5,
        "recommendation": 5,
        "unsupported": 5,
    }
