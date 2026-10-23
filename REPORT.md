# Project 1 Report: Integrated Inventory and Analytics System

**Course:** CSQ242 Work Integrated Training-I
**Dataset:** Amazon Sale Report (CSV)
**Constraints followed:** no pandas or numpy, no `csv` module, no SQL, all data held in memory using core Python data structures. matplotlib is used for drawing only.

---

## 1. Overview and design

The system loads the Amazon Sale Report into memory as `Order` objects, controls who may read or change them through user roles, answers sales and inventory questions with algorithms written from scratch, and draws charts from the computed results.

### 1.1 Files (all in `src/`)

| File | Purpose |
|---|---|
| `order.py` | `Order` class: one line item, with validated setters |
| `order_manager.py` | `OrderManager`: loads the CSV, role checks, add/edit/delete, search, sort |
| `users.py` | `UserManager`, `User`, roles, login errors |
| `algorithms.py` | Linear search, binary search, hash index, quick sort, merge sort, heap top-N |
| `analysis.py` | Part 3 items 1-5 (top products, location, status, category, order value) |
| `analysis_advanced.py` | Part 3 items 6-9 (cancellations, seasonality, turnover, promotions) |
| `indexing.py` | Order-ID binary search and SKU / ship-city hash indexes |
| `charts.py` | The four matplotlib charts |

### 1.2 Object-oriented design

- **Encapsulation:** `Order` keeps identifiers (index, Order ID, SKU) read-only and exposes the mutable fields (date, status, quantity, amount) through properties that reject invalid values, for example a negative quantity. `User` is read-only after login, so a role cannot be changed once authenticated.
- **Inheritance:** `OrderManager` inherits from `AnalysisMixin`, `AdvancedAnalysisMixin` and `IndexMixin`. This keeps each file small while every analysis method still belongs to `OrderManager` and goes through the same permission check.
- **Custom exceptions:** `PermissionDenied` and `AuthenticationError` give clear, specific failures instead of silent ones.

### 1.3 Roles and access control

- Passwords are never stored in plain text. Each is stored as a SHA-256 hash with a random salt. A wrong username and a wrong password return the same message, so a login attempt does not reveal which usernames exist.
- Every public `OrderManager` method begins with `_require(user, allowed_roles)`:
  - **Manager:** add, edit, delete, plus everything a Junior Manager can do.
  - **Junior Manager:** search (Order ID, Status, Category, ship-city), sort (Date, Amount, Qty) and all analyses. May not add, edit or delete.
  - **Unauthenticated:** nothing. Any violation raises `PermissionDenied`.
- `load_orders` is deliberately not role-gated: it runs once at startup, before any user logs in.
- Editing is limited to a fixed list of fields (status, qty, amount, date, courier status, ship-city, ship-state). Identifiers cannot be edited.

---

## 2. Data loading

- **Result:** 128,975 rows loaded, 0 skipped, 7,795 repaired.
- **Parsing:** the file is read line by line. A small function, `split_csv_line`, splits on commas while respecting quoted fields, since some values contain commas inside quotes.
- **Trailing unnamed column:** handled explicitly. Any column whose header is blank is dropped by position, instead of relying on the parser to ignore it.
- **Missing Amount:** the row is kept with Amount set to 0.0 and logged as a warning. Cancelled orders legitimately have no amount, and the cancellation analysis needs those rows.
- **Missing or invalid Qty, or a malformed date:** the row is skipped and recorded with its line number and the reason.
- **Date format:** several formats are tried in turn (`mm-dd-yy`, `mm-dd-yyyy`, `yyyy-mm-dd`).
- **Date coverage:** the data runs from 2022-03-31 to 2022-06-29, about three months and not the full year the brief describes. March contains a single day.
- **Skip log test:** TODO: describe the test with deliberately broken rows (the real file produced no skips, so this shows the logging works).

---

## 3. Assumptions

- **Cancelled orders are not sales.** They keep an Amount in the data but have Qty 0, so they are excluded from every sales total. They are included in status counts and in the cancellation analysis.
- **"Product" means SKU** in the top-products analysis, since SKU identifies a specific product variant.
- **Order-level counts use distinct Order IDs**, because one order can contain several line items.
- **Search is case-insensitive** and ignores surrounding spaces, so "mumbai" and "MUMBAI" find the same orders.

---

## 4. Analysis results

TODO: paste the main numbers from `test_analysis.py`: top 5 SKUs by amount and by quantity, totals for a chosen city and state, orders per status, total amount and quantity per category, and the top 5 orders by value.

### 4.1 Order value and why CLV cannot be computed (item 5)

The dataset has no customer identifier, and Order ID identifies a transaction, not a person. Only order-level value is computed: the sum of Amount over all line items sharing an Order ID. A true Customer Lifetime Value needs a field such as a Customer ID or buyer account ID, so that several orders can be linked to one person over time.

### 4.2 Cancellations as a stockout proxy (item 6)

