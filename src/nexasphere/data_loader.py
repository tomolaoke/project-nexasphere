"""Deterministic, cached loading of the NexaSphere retail dataset.

All numbers shown anywhere in the app must trace back to a DataFrame
produced by this module or by nexasphere.analytics. Nothing here calls
an LLM. This is the single source of truth for "what is true" in the system.
"""
from __future__ import annotations

import functools
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

_DATE_COLUMNS = {
    "sales.csv": ["order_date"],
    "returns.csv": ["return_date"],
    "deliveries.csv": ["order_date"],
    "inventory_daily.csv": ["snapshot_date"],
}


def _read_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"Required dataset file missing: {path}. "
            "Place the NexaSphere CSV files in the /data directory."
        )
    parse_dates = _DATE_COLUMNS.get(name)
    df = pd.read_csv(path, parse_dates=parse_dates)
    df.columns = [c.strip() for c in df.columns]
    return df


@functools.lru_cache(maxsize=1)
def load_sales() -> pd.DataFrame:
    return _read_csv("sales.csv")


@functools.lru_cache(maxsize=1)
def load_products() -> pd.DataFrame:
    return _read_csv("products.csv")


@functools.lru_cache(maxsize=1)
def load_stores() -> pd.DataFrame:
    return _read_csv("stores.csv")


@functools.lru_cache(maxsize=1)
def load_customers() -> pd.DataFrame:
    return _read_csv("customers.csv")


@functools.lru_cache(maxsize=1)
def load_employees() -> pd.DataFrame:
    return _read_csv("employees.csv")


@functools.lru_cache(maxsize=1)
def load_returns() -> pd.DataFrame:
    return _read_csv("returns.csv")


@functools.lru_cache(maxsize=1)
def load_deliveries() -> pd.DataFrame:
    return _read_csv("deliveries.csv")


@functools.lru_cache(maxsize=1)
def load_delivery_partners() -> pd.DataFrame:
    return _read_csv("delivery_partners.csv")


@functools.lru_cache(maxsize=1)
def load_marketing() -> pd.DataFrame:
    return _read_csv("marketing.csv")


@functools.lru_cache(maxsize=1)
def load_inventory() -> pd.DataFrame:
    return _read_csv("inventory_daily.csv")


@functools.lru_cache(maxsize=1)
def load_targets() -> pd.DataFrame:
    return _read_csv("targets.csv")


@functools.lru_cache(maxsize=1)
def load_hubs() -> pd.DataFrame:
    return _read_csv("hubs.csv")


def sales_enriched() -> pd.DataFrame:
    """Sales joined with product, store and customer dimensions.

    This is the workhorse table for most analytics functions, so it is
    built once and reused rather than re-joined in every calculation.
    """
    # sales.csv already carries its own `category` column; drop it before
    # merging so products.csv's `category` remains the single, unambiguous
    # source of truth for the product category dimension (avoids pandas
    # emitting category_x/category_y).
    sales = load_sales().drop(columns=["category"], errors="ignore")
    products = load_products()[["product_id", "product_name", "category", "brand"]]
    stores = load_stores()[["store_id", "store_name", "region", "city", "store_type"]]
    customers = load_customers()[["customer_id", "segment", "acquisition_channel"]].rename(
        columns={"segment": "customer_segment"}
    )
    df = sales.merge(products, on="product_id", how="left")
    df = df.merge(stores, on="store_id", how="left", suffixes=("", "_store"))
    df = df.merge(customers, on="customer_id", how="left")
    return df


def clear_cache() -> None:
    """Reset all cached loaders. Used by tests that swap the data directory."""
    for fn in (
        load_sales, load_products, load_stores, load_customers, load_employees,
        load_returns, load_deliveries, load_delivery_partners, load_marketing,
        load_inventory, load_targets, load_hubs,
    ):
        fn.cache_clear()
