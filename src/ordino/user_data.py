"""Generic, schema-agnostic analytics adapter for user-uploaded business data.

This is the "Analyze My Business" pipeline, kept structurally identical to
the Ordino demo pipeline (ordino.analytics / insights / nlg) but
without assuming any fixed schema:

    Uploaded CSV
        -> profile_dataset()          (row/col counts, dtypes, missingness)
        -> suggest_mapping()          (best-guess column -> canonical concept)
        -> [user confirms/edits the mapping in the UI]
        -> build_canonical_frame()    (renamed + type-coerced subset)
        -> capability_matrix()        (which analyses this data can support)
        -> generic analytics functions (only run when their required
           canonical columns are present)
        -> Finding-shaped evidence dicts (ordino.insights.Finding)
        -> ordino.nlg (unchanged -- already dataset-agnostic) for
           grounded AI narration.

Nothing in this module (or downstream) ever hands the raw uploaded
dataframe to an LLM. Every number an AI narrates comes from a dict this
module computed with pandas, exactly like the demo pipeline.

ordino.analytics / ordino.insights are intentionally NOT reused
here: they are hardcoded to the Ordino CSV schema (specific joins,
specific column names) and generalizing them would risk breaking the
competition demo. This module is a deliberately separate, smaller,
schema-agnostic engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
import pandas as pd

MAX_UPLOAD_ROWS = 500_000  # sanity ceiling, not a hard product limit

# ---------------------------------------------------------------------------
# Canonical business concepts and the column-name synonyms used to guess them
# ---------------------------------------------------------------------------

CANONICAL_FIELDS: dict[str, list[str]] = {
    "date": ["date", "order_date", "transaction_date", "sale_date", "invoice_date", "purchase_date", "created_at"],
    "revenue": ["revenue", "sales", "sales_amount", "total_sales", "amount", "total", "order_total",
                "total_amount", "net_sales", "price_total", "line_total"],
    "cost": ["cost", "cogs", "unit_cost", "total_cost", "cost_of_goods"],
    "profit": ["profit", "gross_profit", "net_profit", "margin_amount", "profit_amount"],
    "quantity": ["quantity", "qty", "units", "units_sold", "item_count"],
    "product": ["product", "product_name", "item", "item_name", "sku", "product_id"],
    "customer": ["customer", "customer_id", "customer_name", "client", "client_id", "buyer"],
    "store": ["store", "store_name", "branch", "outlet", "location_name"],
    "region": ["region", "area", "territory", "zone", "city", "state", "country"],
    "category": ["category", "product_category", "segment", "type", "department"],
    "campaign": ["campaign", "campaign_name", "channel", "marketing_channel", "source"],
    "return_flag": ["return", "returned", "is_return", "return_flag", "refunded"],
    "employee": ["employee", "employee_name", "staff", "salesperson", "rep", "agent"],
}

_NUMERIC_CONCEPTS = {"revenue", "cost", "profit", "quantity"}


def _normalize(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    missing_count: int
    missing_pct: float
    n_unique: int
    is_numeric: bool
    is_datelike: bool


@dataclass
class DatasetProfile:
    n_rows: int
    n_cols: int
    columns: list[ColumnProfile]
    duplicate_rows: int

    def as_dict(self) -> dict:
        return {
            "n_rows": self.n_rows,
            "n_cols": self.n_cols,
            "duplicate_rows": self.duplicate_rows,
            "columns": [c.__dict__ for c in self.columns],
        }


class DatasetError(ValueError):
    """Raised for an uploaded file that can't be safely analyzed."""


