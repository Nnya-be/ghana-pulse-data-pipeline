"""Load raw daily weather from Open-Meteo into data/raw/weather/.

One partition per city per month:

    data/raw/weather/city=<slug>/month=<YYYY-MM>/response.json   exactly what the API sent
    data/raw/weather/city=<slug>/month=<YYYY-MM>/meta.json       what was asked, and when

Run from the repository root:

    python ingest/load_weather.py --cities kumasi accra tamale   # a first small test
    python ingest/load_weather.py                                # all 16 cities, 2024-10 to 2026-10
    python ingest/load_weather.py --force                        # refetch everything

Running it twice is safe: a partition is skipped when it is complete and was
fetched with the same inputs (coordinates, dates, variables).
"""
import argparse
import csv
import logging
import sys
import time
from collections import Counter
from pathlib import Path

import common

WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
DAILY_VARIABLES = "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode"
TIMEZONE = "Africa/Accra"
CITIES_FILE = Path("ingest/config/cities.csv")
DEFAULT_START = "2024-10"
DEFAULT_END = "2026-10"
DEFAULT_PAUSE = 1.0  # seconds between real requests; check Open-Meteo's rate limits


def read_cities(path: Path = CITIES_FILE) -> list[dict]:
    """Rows of cities.csv as dictionaries (city_slug, city, region, latitude, ...)."""
    with open(path, newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def build_weather_request(city: dict, first_day: str, last_day: str) -> dict:
    """The request parameters for one city and one month.

    This dict is the single source of truth: it is sent to the API, saved in
    meta.json, and compared by the skip check. Coordinates are the ones I
    requested; the API snaps them to its own grid cell.
    """
    return {
        "latitude": float(city["latitude"]),
        "longitude": float(city["longitude"]),
        "start_date": first_day,
        "end_date": last_day,
        "daily": DAILY_VARIABLES,
        "timezone": TIMEZONE,
    }


def weather_partition(city_slug: str, month: str, root: Path = common.DATA_ROOT) -> Path:
    return common.partition_dir("weather", month, root, city=city_slug)


def load_city_month(city: dict, month: str, first_day: str, last_day: str,
                    root: Path = common.DATA_ROOT, *, force: bool = False) -> str:
    """Returns 'skipped', 'fetched' or 'failed'."""
    params = build_weather_request(city, first_day, last_day)
    partition = weather_partition(city["city_slug"], month, root)
    extra_meta = {
        "source": "open-meteo-archive",
        "city_slug": city["city_slug"],
        "month": month,
        "first_day": first_day,
        "last_day": last_day,
    }
    return common.load_partition(WEATHER_URL, params, partition, extra_meta, force=force)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load raw daily weather per city per month.")
    parser.add_argument("--cities", nargs="+", metavar="SLUG",
                        help="city slugs to load (default: every city in the CSV)")
    parser.add_argument("--start", default=DEFAULT_START, help="first month, YYYY-MM")
    parser.add_argument("--end", default=DEFAULT_END, help="last month, YYYY-MM")
    parser.add_argument("--force", action="store_true", help="refetch even if up to date")
    parser.add_argument("--pause", type=float, default=DEFAULT_PAUSE,
                        help="seconds to wait after each real request")
    parser.add_argument("--root", type=Path, default=common.DATA_ROOT, help="raw data folder")
    parser.add_argument("--cities-file", type=Path, default=CITIES_FILE)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    cities = read_cities(args.cities_file)
    if args.cities:
        known = {city["city_slug"] for city in cities}
        unknown = sorted(set(args.cities) - known)
        if unknown:
            parser.error(f"unknown city slug(s): {', '.join(unknown)}")
        cities = [city for city in cities if city["city_slug"] in args.cities]

    months = common.month_ranges(args.start, args.end)
    results: Counter = Counter()
    failed: list[str] = []

    for city in cities:
        for month, first_day, last_day in months:
            result = load_city_month(city, month, first_day, last_day, args.root,
                                     force=args.force)
            results[result] += 1
            if result == "failed":
                failed.append(f"{city['city_slug']} {month}")
            elif result == "fetched":
                time.sleep(args.pause)
        logging.info("%s done", city["city_slug"])

    print(f"\nweather: {len(cities)} cities x {len(months)} months = "
          f"{len(cities) * len(months)} partitions")
    print(f"  skipped: {results['skipped']}  fetched: {results['fetched']}  "
          f"failed: {results['failed']}")
    if failed:
        print("failed partitions (run again to retry them):")
        for item in failed:
            print("  ", item)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())