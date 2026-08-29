"""Insight engine: turns deterministic analytics output into a ranked list
of business findings with an explicit evidence citation on every finding.

A Finding is the unit of trust in this system. Nothing downstream (the LLM
narration layer, the UI) is allowed to state a number that isn't present in
a Finding's `evidence` dict. This is what makes "no hallucinated numbers"
enforceable rather than aspirational.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import analytics as an


@dataclass
class Finding:
    id: str
    title: str
    category: str          # profitability | returns | delivery | inventory | marketing | targets
    severity: str           # info | watch | warning | critical
    summary: str             # plain sentence, built only from `evidence`
    evidence: dict[str, Any] = field(default_factory=dict)
    recommendation: str = ""
    possible_drivers: list[str] = field(default_factory=list)
    confidence: str = "medium"   # high | medium | low -- see docstring on `_CONFIDENCE_NOTES`

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "severity": self.severity,
            "summary": self.summary,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "possible_drivers": self.possible_drivers,
            "confidence": self.confidence,
        }


# Confidence is a transparent, documented judgment call, not a model output:
# - "high"   -- computed directly from the full dataset (a sum, ratio or exact
#               attainment figure), no statistical inference involved.
# - "medium" -- involves a z-score/outlier judgment over a small number of
#               categories or partners (n < 10), where a single data point can
#               swing the mean/std noticeably. The finding is still computed
#               from real data; the *statistical confidence in "outlier"
#               status specifically* is what's capped at medium.
_CONFIDENCE_NOTES = {
    "profitability": "high",  # direct aggregate comparison, no sampling
    "returns": "medium",       # z-score over ~8 categories
    "delivery": "medium",      # z-score over 5 partners
    "inventory": "high",       # direct flag counts across thousands of store/product/day rows
    "marketing": "high",       # ROI is an exact computed ratio, not a statistical estimate
    "targets": "high",         # direct attainment ratio
}


_SEVERITY_ORDER = {"critical": 0, "warning": 1, "watch": 2, "info": 3}


def _fmt_money(x: float) -> str:
    return f"{x:,.2f}"


def finding_profitability(window_days: int = 30) -> Finding:
    data = an.revenue_profit_growth_gap(window_days)
    rev_pct = data["change"]["revenue_pct"]
    gp_pct = data["change"]["gross_profit_pct"]
    margin_pp = data["change"]["margin_pp"]
    severity = "warning" if data["margin_pressure"] else "info"

    if data["margin_pressure"]:
        summary = (
            f"Revenue grew {rev_pct:.1f}% over the last {window_days} days versus the prior "
            f"{window_days}-day period, but gross profit grew only {gp_pct:.1f}%. Gross margin "
            f"moved from {data['previous_period']['margin_pct']:.2f}% to "
            f"{data['latest_period']['margin_pct']:.2f}% ({margin_pp:+.2f} pp). "
            f"Revenue growth is currently outpacing profit growth."
        )
        rec = (
            "Review margin performance by product category and store before increasing sales "
            "targets, and investigate the pricing and discounting practices behind the recent "
            "revenue growth."
        )
        drivers = [
            "Pattern is consistent with possible pricing or discounting pressure -- not confirmed.",
            "Pattern is consistent with a shift toward lower-margin products in the sales mix -- not confirmed.",
            "Pattern is consistent with rising unit costs -- not confirmed.",
        ]
    else:
        summary = (
            f"Revenue changed {rev_pct:.1f}% and gross profit changed {gp_pct:.1f}% over the last "
            f"{window_days} days versus the prior {window_days}-day period "
            f"({margin_pp:+.2f} pp margin movement). Profitability is broadly tracking revenue."
        )
        rec = "No immediate action required; continue routine margin monitoring."
        drivers = []

    return Finding(
        id="profitability_growth_gap",
        title="Revenue vs. Profit Growth",
        category="profitability",
        severity=severity,
        summary=summary,
        evidence=data,
        recommendation=rec,
        possible_drivers=drivers,
        confidence=_CONFIDENCE_NOTES["profitability"],
    )


def finding_returns(threshold_zscore: float = 1.2) -> Finding:
    df = an.return_analysis()
    n_categories = len(df)
    scored = an.zscore_outliers(df, "return_rate_pct", threshold=threshold_zscore)
    top = scored.iloc[0]
    severity = "warning" if top["is_outlier"] else "info"
    reasons = an.return_reasons_for_category(top["category"])
    top_reason = reasons.iloc[0]["return_reason"] if len(reasons) else None

    summary = (
        f"{top['category']} has the highest return rate in the catalogue at "
        f"{top['return_rate_pct']:.2f}% of units sold ({int(top['returned_units'])} units, "
        f"{_fmt_money(top['refund_value'])} refunded), "
        f"{top['zscore']:.2f} standard deviations above the average of {n_categories} categories."
    )
    if top_reason:
        summary += f" The most common return reason in this category is '{top_reason}'."

    rec = (
        f"Investigate {top['category']} quality and listing accuracy, focusing on the "
        f"'{top_reason}' return reason, before this pattern continues to erode margin."
        if severity == "warning"
        else "Return rates are within normal range across categories."
    )
    drivers = []
    if severity == "warning":
        reason_note = f", most common reason is '{top_reason}'" if top_reason else ""
        drivers = [
            f"Pattern is consistent with a product-quality or supplier issue concentrated in "
            f"{top['category']} -- not confirmed{reason_note}.",
            "Pattern is consistent with a listing/description mismatch driving 'not as expected' "
            "returns -- not confirmed.",
        ]

    return Finding(
        id="returns_outlier_category",
        title="Elevated Category Returns",
        category="returns",
        severity=severity,
        summary=summary,
        evidence={
            "by_category": scored.to_dict(orient="records"),
            "top_category_reasons": reasons.to_dict(orient="records"),
            "sample_size_categories": n_categories,
        },
        recommendation=rec,
        possible_drivers=drivers,
        confidence=_CONFIDENCE_NOTES["returns"],
    )


def finding_delivery(threshold_zscore: float = 1.2) -> Finding:
    df = an.delivery_partner_performance()
    n_partners = len(df)
    scored = an.zscore_outliers(df, "delayed_rate_pct", threshold=threshold_zscore)
    top = scored.iloc[0]
    # 20pp is a documented, fixed policy threshold (roughly double a typical
    # 8-12% delay rate seen across the other partners), not tuned to this
    # dataset -- it separates "notably worse" from "operationally broken".
    severity = "critical" if top["is_outlier"] and top["delayed_rate_pct"] > 20 else (
        "warning" if top["is_outlier"] else "info"
    )
    others_avg = df.loc[df["delivery_partner_id"] != top["delivery_partner_id"], "delayed_rate_pct"].mean()

    summary = (
        f"{top['partner_name']} ({top['delivery_partner_id']}) has a {top['delayed_rate_pct']:.1f}% "
        f"delayed-delivery rate and an average customer rating of {top['avg_rating']:.2f}/5, "
        f"compared with an average of {others_avg:.1f}% delayed across the other "
        f"{n_partners - 1} delivery partners."
    )
    rec = (
        f"Review {top['partner_name']}'s service levels and consider reallocating volume to "
        f"better-performing partners until delay rates normalise."
        if severity != "info"
        else "Delivery partner performance is within normal range."
    )
    drivers = [
        f"Pattern is consistent with an operational or capacity issue specific to "
        f"{top['partner_name']} -- not confirmed.",
    ] if severity != "info" else []

    return Finding(
        id="delivery_partner_outlier",
        title="Delivery Partner Performance Gap",
        category="delivery",
        severity=severity,
        summary=summary,
        evidence={"by_partner": scored.to_dict(orient="records"), "sample_size_partners": n_partners},
        recommendation=rec,
        possible_drivers=drivers,
        confidence=_CONFIDENCE_NOTES["delivery"],
    )


def finding_inventory() -> Finding:
    summary_data = an.inventory_imbalance_summary()
    stockouts = an.stockout_hotspots(top_n=10)
    excess = an.excess_stock_hotspots(top_n=10)

    has_signal = summary_data["top_stockout_category"] is not None and summary_data["top_excess_category"] is not None
    severity = "warning" if has_signal else "info"

    if has_signal:
        summary = (
            f"{summary_data['top_stockout_category']} products account for the most stockout-days "
            f"({summary_data['top_stockout_category_days']} store-days across "
            f"{summary_data['affected_store_product_pairs_stockout']} store/product combinations), "
            f"while {summary_data['top_excess_category']} carries the most excess-stock-days "
            f"({summary_data['top_excess_category_days']} store-days across "
            f"{summary_data['affected_store_product_pairs_excess']} store/product combinations). "
            f"Demand and inventory allocation appear misaligned across categories."
        )
        rec = (
            f"Review replenishment priorities for {summary_data['top_stockout_category']} in the "
            f"affected stores, and evaluate whether excess {summary_data['top_excess_category']} stock "
            f"can be transferred or promoted rather than left idle."
        )
    else:
        summary = "No material stockout or excess-inventory imbalance detected."
        rec = "Continue routine inventory monitoring."

    drivers = [
        "Pattern is consistent with a replenishment/allocation mismatch between "
        "high-demand and slow-moving categories -- not confirmed.",
    ] if has_signal else []

    return Finding(
        id="inventory_imbalance",
        title="Inventory Imbalance: Stockouts vs. Excess Stock",
        category="inventory",
        severity=severity,
        summary=summary,
        evidence={
            "summary": summary_data,
            "top_stockouts": stockouts.to_dict(orient="records"),
            "top_excess": excess.to_dict(orient="records"),
        },
        recommendation=rec,
        possible_drivers=drivers,
        confidence=_CONFIDENCE_NOTES["inventory"],
    )


def finding_marketing() -> Finding:
    df = an.campaign_roi()
    best = df.iloc[0]
    worst = df.iloc[-1]
    summary = (
        f"{best['campaign_name']} has the strongest marketing ROI at {best['roi']:.2f}x "
        f"(spend {_fmt_money(best['spend'])}, attributed revenue {_fmt_money(best['attributed_revenue'])}), "
        f"while {worst['campaign_name']} has the weakest ROI at {worst['roi']:.2f}x."
    )
    rec = (
        f"{best['campaign_name']}'s ROI supports increased investment, subject to validating "
        f"attribution quality, fulfilment capacity and diminishing returns at higher spend. "
        f"Review {worst['campaign_name']}'s targeting and channel mix before further spend."
    )
    return Finding(
        id="marketing_roi_spread",
        title="Marketing Campaign ROI",
        category="marketing",
        severity="info",
        summary=summary,
        evidence={"campaigns": df.to_dict(orient="records")},
        recommendation=rec,
        possible_drivers=[],
        confidence=_CONFIDENCE_NOTES["marketing"],
    )


def finding_targets(month: str | None = None) -> Finding:
    df = an.target_vs_actual(month)
    below = df[df["revenue_attainment_pct"] < 100]
    worst = df.iloc[0]  # target_vs_actual is sorted by attainment ascending
    severity = "warning" if len(below) > 0 else "info"

    if severity == "warning":
        summary = (
            f"For {df['month'].iloc[0]}, {len(below)} of {len(df)} stores are below their revenue target. "
            f"{worst['store_name']} has the largest shortfall at {worst['revenue_attainment_pct']:.1f}% "
            f"of its {_fmt_money(worst['revenue_target'])} revenue target."
        )
        rec = (
            f"Review {worst['store_name']}'s local demand drivers, staffing and inventory availability "
            "to close the revenue gap."
        )
    else:
        summary = (
            f"For {df['month'].iloc[0]}, all {len(df)} stores met or exceeded their revenue target. "
            f"{worst['store_name']} has the lowest attainment of the group at "
            f"{worst['revenue_attainment_pct']:.1f}% of its {_fmt_money(worst['revenue_target'])} target, "
            "still above 100%."
        )
        rec = (
            "All stores are meeting revenue targets; consider reviewing whether current targets are "
            "calibrated to actual demand for the next planning cycle."
        )

    return Finding(
        id="target_shortfall",
        title="Target vs. Actual Performance",
        category="targets",
        severity=severity,
        summary=summary,
        evidence={"stores": df.to_dict(orient="records")},
        recommendation=rec,
        possible_drivers=[
            f"Pattern is consistent with local demand, staffing or inventory availability "
            f"issues at {worst['store_name']} -- not confirmed.",
        ] if severity == "warning" else [],
        confidence=_CONFIDENCE_NOTES["targets"],
    )


def generate_findings(window_days: int = 30) -> list[Finding]:
    """The 'Discover' mode: everything management should know right now,
    ranked by severity.
    """
    findings = [
        finding_profitability(window_days),
        finding_returns(),
        finding_delivery(),
        finding_inventory(),
        finding_marketing(),
        finding_targets(),
    ]
    findings.sort(key=lambda f: _SEVERITY_ORDER.get(f.severity, 9))
    return findings
