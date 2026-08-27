"""Tests for the generic "Analyze My Business" dataset adapter
(nexasphere.user_data): CSV loading, profiling, column-mapping suggestions,
capability detection, generic analytics, and capability-aware Q&A.

These intentionally use small synthetic CSVs with schemas that do NOT match
the NexaSphere demo dataset, to prove the adapter is genuinely generic and
not secretly coupled to the competition schema.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nexasphere import user_data as ud  # noqa: E402
from nexasphere.nlg import _numbers_are_grounded  # noqa: E402


def _csv_file(text: str):
    return io.StringIO(text)


RETAIL_CSV = """transaction_date,sales_amount,cost,product_name,customer_id,region
2026-01-01,100.00,60.00,Widget A,C001,North
2026-01-02,150.00,90.00,Widget B,C002,South
2026-01-15,200.00,80.00,Widget A,C001,North
2026-02-01,120.00,70.00,Widget C,C003,East
2026-02-10,300.00,150.00,Widget B,C002,South
"""

HR_CSV = """employee_name,department,salary,performance_score
Alice,Engineering,90000,4.2
Bob,Sales,70000,3.8
Carol,Engineering,95000,4.6
"""

MALFORMED_CSV = "not,a,valid\ncsv\"file"


def test_load_uploaded_csv_success():
    df = ud.load_uploaded_csv(_csv_file(RETAIL_CSV))
    assert len(df) == 5
    assert "sales_amount" in df.columns


def test_load_uploaded_csv_empty_rows():
    with pytest.raises(ud.DatasetError):
        ud.load_uploaded_csv(_csv_file("col1,col2\n"))


def test_load_uploaded_csv_no_columns():
    with pytest.raises(ud.DatasetError):
        ud.load_uploaded_csv(_csv_file(""))


def test_profile_dataset_basic_stats():
    df = ud.load_uploaded_csv(_csv_file(RETAIL_CSV))
    profile = ud.profile_dataset(df)
    assert profile.n_rows == 5
    assert profile.n_cols == 6
    assert profile.duplicate_rows == 0
    col_names = {c.name for c in profile.columns}
    assert "sales_amount" in col_names


def test_profile_detects_dates_and_numerics():
    df = ud.load_uploaded_csv(_csv_file(RETAIL_CSV))
    profile = ud.profile_dataset(df)
    by_name = {c.name: c for c in profile.columns}
    assert by_name["transaction_date"].is_datelike
    assert by_name["sales_amount"].is_numeric
    assert not by_name["product_name"].is_numeric


def test_suggest_mapping_detects_retail_schema():
    df = ud.load_uploaded_csv(_csv_file(RETAIL_CSV))
    profile = ud.profile_dataset(df)
    mapping = ud.suggest_mapping(df, profile)
    assert mapping["date"] == "transaction_date"
    assert mapping["revenue"] == "sales_amount"
    assert mapping["cost"] == "cost"
    assert mapping["product"] == "product_name"
    assert mapping["customer"] == "customer_id"
    assert mapping["region"] == "region"
    # concepts genuinely absent from this schema must map to None, never guessed
    assert mapping["employee"] is None
    assert mapping["campaign"] is None


def test_suggest_mapping_does_not_map_non_numeric_to_numeric_concept():
    """A 'department' column full of text should never be guessed as
    revenue/cost/profit/quantity even if a name partially matched.
    """
    df = ud.load_uploaded_csv(_csv_file(HR_CSV))
    profile = ud.profile_dataset(df)
    mapping = ud.suggest_mapping(df, profile)
    assert mapping["revenue"] is None
    assert mapping["cost"] is None


def test_build_canonical_frame_renames_and_coerces():
    df = ud.load_uploaded_csv(_csv_file(RETAIL_CSV))
    profile = ud.profile_dataset(df)
    mapping = ud.suggest_mapping(df, profile)
    cdf = ud.build_canonical_frame(df, mapping)
    assert "revenue" in cdf.columns
    assert pd.api.types.is_numeric_dtype(cdf["revenue"])
    assert pd.api.types.is_datetime64_any_dtype(cdf["date"])
    assert "employee" not in cdf.columns  # never fabricated


def test_candidate_columns_date_offers_only_datelike():
    """The mapping UI used to offer every column for every concept, so the
    Date dropdown listed numeric revenue columns. Each dropdown must now only
    offer columns whose detected type suits that concept.
    """
    df = ud.load_uploaded_csv(_csv_file(RETAIL_CSV))
    profile = ud.profile_dataset(df)
    options = ud.candidate_columns("date", profile)
    assert options == ["transaction_date"]
    assert "sales_amount" not in options


def test_candidate_columns_numeric_concepts_exclude_text():
    df = ud.load_uploaded_csv(_csv_file(RETAIL_CSV))
    profile = ud.profile_dataset(df)
    for concept in ("revenue", "cost", "profit", "quantity"):
        options = ud.candidate_columns(concept, profile)
        assert "product_name" not in options, concept
        assert "transaction_date" not in options, concept
        assert "sales_amount" in options, concept


def test_candidate_columns_dimensions_exclude_dates():
    df = ud.load_uploaded_csv(_csv_file(RETAIL_CSV))
    profile = ud.profile_dataset(df)
    for concept in ("product", "customer", "region"):
        options = ud.candidate_columns(concept, profile)
        assert "transaction_date" not in options, concept
        assert "product_name" in options, concept


def test_candidate_columns_return_flag_prefers_low_cardinality():
    csv = "id,returned,note\n1,yes,a\n2,no,b\n3,yes,c\n4,no,d\n"
    df = ud.load_uploaded_csv(_csv_file(csv))
    profile = ud.profile_dataset(df)
    options = ud.candidate_columns("return_flag", profile)
    assert "returned" in options
    assert "note" not in options  # 4 distinct values but high relative cardinality


def test_dataset_window_reports_user_data_range():
    cdf = _canonical_retail_frame()
    window = ud.dataset_window(cdf)
    assert window is not None
    start, end = window
    assert str(start.date()) == "2026-01-01"
    assert str(end.date()) == "2026-02-10"


def test_dataset_window_none_without_date_column():
    """Must return None rather than falling back to any other date source --
    showing the demo dataset's window for a user's data would describe a
    different business entirely.
    """
    df = ud.load_uploaded_csv(_csv_file(HR_CSV))
    profile = ud.profile_dataset(df)
    cdf = ud.build_canonical_frame(df, ud.suggest_mapping(df, profile))
    assert ud.dataset_window(cdf) is None


def test_capability_matrix_retail_dataset():
    df = ud.load_uploaded_csv(_csv_file(RETAIL_CSV))
    profile = ud.profile_dataset(df)
    mapping = ud.suggest_mapping(df, profile)
    cdf = ud.build_canonical_frame(df, mapping)
    caps = ud.capability_matrix(set(cdf.columns))
    assert caps["Revenue trend over time"] is True
    assert caps["Product performance"] is True
    assert caps["Customer analysis"] is True
    assert caps["Regional / store performance"] is True
    # this dataset has no employee/campaign/return columns
    assert caps["Employee performance"] is False
    assert caps["Marketing / campaign ROI"] is False
    assert caps["Returns analysis"] is False


def test_capability_matrix_agrees_with_kpi_when_only_cost_is_mapped():
    """Regression: a dataset with revenue+cost (no explicit profit column)
    must show Profitability as supported, matching the profit/margin figures
    kpi_summary actually displays -- otherwise the UI contradicts itself
    (shows a margin % right next to "Profitability: not detected").
    """
    cdf = _canonical_retail_frame()  # RETAIL_CSV has cost but no profit column
    assert "cost" in cdf.columns
    assert "profit" in cdf.columns  # derived by build_canonical_frame from revenue - cost
    caps = ud.capability_matrix(set(cdf.columns))
    assert caps["Profitability"] is True
    kpi = ud.kpi_summary(cdf)
    assert "profit" in kpi and "margin_pct" in kpi


def test_capability_matrix_hr_dataset_supports_almost_nothing():
    df = ud.load_uploaded_csv(_csv_file(HR_CSV))
    profile = ud.profile_dataset(df)
    mapping = ud.suggest_mapping(df, profile)
    cdf = ud.build_canonical_frame(df, mapping)
    caps = ud.capability_matrix(set(cdf.columns))
    # No revenue-bearing column exists at all in an HR dataset -- nothing
    # revenue-based should ever be claimed as supported.
    assert caps["Revenue trend over time"] is False
    assert caps["Profitability"] is False
    assert caps["Product performance"] is False


def _canonical_retail_frame():
    df = ud.load_uploaded_csv(_csv_file(RETAIL_CSV))
    profile = ud.profile_dataset(df)
    mapping = ud.suggest_mapping(df, profile)
    return ud.build_canonical_frame(df, mapping)


def test_kpi_summary_matches_manual_sum():
    cdf = _canonical_retail_frame()
    kpi = ud.kpi_summary(cdf)
    assert kpi["revenue"] == pytest.approx(870.00)
    assert kpi["profit"] == pytest.approx(870.00 - 450.00)


def test_breakdown_by_product_ranks_correctly():
    cdf = _canonical_retail_frame()
    df = ud.breakdown_by(cdf, "product", top_n=5)
    assert list(df["product"])[0] in ("Widget B", "Widget A")  # Widget B has highest combined revenue (450)
    top = df.iloc[0]
    assert top["product"] == "Widget B"
    assert top["revenue"] == pytest.approx(450.00)


def test_breakdown_by_missing_dimension_returns_empty():
    cdf = _canonical_retail_frame()
    df = ud.breakdown_by(cdf, "employee", top_n=5)
    assert df.empty


def test_generate_user_findings_grounded_in_evidence():
    cdf = _canonical_retail_frame()
    caps = ud.capability_matrix(set(cdf.columns))
    findings = ud.generate_user_findings(cdf, caps)
    assert len(findings) > 0
    for f in findings:
        assert _numbers_are_grounded(f.summary, f.evidence), f"Ungrounded number in: {f.summary}"


def test_answer_user_question_supported_revenue():
    cdf = _canonical_retail_frame()
    caps = ud.capability_matrix(set(cdf.columns))
    result = ud.answer_user_question("What is our total revenue?", cdf, caps)
    assert result.supported is True
    assert "870" in result.template_answer


def test_answer_user_question_unsupported_is_honest_not_hallucinated():
    cdf = _canonical_retail_frame()
    caps = ud.capability_matrix(set(cdf.columns))
    result = ud.answer_user_question("Which delivery partner performs worst?", cdf, caps)
    assert result.supported is False
    assert "couldn't map" in result.template_answer.lower()
    assert "delivery" not in result.template_answer.lower()  # never invents a delivery answer


def test_answer_user_question_named_capability_gap_explains_missing_columns():
    cdf = _canonical_retail_frame()
    caps = ud.capability_matrix(set(cdf.columns))
    result = ud.answer_user_question("Which employees perform best?", cdf, caps)
    assert result.supported is False
    assert "can't answer" in result.template_answer.lower()
    assert "employee" in result.template_answer.lower()


def test_answer_user_question_on_hr_dataset_is_honest_about_missing_revenue():
    df = ud.load_uploaded_csv(_csv_file(HR_CSV))
    profile = ud.profile_dataset(df)
    mapping = ud.suggest_mapping(df, profile)
    cdf = ud.build_canonical_frame(df, mapping)
    caps = ud.capability_matrix(set(cdf.columns))
    result = ud.answer_user_question("What is our revenue?", cdf, caps)
    assert result.supported is False


def test_data_quality_score_penalizes_missing_and_duplicates():
    dirty_csv = "a,b\n1,2\n1,2\n,4\n"  # one exact dup row, one missing value
    df = ud.load_uploaded_csv(_csv_file(dirty_csv))
    profile = ud.profile_dataset(df)
    quality = ud.data_quality_score(profile)
    assert quality["score"] < 100
    assert quality["duplicate_pct"] > 0
