"""Load raw exchange rates from Frankfurter (Bank of Ghana rates) into data/raw/fx/.

One partition per currency pair per month:

    data/raw/fx/provider=<key>/pair=<base>-<quote>/month=<YYYY-MM>/response.json
    data/raw/fx/provider=<key>/pair=<base>-<quote>/month=<YYYY-MM>/meta.json

Run from the repository root:

    python ingest/load_fx.py                              # usd-ghs, 2024-10 to 2026-10
    python ingest/load_fx.py --pairs usd-ghs eur-ghs gbp-ghs
    python ingest/load_fx.py --force

Things I observed and the loader must tolerate (see ingest/README.md):

* The Bank of Ghana publishes on business days only, so weekends and public
  holidays have no record. Bronze keeps exactly what arrived; gold fills gaps.
* A range that starts on a day with no rate can come back with one extra
  earlier record (a range starting on Sunday 2026-11-01 returned 2026-10-30).
  So two neighbouring partitions can hold the same record. That is expected:
  silver upserts on (date, base, quote).
"""
import argparse
import logging
import sys
import time
from collections import Counter
from pathlib import Path

import common

FX_URL = "https://api.frankfurter.dev/v2/rates"
DEFAULT_PROVIDER = "bog"
DEFAULT_PAIRS = ["usd-ghs"]
DEFAULT_START = "2024-10"
DEFAULT_END = "2026-10"
DEFAULT_PAUSE = 0.5


def split_pair(pair: str) -> tuple[str, str]:
    """'usd-ghs' -> ('USD', 'GHS')"""
    base, quote = pair.split("-")
    return base.upper(), quote.upper()


def build_fx_request(pair: str, provider: str, first_day: str, last_day: str) -> dict:
    """The request parameters for one pair and one month (see load_weather)."""
    base, quote = split_pair(pair)
    return {
        "from": first_day,
        "to": last_day,
        "base": base,
        "quotes": quote,
        "providers": provider,
    }


def fx_partition(provider: str, pair: str, month: str, root: Path = common.DATA_ROOT) -> Path:
    return common.partition_dir("fx", month, root, provider=provider, pair=pair)


def load_pair_month(pair: str, provider: str, month: str, first_day: str, last_day: str,
                    root: Path = common.DATA_ROOT, *, force: bool = False) -> str:
    """Returns 'skipped', 'fetched' or 'failed'."""
    params = build_fx_request(pair, provider, first_day, last_day)
    partition = fx_partition(provider, pair, month, root)
    extra_meta = {
        "source": "frankfurter-v2",
        "provider": provider,
        "pair": pair,
        "month": month,
        "first_day": first_day,
        "last_day": last_day,
    }
    return common.load_partition(FX_URL, params, partition, extra_meta, force=force)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load raw exchange rates per pair per month.")
    parser.add_argument("--pairs", nargs="+", default=DEFAULT_PAIRS, metavar="BASE-QUOTE")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER)
    parser.add_argument("--start", default=DEFAULT_START, help="first month, YYYY-MM")
    parser.add_argument("--end", default=DEFAULT_END, help="last month, YYYY-MM")
    parser.add_argument("--force", action="store_true", help="refetch even if up to date")
    parser.add_argument("--pause", type=float, default=DEFAULT_PAUSE)
    parser.add_argument("--root", type=Path, default=common.DATA_ROOT)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    pairs = [pair.lower() for pair in args.pairs]
    for pair in pairs:
        if pair.count("-") != 1:
            parser.error(f"pair '{pair}' must look like usd-ghs")

    months = common.month_ranges(args.start, args.end)
    results: Counter = Counter()
    failed: list[str] = []

    for pair in pairs:
        for month, first_day, last_day in months:
            result = load_pair_month(pair, args.provider, month, first_day, last_day,
                                     args.root, force=args.force)
            results[result] += 1
            if result == "failed":
                failed.append(f"{pair} {month}")
            elif result == "fetched":
                time.sleep(args.pause)
        logging.info("%s done", pair)

    print(f"\nfx: {len(pairs)} pairs x {len(months)} months = {len(pairs) * len(months)} partitions")
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