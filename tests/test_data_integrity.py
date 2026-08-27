"""Dataset integrity checks.

These codify the manual checks run during the post-audit engineering review
(see EngineerDiary.md) so a future change to the dataset can't silently
reintroduce a broken relationship, an impossible value, or a duplicate key
without a test failing. This suite validates the DATA, not the analytics
code -- it would fail even if analytics.py were deleted entirely.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def sales():
    return pd.read_csv(DATA / "sales.csv", parse_dates=["order_date"])


@pytest.fixture(scope="module")
def products():
    return pd.read_csv(DATA / "products.csv")


@pytest.fixture(scope="module")
def stores():
    return pd.read_csv(DATA / "stores.csv")


@pytest.fixture(scope="module")
def customers():
    return pd.read_csv(DATA / "customers.csv")


@pytest.fixture(scope="module")
def returns():
    return pd.read_csv(DATA / "returns.csv", parse_dates=["return_date"])


@pytest.fixture(scope="module")
def deliveries():
    return pd.read_csv(DATA / "deliveries.csv", parse_dates=["order_date"])


@pytest.fixture(scope="module")
def inventory():
    return pd.read_csv(DATA / "inventory_daily.csv", parse_dates=["snapshot_date"])


# ---------------------------------------------------------------------------
# Primary keys / duplicates
# ---------------------------------------------------------------------------

def test_sales_order_id_is_unique(sales):
    assert sales["order_id"].duplicated().sum() == 0


def test_returns_return_id_is_unique(returns):
    assert returns["return_id"].duplicated().sum() == 0


def test_deliveries_order_id_is_unique(deliveries):
    assert deliveries["order_id"].duplicated().sum() == 0


# ---------------------------------------------------------------------------
# Referential integrity (no orphans)
# ---------------------------------------------------------------------------

def test_sales_product_references_are_valid(sales, products):
    assert (~sales["product_id"].isin(products["product_id"])).sum() == 0


def test_sales_store_references_are_valid(sales, stores):
    assert (~sales["store_id"].isin(stores["store_id"])).sum() == 0


def test_sales_customer_references_are_valid(sales, customers):
    assert (~sales["customer_id"].isin(customers["customer_id"])).sum() == 0


def test_returns_order_references_are_valid(returns, sales):
    assert (~returns["order_id"].isin(sales["order_id"])).sum() == 0


def test_deliveries_order_references_are_valid(deliveries, sales):
    assert (~deliveries["order_id"].isin(sales["order_id"])).sum() == 0


def test_every_sale_has_exactly_one_delivery_row(sales, deliveries):
    assert (~sales["order_id"].isin(deliveries["order_id"])).sum() == 0
    assert deliveries["order_id"].duplicated().sum() == 0


# ---------------------------------------------------------------------------
# Value-range sanity
# ---------------------------------------------------------------------------

def test_sales_quantities_are_positive(sales):
    assert (sales["quantity"] <= 0).sum() == 0


def test_sales_revenue_and_cost_are_non_negative(sales):
    assert (sales["revenue"] < 0).sum() == 0
    assert (sales["cost"] < 0).sum() == 0


def test_sales_discount_pct_is_a_valid_fraction(sales):
    assert ((sales["discount_pct"] < 0) | (sales["discount_pct"] > 1)).sum() == 0


def test_sales_unit_price_never_exceeds_list_price(sales):
    assert (sales["unit_price"] > sales["list_price"]).sum() == 0


def test_returns_quantities_are_positive(returns):
    assert (returns["quantity"] <= 0).sum() == 0


def test_inventory_closing_stock_is_never_negative(inventory):
    assert (inventory["closing_stock"] < 0).sum() == 0


# ---------------------------------------------------------------------------
# Flag consistency (derived columns must agree with the raw values they
# describe -- this is what actually matters for the app's correctness,
# since the app reads the flags directly rather than recomputing them)
# ---------------------------------------------------------------------------

def test_stockout_flag_matches_zero_closing_stock(inventory):
    flagged = inventory["stockout_flag"].astype(str).str.lower() == "true"
    is_zero = inventory["closing_stock"] == 0
    assert (flagged & ~is_zero).sum() == 0, "stockout_flag=True but closing_stock != 0"
    assert (~flagged & is_zero).sum() == 0, "closing_stock == 0 but stockout_flag != True"


def test_excess_stock_flag_rows_are_exactly_the_replenishment_days(inventory):
    """Documents and locks in the intentional arithmetic behavior described
    in docs/DATASET_METHODOLOGY.md: every row where closing_stock exceeds
    opening_stock - units_sold is a same-day-replenishment row, and every
    such row is flagged excess_stock_flag=True (verified 1:1, not just
    'most of them').
    """
    expected_closing = inventory["opening_stock"] - inventory["units_sold"]
    replenished = inventory["closing_stock"] > expected_closing
    flagged = inventory["excess_stock_flag"].astype(str).str.lower() == "true"
    assert replenished.sum() == flagged.sum()
    assert (replenished != flagged).sum() == 0
