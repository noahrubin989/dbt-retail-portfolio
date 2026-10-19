"""Generate synthetic raw retail data into DuckDB (schema: raw).

Usage (from the repo root):
    python scripts/generate_data.py [path/to/database.duckdb]

The default database path is retail_dbt/retail.duckdb. It must match the
`path:` in your ~/.dbt/profiles.yml, or dbt will look in a different file.

Clean data is generated first, then deliberate mess is applied on top, so
you always know exactly what was broken (see docs/sources.md). A fixed
seed means the output is identical on every run.
"""
import csv
import random
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import duckdb

SEED = 42
DB_PATH = sys.argv[1] if len(sys.argv) > 1 else "retail_dbt/retail.duckdb"

N_CUSTOMERS = 500
N_PRODUCTS = 200
N_ORDERS = 20_000

DATA_START = datetime(2025, 1, 1)
DATA_END = datetime(2026, 10, 18, 23, 59, 59)

random.seed(SEED)


# ---------------------------------------------------------------- helpers
def rand_dt(start, end):
    seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, seconds))


def mangle(value, p=0.15):
    """Randomly break the casing or whitespace of a text value."""
    if value is None or random.random() >= p:
        return value
    kind = random.choice(["upper", "lower", "pad_left", "pad_right", "pad_both"])
    if kind == "upper":
        return value.upper()
    if kind == "lower":
        return value.lower()
    if kind == "pad_left":
        return "  " + value
    if kind == "pad_right":
        return value + "  "
    return " " + value + " "


def messy_flag(is_true):
    """Mixed true/false, yes/no, 1/0 representations."""
    if is_true:
        return random.choice(["true", "yes", "1"])
    return random.choice(["false", "no", "0"])


