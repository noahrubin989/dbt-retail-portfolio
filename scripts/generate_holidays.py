"""Generate the Australian public holidays seed.

Usage (from the repo root):
    python scripts/generate_holidays.py

Writes retail_dbt/seeds/au_public_holidays.csv with national public holidays
from 2020 to 2075, the same range as dim_date. Uses the `holidays` library,
which knows moving dates such as Easter and one-off holidays. Future years
follow today's rules, so regenerate the file if a holiday is added or moved.
"""
import csv
from pathlib import Path

import holidays

FIRST_YEAR = 2020
LAST_YEAR = 2075
OUT_PATH = Path("retail_dbt/seeds/au_public_holidays.csv")  


def main():
    au_holidays = holidays.Australia(years=range(FIRST_YEAR, LAST_YEAR + 1))
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["holiday_date", "holiday_name"])
        for holiday_date, holiday_name in sorted(au_holidays.items()):
            writer.writerow([holiday_date.isoformat(), holiday_name])
    print(f"Wrote {len(au_holidays)} holidays to {OUT_PATH}")


if __name__ == "__main__":
    main()