# Data Profiling and Semantic Mapping

Implementation: [`user_data.py`](../src/ordino/user_data.py).

## Column profile

Per column: `name`, `dtype`, `missing_count`, `missing_pct`, `n_unique`,
`is_numeric`, `is_datelike`. Per dataset: row count, column count, duplicate
rows.

### Date detection
A column is date-like if it is already a datetime dtype, or if ≥80% of a
50-value sample parses with `pd.to_datetime(..., format="mixed")`. The sample
keeps profiling fast on large files; the 80% threshold tolerates a few bad rows
without accepting a column that merely contains occasional digits.

## Data-quality score

Starts at 100. Deducts up to 40 for average missingness (×1.5) and up to 20 for
duplicate rows (×1.0), floored at 0, and reports findings in plain language
("4.2% of values are missing on average"). Capped deductions stop one very
sparse column from zeroing an otherwise usable dataset.

## Semantic mapping

Thirteen canonical concepts: `date`, `revenue`, `cost`, `profit`, `quantity`,
`product`, `customer`, `store`, `region`, `category`, `campaign`,
`return_flag`, `employee`.

Matching runs in three passes: exact normalised name against a synonym list;
then substring (`total_revenue` contains `revenue`); then a **type sanity
check** that rejects a non-numeric column proposed for a numeric concept, or a
non-date column proposed for `date`. Each column is claimed at most once.

Every proposal is displayed and editable. Nothing is analysed until confirmed.

### Type-filtered options
Each dropdown offers only suitable columns — dates for Date, numerics for
Revenue/Cost/Profit/Quantity, columns with ≤3 distinct values for Return flag,
and non-date non-float columns for dimensions (a float measure would produce one
group per row). Offering every column for every concept pushed type-checking
back onto the user and allowed mappings that could only fail at coercion.

### Derived profit
If `cost` is mapped but `profit` isn't, `profit = revenue − cost` is derived
once in `build_canonical_frame`, so every downstream function sees one
consistent column. Deriving it in each function separately caused the
capability matrix to report "Profitability: not detected" beside a displayed
margin figure.

## Capability matrix

Maps each of nine analyses to its required canonical columns and reports
supported vs. not, naming what's missing. `Profitability` accepts `profit` *or*
`cost`; `Regional / store performance` accepts `region` *or* `store`.

## Tests
See [`test_user_data.py`](../tests/test_user_data.py) — profiling, type
detection, mapping proposals, option filtering, capability detection, derived
profit, dataset window, and honest refusal.
