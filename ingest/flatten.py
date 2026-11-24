"""Flatten raw weather and FX files into CSV files for loading.

Reads the bronze files under data/raw and writes two CSV files:
    data/flat/weather_daily.csv   one row per city per day
    data/flat/fx_rates.csv        one row per (date, base, quote)

Run from the repository root:
    python ingest/flatten.py
    python ingest/flatten.py --root data/raw --out data/flat

Rules this script follows:
* It only RESHAPES. Column names stay exactly as the sources named them; the dbt
  staging models rename them later.
* A partition without meta.json was never finished, so it is skipped and counted.
* The output is deterministic: rows are sorted and files use "\\n" line endings,
  so running it twice gives byte-identical files.
* FX rates are read as Decimal, so 11.60 stays 11.60 (a float would give 11.6).
"""
import argparse
import csv
import json
from decimal import Decimal
from pathlib import Path

import common

WEATHER_VARIABLES = ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "weathercode"]
WEATHER_COLUMNS = ["city_slug", "time", *WEATHER_VARIABLES]
FX_COLUMNS = ["date", "base", "quote", "rate"]


def columns_to_rows(daily: dict) -> list[dict]:
    """Step 1. Turn {"time": [...], "temperature_2m_max": [...], ...} into one dict per day.

    Each row has the key "time" and the four WEATHER_VARIABLES.
    Raises ValueError if any list is not as long as the "time" list.
    A None value stays None.
    """
    times = daily["time"]

    # Check every list BEFORE building rows, so a broken file never produces a half-right result.
    for name in WEATHER_VARIABLES:
        if len(daily[name]) != len(times):
            raise ValueError(f"{name} has {len(daily[name])} values for {len(times)} days")

    rows = []
    for i in range(len(times)):  # i is the day number: 0, 1, 2, ...
        row = {"time": times[i]}
        for name in WEATHER_VARIABLES:
            row[name] = daily[name][i]  # the value at position i of the list called `name`
        rows.append(row)
    return rows


def read_weather_partition(partition: Path) -> list[dict]:
    """Step 2. The rows of one city and month.

    Reads response.json for the data and meta.json for the city_slug, and puts the
    city_slug into every row. Each row has exactly the keys in WEATHER_COLUMNS.
    """
    meta = json.loads((partition / common.META_FILE).read_text(encoding="utf-8"))
    response = json.loads((partition / common.RESPONSE_FILE).read_text(encoding="utf-8"))

    rows = []
    for day in columns_to_rows(response["daily"]):
        # {"city_slug": ..., **day} makes a new dict: city_slug first, then everything in `day`.
        rows.append({"city_slug": meta["city_slug"], **day})
    return rows


def flatten_weather(root: Path) -> tuple[list[dict], int]:
    """Step 3. All weather rows under <root>/weather/city=*/month=*.

    A partition without meta.json is unfinished: skip it and count it.
    Returns (rows, number_of_skipped_partitions). Rows are sorted by (city_slug, time).
    A root with no weather folder gives ([], 0).
    """
    rows = []
    skipped = 0
    for partition in sorted(Path(root).glob("weather/city=*/month=*")):
        if not (partition / common.META_FILE).is_file():
            skipped += 1  # meta.json is the "done" marker, so this one was never finished
            continue
        rows.extend(read_weather_partition(partition))

    rows.sort(key=lambda row: (row["city_slug"], row["time"]))
    return rows, skipped


def flatten_fx(root: Path, provider: str = "bog") -> tuple[list[dict], int]:
    """Step 4. All FX rows under <root>/fx/provider=<provider>/pair=*/month=*.

    Parse the JSON with parse_float=Decimal so a rate like 11.60 keeps its exact text.
    The same (date, base, quote) can appear in two neighbouring partitions: keep it once.
    If two partitions give different rates for the same key, raise ValueError.
    Skip and count partitions without meta.json. Rows are sorted by (date, base, quote).
    """
    rates = {}  # (date, base, quote) -> rate
    skipped = 0
    for partition in sorted(Path(root).glob(f"fx/provider={provider}/pair=*/month=*")):
        if not (partition / common.META_FILE).is_file():
            skipped += 1
            continue
        text = (partition / common.RESPONSE_FILE).read_text(encoding="utf-8")
        for record in json.loads(text, parse_float=Decimal):
            key = (record["date"], record["base"], record["quote"])
            if key in rates and rates[key] != record["rate"]:
                raise ValueError(f"two different rates for {key}: {rates[key]} and {record['rate']}")
            rates[key] = record["rate"]  # a repeat with the same rate just overwrites itself

    rows = []
    for (day, base, quote), rate in sorted(rates.items()):
        rows.append({"date": day, "base": base, "quote": quote, "rate": rate})
    return rows, skipped


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    """Step 5. Write a header row, then each row in the order of `columns`.

    - Create the parent folder if it does not exist.
    - Use "\\n" line endings, so the file is the same on every computer.
    - None becomes an empty cell. A Decimal is written as its exact text.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # newline="" lets the csv module control line endings; lineterminator="\n" fixes them.
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in columns})  # None is written as empty


def main(argv: list[str] | None = None) -> int:
    """Step 6. Command line: --root (default common.DATA_ROOT), --out (default data/flat).

    Flatten both sources, write weather_daily.csv and fx_rates.csv into --out, and
    print how many rows were written and how many partitions were skipped (the word
    "skipped" must appear). If flattening raises ValueError, print the message and
    return 1. Otherwise return 0.
    """
    parser = argparse.ArgumentParser(description="Flatten raw weather and FX files into CSV files.")
    parser.add_argument("--root", type=Path, default=common.DATA_ROOT, help="raw data folder")
    parser.add_argument("--out", type=Path, default=Path("data/flat"), help="folder for the CSV files")
    args = parser.parse_args(argv)

    try:
        weather_rows, weather_skipped = flatten_weather(args.root)
        fx_rows, fx_skipped = flatten_fx(args.root)
    except ValueError as error:
        print(f"error: {error}")
        return 1

    write_csv(args.out / "weather_daily.csv", weather_rows, WEATHER_COLUMNS)
    write_csv(args.out / "fx_rates.csv", fx_rows, FX_COLUMNS)
    print(f"weather: {len(weather_rows)} rows written, skipped {weather_skipped} unfinished partitions")
    print(f"fx: {len(fx_rows)} rows written, skipped {fx_skipped} unfinished partitions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())