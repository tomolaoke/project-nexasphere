"""Deterministic analytics engine.

Every function here returns plain Python / pandas structures computed with
ordinary arithmetic and pandas aggregation. No LLM call happens in this
module. This is deliberate: the AI layer (ordino.nlg) is only ever
allowed to *narrate* the numbers this module produces, never invent them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Optional

import numpy as np
import pandas as pd

from . import data_loader as dl


# ---------------------------------------------------------------------------
# Core KPI calculations
# ---------------------------------------------------------------------------

@dataclass
class KPISnapshot:
    revenue: float
    gross_profit: float
    margin_pct: float
    orders: int
    units: int
    avg_order_value: float
    return_value: float = 0.0
    net_revenue: float = 0.0

    def as_dict(self) -> dict:
        return {
            "revenue": round(self.revenue, 2),
            "gross_profit": round(self.gross_profit, 2),
            "margin_pct": round(self.margin_pct, 2),
            "orders": int(self.orders),
            "units": int(self.units),
            "avg_order_value": round(self.avg_order_value, 2),
            "return_value": round(self.return_value, 2),
            "net_revenue": round(self.net_revenue, 2),
        }


def _date_bounds(df: pd.DataFrame, date_col: str = "order_date"):
    return df[date_col].min(), df[date_col].max()


def dataset_date_range() -> tuple:
    return _date_bounds(dl.load_sales())


def kpi_for_window(start, end, date_col: str = "order_date") -> KPISnapshot:
    """KPIs for sales with start <= order_date <= end (inclusive)."""
    sales = dl.load_sales()
    mask = (sales[date_col] >= pd.Timestamp(start)) & (sales[date_col] <= pd.Timestamp(end))
    window = sales.loc[mask]

    revenue = float(window["revenue"].sum())
    gross_profit = float(window["gross_profit"].sum())
    margin_pct = (gross_profit / revenue * 100) if revenue else 0.0
    orders = window["order_id"].nunique()
    units = int(window["quantity"].sum())
    aov = (revenue / orders) if orders else 0.0

    returns = dl.load_returns()
    rmask = (returns["return_date"] >= pd.Timestamp(start)) & (returns["return_date"] <= pd.Timestamp(end))
    return_value = float(returns.loc[rmask, "refund_amount"].sum())

    return KPISnapshot(
        revenue=revenue,
        gross_profit=gross_profit,
        margin_pct=margin_pct,
        orders=orders,
        units=units,
        avg_order_value=aov,
        return_value=return_value,
        net_revenue=revenue - return_value,
    )


def rolling_period_comparison(window_days: int = 30) -> dict:
    """Compare the most recent `window_days` of data with the preceding
    equal-length window. Mirrors the standard "last 30 vs previous 30" view.
    """
    sales = dl.load_sales()
    max_date = sales["order_date"].max()
    latest_start = max_date - timedelta(days=window_days - 1)
    prev_end = latest_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=window_days - 1)

    latest = kpi_for_window(latest_start, max_date)
    previous = kpi_for_window(prev_start, prev_end)

    def pct_change(new, old):
        if old == 0:
            return None
        return (new - old) / old * 100

    return {
        "window_days": window_days,
        "latest_period": {"start": str(latest_start.date()), "end": str(max_date.date()), **latest.as_dict()},
        "previous_period": {"start": str(prev_start.date()), "end": str(prev_end.date()), **previous.as_dict()},
        "change": {
            "revenue_pct": pct_change(latest.revenue, previous.revenue),
            "gross_profit_pct": pct_change(latest.gross_profit, previous.gross_profit),
            "margin_pp": round(latest.margin_pct - previous.margin_pct, 2),
            "orders_pct": pct_change(latest.orders, previous.orders),
        },
    }


def revenue_profit_growth_gap(window_days: int = 30) -> dict:
    """Flags the signature 'revenue growing faster than profit' condition."""
    comp = rolling_period_comparison(window_days)
    rev_pct = comp["change"]["revenue_pct"] or 0.0
    gp_pct = comp["change"]["gross_profit_pct"] or 0.0
    gap = rev_pct - gp_pct
    return {
        **comp,
        "growth_gap_pp": round(gap, 2),
        "margin_pressure": gap > 2.0 and comp["change"]["margin_pp"] < 0,
    }


# ---------------------------------------------------------------------------
# Dimensional breakdowns / comparisons
# ---------------------------------------------------------------------------

_DIMENSION_COLUMNS = {
    "category": "category",
    "brand": "brand",
    "store": "store_name",
    "region": "region",
    "channel": "channel",
    "customer_segment": "customer_segment",
    "product": "product_name",
}


def breakdown_by(dimension: str, start=None, end=None, top_n: Optional[int] = None) -> pd.DataFrame:
    """Revenue / profit / margin / units grouped by a business dimension.

    dimension must be one of _DIMENSION_COLUMNS keys.
    """
    if dimension not in _DIMENSION_COLUMNS:
        raise ValueError(f"Unknown dimension '{dimension}'. Options: {list(_DIMENSION_COLUMNS)}")
    col = _DIMENSION_COLUMNS[dimension]
    df = dl.sales_enriched()
    if start is not None and end is not None:
        df = df[(df["order_date"] >= pd.Timestamp(start)) & (df["order_date"] <= pd.Timestamp(end))]

    g = df.groupby(col, dropna=False).agg(
        revenue=("revenue", "sum"),
        gross_profit=("gross_profit", "sum"),
        units=("quantity", "sum"),
        orders=("order_id", "nunique"),
    ).reset_index().rename(columns={col: dimension})
    g["margin_pct"] = np.where(g["revenue"] > 0, g["gross_profit"] / g["revenue"] * 100, 0.0)
    g = g.sort_values("revenue", ascending=False).reset_index(drop=True)
    for c in ("revenue", "gross_profit", "margin_pct"):
        g[c] = g[c].round(2)
    if top_n:
        g = g.head(top_n)
    return g


def employee_store_performance() -> pd.DataFrame:
    """Approximate per-store performance (revenue, profit, headcount).

    Sales are recorded per-store, not per-employee, so employee performance
    is reported at the store level the employee belongs to, plus headcount
    and role mix -- this is stated explicitly rather than fabricating an
    individual attribution the source data does not support.
    """
    sales = dl.sales_enriched()
    store_perf = sales.groupby(["store_id", "store_name", "region"], dropna=False).agg(
        revenue=("revenue", "sum"),
        gross_profit=("gross_profit", "sum"),
        orders=("order_id", "nunique"),
    ).reset_index()
    store_perf["margin_pct"] = (store_perf["gross_profit"] / store_perf["revenue"] * 100).round(2)

    employees = dl.load_employees()
    headcount = employees.groupby("store_id").agg(
        headcount=("employee_id", "count"),
        managers=("role", lambda s: (s == "Store Manager").sum()),
    ).reset_index()

    out = store_perf.merge(headcount, on="store_id", how="left")
    out["revenue_per_employee"] = (out["revenue"] / out["headcount"]).round(2)
    out["profit_per_employee"] = (out["gross_profit"] / out["headcount"]).round(2)
    for c in ("revenue", "gross_profit"):
        out[c] = out[c].round(2)
    return out.sort_values("revenue_per_employee", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Returns analysis
# ---------------------------------------------------------------------------

def return_analysis() -> pd.DataFrame:
    returns = dl.load_returns()
    products = dl.load_products()[["product_id", "category"]]
    sales = dl.load_sales().drop(columns=["category"], errors="ignore")

    r = returns.merge(products, on="product_id", how="left")
    by_cat = r.groupby("category", dropna=False).agg(
        returned_units=("quantity", "sum"),
        refund_value=("refund_amount", "sum"),
        return_events=("return_id", "count"),
    ).reset_index()

    sold = sales.merge(products, on="product_id", how="left").groupby("category", dropna=False).agg(
        units_sold=("quantity", "sum")
    ).reset_index()

    out = by_cat.merge(sold, on="category", how="left")
    out["return_rate_pct"] = (out["returned_units"] / out["units_sold"] * 100).round(2)
    out["refund_value"] = out["refund_value"].round(2)
    return out.sort_values("return_rate_pct", ascending=False).reset_index(drop=True)


def return_reasons_for_category(category: str) -> pd.DataFrame:
    returns = dl.load_returns()
    products = dl.load_products()[["product_id", "category"]]
    r = returns.merge(products, on="product_id", how="left")
    r = r[r["category"] == category]
    out = r.groupby("return_reason").agg(
        events=("return_id", "count"),
        units=("quantity", "sum"),
        refund_value=("refund_amount", "sum"),
    ).reset_index().sort_values("events", ascending=False)
    out["refund_value"] = out["refund_value"].round(2)
    return out.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Delivery performance
# ---------------------------------------------------------------------------

def delivery_partner_performance() -> pd.DataFrame:
    deliveries = dl.load_deliveries()
    partners = dl.load_delivery_partners()

    g = deliveries.groupby("delivery_partner_id").agg(
        total_deliveries=("order_id", "count"),
        delayed=("delivery_status", lambda s: (s == "Delayed").sum()),
        avg_rating=("delivery_rating", "mean"),
        avg_promised_days=("promised_days", "mean"),
        avg_actual_days=("actual_days", "mean"),
    ).reset_index()
    g["delayed_rate_pct"] = (g["delayed"] / g["total_deliveries"] * 100).round(2)
    g["avg_rating"] = g["avg_rating"].round(2)
    g["avg_promised_days"] = g["avg_promised_days"].round(2)
    g["avg_actual_days"] = g["avg_actual_days"].round(2)
    g = g.merge(partners, on="delivery_partner_id", how="left")
    return g.sort_values("delayed_rate_pct", ascending=False).reset_index(drop=True)


def delivery_trend(partner_id: str, freq: str = "W") -> pd.DataFrame:
    deliveries = dl.load_deliveries()
    d = deliveries[deliveries["delivery_partner_id"] == partner_id].copy()
    d["period"] = d["order_date"].dt.to_period(freq).dt.start_time
    g = d.groupby("period").agg(
        total=("order_id", "count"),
        delayed=("delivery_status", lambda s: (s == "Delayed").sum()),
        avg_rating=("delivery_rating", "mean"),
    ).reset_index()
    g["delayed_rate_pct"] = (g["delayed"] / g["total"] * 100).round(2)
    g["avg_rating"] = g["avg_rating"].round(2)
    return g


# ---------------------------------------------------------------------------
# Marketing / campaign ROI
# ---------------------------------------------------------------------------

def campaign_roi() -> pd.DataFrame:
    m = dl.load_marketing().copy()
    m = m.sort_values("roi", ascending=False).reset_index(drop=True)
    return m


# ---------------------------------------------------------------------------
# Inventory: stockouts and excess stock
# ---------------------------------------------------------------------------

def stockout_hotspots(top_n: int = 15) -> pd.DataFrame:
    inv = dl.load_inventory()
    products = dl.load_products()[["product_id", "product_name", "category"]]
    stores = dl.load_stores()[["store_id", "store_name", "region"]]

    stockout_days = inv[inv["stockout_flag"].astype(str).str.lower() == "true"].groupby(
        ["store_id", "product_id"]
    ).size().reset_index(name="stockout_days")

    out = stockout_days.merge(products, on="product_id", how="left").merge(stores, on="store_id", how="left")
    return out.sort_values("stockout_days", ascending=False).head(top_n).reset_index(drop=True)


def excess_stock_hotspots(top_n: int = 15) -> pd.DataFrame:
    inv = dl.load_inventory()
    products = dl.load_products()[["product_id", "product_name", "category"]]
    stores = dl.load_stores()[["store_id", "store_name", "region"]]

    excess_days = inv[inv["excess_stock_flag"].astype(str).str.lower() == "true"].groupby(
        ["store_id", "product_id"]
    ).size().reset_index(name="excess_days")

    out = excess_days.merge(products, on="product_id", how="left").merge(stores, on="store_id", how="left")
    return out.sort_values("excess_days", ascending=False).head(top_n).reset_index(drop=True)


def inventory_imbalance_summary() -> dict:
    stockouts = stockout_hotspots(top_n=10_000)
    excess = excess_stock_hotspots(top_n=10_000)
    stockout_categories = stockouts.groupby("category")["stockout_days"].sum().sort_values(ascending=False)
    excess_categories = excess.groupby("category")["excess_days"].sum().sort_values(ascending=False)
    return {
        "top_stockout_category": stockout_categories.index[0] if len(stockout_categories) else None,
        "top_stockout_category_days": int(stockout_categories.iloc[0]) if len(stockout_categories) else 0,
        "top_excess_category": excess_categories.index[0] if len(excess_categories) else None,
        "top_excess_category_days": int(excess_categories.iloc[0]) if len(excess_categories) else 0,
        "affected_store_product_pairs_stockout": len(stockouts),
        "affected_store_product_pairs_excess": len(excess),
    }


# ---------------------------------------------------------------------------
# Targets vs actuals
# ---------------------------------------------------------------------------

def target_vs_actual(month: Optional[str] = None) -> pd.DataFrame:
    """month format 'YYYY-MM'. If None, uses the latest month in targets.csv."""
    targets = dl.load_targets().copy()
    if month is None:
        month = sorted(targets["month"].unique())[-1]
    targets = targets[targets["month"] == month]

    sales = dl.load_sales().copy()
    sales["month"] = sales["order_date"].dt.strftime("%Y-%m")
    actual = sales[sales["month"] == month].groupby("store_id").agg(
        actual_revenue=("revenue", "sum"),
        actual_gross_profit=("gross_profit", "sum"),
    ).reset_index()

    deliveries = dl.load_deliveries().copy()
    deliveries["month"] = deliveries["order_date"].dt.strftime("%Y-%m")
    d = deliveries[deliveries["month"] == month]
    on_time = d.groupby("store_id").agg(
        on_time_pct=("delivery_status", lambda s: (s == "On Time").mean() * 100)
    ).reset_index()

    returns = dl.load_returns().merge(dl.load_sales()[["order_id", "store_id", "revenue"]], on="order_id", how="left")
    returns["month"] = pd.to_datetime(returns["return_date"]).dt.strftime("%Y-%m")
    r = returns[returns["month"] == month]
    store_revenue = sales[sales["month"] == month].groupby("store_id")["revenue"].sum()
    return_value_by_store = r.groupby("store_id")["refund_amount"].sum()
    return_rate = (return_value_by_store / store_revenue * 100).rename("return_rate_pct").reset_index()

    stores = dl.load_stores()[["store_id", "store_name", "region"]]

    out = targets.merge(actual, on="store_id", how="left").merge(on_time, on="store_id", how="left")
    out = out.merge(return_rate, on="store_id", how="left").merge(stores, on="store_id", how="left")

    out["actual_revenue"] = out["actual_revenue"].fillna(0)
    out["actual_gross_profit"] = out["actual_gross_profit"].fillna(0)
    out["revenue_attainment_pct"] = (out["actual_revenue"] / out["revenue_target"] * 100).round(2)
    out["profit_attainment_pct"] = (out["actual_gross_profit"] / out["gross_profit_target"] * 100).round(2)
    out["on_time_gap_pp"] = (out["on_time_pct"].fillna(0) - out["on_time_delivery_target_pct"]).round(2)
    out["return_rate_gap_pp"] = (out["return_rate_pct"].fillna(0) - out["return_rate_target_pct"]).round(2)
    for c in ("actual_revenue", "actual_gross_profit", "on_time_pct", "return_rate_pct"):
        out[c] = out[c].round(2)
    return out.sort_values("revenue_attainment_pct").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Customer segment value
# ---------------------------------------------------------------------------

def customer_segment_value() -> pd.DataFrame:
    df = dl.sales_enriched()
    g = df.groupby("customer_segment", dropna=False).agg(
        revenue=("revenue", "sum"),
        gross_profit=("gross_profit", "sum"),
        orders=("order_id", "nunique"),
        customers=("customer_id", "nunique"),
    ).reset_index()
    g["margin_pct"] = (g["gross_profit"] / g["revenue"] * 100).round(2)
    g["revenue_per_customer"] = (g["revenue"] / g["customers"]).round(2)
    for c in ("revenue", "gross_profit"):
        g[c] = g[c].round(2)
    return g.sort_values("revenue", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Generic anomaly detection (z-score across a dimension)
# ---------------------------------------------------------------------------

def zscore_outliers(df: pd.DataFrame, value_col: str, threshold: float = 1.5) -> pd.DataFrame:
    """Flags rows whose value_col is more than `threshold` std-deviations
    from the mean of that column. Used to surface categories/partners/stores
    that stand out, rather than hard-coding which ones are "the story".
    """
    out = df.copy()
    mean = out[value_col].mean()
    std = out[value_col].std(ddof=0)
    if std == 0 or np.isnan(std):
        out["zscore"] = 0.0
    else:
        out["zscore"] = ((out[value_col] - mean) / std).round(2)
    out["is_outlier"] = out["zscore"].abs() >= threshold
    return out.sort_values("zscore", ascending=False).reset_index(drop=True)


def monthly_revenue_trend() -> pd.DataFrame:
    sales = dl.load_sales()
    s = sales.copy()
    s["month"] = s["order_date"].dt.to_period("M").dt.start_time
    g = s.groupby("month").agg(
        revenue=("revenue", "sum"),
        gross_profit=("gross_profit", "sum"),
        orders=("order_id", "nunique"),
    ).reset_index()
    g["margin_pct"] = (g["gross_profit"] / g["revenue"] * 100).round(2)
    for c in ("revenue", "gross_profit"):
        g[c] = g[c].round(2)
    return g