def cell(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value


# ---------------------------------------------------------- clean: stores
def make_stores():
    return [
        [1, "Sydney Central", "physical", "Sydney", "NSW", "2019-03-15"],
        [2, "Melbourne CBD", "physical", "Melbourne", "VIC", "2020-06-01"],
        [3, "Brisbane North", "physical", "Brisbane", "QLD", "2021-02-20"],
        [4, "Perth Waterfront", "physical", "Perth", "WA", "2022-09-10"],
        [5, "Online Store", "online", None, None, "2019-01-01"],
    ]


def make_payment_methods():
    return [
        [1, "Visa", "Y"],
        [2, "Mastercard", "Y"],
        [3, "Cash", "Y"],
        [4, "PayPal", "Y"],
        [5, "Gift card", "Y"],
        [6, "Cheque", "N"],
    ]


# ------------------------------------------------------- clean: customers
FIRST_NAMES = [
    "Olivia", "Noah", "Charlotte", "Oliver", "Amelia", "William", "Isla", "Jack",
    "Mia", "Henry", "Ava", "Leo", "Grace", "Lucas", "Chloe", "Thomas", "Ella",
    "Ethan", "Sophie", "James", "Ruby", "Mason", "Zoe", "Harry", "Lily",
    "Max", "Emily", "Samuel", "Hannah", "Daniel",
]
LAST_NAMES = [
    "Smith", "Jones", "Williams", "Brown", "Wilson", "Taylor", "Anderson",
    "Thompson", "Walker", "White", "Harris", "Martin", "Davis", "Clark",
    "Lewis", "Young", "King", "Wright", "Scott", "Green", "Baker", "Adams",
    "Nelson", "Hill", "Campbell", "Mitchell", "Roberts", "Carter", "Evans",
    "Turner",
]


def make_customers():
    rows = []
    for customer_id in range(1, N_CUSTOMERS + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        email = f"{first}.{last}{customer_id}@example.com".lower()
        mobile = (
            f"+61 4{random.randint(10, 99)} "
            f"{random.randint(100, 999)} {random.randint(100, 999)}"
        )
        opt_in = random.random() < 0.6
        verified = random.random() < 0.8
        sex = random.choices(["male", "female", "other"], [48, 48, 4])[0]
        created = rand_dt(datetime(2023, 1, 1), datetime(2024, 12, 31))
        updated = min(created + timedelta(days=random.randint(0, 400)), DATA_END)
        rows.append(
            [customer_id, first, last, email, mobile, opt_in, verified, sex, created, updated]
        )
    return rows


# --------------------------------------------------------- clean: products
CATALOG = {
    "Kitchen": (["kettle", "toaster", "blender", "pan"], ["Brewmaster", "Hearthware", "Kitchenly"], (15, 180)),
    "Electronics": (["phone", "headphones", "tablet", "speaker"], ["Voltix", "Nexora", "Pulsar"], (30, 1200)),
    "Clothing": (["t-shirt", "jeans", "jacket", "socks"], ["Threadly", "Northcoast", "Urbanline"], (8, 150)),
    "Home": (["lamp", "cushion", "rug", "mirror"], ["Nestwell", "Homewood", "Softhaus"], (10, 250)),
    "Toys": (["puzzle", "board game", "doll", "building set"], ["Playmore", "Funbox", "Kidzone"], (6, 90)),
    "Sports": (["yoga mat", "dumbbell set", "football", "tent"], ["Peakform", "Fieldpro", "Trailmate"], (10, 300)),
}

PRODUCT_BASE_PRICE = {}


def make_products():
    rows = []
    categories = list(CATALOG)
    for product_id in range(1, N_PRODUCTS + 1):
        category = random.choice(categories)
        subs, brands, (lo, hi) = CATALOG[category]
        sub = random.choice(subs)
        brand = random.choice(brands)
        name = f"{brand} {sub} M{random.randint(100, 999)}"
        PRODUCT_BASE_PRICE[product_id] = round(random.uniform(lo, hi), 2)
        created = rand_dt(datetime(2022, 1, 1), datetime(2024, 12, 31))
        updated = min(created + timedelta(days=random.randint(0, 600)), DATA_END)
        rows.append([product_id, name, brand, category, sub, created, updated])
    return rows


# ------------------------------------------- clean: orders, lines, returns
def make_orders_lines_returns():
    orders, lines, returns = [], [], []
    order_ts = {}
    line_id = 0
    return_id = 0

    for order_id in range(1, N_ORDERS + 1):
        ts = rand_dt(DATA_START, DATA_END)
        order_ts[order_id] = ts

        store_id = random.choices([1, 2, 3, 4, 5], [20, 18, 16, 16, 30])[0]
        if store_id == 5:
            customer_id = random.randint(1, N_CUSTOMERS)
            payment_id = random.choice([1, 2, 4])
        else:
            customer_id = None if random.random() < 0.25 else random.randint(1, N_CUSTOMERS)
            payment_id = random.choices([1, 2, 3, 4, 5], [30, 25, 20, 15, 10])[0]

        # Most rows are written within minutes; a few arrive days late.
        if random.random() < 0.02:
            created = ts + timedelta(hours=random.randint(6, 72))
        else:
            created = ts + timedelta(seconds=random.randint(1, 300))
        created = min(created, DATA_END)
        updated = created if random.random() < 0.9 else min(created + timedelta(hours=random.randint(1, 48)), DATA_END)

        orders.append([order_id, customer_id, store_id, payment_id, ts, created, updated])

        n_lines = random.choices([1, 2, 3, 4, 5], [35, 30, 20, 10, 5])[0]
        for product_id in random.sample(range(1, N_PRODUCTS + 1), n_lines):
            line_id += 1
            quantity = random.choices([1, 2, 3, 4], [60, 25, 10, 5])[0]
            unit_price = round(PRODUCT_BASE_PRICE[product_id] * random.choice([1.0, 1.0, 1.0, 0.9, 0.8]), 2)
            lines.append([line_id, order_id, product_id, quantity, unit_price, created, updated])

            if random.random() < 0.06:
                return_ts = ts + timedelta(days=random.randint(1, 30), seconds=random.randint(0, 86399))
                if return_ts <= DATA_END:
                    return_id += 1
                    returns.append(
                        [return_id, line_id, random.randint(1, quantity), return_ts, return_ts, return_ts]
                    )
    return orders, lines, returns


# ------------------------------------------------------------ apply mess
def mess_up(stores, payment_methods, customers, products, orders, lines, returns):
    for r in stores:
        r[2] = mangle(r[2], 0.4)
        r[3] = mangle(r[3], 0.4)
        r[4] = mangle(r[4], 0.4)

    for r in payment_methods:
        r[1] = mangle(r[1], 0.4)

    for r in customers:
        r[1] = mangle(r[1])
        r[2] = mangle(r[2])
        r[3] = mangle(r[3])
        r[5] = messy_flag(r[5])
        r[6] = messy_flag(r[6])
        r[7] = mangle(r[7])

    for r in products:
        r[3] = mangle(r[3])
        r[4] = mangle(r[4])

    # orders: null store_id / payment_method_id (should never happen)
    for i in random.sample(range(len(orders)), 20):
        orders[i][2] = None
    for i in random.sample(range(len(orders)), 20):
        orders[i][3] = None
    # orders: duplicated order_id rows, the copy updated an hour later
    for i in random.sample(range(len(orders)), 15):
        dup = list(orders[i])
        dup[6] = dup[6] + timedelta(hours=1)
        orders.append(dup)

    # order_lines: price as text, some with a currency symbol
    for r in lines:
        r[4] = f"${r[4]:.2f}" if random.random() < 0.05 else f"{r[4]:.2f}"
    # order_lines: orphan lines pointing at orders that don't exist
    for k, i in enumerate(random.sample(range(len(lines)), 25)):
        lines[i][1] = 900_000 + k

    # returns: orphan returns pointing at order lines that don't exist
    for k, i in enumerate(random.sample(range(len(returns)), 10)):
        returns[i][1] = 9_000_000 + k


# ------------------------------------------------------------- load DuckDB
TABLES = {
    "stores": "store_id INTEGER, store_name VARCHAR, store_type VARCHAR, city VARCHAR, state VARCHAR, opened_date DATE, created_at TIMESTAMP, updated_at TIMESTAMP",
    "payment_methods": "payment_method_id INTEGER, method_name VARCHAR, is_active VARCHAR",
    "customers": "customer_id INTEGER, first_name VARCHAR, last_name VARCHAR, email VARCHAR, mobile_number VARCHAR, marketing_opt_in_flag VARCHAR, email_verified_flag VARCHAR, sex VARCHAR, created_at TIMESTAMP, updated_at TIMESTAMP",
    "products": "product_id INTEGER, product_name VARCHAR, brand VARCHAR, product_category VARCHAR, product_subcategory VARCHAR, created_at TIMESTAMP, updated_at TIMESTAMP",
    "orders": "order_id INTEGER, customer_id INTEGER, store_id INTEGER, payment_method_id INTEGER, order_timestamp TIMESTAMP, created_at TIMESTAMP, updated_at TIMESTAMP",
    "order_lines": "order_line_id INTEGER, order_id INTEGER, product_id INTEGER, quantity INTEGER, unit_price VARCHAR, created_at TIMESTAMP, updated_at TIMESTAMP",
    "returns": "return_id INTEGER, order_line_id INTEGER, quantity_returned INTEGER, return_timestamp TIMESTAMP, created_at TIMESTAMP, updated_at TIMESTAMP",
}


def stores_with_timestamps(stores):
    out = []
    for r in stores:
        opened = datetime.strptime(r[5], "%Y-%m-%d")
        out.append(r[:5] + [r[5], opened, opened])
    return out


def load(con, name, rows, tmpdir):
    path = Path(tmpdir) / f"{name}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for r in rows:
            writer.writerow([cell(v) for v in r])
    con.execute(f"DROP TABLE IF EXISTS raw.{name}")
    con.execute(f"CREATE TABLE raw.{name} ({TABLES[name]})")
    con.execute(f"COPY raw.{name} FROM '{path.as_posix()}' (FORMAT csv, HEADER false)")


def main():
    stores = make_stores()
    payment_methods = make_payment_methods()
    customers = make_customers()
    products = make_products()
    orders, lines, returns = make_orders_lines_returns()

    stores = stores_with_timestamps(stores)
    mess_up(stores, payment_methods, customers, products, orders, lines, returns)

    # payment_methods has no timestamps in sources.md, so nothing to add.
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(DB_PATH)
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    with tempfile.TemporaryDirectory() as tmpdir:
        load(con, "stores", stores, tmpdir)
        load(con, "payment_methods", payment_methods, tmpdir)
        load(con, "customers", customers, tmpdir)
        load(con, "products", products, tmpdir)
        load(con, "orders", orders, tmpdir)
        load(con, "order_lines", lines, tmpdir)
        load(con, "returns", returns, tmpdir)

    print(f"Wrote raw schema to {DB_PATH}")
    for name in TABLES:
        count = con.execute(f"SELECT count(*) FROM raw.{name}").fetchone()[0]
        print(f"  raw.{name}: {count:,} rows")
    con.close()


if __name__ == "__main__":
    main()