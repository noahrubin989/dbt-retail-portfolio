"""Simulate the next load of the source system, so snapshots have history to record.

Usage (from the repo root, after generate_data.py and a first `dbt snapshot`):
    python scripts/simulate_next_load.py [path/to/database.duckdb]

The default database path is retail_dbt/dev.duckdb, the `path:` of the dev
target in ~/.dbt/profiles.yml.

What changes in raw, all dated after the original data ends (2026-10-18):
- 40 customers change: a new email, a flipped marketing opt-in, or both.
  Their updated_at moves to the date of the change, which is what the
  timestamp snapshot strategy looks at.
- Each changed customer places 1 to 3 new web orders after their change,
  so fact_sales has sales on both the old and the new version.

raw.customers is updated in place, like a source system would, so the old
values survive only in the snapshot. Run `dbt snapshot` again afterwards.
The script refuses to run twice; rerun generate_data.py to start over.
"""
import random
import sys
from datetime import datetime, timedelta

import duckdb

SEED = 7
DB_PATH = sys.argv[1] if len(sys.argv) > 1 else "retail_dbt/dev.duckdb"

DATA_END = datetime(2026, 10, 18, 23, 59, 59)
CHANGES_START = datetime(2026, 10, 19)
CHANGES_END = datetime(2026, 10, 25, 23, 59, 59)
LOAD_END = datetime(2026, 10, 31, 23, 59, 59)

N_CHANGED_CUSTOMERS = 40
ONLINE_STORE_ID = 5
ONLINE_PAYMENT_IDS = [1, 2, 4]

random.seed(SEED)


def rand_dt(start, end):
    seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, seconds))


def messy_flag(is_true):
    """Same mixed representations as generate_data.py."""
    if is_true:
        return random.choice(["true", "yes", "1"])
    return random.choice(["false", "no", "0"])


def parse_flag(value):
    return value.strip().lower() in ("1", "yes", "true")


def change_customers(con):
    customers = con.execute(
        "select customer_id, email, marketing_opt_in_flag from raw.customers order by customer_id"
    ).fetchall()
    changed = {}
    for customer_id, email, opt_in_flag in random.sample(customers, N_CHANGED_CUSTOMERS):
        kind = random.choice(["email", "opt_in", "both"])
        new_email = email
        new_flag = opt_in_flag
        if kind in ("email", "both"):
            new_email = email.strip().lower().replace("@example.com", "@newmail.example.com")
        if kind in ("opt_in", "both"):
            new_flag = messy_flag(not parse_flag(opt_in_flag))
        changed_at = rand_dt(CHANGES_START, CHANGES_END)
        con.execute(
            """
            update raw.customers
            set email = ?, marketing_opt_in_flag = ?, updated_at = ?
            where customer_id = ?
            """,
            [new_email, new_flag, changed_at, customer_id],
        )
        changed[customer_id] = (kind, changed_at)
    return changed


def add_orders(con, changed):
    next_order_id = con.execute("select max(order_id) + 1 from raw.orders").fetchone()[0]
    next_line_id = con.execute("select max(order_line_id) + 1 from raw.order_lines").fetchone()[0]
    # Highest price seen per product is its list price (sales only ever discount it).
    prices = dict(
        con.execute(
            """
            select product_id, max(cast(replace(unit_price, '$', '') as decimal(10, 2)))
            from raw.order_lines
            group by product_id
            """
        ).fetchall()
    )
    product_ids = sorted(prices)

    orders, lines = [], []
    for customer_id, (_, changed_at) in sorted(changed.items()):
        for _ in range(random.randint(1, 3)):
            ts = rand_dt(changed_at + timedelta(hours=1), LOAD_END)
            created = ts + timedelta(seconds=random.randint(1, 300))
            orders.append(
                [next_order_id, customer_id, ONLINE_STORE_ID, random.choice(ONLINE_PAYMENT_IDS), ts, created, created]
            )
            for product_id in random.sample(product_ids, random.randint(1, 3)):
                quantity = random.choices([1, 2, 3], [70, 20, 10])[0]
                lines.append(
                    [next_line_id, next_order_id, product_id, quantity, f"{prices[product_id]:.2f}", created, created]
                )
                next_line_id += 1
            next_order_id += 1

    con.executemany("insert into raw.orders values (?, ?, ?, ?, ?, ?, ?)", orders)
    con.executemany("insert into raw.order_lines values (?, ?, ?, ?, ?, ?, ?)", lines)
    return len(orders), len(lines)


def main():
    con = duckdb.connect(DB_PATH)
    latest = con.execute("select max(updated_at) from raw.customers").fetchone()[0]
    if latest > DATA_END:
        print(f"Next load already applied to {DB_PATH} (latest customer update {latest}).")
        print("Rerun scripts/generate_data.py to reset raw first.")
        con.close()
        sys.exit(1)

    con.begin()
    changed = change_customers(con)
    n_orders, n_lines = add_orders(con, changed)
    con.commit()

    kinds = [kind for kind, _ in changed.values()]
    print(f"Applied next load to {DB_PATH}")
    print(
        f"  raw.customers: {len(changed)} changed "
        f"({kinds.count('email')} email, {kinds.count('opt_in')} opt-in, {kinds.count('both')} both)"
    )
    print(f"  raw.orders: {n_orders} new orders")
    print(f"  raw.order_lines: {n_lines} new lines")
    print(f"  changed customer_ids: {sorted(changed)[:10]} ...")
    con.close()


if __name__ == "__main__":
    main()
