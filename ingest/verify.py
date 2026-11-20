"""Check the raw data on disk: coverage, duplicates, and a fingerprint of the data.

    python ingest/verify.py weather
    python ingest/verify.py weather --cities kumasi accra tamale
    python ingest/verify.py fx --pairs usd-ghs

The IDEMPOTENCY TEST:
    1. run the loader, then run verify.py and note the numbers and the fingerprint
    2. run the loader again, then run verify.py again
    3. the counts and the fingerprint must be identical

The fingerprint is a hash of the data VALUES, keyed by (city, date) for weather
and (date, base, quote) for FX. Whole files are never compared, because the
weather API adds a field (generationtime_ms) that changes on every call.
"""
import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

import common
import load_fx
import load_weather

def days_between(first_day: str, last_day: str) -> list[str]:
    """Every ISO date from first_day to last_day, inclusive."""
    start = date.fromisoformat(first_day)
    end = date.fromisoformat(last_day)
    return [(start + timedelta(days=n)).isoformat() for n in range((end - start).days + 1)]


def fingerprint(records: dict) -> str:
    """A short hash of all (key, values) pairs, independent of file formatting."""
    text = json.dumps([[list(key), value] for key, value in sorted(records.items())])
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def read_response(partition: Path):
    return json.loads((partition / common.RESPONSE_FILE).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# Weather
# --------------------------------------------------------------------------
def verify_weather(root: Path, cities: list[dict], start: str, end: str) -> dict:
    variables = load_weather.DAILY_VARIABLES.split(",")
    months = common.month_ranges(start, end)
    missing, stale, problems = [], [], []
    records: dict = {}
    duplicates = 0
    nulls: Counter = Counter()
    partitions_ok = 0

    for city in cities:
        slug = city["city_slug"]
        for month, first_day, last_day in months:
            label = f"{slug} {month}"
            partition = load_weather.weather_partition(slug, month, root)
            params = load_weather.build_weather_request(city, first_day, last_day)

            if not (partition / common.RESPONSE_FILE).is_file():
                missing.append(label)
                continue
            if not common.is_up_to_date(partition, params):
                stale.append(label)  # incomplete, corrupt, or fetched with other inputs
                continue

            daily = read_response(partition).get("daily", {})
            times = daily.get("time", [])
            expected_days = days_between(first_day, last_day)
            if times != expected_days:
                problems.append(f"{label}: dates do not match the month "
                                f"({len(times)} found, {len(expected_days)} expected)")
                continue

            columns, usable = {}, True
            for name in variables:
                values = daily.get(name)
                if values is None or len(values) != len(times):
                    problems.append(f"{label}: '{name}' is missing or has the wrong length")
                    usable = False
                    break
                columns[name] = values
            if not usable:
                continue

            partitions_ok += 1
            for index, day in enumerate(times):
                row = [columns[name][index] for name in variables]
                nulls.update(name for name, value in zip(variables, row) if value is None)
                if (slug, day) in records:
                    duplicates += 1
                records[(slug, day)] = row

    expected_rows = len(cities) * sum(len(days_between(first, last)) for _, first, last in months)
    ok = (not missing and not stale and not problems and not duplicates
          and len(records) == expected_rows)
    return {
        "kind": "weather", "ok": ok,
        "partitions_expected": len(cities) * len(months), "partitions_ok": partitions_ok,
        "missing": missing, "stale": stale, "problems": problems,
        "rows": len(records), "rows_expected": expected_rows,
        "duplicates": duplicates, "null_values": dict(nulls),
        "fingerprint": fingerprint(records), "gaps": [],
    }


# --------------------------------------------------------------------------
# FX
# --------------------------------------------------------------------------
def verify_fx(root: Path, pairs: list[str], provider: str, start: str, end: str) -> dict:
    months = common.month_ranges(start, end)
    range_first, range_last = months[0][1], months[-1][2]
    missing, stale, problems, conflicts = [], [], [], []
    records: dict = {}
    dates_by_pair: dict = {pair: set() for pair in pairs}
    overlaps = outside_range = partitions_ok = 0

    for pair in pairs:
        base, quote = load_fx.split_pair(pair)
        for month, first_day, last_day in months:
            label = f"{pair} {month}"
            partition = load_fx.fx_partition(provider, pair, month, root)
            params = load_fx.build_fx_request(pair, provider, first_day, last_day)

            if not (partition / common.RESPONSE_FILE).is_file():
                missing.append(label)
                continue
            if not common.is_up_to_date(partition, params):
                stale.append(label)
                continue

            data = read_response(partition)
            if not isinstance(data, list):
                problems.append(f"{label}: the response is not a list of records")
                continue

            partitions_ok += 1
            for record in data:
                try:
                    key = (record["date"], record["base"], record["quote"])
                    rate = record["rate"]
                except (KeyError, TypeError):
                    problems.append(f"{label}: a record is missing date, base, quote or rate")
                    continue
                if (record["base"], record["quote"]) != (base, quote):
                    problems.append(f"{label}: unexpected pair {record['base']}/{record['quote']}")
                    continue
                if not range_first <= record["date"] <= range_last:
                    outside_range += 1  # e.g. the extra earlier record seen at a range start
                if key in records:
                    overlaps += 1  # the same record in two neighbouring partitions
                    if records[key] != rate:
                        conflicts.append(f"{key}: {records[key]} against {rate}")
                else:
                    records[key] = rate
                dates_by_pair[pair].add(record["date"])

    # The Bank of Ghana publishes on business days, so every Monday to Friday
    # with no record is listed. These are usually public holidays, so they are
    # information, not an error. (A rule like "a gap longer than a weekend"
    # would miss a single holiday in the middle of a week.)
    gaps = []
    all_days = days_between(range_first, range_last)
    for pair, dates in dates_by_pair.items():
        for day in all_days:
            weekday = date.fromisoformat(day)
            if weekday.weekday() < 5 and day not in dates:
                gaps.append(f"{pair}: no rate on {day} ({weekday.strftime('%A')})")

    problems.extend(f"conflicting rates for {item}" for item in conflicts)
    ok = not missing and not stale and not problems
    return {
        "kind": "fx", "ok": ok,
        "partitions_expected": len(pairs) * len(months), "partitions_ok": partitions_ok,
        "missing": missing, "stale": stale, "problems": problems,
        "rows": len(records), "rows_expected": None,
        "duplicates": 0, "overlaps": overlaps, "outside_range": outside_range,
        "null_values": {}, "fingerprint": fingerprint(records), "gaps": gaps,
    }


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------
def print_report(report: dict, limit: int = 15) -> None:
    def show(title: str, items: list) -> None:
        if items:
            print(f"{title} ({len(items)}):")
            for item in items[:limit]:
                print("  ", item)
            if len(items) > limit:
                print(f"   ... and {len(items) - limit} more")

    print(f"\n{report['kind']} verification: {'OK' if report['ok'] else 'PROBLEMS FOUND'}")
    print(f"  partitions: {report['partitions_ok']} usable of {report['partitions_expected']} expected")
    expected = report["rows_expected"]
    print(f"  rows: {report['rows']}" + (f" of {expected} expected" if expected else ""))
    if report["kind"] == "weather":
        print(f"  duplicate (city, day) rows: {report['duplicates']}")
        print(f"  null values: {report['null_values'] or 'none'}")
    else:
        print(f"  records present in two neighbouring partitions: {report['overlaps']}")
        print(f"  records dated outside the requested range: {report['outside_range']}")
    print(f"  fingerprint: {report['fingerprint']}")
    show("missing partitions", report["missing"])
    show("stale or incomplete partitions", report["stale"])
    show("problems", report["problems"])
    show("weekdays with no published rate (public holidays?)", report["gaps"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the raw data on disk.")
    sub = parser.add_subparsers(dest="kind", required=True)

    weather = sub.add_parser("weather")
    weather.add_argument("--cities", nargs="+", metavar="SLUG")
    weather.add_argument("--start", default=load_weather.DEFAULT_START)
    weather.add_argument("--end", default=load_weather.DEFAULT_END)
    weather.add_argument("--root", type=Path, default=common.DATA_ROOT)
    weather.add_argument("--cities-file", type=Path, default=load_weather.CITIES_FILE)

    fx = sub.add_parser("fx")
    fx.add_argument("--pairs", nargs="+", default=load_fx.DEFAULT_PAIRS)
    fx.add_argument("--provider", default=load_fx.DEFAULT_PROVIDER)
    fx.add_argument("--start", default=load_fx.DEFAULT_START)
    fx.add_argument("--end", default=load_fx.DEFAULT_END)
    fx.add_argument("--root", type=Path, default=common.DATA_ROOT)

    args = parser.parse_args(argv)

    if args.kind == "weather":
        cities = load_weather.read_cities(args.cities_file)
        if args.cities:
            cities = [city for city in cities if city["city_slug"] in args.cities]
        report = verify_weather(args.root, cities, args.start, args.end)
    else:
        report = verify_fx(args.root, [p.lower() for p in args.pairs], args.provider,
                           args.start, args.end)

    print_report(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())