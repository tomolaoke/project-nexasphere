# Business Impact

## The workflow this replaces

**Before:** A manager suspects something is off (e.g. revenue is up but the
bank balance doesn't feel like it). They open the sales spreadsheet, filter
by date, manually compute two period totals, open the products sheet to
check category mix, open the returns log, open the delivery tracker, and
try to mentally connect all of it into a story — a process that easily
takes 30-60+ minutes per question, repeated every time a new question comes
up, and is only as good as which spreadsheets the manager remembers to
check.

**With Ordino:** The manager opens one screen and sees the ranked
findings immediately (computed in under a second from the full dataset), or
types the question directly and gets a grounded answer in seconds.

## Concrete findings this system surfaces automatically

From the current dataset, computed live (not hard-coded):

- Revenue grew **+63.2%** over the last 30 days, but gross profit grew only
  **+53.8%** — a **-1.45 percentage point** margin decline hiding under
  apparently strong top-line growth.
- **Audio** has a return rate of **12.77%** of units sold (891 units,
  ₦294,656.64 refunded) — **2.28 standard deviations** above the category
  average, driven primarily by "Not as Expected" returns.
- **UrbanMove (DP04)** has a **34.0%** delayed-delivery rate versus **~7.8%**
  average across the other four delivery partners, with a materially lower
  customer rating.
- Inventory is imbalanced: TVs have the most stockout-days while Air
  Conditioners carry the most excess-stock-days across affected
  store/product pairs — too little of what's in demand, too much of what
  isn't, at the same time.
- **Summer Cooling** is the strongest marketing campaign by ROI (**5.71x**),
  meaning further validated investment there is more defensible than in
  weaker campaigns.

Each of the above would otherwise require a manager to independently notice
the signal, pull the right two or three spreadsheets, and manually compute
the comparison — this system does all of it on every page load.

## Who benefits and how

- **Operations managers** get an early warning on delivery-partner and
  inventory problems before they become customer complaints.
- **Commercial/finance managers** get the profitability-vs-revenue signal
  immediately instead of discovering it at month-end reconciliation.
- **Category managers** get a return-rate outlier flagged with the specific
  return reason driving it, rather than an aggregate return percentage that
  hides which category and which reason matter.

## Why this generalizes beyond Ordino

The underlying pattern — join disparate operational datasets, compute
verified KPIs, rank findings by statistical deviation, explain in plain
language, recommend investigation — is not retail-specific. The same
architecture applies to any organisation that already has structured
operational data but lacks the analyst time to connect it: e-commerce,
logistics, manufacturing, financial services, or SaaS operations.
