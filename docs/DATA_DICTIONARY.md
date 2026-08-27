# Data Dictionary

This is the human-readable companion to [`data/data_dictionary.csv`](../data/data_dictionary.csv) --
same facts, with relationships and calculation notes a raw CSV can't carry.
If the two ever disagree, treat this file as stale and the CSV as current;
the CSV is small enough to be the safer source of truth to hand-edit.

## sales.csv (32,000 rows, one row per order line)

| Field | Type | Meaning | Notes |
|---|---|---|---|
| `order_id` | string | Unique order identifier | Primary key. 0 duplicates confirmed. |
| `order_date` | date | Date of order | Range: 2026-01-01 to 2026-06-30 |
| `customer_id` | string | FK -> `customers.csv` | 0 orphans confirmed |
| `product_id` | string | FK -> `products.csv` | 0 orphans confirmed |
| `store_id` | string | FK -> `stores.csv` | 0 orphans confirmed |
| `channel` | categorical | Sales channel (e.g. Mobile App, In-Store) | |
| `quantity` | integer | Units sold on this line | Always > 0 |
| `payment_method` | categorical | e.g. Card, Transfer | |
| `unit_cost`, `list_price`, `unit_price` | numeric | Per-unit cost/list/actual price | `unit_price <= list_price` always |
| `discount_pct` | decimal | Discount applied to list price | Always in [0, 1] |
| `revenue` | numeric | `quantity * unit_price` | |
| `cost` | numeric | `quantity * unit_cost` | |
| `gross_profit` | numeric | `revenue - cost` | |
| `gross_margin_pct` | decimal | `gross_profit / revenue * 100` | |
| `category` | categorical | Denormalized copy of `products.category` | **Do not merge sales with products on `product_id` without dropping this column first** -- see the "Known gotcha" section of [architecture.md](architecture.md) |

## products.csv (80 rows)

`product_id` (PK), `product_name`, `category`, `brand`, `unit_cost`, `list_price`, `target_margin_pct`.
8 categories, 5 brands, 10 products per category.

## stores.csv (9 rows)

`store_id` (PK), `store_name`, `region` (West/East/North/Central), `city`, `store_type` (Standard/Flagship/Outlet).

## hubs.csv (4 rows) -- loaded, not yet analyzed

`hub_id`, `hub_name`, `region`. Represents NexaSphere's fulfilment hubs.
**Honest status**: the loader (`data_loader.load_hubs`) exists but no
analytics function currently uses it -- there is no per-hub fulfilment
performance metric in this prototype. Flagged as a known gap, not hidden.

## customers.csv (5,000 rows)

`customer_id` (PK), `segment` (5 segments: Value Seekers, Professionals, Home Makers, Premium, Gamers/Corporate mix), `region`, `acquisition_channel`.

## returns.csv (2,024 rows)

`return_id` (PK), `order_id` (FK -> sales, 0 orphans), `return_date`, `product_id`, `quantity` (always > 0), `return_reason`, `refund_amount`.

## deliveries.csv (32,000 rows, one row per order)

`order_id` (FK -> sales, 1:1, 0 orphans either direction), `delivery_partner_id` (FK -> delivery_partners), `promised_days`, `actual_days`, `delivery_status` (On Time / Delayed), `delivery_rating` (1-5).

## delivery_partners.csv (5 rows)

`delivery_partner_id` (PK), `partner_name`, `base_delay_prob` -- the underlying probability parameter used when the dataset was generated (see [DATASET_METHODOLOGY.md](DATASET_METHODOLOGY.md)); the *observed* delay rate in `deliveries.csv` is what the analytics engine actually reports, not this input parameter.

## marketing.csv (8 rows) / campaigns.csv (unused duplicate)

`marketing.csv` has `campaign_id`, `campaign_name`, `channel`, `spend`, `target_segment`, `period`, `attributed_revenue`, `conversions`, `roi`. `campaigns.csv` is a strict column-subset of `marketing.csv` (no `attributed_revenue`/`conversions`/`roi`) and is not loaded by any code -- it predates the final schema and is kept only because the vendor-provided dataset shipped it. Safe to delete; not deleted yet so this file continues to reference why it exists.

## inventory_daily.csv (130,320 rows: 9 stores x 80 products x 181 days)

| Field | Type | Meaning |
|---|---|---|
| `snapshot_date` | date | 2026-01-01 to 2026-06-30 |
| `store_id`, `product_id` | string | FKs |
| `opening_stock`, `units_sold`, `closing_stock` | integer | See arithmetic note below |
| `stockout_flag` | boolean | True iff `closing_stock == 0` (verified: 100% consistent, 456/130,320 rows) |
| `excess_stock_flag` | boolean | True for a deliberately elevated-stock scenario (verified: 1,810/130,320 rows) |

**Arithmetic note (verified, not a bug):** `opening_stock - units_sold` does not
always equal `closing_stock`. We checked all 2,350 mismatched rows by hand:
- **1,810 rows** have `closing_stock > opening_stock - units_sold` and every
  one of them has `excess_stock_flag = True` -- same-day replenishment on the
  intentionally-elevated-stock days.
- **540 rows** have `closing_stock == 0` despite `opening_stock - units_sold > 0`,
  and every one of them is a TV SKU (P0021-P0024) -- the stockout scenario
  clamps `closing_stock` to 0 to simulate "no more available to sell that day"
  rather than leaving a small residual balance. This is intentional dataset
  design, confirmed by cross-checking against `stockout_flag`, not a
  generation defect.

## employees.csv (90 rows)

`employee_id` (PK), `employee_name`, `store_id` (FK), `role` (Sales Associate / Senior Sales Associate / Store Manager). **No sales are attributed to individual employees anywhere in the dataset** -- `employee_store_performance()` reports store-level aggregates plus headcount, and says so explicitly in its output, rather than inventing an individual attribution the data doesn't support.

## targets.csv (54 rows: 9 stores x 6 months)

`month` (YYYY-MM), `store_id`, `revenue_target`, `gross_profit_target`, `on_time_delivery_target_pct`, `return_rate_target_pct`.
