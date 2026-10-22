# Project 1 Report: Integrated Inventory and Analytics System

## 1. Data loading
- Dataset: Amazon Sale Report, 128,975 rows loaded, 0 skipped, 7,795 repaired.
- The unnamed trailing column is dropped explicitly by checking the header for blank names.
- Missing Amount: row kept with Amount set to 0.0 and logged as a warning. Cancelled orders legitimately have no amount, and the cancellation analysis needs them.
- Missing or invalid Qty and malformed dates: row skipped and logged with line number and reason.
- Date coverage: 2022-03-31 to 2022-06-29 (about three months, not a full year). March contains a single day.

## 2. Assumptions
- Cancelled orders keep an Amount in the data but have Qty 0, so they are excluded from all sales totals.
- "Product" means SKU in the top-products analysis.
- The hash-index and promotion analyses count distinct Order IDs.

## 3. Analysis results
TODO: paste the main numbers from test_analysis.py (top products, state and city totals, status counts, category totals, top orders).

### Order value and CLV (item 5)
Order ID identifies a transaction, not a person, so only order-level value is computed. A true Customer Lifetime Value needs a customer identifier (for example a Customer ID or buyer account ID) so that several orders can be linked to one person over time. The dataset has no such field.

### Cancellations as a stockout proxy (item 6)
- Overall baseline: 18,427 of 128,975 order lines (about 14.3%) are cancelled by Status or Courier Status.
- Assumption: a high cancellation rate on one SKU may signal a stockout. The data records that an order was cancelled, not why.
- SKUs with fewer than 30 orders are ignored, because a rate on a handful of orders is unreliable.
- Highest: JNE3608-KR-L at 59.4% (19 of 32), about four times the baseline.
- To confirm: stock levels per SKU over time, and a cancellation reason or initiator (seller or customer).

### Seasonal patterns (item 7)
- Monthly lines: April 41,930, May 36,166, June 32,394 (about 23% decline from April to June).
- With only three months of data, quarter analysis is not meaningful (Q1 has one day) and peak months mostly reflect April being the first full month.

### Inventory turnover (item 8)
- No stock levels exist. Proxy: average stock = peak monthly Qty for that SKU, on the assumption that the seller holds enough stock to cover its busiest month. Turnover = total Qty / peak monthly Qty.
- With three full months, the maximum possible ratio is 3.00. Several SKUs reach it, so the ratio here measures how steady demand is (near 3 = steady, near 1 = one-month spike), not how quickly stock sells.

### Promotions (item 9)
- Top promotion: IN Core Free Shipping, on 41,982 orders.
- Three AAT-... promotions have identical order counts and sales, so they are always applied together and behave as one bundle.
- An order with several promotions counts under each one, so promotion totals overlap and must not be added together.

## 4. Algorithms (item 10)
TODO: written answers, added as the algorithm code is wired in.

## 5. Visualization
TODO

## 6. How to run
See README.md.