## customers

One row per customer.

| column | type | notes |
|---|---|---|
| customer_id | integer | primary key |
| first_name | text | |
| last_name | text | |
| email | text | |
| mobile_number | text | includes dial code |
| marketing_opt_in_flag | text | mixed values, see below |
| email_verified_flag | text | mixed values, see below |
| sex | text | |
| created_at | timestamp | |
| updated_at | timestamp | |

**Messy on purpose:**
- Inconsistent casing and stray leading/trailing whitespace in text columns (names, email, sex).
- Flags mix `true`/`false`, `yes`/`no` and `1`/`0`.

## products

One row per product the store sells.

| column | type | notes |
|---|---|---|
| product_id | integer | primary key |
| product_name | text | |
| brand | text | |
| product_category | text | |
| product_subcategory | text | |
| created_at | timestamp | |
| updated_at | timestamp | |

**Messy on purpose:** Inconsistent casing and stray whitespace in `product_category` and `product_subcategory` (e.g. `Kitchen`, `kitchen `).

## stores

One row per store, including the web channel.

| column | type | notes |
|---|---|---|
| store_id | integer | primary key |
| store_name | text | |
| store_type | text | 'physical' or 'online' |
| city | text | null for the online store |
| state | text | null for the online store |
| opened_date | date | |
| created_at | timestamp | |
| updated_at | timestamp | |

**Messy on purpose:** Inconsistent casing and stray whitespace in text columns (e.g. `Sydney`, `sydney `, `PHYSICAL`).


One row per order (the header). Products are in order_lines.

| column | type | notes |
|---|---|---|
| order_id | integer | primary key |
| customer_id | integer | null for walk-in sales |
| store_id | integer | which store or web channel |
| payment_method_id | integer | how it was paid |
| order_timestamp | timestamp | when the sale happened |
| created_at | timestamp | |
| updated_at | timestamp | |

**Messy on purpose:**
- Some `store_id` or `payment_method_id` values are null, which shouldn't happen. These are for dbt tests to catch.
- `customer_id` is null for walk-in sales, which is expected and gets mapped to the Guest customer.
- A few duplicate `order_id` rows, so staging has something to deduplicate (optional).


## order_lines

One row per product on an order.

| column | type | notes |
|---|---|---|
| order_line_id | integer | primary key |
| order_id | integer | links to orders |
| product_id | integer | links to products |
| quantity | integer | negative for returns (to be decided) |
| unit_price | decimal | price per unit at time of sale |
| created_at | timestamp | |
| updated_at | timestamp | |

**Messy on purpose:**
- A few `order_id` values in `order_lines` don't exist in `orders` (orphan lines). A dbt `relationships` test catches these.
- Some `unit_price` values are stored as text with a currency symbol (e.g. `$40.00`), so staging has to clean and cast them.

## returns

One row per returned product line.

| column | type | notes |
|---|---|---|
| return_id | integer | primary key |
| order_line_id | integer | the original line being returned |
| quantity_returned | integer | positive; dbt flips the sign later |
| return_timestamp | timestamp | when the return happened |
| created_at | timestamp | |
| updated_at | timestamp | |

**Messy on purpose:**
- A few `order_line_id` values don't exist in `order_lines` (orphan returns). A `relationships` test catches these.
