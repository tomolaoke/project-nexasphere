# Sample Inputs and Outputs

Real outputs from the running system. Every figure below is produced by
`nexasphere.analytics`; the AI layer only rephrases them.

---

## 1. The hero question

**Input:** *"Is revenue growth leading to stronger profitability?"*

**Matched intent:** `growth_vs_profitability`

**Answer (AI-narrated, grounded):**

> No, revenue has surged 63.2% in the past month, yet gross profit only rose
> 53.8%, and the margin fell by 1.45 percentage points. Thus, revenue growth is
> outpacing profit growth.

**Evidence (excerpt):**

```json
{
  "window_days": 30,
  "latest_period":   { "revenue": 11758775.24, "gross_profit": 2803150.39, "margin_pct": 23.84 },
  "previous_period": { "revenue": 7203316.72,  "gross_profit": 1822063.05, "margin_pct": 25.29 },
  "change": { "revenue_pct": 63.2, "gross_profit_pct": 53.8, "margin_pp": -1.45 },
  "margin_pressure": true
}
```

---

## 2. Suggested business questions (all nine from the case study)

| Input | Intent | Output (deterministic) |
|---|---|---|
| Which products, stores or regions generate the most revenue and profit? | `revenue_profit_leaders` | By region, **West** generates the most revenue (16,234,729.09) and 4,187,371.03 gross profit (25.79% margin). |
| Is revenue growth leading to stronger profitability? | `growth_vs_profitability` | No. Revenue +63.2%, gross profit +53.8%, margin −1.45 pp. |
| Which products have unusually high return rates? | `returns_by_category` | **Audio** has the highest return rate at 12.77% of units sold (891 units, 294,656.64 refunded). |
| Which marketing campaigns generate the best return on investment? | `marketing_roi` | **Summer Cooling** — 5.71x ROI (spend 38,000.00, attributed revenue 255,000.00). |
| Which stores are experiencing stockouts or excess inventory? | `inventory_imbalance` | **TVs** carry the most stockout-days (456 across 12 store/product pairs); **Air Conditioners** the most excess-stock-days (1,810 across 10). |
| Which delivery partners are associated with delays or poor customer ratings? | `delivery_partner_performance` | **UrbanMove** — 34.0% delayed-delivery rate, average rating 4.38/5. |
| Which customer segments are the most valuable? | `customer_segment_value` | Ranked by revenue, margin and revenue per customer. |
| Which employees perform well based on both revenue and profitability? | `employee_store_performance` | Store-level revenue per employee, with an explicit note that sales are recorded per store, not per individual. |
| Where is the business failing to meet its targets? | `target_attainment` | For 2026-06 all 9 stores met target; lowest attainment named. |

---

## 3. Informal and Nigerian Pidgin

**Input:** *"Sales dey go up, profit dey follow?"* → `growth_vs_profitability`

**Answer:**

> No, revenue don climb 63.2% but gross profit only rise 53.8%, and margin drop
> by 1.45 percentage points.

Same intent, same verified numbers, answered in the user's own register.

Other phrasings that resolve to the same intent: *"Are we making more money?"*,
*"Is our profit keeping pace with revenue?"*, *"Sales are up. Did profitability
improve?"*

---

## 4. Meta question

**Input:** *"What questions can I ask?"* → `meta_capabilities`

**Output:** a grouped menu (Performance & profitability, Customers, Products &
returns, Operations, Marketing, People) with example questions.

> Previously this fell through to a KPI dump. Answering a question *about the
> assistant* with unrelated revenue totals is a bug, not a graceful fallback.

---

## 5. Refusals — the honesty cases

| Input | Intent | Output |
|---|---|---|
| "What is the capital of France?" | `out_of_scope` | *"I'm focused on helping you understand your business data…"* — no numbers. |
| "What is the meaning of life?" | `fallback_unmatched` | *"I couldn't match that to one of the business analyses…"* — no numbers. |
| "Which delivery partner performs worst?" *(on an uploaded dataset with no delivery data)* | `unsupported` | *"I can't answer that from this dataset…"* plus the columns that would be needed. |

---

## 6. Analyze My Business — a non-NexaSphere schema

**Input file** `bella_sales.csv` (10 rows):

```csv
transaction_date,sales_amount,cost,product_name,customer_id,region
2026-01-05,100,60,Jollof Mix,C001,Lagos
2026-01-12,150,90,Pepper Sauce,C002,Abuja
...
```

**Detected mapping** (user-confirmable, each dropdown filtered by type):

```
date → transaction_date      product  → product_name
revenue → sales_amount       customer → customer_id
cost → cost                  region   → region
```

**Capability matrix:** supports 5 of 9 — Revenue trend, Profitability, Product
performance, Customer analysis, Regional/store performance. Not detected:
Category breakdown, Returns, Marketing ROI, Employee performance.

**Computed output:** Total revenue 2,090.00 · Total profit 1,080.00 · Margin
51.67% · 10 records · data window 2026-01-05 → 2026-04-08.

**Finding:** *Revenue vs. Profit Growth* (WARNING) with its evidence and a
recommendation.

**Charts generated from these columns:** revenue over time (area), margin over
time (line), period-on-period change (bar), top products and top customers
(horizontal bars), revenue share by region (donut), transaction-value
distribution (histogram), revenue-vs-margin (scatter).

---

## 7. Grounding rejection (adversarial)

Given evidence stating UrbanMove's delayed rate is 34.0%:

| Model output | Verdict |
|---|---|
| "Revenue increased 90%" (actual 63.2%) | **Rejected** — number absent from evidence |
| "SwiftShip has a 34.0% delay rate" | **Rejected** — 34.0% belongs to a different entity |
| "UrbanMove has a 34.0% delay rate" | Accepted |

On rejection the deterministic template is shown and labelled as such. Covered
by tests in [test_analytics.py](../tests/test_analytics.py).
