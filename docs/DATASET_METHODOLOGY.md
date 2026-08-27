# Dataset Methodology

## Honest provenance statement

The AI BuildFest 2026 case study brief describes NexaSphere Retail Ltd. but
does not ship a dataset. This dataset was constructed to represent that
fictional scenario -- **it is not real company data, and no dataset
generator script or fixed random seed exists in this repository.** The
CSVs in `/data` are static files; "reproducible" in this project means "the
analytics engine is deterministic against these fixed files" (verified by
the test suite), not "the dataset itself can be regenerated from a
documented seed." That distinction matters and we're not glossing over it:
if asked to regenerate the dataset from scratch today, we could not, only
re-run the same static files through the same deterministic code.

## Why a synthetic dataset was necessary

The case study's required business questions (revenue/profit leaders,
returns outliers, delivery performance, inventory imbalance, marketing ROI,
customer segment value, employee/store performance, target attainment) all
need data that actually contains those signals. A dataset generated with
uniform randomness wouldn't reliably produce a discoverable margin-pressure
story, return-rate outlier, or delivery-partner gap -- so the dataset was
deliberately constructed with specific business conditions planted in it
(see below), rather than left to chance.

## Structure

13 relationally-consistent CSVs covering 6 months (2026-01-01 to
2026-06-30) of a 9-store, 80-product, 8-category omnichannel retailer:
sales (32,000 order lines), returns (2,024), deliveries (32,000, 1:1 with
sales), daily inventory snapshots (130,320: 9 stores x 80 products x 181
days), 5,000 customers, 90 employees, 8 marketing campaigns, 5 delivery
partners, and monthly store targets. Full field-level detail:
[DATA_DICTIONARY.md](DATA_DICTIONARY.md).

## Verified relational integrity

We ran our own integrity checks by hand against the actual files (see
`tests/test_data_integrity.py` for the automated version added after this
audit): zero duplicate primary keys in sales/returns/deliveries, zero
orphaned foreign keys across sales<->products/stores/customers and
returns/deliveries<->sales, zero negative revenue/cost/quantity values,
`discount_pct` always in [0, 1], `unit_price` never exceeds `list_price`.

## The planted business conditions

These are the specific, intentional signals the dataset was built to
contain, each independently verified against
`internal_validation/GROUND_TRUTH_INTERNAL.json` (an internal-only reference
file, excluded from `/data` and from the public app per the original
dataset README's instruction) and re-confirmed live by the analytics engine:

1. **Margin pressure in the final period.** The most recent 30-day window
   shows +63.2% revenue growth against only +53.8% gross-profit growth
   (-1.45pp margin), versus the prior 30-day window. This is the intended
   hero story: revenue growth outpacing profit growth.
2. **Elevated Audio-category returns.** 12.77% of Audio units sold are
   returned (891 units, 294,656.64 refunded) -- the highest of 8 categories,
   2.28 standard deviations above the category average, driven primarily by
   "Not as Expected" as the return reason.
3. **UrbanMove (DP04) delivery deterioration.** 34.0% delayed-delivery rate
   versus ~6-10% for the other four partners, with a correspondingly lower
   average customer rating.
4. **TV stockouts / air-conditioner excess stock, concentrated by store.**
   The highest stockout-day counts are concentrated in TV SKUs (P0021-P0024)
   in West-region stores; the highest excess-stock-day counts are
   concentrated in air-conditioner SKUs, mostly North/Central stores.
5. **Summer Cooling as the standout marketing campaign**, at 5.71x ROI
   against a next-best of 4.96x and a worst of 1.84x.

## What was NOT hard-coded

The application never special-cases "Audio" or "UrbanMove" or "Summer
Cooling" by name anywhere in `analytics.py` or `insights.py`. The insight
engine computes the same generic return-rate/delay-rate/ROI calculations
across every category, partner and campaign, and the specific names above
emerge from ranking and z-score comparison against the full dataset --
they're the *output* of running the same code that would surface a
different name if the underlying numbers were different. This is what lets
us say the findings are discovered, not displayed from a fixed script.

## Known limitations, stated plainly

- No seeded generator script exists in this repo (see provenance statement
  above) -- this is the single biggest gap if asked to prove full
  reproducibility from scratch.
- The z-score-based outlier detection for returns (8 categories) and
  delivery partners (5 partners) operates on small samples, where a single
  data point noticeably moves the mean/std. The findings themselves are
  computed from real, complete data; the *statistical confidence in "this is
  a genuine outlier" specifically* is capped at "medium" in the UI for this
  reason -- see `insights._CONFIDENCE_NOTES`.
- `inventory_daily.csv`'s `opening_stock - units_sold` does not always equal
  `closing_stock`; this is intentional (same-day restocking on
  excess-flagged days, and clamp-to-zero on stockout days), not a
  generation defect -- fully explained in DATA_DICTIONARY.md, and verified
  row-by-row rather than assumed.
- `hubs.csv` is loaded but not yet used by any analytics function --
  fulfilment-hub-level analysis is not implemented in this prototype.
