"""Natural-language question router.

Rather than sending the raw question to an LLM and hoping it produces the
right SQL/pandas or -- worse -- hoping it invents a plausible-sounding
answer, this module matches the question to one of a fixed set of business
intents via keyword rules, executes the matching deterministic analytics
function, and only then hands the *result* to nlg.narrate_answer for
phrasing. This is the "intent detection -> deterministic calculation ->
verified result -> AI explanation" pipeline described in the architecture
docs.

Because the case study enumerates the exact business questions the system
must answer, a rule-based router covers 100% of the required scope without
depending on a paid/hosted NLU model -- consistent with the zero-budget
constraint -- while remaining fully explainable and testable.

Routing design (post-audit rewrite)
------------------------------------
Intents are checked from MOST specific keyword set to LEAST specific, so a
narrow topic (e.g. "employee") always wins over a broad one (e.g. generic
profitability language) when a question could plausibly mention both. Two
concrete bugs drove this design:

1. "Which marketing campaigns generate the best return on investment?" was
   being caught by the returns-analysis matcher because "return on
   investment" contains the substring "return". Fixed by checking the
   marketing/ROI intent first and by excluding ROI/campaign phrasing from
   the returns matcher.
2. Paraphrases of the hero question ("Are we making more money?", "Is our
   profit keeping pace with revenue?") fell through to the honest fallback
   because the old matcher only recognized the literal suggested-question
   wording. Fixed by matching on business *concepts* (a profit-related
   word, optionally combined with a revenue/comparison word) rather than
   fixed phrases.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from . import analytics as an
from . import insights as ins
from . import nlg


@dataclass
class QAResult:
    intent: str
    question: str
    result: Any
    template_answer: str
    narration: nlg.NarrationResult


def _df_records(df, n=10):
    return df.head(n).to_dict(orient="records")


def _any(q: str, phrases: list[str]) -> bool:
    return any(p in q for p in phrases)


# ---------------------------------------------------------------------------
# Concept word groups used by the profitability matcher (see module docstring)
# ---------------------------------------------------------------------------
_PROFIT_WORDS = ["profit", "profitability", "margin", "bottom line"]
_PROFIT_STRONG_PHRASES = [
    "making more money", "making money", "more money", "actually profitable",
    "profitable now", "keeping pace",
]
_REVENUE_WORDS = ["revenue", "sales", "top line", "turnover"]
_COMPARISON_WORDS = [
    "growth", "growing", "grow", "increasing", "increase", "translat",
    "stronger", "improv", "declin", "pace with", "despite", "keeping up",
]
_RANKING_PHRASES = [
    "most revenue", "most profit", "top revenue", "top profit",
    "highest revenue", "highest profit", "best performing", "which products",
    "which stores", "which regions",
]


def _intent_employee_performance(q: str) -> QAResult | None:
    if not _any(q, ["employee", "staff", "team perform"]):
        return None
    df = an.employee_store_performance()
    top = df.iloc[0]
    result = {"by_store": _df_records(df)}
    template = (
        f"{top['store_name']} has the highest revenue per employee at "
        f"{top['revenue_per_employee']:,.2f} ({top['headcount']} staff, "
        f"{top['margin_pct']:.2f}% margin). Note: sales are recorded per store, not per "
        f"individual employee, so this reflects store-level team performance."
    )
    return QAResult("employee_store_performance", q, result, template, nlg.narrate_answer(q, result, template))


def _intent_customer_segment(q: str) -> QAResult | None:
    if not _any(q, ["customer segment", "valuable customer", "segment"]):
        return None
    df = an.customer_segment_value()
    top = df.iloc[0]
    result = {"segments": _df_records(df)}
    template = (
        f"{top['customer_segment']} is the most valuable segment, generating "
        f"{top['revenue']:,.2f} in revenue ({top['margin_pct']:.2f}% margin) from "
        f"{int(top['customers'])} customers ({top['revenue_per_customer']:,.2f} per customer)."
    )
    return QAResult("customer_segment_value", q, result, template, nlg.narrate_answer(q, result, template))


def _intent_marketing_roi(q: str) -> QAResult | None:
    if not _any(q, ["campaign", "marketing", "roi", "return on investment"]):
        return None
    df = an.campaign_roi()
    top = df.iloc[0]
    result = {"campaigns": _df_records(df, 10)}
    template = (
        f"{top['campaign_name']} generates the best marketing ROI at {top['roi']:.2f}x "
        f"(spend {top['spend']:,.2f}, attributed revenue {top['attributed_revenue']:,.2f})."
    )
    return QAResult("marketing_roi", q, result, template, nlg.narrate_answer(q, result, template))


def _intent_delivery(q: str) -> QAResult | None:
    if not _any(q, ["delivery", "delay", "shipping", "courier", "partner"]):
        return None
    df = an.delivery_partner_performance()
    top = df.iloc[0]
    result = {"by_partner": _df_records(df)}
    template = (
        f"{top['partner_name']} has the highest delayed-delivery rate at "
        f"{top['delayed_rate_pct']:.1f}%, with an average customer rating of "
        f"{top['avg_rating']:.2f}/5."
    )
    return QAResult("delivery_partner_performance", q, result, template, nlg.narrate_answer(q, result, template))


def _intent_inventory(q: str) -> QAResult | None:
    if not _any(q, ["stockout", "excess inventory", "excess stock", "out of stock", "inventory"]):
        return None
    summary = an.inventory_imbalance_summary()
    stockouts = an.stockout_hotspots(top_n=10)
    excess = an.excess_stock_hotspots(top_n=10)
    result = {"summary": summary, "top_stockouts": _df_records(stockouts), "top_excess": _df_records(excess)}
    template = (
        f"{summary['top_stockout_category']} has the most stockout-days "
        f"({summary['top_stockout_category_days']} across "
        f"{summary['affected_store_product_pairs_stockout']} store/product pairs), while "
        f"{summary['top_excess_category']} has the most excess-stock-days "
        f"({summary['top_excess_category_days']} across "
        f"{summary['affected_store_product_pairs_excess']} store/product pairs)."
    )
    return QAResult("inventory_imbalance", q, result, template, nlg.narrate_answer(q, result, template))


def _intent_targets(q: str) -> QAResult | None:
    if not _any(q, ["target", "meet its target", "missing target", "goal"]):
        return None
    df = an.target_vs_actual()
    below = df[df["revenue_attainment_pct"] < 100]
    worst = df.iloc[0]
    result = {"month": df["month"].iloc[0], "stores": _df_records(df, len(df))}
    if len(below) > 0:
        template = (
            f"For {df['month'].iloc[0]}, {len(below)} of {len(df)} stores are below their revenue "
            f"target. {worst['store_name']} has the largest shortfall at "
            f"{worst['revenue_attainment_pct']:.1f}% of target."
        )
    else:
        template = (
            f"For {df['month'].iloc[0]}, all {len(df)} stores met or exceeded their revenue target. "
            f"{worst['store_name']} has the lowest attainment of the group at "
            f"{worst['revenue_attainment_pct']:.1f}% of target, still above 100%."
        )
    return QAResult("target_attainment", q, result, template, nlg.narrate_answer(q, result, template))


def _intent_returns(q: str) -> QAResult | None:
    # "return" alone is too generic (it collides with "return on investment"),
    # so this only fires on genuine return/refund language.
    if _any(q, ["return on investment", "roi", "campaign"]):
        return None
    if not _any(q, ["return rate", "returns", "returned", "refund", "return reason"]) and "return" not in q:
        return None
    df = an.return_analysis()
    top = df.iloc[0]
    result = {"by_category": _df_records(df, 10)}
    template = (
        f"{top['category']} has the highest return rate at {top['return_rate_pct']:.2f}% "
        f"of units sold ({int(top['returned_units'])} units returned, "
        f"{top['refund_value']:,.2f} refunded)."
    )
    return QAResult("returns_by_category", q, result, template, nlg.narrate_answer(q, result, template))


def _intent_revenue_profit_leaders(q: str) -> QAResult | None:
    if not (_any(q, _RANKING_PHRASES) and _any(q, _REVENUE_WORDS + _PROFIT_WORDS)):
        return None
    if "region" in q:
        dim = "region"
    elif "store" in q:
        dim = "store"
    else:
        dim = "category"
    df = an.breakdown_by(dim, top_n=5)
    top = df.iloc[0]
    result = {"dimension": dim, "leaders": _df_records(df)}
    template = (
        f"By {dim}, {top[dim]} generates the most revenue ({top['revenue']:,.2f}) "
        f"and {top['gross_profit']:,.2f} in gross profit ({top['margin_pct']:.2f}% margin)."
    )
    return QAResult("revenue_profit_leaders", q, result, template, nlg.narrate_answer(q, result, template))


def _intent_growth_profitability(q: str) -> QAResult | None:
    """Broadest matcher, checked last among topic intents on purpose: it
    catches any phrasing about profitability trend that a more specific
    intent above didn't already claim.
    """
    # "margin", "profitability" and "bottom line" are unambiguous on their
    # own -- nothing else in this router means those words -- so they don't
    # need a companion revenue/comparison word. Bare "profit" is more
    # generic (e.g. it can appear in ranking phrasing like "most profit",
    # which the revenue_profit_leaders intent -- checked earlier -- already
    # claims), so it still requires a companion signal to avoid over-firing.
    _UNAMBIGUOUS_PROFIT_WORDS = ["margin", "profitability", "bottom line"]
    has_unambiguous = _any(q, _UNAMBIGUOUS_PROFIT_WORDS)
    has_profit_word = _any(q, _PROFIT_WORDS)
    has_strong_phrase = _any(q, _PROFIT_STRONG_PHRASES)
    if not (has_profit_word or has_strong_phrase):
        return None
    if not (has_unambiguous or has_strong_phrase or _any(q, _REVENUE_WORDS) or _any(q, _COMPARISON_WORDS)):
        return None

    data = an.revenue_profit_growth_gap()
    result = data
    if data["margin_pressure"]:
        template = (
            f"No. Revenue grew {data['change']['revenue_pct']:.1f}% over the last "
            f"{data['window_days']} days but gross profit grew only "
            f"{data['change']['gross_profit_pct']:.1f}%, and gross margin moved "
            f"{data['change']['margin_pp']:+.2f} percentage points. Revenue growth is "
            f"currently outpacing profit growth."
        )
    else:
        template = (
            f"Revenue changed {data['change']['revenue_pct']:.1f}% and gross profit changed "
            f"{data['change']['gross_profit_pct']:.1f}% over the last {data['window_days']} days; "
            f"profitability is broadly tracking revenue."
        )
    return QAResult("growth_vs_profitability", q, result, template, nlg.narrate_answer(q, result, template))


# Ordered most-specific to least-specific. See module docstring.
_INTENTS: list[Callable[[str], QAResult | None]] = [
    _intent_employee_performance,
    _intent_customer_segment,
    _intent_marketing_roi,
    _intent_delivery,
    _intent_inventory,
    _intent_targets,
    _intent_returns,
    _intent_revenue_profit_leaders,
    _intent_growth_profitability,
]


def answer_question(question: str) -> QAResult:
    q = question.lower().strip()
    for matcher in _INTENTS:
        result = matcher(q)
        if result is not None:
            return result

    # Fallback: no rule matched -- give an honest, grounded overview instead
    # of guessing at intent.
    kpi = an.kpi_for_window(*an.dataset_date_range())
    result = kpi.as_dict()
    template = (
        "I couldn't map that question to one of the supported business analyses "
        "(profitability, returns, marketing ROI, inventory, delivery, customer segments, "
        "store/employee performance, or targets). Here is the overall business snapshot instead: "
        f"total revenue {result['revenue']:,.2f}, gross profit {result['gross_profit']:,.2f} "
        f"({result['margin_pct']:.2f}% margin) across {result['orders']:,} orders. "
        "Try rephrasing using one of the suggested questions."
    )
    return QAResult("fallback_overview", question, result, template, nlg.narrate_answer(question, result, template))


SUGGESTED_QUESTIONS = [
    "Which products, stores or regions generate the most revenue and profit?",
    "Is revenue growth leading to stronger profitability?",
    "Which products have unusually high return rates?",
    "Which marketing campaigns generate the best return on investment?",
    "Which stores are experiencing stockouts or excess inventory?",
    "Which delivery partners are associated with delays or poor customer ratings?",
    "Which customer segments are the most valuable?",
    "Which employees perform well based on both revenue and profitability?",
    "Where is the business failing to meet its targets?",
]

# Maps each suggested question (and known paraphrases) to the intent it must
# resolve to. Used by tests to assert *correctness*, not just "not fallback".
EXPECTED_INTENTS = {
    "Which products, stores or regions generate the most revenue and profit?": "revenue_profit_leaders",
    "Is revenue growth leading to stronger profitability?": "growth_vs_profitability",
    "Which products have unusually high return rates?": "returns_by_category",
    "Which marketing campaigns generate the best return on investment?": "marketing_roi",
    "Which stores are experiencing stockouts or excess inventory?": "inventory_imbalance",
    "Which delivery partners are associated with delays or poor customer ratings?": "delivery_partner_performance",
    "Which customer segments are the most valuable?": "customer_segment_value",
    "Which employees perform well based on both revenue and profitability?": "employee_store_performance",
    "Where is the business failing to meet its targets?": "target_attainment",
    # paraphrases of the hero question, flagged in the engineering audit
    "Are we making more money?": "growth_vs_profitability",
    "Is our profit keeping pace with revenue?": "growth_vs_profitability",
    "Sales are up. Did profitability improve?": "growth_vs_profitability",
    "Has our margin improved despite sales growth?": "growth_vs_profitability",
}
