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