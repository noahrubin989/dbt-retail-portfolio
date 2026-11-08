# Design: dbt Retail Portfolio

Store: a Walmart-style retailer that sells anything, with physical shops and a web channel. All data is synthetic.

## Fact table: `fact_sales`

**Grain:** one row per product on an order line, with returns recorded as separate negative rows.

**Columns**
- `order_id` (degenerate dimension, no dimension table behind it)
- `customer_key`
- `product_key`
- `store_key`
- `payment_method_key`
- `date_key`
- `quantity`
- `unit_price`
- `line_amount` (= quantity x unit_price)

**Returns:** a return is a new row with negative `quantity` and negative `line_amount`. It keeps the original `unit_price` and the original `order_id`, and has its own `date_key`. The original sale row is never edited.

Example: 2 kettles at $40 bought on Monday, 1 returned on Tuesday.

| order_id | date | product | quantity | unit_price | line_amount |
|---|---|---|---|---|---|
| 2001 | Monday | kettle | 2 | 40 | 80 |
| 2001 | Tuesday | kettle | -1 | 40 | -40 |

## Dimensions

| Table | Primary key |
|---|---|
| `dim_customer` | `customer_key` |
| `dim_product` | `product_key` |
| `dim_store` | `store_key` |
| `dim_payment_method` | `payment_method_key` |
| `dim_date` | `date_key` |

A different brand or model is a different product, so it gets its own row in `dim_product`. Brand is a column there.

## Design decisions

**Web orders:** the web channel is a row in `dim_store` with `store_type = 'online'`. Physical shops have `store_type = 'physical'`.

**Walk-in (guest) sales:** `dim_customer` contains a placeholder row with `customer_key = -1` and name "Guest". Every walk-in sale points to it, so `customer_key` is never null on `fact_sales`.

Why not leave `customer_key` null:
- A null never matches in a join, so an inner join to `dim_customer` would silently drop walk-in sales and understate revenue.
- With the placeholder, every fact row has a valid key. Guest sales are easy to isolate (`customer_key = -1`) or exclude (`<> -1`).
- dbt tests like `not_null` and `relationships` on `customer_key` can stay strict and catch real data problems.

Since `dim_customer` became type 2, its key is a string, so the Guest key is `'-1'`.

## Customer history (SCD type 2)

Customers change: they get a new email or opt out of marketing. If `dim_customer` only held today's values, old sales would be reported against the customer as they are now, not as they were. So `dim_customer` keeps one row per version of a customer, and each sale points at the version that was valid when it happened.

**Snapshot.** `snp_customers` records `raw.customers` with the `timestamp` strategy: when a customer's `updated_at` is newer than the stored version, dbt closes the old version (`dbt_valid_to`) and inserts a new one. The current version has `dbt_valid_to = 9999-12-31` instead of null, so date-range joins need no null handling.

**The snapshot reads raw, not staging.** It records what the source said. Cleaning happens afterwards, in `stg_customers`, which reads the snapshot. If the cleaning logic changes, every version gets cleaned again on the next build. Had we snapshotted the staging model, old versions would keep the old cleaning forever.

**A snapshot can't be rebuilt.** Models can be dropped and rebuilt from raw at any time. The snapshot can't, because the source overwrites its rows and the old values exist nowhere else. Rerunning `generate_data.py` resets raw but leaves the history intact.

**Simulated history.** The source data is a single load, so `scripts/simulate_next_load.py` plays the next one: 40 customers change their email, their marketing opt-in, or both, between 19 and 25 October 2026, and place new web orders afterwards. That gives 540 versions of 500 customers, and sales on both sides of each change.

**Keys.** `customer_id` repeats across versions, so `customer_key` is `dbt_utils.generate_surrogate_key(['customer_id', 'valid_from'])`, a hash per version. It uses the version's original `valid_from` (see below), so the key does not depend on the 1900 rule. `customer_id` stays in the dimension as the customer's identity across versions.

**First versions start in 1900.** With the timestamp strategy, a first version starts at the customer's last `updated_at` before snapshotting began, not when they became a customer. 1,929 order lines were placed before their customer's first version and would have matched nothing. A customer's first version is therefore extended back to 1900-01-01. This assumes the oldest values we have are also the best we know for the time before them.

**Point-in-time join.** `fact_sales` joins on `customer_id` and `valid_from <= transaction_timestamp < valid_to`. The range is half-open: an old version ends at the exact moment the new one starts, so a sale at that moment matches only the new version. `mutually_exclusive_ranges` tests that each customer's versions have no gaps or overlaps, which is what guarantees exactly one match per sale.

**Returns use the return time.** A return gets the customer version valid on its return date, the same rule as its `date_key`. Each fact row describes the customer as they were when that event happened.

**Only a null `customer_id` goes to Guest.** Walk-ins map to `'-1'`. A real customer who matched no version is left null rather than sent to Guest, so the `not_null` test on `customer_key` fails instead of the problem being hidden.

Example: customer 24 opted out of marketing on 2026-10-23 14:48:41.

| customer_key | customer_id | valid_from | valid_to | is_current | fact rows |
|---|---|---|---|---|---|
| `b29a5306…` | 24 | 1900-01-01 | 2026-10-23 14:48:41 | false | 63 sales, 3 returns |
| `f4cc2196…` | 24 | 2026-10-23 14:48:41 | 9999-12-31 | true | 2 sales |