- **Definition:** an order counts as cancelled if its Status or its Courier Status mentions cancellation.
- **Baseline:** 18,427 of 128,975 order lines (about 14.3%) are cancelled.
- **Assumption:** a high cancellation rate on one SKU may signal a stockout. The data records that an order was cancelled, not why, so a customer-initiated cancellation cannot be told apart from a seller-side stockout.
- **Reliability filter:** SKUs and styles with fewer than 30 orders are ignored, because a rate based on a handful of orders is unreliable (a SKU with 1 order and 1 cancellation would show 100%).
- **Highest SKUs:** JNE3608-KR-L at 59.4% (19 of 32), SET375-KR-NP-M at 48.6% (17 of 35), JNE3364-KR-1051-A-M at 43.3% (13 of 30). The top SKU is about four times the baseline.
- **Highest styles:** JNE3608 at 36.4% (28 of 77), JNE3408 at 32.6% (15 of 46), J0350 at 30.2% (13 of 43).
- **To confirm a stockout:** stock levels per SKU over time, and a cancellation reason or initiator (seller or customer).

### 4.3 Seasonal patterns (item 7)

- **Monthly order lines:** April 41,930, May 36,166, June 32,394, a decline of about 23% from April to June. March has 153 lines because only its last day is present.
- **Quarters:** Q1 holds one day of data and Q2 holds everything else, so the quarterly view says almost nothing.
- **Peak months:** most categories peak in April (kurta, Set, Bottom, Saree, Blouse), Top, Western Dress and Ethnic Dress peak in May, and Dupatta in June. Because April is the first full month, this mainly reflects the overall decline over the period. Three months of data can describe a trend but cannot establish seasonality.

### 4.4 Inventory turnover (item 8)

- **Proxy:** the dataset has no stock levels, so average stock is taken as the peak monthly Qty for that SKU. The assumption is that a seller holds enough stock to cover its busiest month. Turnover = total Qty sold / peak monthly Qty.
- **Interpretation:** with three full months, the maximum possible ratio is 3.00 (equal sales every month). Several SKUs reach exactly 3.00, so here the ratio measures how steady demand is (near 3 means steady, near 1 means a one-month spike), not how quickly stock sells.
- **Filter:** SKUs with fewer than 20 units sold in total are ignored.

### 4.5 Promotions (item 9)

- The `promotion-ids` field can hold several identifiers per order. It is split on commas.
- **Most widespread promotion:** "IN Core Free Shipping", on 41,982 orders, with sales of 31,868,206.
- Three "Amazon PLCC Free-Financing" promotions (the AAT-... identifiers) have identical order counts (29,158) and sales (21,067,951). They are always applied together and behave as one bundle.
- The most affected categories for every top promotion are Set, kurta and Western Dress.
- An order with several promotions counts under each one, so promotion totals overlap and must not be added together.

---

## 5. Algorithms (item 10)

Each answer names where the code lives (all in `src/`).

**1. Linear search for "Cancelled" (implemented).**
`linear_search` in `algorithms.py` checks every order and keeps those that pass a test. `find_cancelled` in `OrderManager` calls it with the test "status equals Cancelled".

**2. Linear search complexity.**
O(n): in the worst case every one of the n orders is checked. It becomes inefficient at scale because the work grows in step with the data. With 128,975 orders every query scans all of them, and if the data grows tenfold, each query takes tenfold longer. Many queries multiply the cost.

**3. Preparing data for binary search by Order ID.**
Binary search only works on sorted data. Sort the orders by Order ID once (merge sort, O(n log n)) and keep that sorted list. After that each lookup costs O(log n). The sorted list must be rebuilt whenever an order is added, edited or deleted (the code clears its cached indexes after every change). One Order ID can have several line items, so after finding the first match, walk right while the ID still matches (`find_by_order_id`).

**4. Binary search for an order on a given date, then replace that date.**
1. Sort the orders by date.
2. Set `low` to 0 and `high` to the last position.
3. Take the middle item. If its date equals the target, record it and keep searching left for the first match. If the middle date is earlier than the target, move `low` to `mid + 1`. If it is later, move `high` to `mid - 1`.
4. Repeat until `low` passes `high`.
5. From the first match, walk right to collect every order on that date, since many orders share a date.
6. For the order to change, assign the new date through the validated setter (`order.date = new_date`).
7. The sorted list is now out of order for that item, so remove and re-insert it at the correct place, or rebuild the sorted list.

**5. How a hash table improves SKU search.**
A hash table (a Python `dict`) turns the SKU into a storage position with a hash function and jumps straight to it, instead of scanning. It is built once: SKU maps to the list of orders with that SKU. Lookup is O(1) on average, compared with O(n) for linear search. See `HashIndex` and `find_by_sku`.

**6. Hash index on ship-city, and retrieving MUMBAI.**
One pass over all orders builds a dict where the key is the city (trimmed and upper-cased, so "Mumbai" and "MUMBAI" match) and the value is the list of orders shipped there. To get the MUMBAI orders, look up the key "MUMBAI" and receive the whole list at once (`find_by_city`).
*Measured on this dataset:* a linear scan for MUMBAI took 0.0215 s and returned 7,122 orders. The hash lookup returned the same 7,122 orders in a time too small for Python's timer to register (it printed 0.000000 s). The same comparison by Order ID gave 0.0325 s for linear search against an unmeasurably small time for binary search, with identical results.

