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