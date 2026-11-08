# Retail analytics with dbt Core and DuckDB

A dbt Core project that turns raw retail data (customers, products, stores, orders, order lines, returns, payment methods) into a star schema for analytics. It covers layered modelling, data quality testing, handling of bad source data, enforced model contracts, and customer history as a type 2 slowly changing dimension built on a dbt snapshot.

## Stack

- dbt Core 1.12.6 with dbt-duckdb 1.11.0
- dbt_utils 1.4.1 (generic tests and `date_spine`)
- DuckDB (local database file)
- Python 3.12

## Project layout

```
retail_dbt/
  snapshots/        snp_customers: history of raw.customers
  models/
    staging/        cleaned views of each source (7 models); stg_customers reads the snapshot
    intermediate/   joined, business-ready building blocks (2 models)
    marts/          star schema tables with enforced contracts (6 models)
  macros/           reusable SQL (date_to_key)
  analyses/         ad hoc queries, compiled but not materialised
  packages.yml      package dependencies (dbt_utils), pinned in package-lock.yml
scripts/
  generate_data.py        synthetic raw data with deliberate defects
  simulate_next_load.py   a later load that changes 40 customers and adds orders
docs/
  design.md         design decisions, fact table grain, customer history
```

## Data flow

| Layer | Materialised as | Schema | What happens |
|---|---|---|---|
| Snapshot | snapshot table | `snapshots` | `raw.customers` history: a new version whenever `updated_at` changes |
| Staging | view | `staging` | Text trimmed and lowercased, flags typed as booleans, prices cast to decimal, exact duplicate orders removed |
| Intermediate | view | `intermediate` | Order lines joined to orders; returns joined to their original line with quantity made negative |
| Marts | table | `marts` | Five dimensions and one fact table |

## The star schema

`fact_sales` has one row per sale line plus one row per return, with returns stored as negative rows. This lets `sum(line_amount)` give net revenue directly. `order_id` is kept as a degenerate dimension.

Dimensions: `dim_customer`, `dim_product`, `dim_store`, `dim_payment_method`, `dim_date`.

`dim_customer` is a type 2 slowly changing dimension: one row per version of a customer, with `valid_from`, `valid_to` and `is_current`. Each fact row points at the version that was valid when the sale or return happened.

The web channel is modelled as a store with `store_type = 'online'`.

## Design decisions

- **Grain.** A return reuses the `order_line_id` of the sale it reverses, so that column is not unique. A row is identified by `transaction_type` + `order_line_id` + `return_id`, checked by `dbt_utils.unique_combination_of_columns` on `fact_sales`.
- **Guest and Unknown members.** Walk-in sales (null `customer_id`) map to a Guest row with key `'-1'` in `dim_customer`. Orders with a null store or payment method map to an Unknown row with key `-1` in `dim_store` and `dim_payment_method`. No fact row has a null foreign key, and no revenue is dropped.
- **Returns land on the return date.** `date_key` for a return comes from `return_timestamp`, not the original sale date. The customer version follows the same rule.
- **Customer history.** `dim_customer` keys are a hash of `customer_id` and the version's start (`dbt_utils.generate_surrogate_key`), and `fact_sales` finds the right one with a point-in-time join. A customer's first version is extended back to 1900-01-01, so sales from before snapshotting began still find a version. See [docs/design.md](docs/design.md#customer-history-scd-type-2).
- **Other dimension keys equal source ids**, so the fact table carries them without joining to those dimensions. `relationships` tests prove every key resolves.
- **`dim_date` is generated**, not loaded: one row per day from 2020-01-01 to 2075-12-31, built with `dbt_utils.date_spine` so the SQL is not tied to DuckDB.
- **One definition of the date key.** The `date_to_key` macro builds the `yyyymmdd` integer for `dim_date` and both halves of `fact_sales`.
- **Contracts.** All six marts enforce column names and types, so upstream changes can't silently alter the public interface.

## Data quality

A full `dbt build` builds 1 snapshot and 15 models, runs 159 tests and finishes with `PASS=167 WARN=8 ERROR=0`. The 8 warnings are deliberate: the source data was seeded with defects, and they are reported in staging and intermediate and resolved before the marts.

Besides dbt's built-in tests, the project uses dbt_utils tests for rules that span columns or ranges:

- `unique_combination_of_columns`: the `fact_sales` grain.
- `expression_is_true`: sale rows have positive `quantity` and `line_amount`, return rows negative, and `int_returns_signed.quantity` is always negative.
- `accepted_range`: `dim_date` calendar parts stay in range (quarter 1–4, month 1–12, day 1–31, ISO weekday 1–7), and `unit_price` is above zero.
- `mutually_exclusive_ranges`: the versions of each customer in `stg_customers` and `dim_customer` follow on from each other with no gaps or overlaps, so every sale matches exactly one version.

| Test | Rows | Handled by |
|---|---|---|
| `stg_orders` null `store_id` | 20 | Mapped to Unknown (-1) in `fact_sales` |
| `stg_orders` null `payment_method_id` | 20 | Mapped to Unknown (-1) in `fact_sales` |
| `stg_order_lines` orphan `order_id` | 25 | Dropped by inner join in `int_order_lines_joined` |
| `stg_returns` orphan `order_line_id` | 10 | Dropped by inner join in `int_returns_signed` |
| Null `store_id` / `payment_method_id` carried into the intermediate models | 44 / 50 lines, 3 / 3 returns | Mapped to Unknown (-1) in `fact_sales` |

Result: `fact_sales` has 46,765 rows (44,208 sales and 2,557 returns), and `dim_customer` has 541 rows (540 versions of 500 customers, plus Guest). Mart tests produce no warnings.

## Running it

dbt reads its connection from `~/.dbt/profiles.yml`. This project expects:

```yaml
retail_dbt:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: dev.duckdb
      threads: 1
```

Then, in PowerShell:

```
git clone https://github.com/noahrubin989/dbt-retail-portfolio.git
cd dbt-retail-portfolio
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install dbt-core==1.12.6 dbt-duckdb==1.11.0

# 1. First load of raw data, and the first snapshot of it
python scripts/generate_data.py retail_dbt/dev.duckdb
cd retail_dbt
dbt deps
dbt snapshot

# 2. A later load where 40 customers change, then build everything
cd ..
python scripts/simulate_next_load.py retail_dbt/dev.duckdb
cd retail_dbt
dbt build
```

The snapshot has to run between the two loads. The second load overwrites `raw.customers`, so the snapshot is the only place the old values are kept. `dbt build` runs the snapshot again before the models, which records the 40 changes.

## Docs and lineage

```
dbt docs generate
dbt docs serve
```