**7. Drawbacks of hash tables in this context.**
- Extra memory for the index.
- It costs O(n) to build, and must be updated or discarded after every add, edit or delete (the code does this with `_invalidate_indexes`).
- Exact matches only: no range queries such as "orders between two dates", and no sorted order.
- Keys must be cleaned first (case, spaces), or lookups miss.
- Collisions can slow lookups, and in the worst case degrade toward O(n).

**8. How quick sort orders records by Amount.**
Pick a pivot Amount. Split the orders into three groups: smaller than the pivot, equal to it, and larger than it. Sort the smaller and larger groups the same way (recursion), then join them as smaller + equal + larger. Recursion stops when a group has 0 or 1 items.

**9. Quick sort complexity.**
Average case O(n log n). Worst case O(n²), when pivots keep landing at an extreme (for example always the smallest value), so one group holds nearly everything each time. This implementation picks a random pivot and uses a three-way split, so many identical keys (very common in Qty) do not trigger the worst case.

**10. Quick sort by Qty (implemented), step by step.**
`quick_sort(items, key)` in `algorithms.py`, called as `quick_sort(orders, key=lambda o: o.qty)`.
1. If the list has 0 or 1 items, it is already sorted: return it.
2. Choose a random item and take its Qty as the pivot.
3. Walk through every order once. Qty below the pivot goes to `less`, above goes to `greater`, equal goes to `equal`.
4. Recursively sort `less` and `greater`.
5. Return sorted `less`, then `equal`, then sorted `greater`.

It builds new lists instead of sorting in place, so it uses O(n) extra memory.

**11. Why merge sort is stable, and why that matters for Date then Order ID.**
Stable means orders with equal keys keep their original relative order. In `_merge`, when two items have equal keys, the one from the left half is taken first, which preserves their order. To sort by Date with ties ordered by Order ID, first sort by Order ID, then sort by Date using the stable sort. Orders on the same date then remain in Order ID order. An unstable sort could shuffle them.

**12. Merging two sorted sublists by Category.**
Keep one pointer at the start of each list. Compare the two current Categories and append the smaller one to the result, advancing that list's pointer (on a tie, take from the left list). When one list runs out, append the rest of the other. Each item is touched once, so the cost is O(n + m). This is the `_merge` function in `algorithms.py`.

**13. How heap sort finds the top N orders by Amount, and why it is reasonable.**
Keep a min-heap of size N, where the smallest of the current top N sits at the root. For each order, if its Amount is larger than the root, replace the root with it and restore the heap (sift down). Otherwise ignore it. At the end the heap holds the N largest orders, and repeatedly moving the root to the end puts them in order. The cost is about O(m log N) for m orders. It is a good fit because N is small: there is no need to sort all 128,975 orders, and memory use is only O(N). See `heap_top_n`.

**14. Space complexity: heap sort versus merge sort.**
Heap sort works in place, using O(1) extra space. Merge sort needs a temporary list for merging, so it uses O(n) extra space. In the top-N heap used here, the extra space is O(N).

**15. Search method for orders from a ship-state in an unsorted list.**
Linear search. Binary search needs sorted data, and sorting first (O(n log n)) costs more than a single O(n) scan. If many state queries are expected, build a hash index on ship-state once and reuse it.

**16. Sorting algorithm for the top 5 products by Qty.**
Total the Qty per product, then use heap-based top-N selection with N = 5. Only the 5 largest are needed, so a full sort is unnecessary work. If a fully ranked list were needed, merge sort would be the choice.

**17. Combining binary search and hash lookup: Order ID, then Status.**
Binary search on the list sorted by Order ID finds the few line items of that order in O(log n). A hash index on Status over that small group then returns only those with the wanted Status (`find_by_order_id_and_status`). For a group this small, a simple loop would work equally well. The point is the pattern: narrow down with a fast search, then filter.

---

## 6. Visualization

All four charts are drawn with matplotlib from numbers computed by this project's own code, and saved in `charts/`.

| Chart | File | Source |
|---|---|---|
| Bar chart: total sales by ship-state (top 15) | `charts/sales_by_state.png` | `totals_by_group` |
| Pie chart: distribution of order Status (slices under 2% merged into "Other") | `charts/status_pie.png` | `status_counts` |
| Bar chart: total sales by Category | `charts/sales_by_category.png` | `category_totals` |
| Line chart: sales by month, month taken from Date | `charts/sales_over_time.png` | `volume_by_month` |

TODO: add one or two sentences of observation per chart after looking at the images (for example the leading states, and any state names spelled in several ways). The line chart shows a very small March point because only one day of March is in the data.

---

## 7. Interface

TODO: describe the CLI once it is built (login, role-based menu, results, and the summary of skipped and repaired rows shown after loading).

---

## 8. How to run

See `README.md`.