def load_uploaded_csv(file) -> pd.DataFrame:
    """file: a Streamlit UploadedFile (or any file-like object)."""
    try:
        df = pd.read_csv(file)
    except Exception as exc:  # pandas raises many different error types
        raise DatasetError(
            "Couldn't read this file as a CSV. Make sure it's a plain CSV "
            "(comma-separated) file, not an Excel file saved with a .csv "
            f"extension. (Parser error: {exc})"
        ) from exc

    if df.shape[1] == 0:
        raise DatasetError("This file has no columns Ordino can detect.")
    if df.shape[0] == 0:
        raise DatasetError("This file has headers but no data rows.")
    if df.shape[0] > MAX_UPLOAD_ROWS:
        raise DatasetError(
            f"This file has {df.shape[0]:,} rows, which is above the "
            f"{MAX_UPLOAD_ROWS:,}-row limit for this prototype. Try a smaller export."
        )

    df.columns = [str(c).strip() for c in df.columns]
    return df


def _is_datelike(series: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    if not pd.api.types.is_object_dtype(series) and not pd.api.types.is_string_dtype(series):
        return False
    sample = series.dropna().head(50)
    if sample.empty:
        return False
    parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
    return parsed.notna().mean() >= 0.8


def profile_dataset(df: pd.DataFrame) -> DatasetProfile:
    columns = []
    for col in df.columns:
        s = df[col]
        missing = int(s.isna().sum())
        columns.append(ColumnProfile(
            name=col,
            dtype=str(s.dtype),
            missing_count=missing,
            missing_pct=round(missing / len(df) * 100, 2) if len(df) else 0.0,
            n_unique=int(s.nunique(dropna=True)),
            is_numeric=bool(pd.api.types.is_numeric_dtype(s)),
            is_datelike=_is_datelike(s),
        ))
    return DatasetProfile(
        n_rows=len(df),
        n_cols=len(df.columns),
        columns=columns,
        duplicate_rows=int(df.duplicated().sum()),
    )


def suggest_mapping(df: pd.DataFrame, profile: DatasetProfile) -> dict[str, Optional[str]]:
    """Best-guess column -> canonical concept, using normalized name matching
    plus a light dtype sanity check. Returns {concept: column_name_or_None}.
    This is a suggestion only -- the UI must let the user override every
    entry before analytics run on it (never silently assumed).
    """
    profile_by_name = {c.name: c for c in profile.columns}
    normalized_columns = {_normalize(c): c for c in df.columns}

    mapping: dict[str, Optional[str]] = {}
    used: set[str] = set()

    for concept, synonyms in CANONICAL_FIELDS.items():
        match = None
        for syn in synonyms:
            norm_syn = _normalize(syn)
            if norm_syn in normalized_columns and normalized_columns[norm_syn] not in used:
                match = normalized_columns[norm_syn]
                break
        if match is None:
            # substring fallback (e.g. "total_revenue" contains "revenue")
            for norm_col, col in normalized_columns.items():
                if col in used:
                    continue
                if any(_normalize(s) in norm_col for s in synonyms):
                    match = col
                    break
        if match is not None:
            cp = profile_by_name[match]
            if concept in _NUMERIC_CONCEPTS and not cp.is_numeric:
                match = None
            elif concept == "date" and not cp.is_datelike:
                match = None
        if match is not None:
            mapping[concept] = match
            used.add(match)
        else:
            mapping[concept] = None
    return mapping


CONCEPT_HELP: dict[str, str] = {
    "date": "When each record happened — drives all trend and growth analysis.",
    "revenue": "Money earned per record (sales amount, invoice total, turnover).",
    "cost": "What the goods/services cost you. Profit is derived if profit isn't mapped.",
    "profit": "Profit per record, if you already calculate it.",
    "quantity": "Units sold or items per record.",
    "product": "What was sold — product, item or SKU name.",
    "customer": "Who bought — customer name or ID.",
    "store": "Which branch, outlet or store.",
    "region": "Geography — region, city, state or territory.",
    "category": "Product grouping or business segment.",
    "campaign": "Marketing campaign, channel or source.",
    "return_flag": "Whether the record was returned/refunded (yes-no style column).",
    "employee": "Who made the sale — staff or salesperson.",
}


def candidate_columns(concept: str, profile: DatasetProfile) -> list[str]:
    """Columns that could plausibly represent `concept`.

    The mapping UI previously offered every column for every concept, so the
    "Date" dropdown listed numeric revenue columns and "Revenue" listed text
    names -- the user had to do the type-checking Ordino already did during
    profiling. Filtering by detected type makes each dropdown answer its own
    question, and prevents mappings that would fail on coercion anyway.
    """
    if concept == "date":
        return [c.name for c in profile.columns if c.is_datelike]
    if concept in _NUMERIC_CONCEPTS:
        return [c.name for c in profile.columns if c.is_numeric]
    if concept == "return_flag":
        # A returned/refunded marker is binary (yes/no, true/false, 1/0), so
        # cap at 3 distinct values to allow for a third "unknown"-style value.
        # A looser cap lets short free-text columns through, and mapping one
        # of those would silently produce a meaningless return rate.
        return [c.name for c in profile.columns
                if c.n_unique <= 3 and not c.is_datelike]
    # Dimensions: anything that groups records. Dates are excluded (they're
    # handled by the date concept) and so are near-unique float measures,
    # which would produce one group per row.
    out = []
    for c in profile.columns:
        if c.is_datelike:
            continue
        if c.is_numeric and c.dtype.startswith("float"):
            continue
        out.append(c.name)
    return out


def build_canonical_frame(df: pd.DataFrame, mapping: dict[str, Optional[str]]) -> pd.DataFrame:
    """Renames the user-confirmed mapped columns into canonical names and
    coerces types. Unmapped concepts are simply absent as columns -- callers
    must check for column presence, never assume a concept exists.
    """
    out = pd.DataFrame(index=df.index)
    for concept, col in mapping.items():
        if col is None or col not in df.columns:
            continue
        series = df[col]
        if concept == "date":
            series = pd.to_datetime(series, errors="coerce", format="mixed")
        elif concept in _NUMERIC_CONCEPTS:
            series = pd.to_numeric(series, errors="coerce")
        out[concept] = series

    # Derive profit from revenue - cost when the user has cost but not an
    # explicit profit column, so every downstream function (kpi_summary,
    # growth_comparison, breakdown_by, generate_user_findings) sees a single
    # consistent "profit" column rather than each having to special-case
    # "or derive it from cost" separately.
    if "profit" not in out.columns and "revenue" in out.columns and "cost" in out.columns:
        out["profit"] = out["revenue"] - out["cost"]

    return out


# ---------------------------------------------------------------------------
# Capability matrix: which analyses this dataset can honestly support
# ---------------------------------------------------------------------------

CAPABILITY_REQUIREMENTS: dict[str, list[str]] = {
    "Revenue trend over time": ["date", "revenue"],
    "Profitability": ["revenue", "profit"],
    "Product performance": ["product", "revenue"],
    "Customer analysis": ["customer", "revenue"],
    "Category breakdown": ["category", "revenue"],
    "Regional / store performance": ["revenue"],  # + region or store, checked specially
    "Returns analysis": ["return_flag"],
    "Marketing / campaign ROI": ["campaign", "revenue"],
    "Employee performance": ["employee", "revenue"],
}


def capability_matrix(canonical_columns: set[str]) -> dict[str, bool]:
    """Profitability accepts either an explicit `profit` column or a `cost`
    column (kpi_summary derives profit = revenue - cost in that case) -- the
    capability matrix must agree with what kpi_summary/generate_user_findings
    actually compute, or the UI ends up showing a profit/margin figure right
    next to a "Profitability: not detected" badge, which is a genuine
    self-contradiction a user would notice immediately.
    """
    result = {}
    for label, required in CAPABILITY_REQUIREMENTS.items():
        if label == "Regional / store performance":
            result[label] = "revenue" in canonical_columns and (
                "region" in canonical_columns or "store" in canonical_columns
            )
        elif label == "Profitability":
            result[label] = "revenue" in canonical_columns and (
                "profit" in canonical_columns or "cost" in canonical_columns
            )
        else:
            result[label] = all(r in canonical_columns for r in required)
    return result


def missing_requirements(label: str, canonical_columns: set[str]) -> list[str]:
    if label == "Regional / store performance":
        return [] if ("revenue" in canonical_columns and ({"region", "store"} & canonical_columns)) else (
            [c for c in ("revenue",) if c not in canonical_columns] + (
                ["region or store"] if not ({"region", "store"} & canonical_columns) else []
            )
        )
    if label == "Profitability":
        missing = [c for c in ("revenue",) if c not in canonical_columns]
        if "profit" not in canonical_columns and "cost" not in canonical_columns:
            missing.append("profit or cost")
        return missing
    required = CAPABILITY_REQUIREMENTS.get(label, [])
    return [r for r in required if r not in canonical_columns]


# ---------------------------------------------------------------------------
# Generic deterministic analytics (only called when required columns exist)
# ---------------------------------------------------------------------------

def dataset_window(cdf: pd.DataFrame) -> tuple | None:
    """(start, end) of the user's own data, for display. Returns None when no
    usable date column is mapped -- callers must say so rather than showing the
    demo dataset's dates, which describe a different business entirely.
    """
    if "date" not in cdf.columns:
        return None
    dates = cdf["date"].dropna()
    if dates.empty:
        return None
    return dates.min(), dates.max()


def kpi_summary(cdf: pd.DataFrame) -> dict:
    if "revenue" not in cdf.columns:
        return {}
    revenue = float(cdf["revenue"].sum())
    result = {"revenue": round(revenue, 2), "records": int(len(cdf))}
    if "profit" in cdf.columns:  # build_canonical_frame derives this from cost when needed
        profit = float(cdf["profit"].sum())
        result["profit"] = round(profit, 2)
        result["margin_pct"] = round(profit / revenue * 100, 2) if revenue else 0.0
    if "quantity" in cdf.columns:
        result["units"] = float(cdf["quantity"].sum())
    return result


def revenue_trend(cdf: pd.DataFrame, freq: str = "M") -> pd.DataFrame:
    if "date" not in cdf.columns or "revenue" not in cdf.columns:
        return pd.DataFrame()
    d = cdf.dropna(subset=["date"]).copy()
    d["period"] = d["date"].dt.to_period(freq).dt.start_time
    agg = {"revenue": "sum"}
    if "profit" in d.columns:
        agg["profit"] = "sum"
    g = d.groupby("period").agg(agg).reset_index()
    return g


def growth_comparison(cdf: pd.DataFrame, window_days: int = 30) -> dict:
    """Generic version of analytics.revenue_profit_growth_gap: last N days
    vs. the preceding N days. Requires date + revenue.
    """
    if "date" not in cdf.columns or "revenue" not in cdf.columns:
        return {}
    d = cdf.dropna(subset=["date"])
    if d.empty:
        return {}
    max_date = d["date"].max()
    latest_start = max_date - pd.Timedelta(days=window_days - 1)
    prev_end = latest_start - pd.Timedelta(days=1)
    prev_start = prev_end - pd.Timedelta(days=window_days - 1)

    def window_kpi(start, end):
        w = d[(d["date"] >= start) & (d["date"] <= end)]
        rev = float(w["revenue"].sum())
        out = {"revenue": round(rev, 2)}
        if "profit" in w.columns:
            out["profit"] = round(float(w["profit"].sum()), 2)
        return out

    latest = window_kpi(latest_start, max_date)
    previous = window_kpi(prev_start, prev_end)

    def pct_change(new, old):
        if not old:
            return None
        return round((new - old) / old * 100, 2)

    result = {
        "window_days": window_days,
        "latest_period": {"start": str(latest_start.date()), "end": str(max_date.date()), **latest},
        "previous_period": {"start": str(prev_start.date()), "end": str(prev_end.date()), **previous},
        "revenue_pct_change": pct_change(latest["revenue"], previous["revenue"]),
    }
    if "profit" in latest and "profit" in previous:
        result["profit_pct_change"] = pct_change(latest["profit"], previous["profit"])
        if result["revenue_pct_change"] is not None and result["profit_pct_change"] is not None:
            result["growth_gap_pp"] = round(result["revenue_pct_change"] - result["profit_pct_change"], 2)
    return result


def breakdown_by(cdf: pd.DataFrame, dimension: str, top_n: int = 10) -> pd.DataFrame:
    """dimension: one of 'product', 'customer', 'category', 'region', 'store',
    'campaign', 'employee'. Requires that dimension + revenue both exist.
    """
    if dimension not in cdf.columns or "revenue" not in cdf.columns:
        return pd.DataFrame()
    agg = {"revenue": "sum"}
    if "profit" in cdf.columns:
        agg["profit"] = "sum"
    if "quantity" in cdf.columns:
        agg["quantity"] = "sum"
    g = cdf.groupby(dimension, dropna=False).agg(agg).reset_index()
    g = g.sort_values("revenue", ascending=False).reset_index(drop=True)
    for c in agg:
        g[c] = g[c].round(2)
    if "profit" in g.columns:
        g["margin_pct"] = np.where(g["revenue"] > 0, (g["profit"] / g["revenue"] * 100).round(2), 0.0)
    return g.head(top_n)


def returns_summary(cdf: pd.DataFrame) -> dict:
    if "return_flag" not in cdf.columns:
        return {}
    flag = cdf["return_flag"]
    is_return = flag.astype(str).str.lower().isin(["true", "1", "yes", "y", "returned"])
    total = len(cdf)
    returned = int(is_return.sum())
    return {
        "total_records": total,
        "returned_records": returned,
        "return_rate_pct": round(returned / total * 100, 2) if total else 0.0,
    }


# ---------------------------------------------------------------------------
# Data quality score
# ---------------------------------------------------------------------------

def data_quality_score(profile: DatasetProfile) -> dict:
    if not profile.columns:
        return {"score": 0, "notes": ["No columns detected."]}
    avg_missing_pct = sum(c.missing_pct for c in profile.columns) / len(profile.columns)
    dup_pct = (profile.duplicate_rows / profile.n_rows * 100) if profile.n_rows else 0.0

    score = 100.0
    score -= min(avg_missing_pct * 1.5, 40)
    score -= min(dup_pct * 1.0, 20)
    score = max(0, round(score))

    notes = []
    if avg_missing_pct > 5:
        notes.append(f"{avg_missing_pct:.1f}% of values are missing on average across columns.")
    if dup_pct > 0:
        notes.append(f"{dup_pct:.1f}% of rows are exact duplicates.")
    if not notes:
        notes.append("No major data quality issues detected.")
    return {"score": int(score), "avg_missing_pct": round(avg_missing_pct, 2),
             "duplicate_pct": round(dup_pct, 2), "notes": notes}


# ---------------------------------------------------------------------------
# Findings for user data (same Finding shape as ordino.insights.Finding)
# ---------------------------------------------------------------------------

@dataclass
class UserFinding:
    id: str
    title: str
    category: str
    severity: str
    summary: str
    evidence: dict[str, Any] = field(default_factory=dict)
    recommendation: str = ""
    possible_drivers: list[str] = field(default_factory=list)
    confidence: str = "medium"


def generate_user_findings(cdf: pd.DataFrame, capabilities: dict[str, bool]) -> list[UserFinding]:
    findings: list[UserFinding] = []

    if capabilities.get("Revenue trend over time") and capabilities.get("Profitability"):
        growth = growth_comparison(cdf)
        if growth.get("revenue_pct_change") is not None and growth.get("profit_pct_change") is not None:
            gap = growth.get("growth_gap_pp", 0)
            margin_pressure = gap is not None and gap > 2.0
            summary = (
                f"Revenue changed {growth['revenue_pct_change']:+.1f}% over the last "
                f"{growth['window_days']} days versus the prior period, while profit changed "
                f"{growth['profit_pct_change']:+.1f}%."
            )
            findings.append(UserFinding(
                id="user_growth_gap", title="Revenue vs. Profit Growth", category="profitability",
                severity="warning" if margin_pressure else "info", summary=summary, evidence=growth,
                recommendation=(
                    "Revenue is growing faster than profit -- review pricing, discounting and cost "
                    "drivers before scaling revenue further."
                ) if margin_pressure else "Profit is tracking revenue; no immediate concern.",
                confidence="high",
            ))

    for dim, label in (("product", "Product performance"), ("customer", "Customer analysis"),
                        ("category", "Category breakdown")):
        if capabilities.get(label):
            df = breakdown_by(cdf, dim, top_n=5)
            if len(df):
                top = df.iloc[0]
                summary = f"{top[dim]} generates the most revenue at {top['revenue']:,.2f}"
                if "margin_pct" in df.columns:
                    summary += f" ({top['margin_pct']:.1f}% margin)."
                else:
                    summary += "."
                findings.append(UserFinding(
                    id=f"user_top_{dim}", title=f"Top {dim.capitalize()} by Revenue", category=dim,
                    severity="info", summary=summary,
                    evidence={"by_" + dim: df.to_dict(orient="records")},
                    recommendation=f"Consider whether {top[dim]}'s performance can be replicated elsewhere.",
                    confidence="high",
                ))

    if capabilities.get("Returns analysis"):
        r = returns_summary(cdf)
        if r:
            severity = "warning" if r["return_rate_pct"] > 10 else "info"
            findings.append(UserFinding(
                id="user_returns", title="Return Rate", category="returns", severity=severity,
                summary=f"{r['return_rate_pct']:.2f}% of {r['total_records']:,} records are marked as returned.",
                evidence=r,
                recommendation="Investigate return reasons if a return-reason column exists."
                if severity == "warning" else "Return rate is within a typical range.",
                confidence="high",
            ))

    return findings


# ---------------------------------------------------------------------------
# Question routing for user data -- same "keyword -> deterministic calc ->
# evidence" pattern as ordino.qa, but capability-aware: a question is
# only answered if the uploaded data actually supports it.
# ---------------------------------------------------------------------------

@dataclass
class UserQAResult:
    intent: str
    supported: bool
    result: Any
    template_answer: str


def _any(q: str, phrases: list[str]) -> bool:
    return any(p in q for p in phrases)


_META_PHRASES = [
    "what can i ask", "what questions", "what can you do", "what can you analyse",
    "what can you analyze", "what can you tell me", "what do you understand",
    "what data do you", "what analyses", "how do i use", "what should i ask",
    "suggest questions", "give me examples", "what else can",
    "wetin i fit ask", "wetin you fit do", "which question i fit",
]

# Example questions per capability, used to answer "what can I ask?" from the
# user's ACTUAL detected columns rather than a hardcoded list.
_CAPABILITY_QUESTIONS: dict[str, list[str]] = {
    "Revenue trend over time": ["How has revenue changed over time?", "What is our total revenue?"],
    "Profitability": ["Is profit keeping pace with revenue?", "What is our margin?"],
    "Product performance": ["Which products generate the most revenue?"],
    "Customer analysis": ["Which customers are most valuable?"],
    "Category breakdown": ["Which categories perform best?"],
    "Regional / store performance": ["Which regions or stores generate the most revenue?"],
    "Returns analysis": ["What is our return rate?"],
    "Marketing / campaign ROI": ["Which campaigns generate the best return?"],
    "Employee performance": ["Which employees generate the most revenue?"],
}


def answer_user_question(question: str, cdf: pd.DataFrame, capabilities: dict[str, bool]) -> UserQAResult:
    q = question.lower().strip()

    # Meta-question: answer from the detected capabilities of THIS dataset.
    # Never answer "what can I ask?" with a KPI dump -- see the same fix in
    # ordino.qa for the demo workspace.
    if _any(q, _META_PHRASES):
        supported = [label for label, ok in capabilities.items() if ok]
        if not supported:
            answer = (
                "I can't run any of the standard analyses on this dataset yet -- no "
                "revenue-like column was mapped. Check the column mapping step above, "
                "then ask me again."
            )
        else:
            lines = ["Based on the data you uploaded, here's what I can help with:\n"]
            for label in supported:
                for example in _CAPABILITY_QUESTIONS.get(label, []):
                    lines.append(f"- {example}")
            missing = [label for label, ok in capabilities.items() if not ok]
            if missing:
                lines.append(
                    "\nNot available from this dataset: " + ", ".join(missing)
                    + ". Upload data containing those fields to unlock them."
                )
            answer = "\n".join(lines)
        return UserQAResult("meta_capabilities", True,
                            {"supported": [l for l, ok in capabilities.items() if ok]}, answer)

    def unsupported(label: str) -> UserQAResult:
        needed = missing_requirements(label, set(cdf.columns))
        needed_str = ", ".join(needed) if needed else "additional columns"
        return UserQAResult(
            intent="unsupported", supported=False, result={},
            template_answer=(
                f"I can't answer that from this dataset -- it doesn't contain the columns needed for "
                f"'{label}' ({needed_str}). Map or upload data with those columns to unlock this analysis."
            ),
        )

    if _any(q, ["profit", "profitability", "margin", "making money"]):
        label = "Profitability"
        if not capabilities.get(label):
            return unsupported(label)
        growth = growth_comparison(cdf)
        return UserQAResult("profitability", True, growth, (
            f"Revenue changed {growth.get('revenue_pct_change', 0):+.1f}% and profit changed "
            f"{growth.get('profit_pct_change', 0):+.1f}% over the last {growth.get('window_days', 30)} days."
            if growth else "Not enough dated records to compute a growth comparison."
        ))

    for dim, label, keywords in (
        ("product", "Product performance", ["product", "item", "sku"]),
        ("customer", "Customer analysis", ["customer", "client"]),
        ("category", "Category breakdown", ["category", "segment"]),
        ("region", "Regional / store performance", ["region", "area", "territory"]),
        ("store", "Regional / store performance", ["store", "branch", "outlet"]),
        ("campaign", "Marketing / campaign ROI", ["campaign", "marketing", "roi"]),
        ("employee", "Employee performance", ["employee", "staff", "salesperson"]),
    ):
        if _any(q, keywords):
            if not capabilities.get(label) or dim not in cdf.columns:
                return unsupported(label)
            df = breakdown_by(cdf, dim, top_n=10)
            if df.empty:
                return unsupported(label)
            top = df.iloc[0]
            return UserQAResult(f"breakdown_{dim}", True, {"by_" + dim: df.to_dict(orient="records")}, (
                f"{top[dim]} generates the most revenue at {top['revenue']:,.2f}."
            ))

    if _any(q, ["return", "returned", "refund"]):
        label = "Returns analysis"
        if not capabilities.get(label):
            return unsupported(label)
        r = returns_summary(cdf)
        return UserQAResult("returns", True, r, (
            f"{r['return_rate_pct']:.2f}% of {r['total_records']:,} records are marked as returned."
        ))

    if _any(q, ["revenue", "sales", "how much", "total"]):
        if "revenue" not in cdf.columns:
            return unsupported("Revenue trend over time")
        kpi = kpi_summary(cdf)
        return UserQAResult("kpi_overview", True, kpi, (
            f"Total revenue is {kpi.get('revenue', 0):,.2f} across {kpi.get('records', 0):,} records."
            + (f" Profit is {kpi['profit']:,.2f} ({kpi.get('margin_pct', 0):.1f}% margin)." if "profit" in kpi else "")
        ))

    supported_labels = [label for label, ok in capabilities.items() if ok]
    return UserQAResult(
        intent="fallback", supported=False, result={},
        template_answer=(
            "I couldn't map that question to a supported analysis for this dataset. "
            + (f"This dataset currently supports: {', '.join(supported_labels)}."
               if supported_labels else "This dataset doesn't yet support any of the standard analyses -- "
               "check the column mapping step.")
        ),
    )
