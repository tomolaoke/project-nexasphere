"""Validates the deterministic analytics engine against sample inputs and
against the internal ground-truth reference computed independently when the
synthetic dataset was generated (internal_validation/GROUND_TRUTH_INTERNAL.json).

Per the dataset README, the ground-truth file is for internal development
validation only and must not be shipped in the public demo/repo -- it is
read here directly from internal_validation/, kept out of /data.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ordino import analytics as an  # noqa: E402
from ordino import insights as ins  # noqa: E402
from ordino import qa  # noqa: E402

GROUND_TRUTH_PATH = ROOT / "internal_validation" / "GROUND_TRUTH_INTERNAL.json"


@pytest.fixture(scope="module")
def ground_truth():
    if not GROUND_TRUTH_PATH.exists():
        pytest.skip("internal ground-truth file not present in this environment")
    return json.loads(GROUND_TRUTH_PATH.read_text())


def test_kpi_for_window_basic_shape():
    start, end = an.dataset_date_range()
    kpi = an.kpi_for_window(start, end)
    d = kpi.as_dict()
    assert d["revenue"] > 0
    assert d["orders"] > 0
    assert 0 <= d["margin_pct"] <= 100


def test_kpi_matches_manual_calculation():
    """Sanity check the calculation logic against a hand-computed subtotal
    for a narrow, easy-to-verify window (first day of data).
    """
    from ordino import data_loader as dl

    sales = dl.load_sales()
    first_day = sales["order_date"].min()
    expected_revenue = sales.loc[sales["order_date"] == first_day, "revenue"].sum()

    kpi = an.kpi_for_window(first_day, first_day)
    assert kpi.revenue == pytest.approx(expected_revenue, rel=1e-6)


def test_rolling_period_comparison_matches_ground_truth(ground_truth):
    comp = an.rolling_period_comparison(30)
    gt = ground_truth["period_comparison"]

    assert comp["latest_period"]["revenue"] == pytest.approx(gt["last_30_days"]["revenue"], rel=1e-3)
    assert comp["latest_period"]["gross_profit"] == pytest.approx(gt["last_30_days"]["gross_profit"], rel=1e-3)
    assert comp["latest_period"]["orders"] == gt["last_30_days"]["orders"]

    assert comp["previous_period"]["revenue"] == pytest.approx(gt["previous_30_days"]["revenue"], rel=1e-3)
    assert comp["previous_period"]["orders"] == gt["previous_30_days"]["orders"]


def test_margin_pressure_flag_detected():
    result = an.revenue_profit_growth_gap(30)
    # The dataset intentionally plants margin pressure in the most recent window.
    assert result["change"]["revenue_pct"] > 0
    assert result["margin_pressure"] is True


def test_return_analysis_flags_audio_category(ground_truth):
    df = an.return_analysis()
    top_category = df.iloc[0]["category"]
    gt_top = ground_truth["highest_return_categories_by_units"][0]["category"]
    assert top_category == gt_top == "Audio"


def test_delivery_partner_performance_flags_urbanmove(ground_truth):
    df = an.delivery_partner_performance()
    worst = df.iloc[0]
    gt_worst = ground_truth["delivery_partner_performance"][0]
    assert worst["delivery_partner_id"] == gt_worst["delivery_partner_id"] == "DP04"
    assert worst["delayed_rate_pct"] == pytest.approx(gt_worst["delayed_rate"], abs=1.0)


def test_campaign_roi_ranks_summer_cooling_first(ground_truth):
    df = an.campaign_roi()
    top = df.iloc[0]
    gt_top = ground_truth["campaign_performance"][0]
    assert top["campaign_name"] == gt_top["campaign_name"] == "Summer Cooling"
    assert top["roi"] == pytest.approx(gt_top["roi"], abs=0.01)


def test_stockout_hotspots_nonempty_and_matches_scale(ground_truth):
    df = an.stockout_hotspots(top_n=10)
    assert len(df) == 10
    assert df.iloc[0]["stockout_days"] >= 30
    gt_top_days = ground_truth["top_stockout_store_product_pairs"][0]["stockout_days"]
    assert df["stockout_days"].max() == pytest.approx(gt_top_days, abs=2)


def test_breakdown_by_rejects_unknown_dimension():
    with pytest.raises(ValueError):
        an.breakdown_by("not_a_real_dimension")


def test_breakdown_by_category_sums_to_total_revenue():
    total = an.kpi_for_window(*an.dataset_date_range()).revenue
    by_cat = an.breakdown_by("category")
    assert by_cat["revenue"].sum() == pytest.approx(total, rel=1e-6)


# ---------------------------------------------------------------------------
# Insight engine
# ---------------------------------------------------------------------------

def test_generate_findings_returns_six_ranked_findings():
    findings = ins.generate_findings()
    assert len(findings) == 6
    severities = [f.severity for f in findings]
    order = {"critical": 0, "warning": 1, "watch": 2, "info": 3}
    ranks = [order[s] for s in severities]
    assert ranks == sorted(ranks)


def test_every_finding_summary_number_is_grounded_in_evidence():
    """Enforces the 'no hallucinated numbers' requirement structurally:
    every numeric value quoted in a Finding's summary must be traceable to
    a value present in its own evidence payload.
    """
    from ordino.nlg import _numbers_are_grounded

    for f in ins.generate_findings():
        assert _numbers_are_grounded(f.summary, f.evidence), f"Ungrounded number in: {f.summary}"


# ---------------------------------------------------------------------------
# QA router
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question,expected_intent", list(qa.EXPECTED_INTENTS.items()))
def test_questions_route_to_the_correct_intent(question, expected_intent):
    """Asserts CORRECTNESS, not just 'something answered'.

    A prior version of this test only checked `intent != "fallback_overview"`,
    which let a real routing bug ship silently: "Which marketing campaigns
    generate the best return on investment?" was being answered with product
    return-rate data because "return on investment" contains the substring
    "return". Checking the exact expected intent catches that class of bug.
    """
    result = qa.answer_question(question)
    assert result.template_answer
    assert result.intent == expected_intent, (
        f"'{question}' routed to '{result.intent}', expected '{expected_intent}'"
    )


def test_unmatched_question_falls_back_honestly():
    result = qa.answer_question("What is the meaning of life?")
    assert result.intent in qa.DECLINED_INTENTS
    assert "couldn't match" in result.template_answer


def test_unmatched_question_does_not_dump_unrelated_kpis():
    """Regression: an unmatched question used to be answered with the total
    revenue/profit snapshot, which reads as if the system misunderstood the
    question and then bluffed. It must decline cleanly instead.
    """
    result = qa.answer_question("What is the meaning of life?")
    assert "revenue" not in result.template_answer.lower() or "48,089" not in result.template_answer
    assert "gross profit" not in result.template_answer.lower()


def test_meta_question_lists_capabilities_instead_of_dumping_numbers():
    """'What questions can I ask?' is a legitimate product question -- it must
    be answered with the capability menu, never with a KPI dump.
    """
    for phrasing in ("What questions can I ask?", "what can you do?",
                      "What can you tell me about this business?"):
        result = qa.answer_question(phrasing)
        assert result.intent == "meta_capabilities", f"{phrasing!r} -> {result.intent}"
        assert "gross profit" not in result.template_answer.lower()
        # must actually surface real, askable questions
        assert "Is revenue growth leading to stronger profitability?" in result.template_answer


def test_out_of_scope_question_is_declined_politely():
    result = qa.answer_question("What is the capital of France?")
    assert result.intent == "out_of_scope"
    assert "business data" in result.template_answer.lower()
    assert "gross profit" not in result.template_answer.lower()


@pytest.mark.parametrize("question", [
    "Sales dey go up, profit dey follow?",
    "Sales don go up, profit follow am?",
    "We dey gain abi we no dey gain?",
])
def test_pidgin_growth_questions_route_to_profitability(question):
    """Nigerian English / Pidgin phrasings of the hero question must resolve to
    the same structured intent as the formal English version.
    """
    result = qa.answer_question(question)
    assert result.intent == "growth_vs_profitability", f"{question!r} -> {result.intent}"


# ---------------------------------------------------------------------------
# Adversarial AI-grounding tests
#
# The positive-case test above (test_every_finding_summary_number_is_grounded_in_evidence)
# only proves that legitimate template text passes the guard. These tests
# prove the guard actually REJECTS the kinds of hallucination it exists to
# catch -- an unsupported number, and a wrong-entity-with-right-numbers swap.
# ---------------------------------------------------------------------------

def test_grounding_rejects_a_fabricated_percentage():
    from ordino.nlg import _numbers_are_grounded

    evidence = {"revenue_pct": 63.2, "gross_profit_pct": 53.8, "margin_pp": -1.45}
    fabricated = "Revenue grew 72% while profit grew 53.8%, a margin move of -1.45pp."
    assert not _numbers_are_grounded(fabricated, evidence)


def test_grounding_rejects_a_fabricated_currency_value():
    from ordino.nlg import _numbers_are_grounded

    evidence = {"spend": 38000, "attributed_revenue": 255000, "roi": 5.71}
    fabricated = "Summer Cooling spent 38,000.00 to generate 400,000.00 in revenue."
    assert not _numbers_are_grounded(fabricated, evidence)


def test_grounding_accepts_correct_restated_numbers():
    from ordino.nlg import _numbers_are_grounded

    evidence = {"revenue_pct": 63.2, "gross_profit_pct": 53.8}
    correct = "Revenue grew 63.2% while gross profit grew 53.8%."
    assert _numbers_are_grounded(correct, evidence)


def test_entity_grounding_rejects_wrong_partner_name():
    """The numeric guard alone cannot catch an entity swap where every
    number is correct but attributed to the wrong named entity (e.g.
    crediting SwiftShip with UrbanMove's delay rate). This is a known,
    documented limitation -- see docs/ai-architecture.md -- exercised here
    so the gap is visible in test output rather than silently assumed away.
    """
    from ordino.nlg import _entities_are_grounded

    evidence = {"by_partner": [
        {"partner_name": "UrbanMove", "delayed_rate_pct": 34.0},
        {"partner_name": "SwiftShip", "delayed_rate_pct": 6.87},
    ]}
    wrong_entity = "SwiftShip has a 34.0% delayed-delivery rate, the worst in the network."
    assert not _entities_are_grounded(wrong_entity, evidence)

    correct_entity = "UrbanMove has a 34.0% delayed-delivery rate, the worst in the network."
    assert _entities_are_grounded(correct_entity, evidence)
