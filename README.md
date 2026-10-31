# Retail analytics with dbt Core and DuckDB

A dbt Core project that turns raw retail data (customers, products, stores, orders, order lines, returns, payment methods) into a star schema for analytics. It covers layered modelling, data quality testing, handling of bad source data, and enforced model contracts.

## Stack

- dbt Core 1.12.6 with dbt-duckdb 1.11.0
- DuckDB (local database file)
- Python 3.12

## Project layout

```
retail_dbt/
  models/
    staging/        1:1 cleaned views of each source (7 models)
    intermediate/   joined, business-ready building blocks (2 models)
    marts/          star schema tables with enforced contracts (6 models)
  macros/           reusable SQL (date_to_key)
  tests/            singular tests
  analyses/         ad hoc queries, compiled but not materialised
docs/
  design.md         design decisions and fact table grain
```

## Data flow

| Layer | Materialised as | Schema | What happens |
|---|---|---|---|
| Staging | view | `staging` | Text trimmed and lowercased, flags typed as booleans, prices cast to decimal, exact duplicate orders removed |
| Intermediate | view | `intermediate` | Order lines joined to orders; returns joined to their original line with quantity made negative |
| Marts | table | `marts` | Five dimensions and one fact table |

## The star schema

`fact_sales` has one row per sale line plus one row per return, with returns stored as negative rows. This lets `sum(line_amount)` give net revenue directly. `order_id` is kept as a degenerate dimension.

Dimensions: `dim_customer`, `dim_product`, `dim_store`, `dim_payment_method`, `dim_date`.

The web channel is modelled as a store with `store_type = 'online'`.

## Design decisions

- **Grain.** A return reuses the `order_line_id` of the sale it reverses, so that column is not unique. A row is identified by `transaction_type` + `order_line_id` + `return_id`, checked by `tests/assert_fact_sales_grain_is_unique.sql`.
- **Guest and Unknown members.** Walk-in sales (null `customer_id`) map to a Guest row with key `-1` in `dim_customer`. Orders with a null store or payment method map to an Unknown row with key `-1` in `dim_store` and `dim_payment_method`. No fact row has a null foreign key, and no revenue is dropped.
- **Returns land on the return date.** `date_key` for a return comes from `return_timestamp`, not the original sale date.
- **Dimension keys equal source ids**, so the fact table carries keys without joining to the dimensions. `relationships` tests prove every key resolves.
- **`dim_date` is generated**, not loaded: one row per day from 2020-01-01 to 2075-12-31.
- **One definition of the date key.** The `date_to_key` macro builds the `yyyymmdd` integer for `dim_date` and both halves of `fact_sales`.
- **Contracts.** All six marts enforce column names and types, so upstream changes can't silently alter the public interface.

## Data quality

A full `dbt build` runs 156 tests and finishes with `PASS=148 WARN=8 ERROR=0`. The 8 warnings are deliberate: the source data was seeded with defects, and they are reported in staging and intermediate and resolved before the marts.

| Test | Rows | Handled by |
|---|---|---|
| `stg_orders` null `store_id` | 20 | Mapped to Unknown (-1) in `fact_sales` |
| `stg_orders` null `payment_method_id` | 20 | Mapped to Unknown (-1) in `fact_sales` |
| `stg_order_lines` orphan `order_id` | 25 | Dropped by inner join in `int_order_lines_joined` |
| `stg_returns` orphan `order_line_id` | 10 | Dropped by inner join in `int_returns_signed` |
| Null `store_id` / `payment_method_id` carried into the intermediate models | 44 / 50 lines, 3 / 3 returns | Mapped to Unknown (-1) in `fact_sales` |

Result: `fact_sales` has 46,605 rows (44,048 sales and 2,557 returns). Mart tests produce no warnings.

## Running it

```
git clone https://github.com/noahrubin989/dbt-retail-portfolio.git
cd dbt-retail-portfolio
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install dbt-core==1.12.6 dbt-duckdb==1.11.0
cd retail_dbt
dbt build
```

## Docs and lineage

```
dbt docs generate
dbt docs serve
```