"""Shared helpers for the raw-data loaders (weather and FX).

Bronze rules these helpers enforce:

* A partition always lives at the same path, so a rerun overwrites it and
  never adds a second copy.
* response.json is written first and meta.json last. meta.json is the
  "done" marker: a partition without it is treated as unfinished.
* Every file is written under a temporary name and then renamed, so a crash
  can never leave a half-written file at the final path.
* A failed request writes nothing.
* The skip check compares the INPUTS of a request (coordinates, dates,
  variables), never the results (fetch time, size), which change every run.
"""
import calendar
import hashlib
import json
import logging
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

log = logging.getLogger("ingest")

DATA_ROOT = Path("data/raw")
RESPONSE_FILE = "response.json"
META_FILE = "meta.json"
RETRY_STATUSES = {429, 500, 502, 503, 504}


# --------------------------------------------------------------------------
# Months and paths (pure functions: no network, no files)
# --------------------------------------------------------------------------
def month_ranges(start: str, end: str) -> list[tuple[str, str, str]]:
    """start and end are 'YYYY-MM', both inclusive.

    Returns one (month, first_day, last_day) tuple per month, for example
    ('2024-02', '2024-02-01', '2024-02-29').
    Raises ValueError if start is after end.
    """
    start_year, start_month = (int(part) for part in start.split("-"))
    end_year, end_month = (int(part) for part in end.split("-"))
    if (start_year, start_month) > (end_year, end_month):
        raise ValueError(f"start {start} must not be after end {end}")

    ranges = []
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        # monthrange returns (weekday the month starts on, number of days)
        last_day = calendar.monthrange(year, month)[1]
        label = f"{year}-{month:02d}"
        ranges.append((label, f"{label}-01", f"{label}-{last_day:02d}"))
        month += 1
        if month == 13:  # December rolls over into January
            month = 1
            year += 1
    return ranges


def partition_dir(source: str, month: str, root: Path = DATA_ROOT, **keys: str) -> Path:
    """Folder for one partition: <root>/<source>/<key>=<value>/.../month=<month>

    partition_dir('weather', '2025-03', city='kumasi')
        -> data/raw/weather/city=kumasi/month=2025-03
    The same inputs always give the same path.
    """
    path = Path(root) / source
    for key, value in keys.items():
        path = path / f"{key}={value}"
    return path / f"month={month}"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------
# Writing files safely
# --------------------------------------------------------------------------
def write_atomic(path: Path, data: bytes) -> None:
    """Write data to a temporary file in the same folder, then rename it.

    The rename is atomic, so readers see either the old file or the complete
    new one, never a half-written file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as tmp_file:
            tmp_file.write(data)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def write_partition(partition: Path, body: bytes, meta: dict) -> None:
    """Write response.json first, then meta.json (the 'done' marker)."""
    write_atomic(partition / RESPONSE_FILE, body)
    full_meta = {**meta, "bytes": len(body), "sha256": sha256_bytes(body)}
    meta_bytes = json.dumps(full_meta, indent=2, sort_keys=True).encode("utf-8")
    write_atomic(partition / META_FILE, meta_bytes)


# --------------------------------------------------------------------------
# Deciding whether to skip
# --------------------------------------------------------------------------
def is_up_to_date(partition: Path, request_params: dict) -> bool:
    """True only if the partition is complete AND was fetched with these inputs.

    - response.json and meta.json both exist
    - meta.json says the HTTP status was 200
    - the size and SHA-256 of response.json match what meta.json recorded
    - the request parameters recorded in meta.json equal request_params
    Anything else, including an unreadable meta.json, returns False.
    """
    partition = Path(partition)
    response_path = partition / RESPONSE_FILE
    meta_path = partition / META_FILE
    if not response_path.is_file() or not meta_path.is_file():
        return False
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        body = response_path.read_bytes()
        return (
            meta["http_status"] == 200
            and meta["bytes"] == len(body)
            and meta["sha256"] == sha256_bytes(body)
            and meta["request_params"] == request_params
        )
    except (ValueError, KeyError, TypeError, OSError):
        # ValueError covers a corrupt meta.json (JSONDecodeError is one)
        return False


# --------------------------------------------------------------------------
# Talking to the network
# --------------------------------------------------------------------------
def _wait_seconds(response, attempt: int, base_wait: float) -> float:
    """Honour a numeric Retry-After header, otherwise back off exponentially."""
    retry_after = response.headers.get("Retry-After", "")
    if retry_after.isdigit():
        return min(int(retry_after), 60)
    return base_wait * 2 ** (attempt - 1)


def fetch(url: str, params: dict, *, max_attempts: int = 5,
          base_wait: float = 2.0, timeout: int = 30) -> tuple[int, bytes, str]:
    """GET with a timeout. Retries with a growing wait on 429, 5xx and
    connection problems. Other 4xx errors are my mistakes, so they are not
    retried. Returns (status_code, body_bytes, final_url).
    Raises requests.RequestException if every attempt failed to connect.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(url, params=params, timeout=timeout)
        except (requests.ConnectionError, requests.Timeout) as error:
            if attempt == max_attempts:
                raise
            wait = base_wait * 2 ** (attempt - 1)
            log.warning("attempt %s failed (%s), waiting %.0fs",
                        attempt, type(error).__name__, wait)
            time.sleep(wait)
            continue

        if response.status_code in RETRY_STATUSES and attempt < max_attempts:
            wait = _wait_seconds(response, attempt, base_wait)
            log.warning("attempt %s got HTTP %s, waiting %.0fs",
                        attempt, response.status_code, wait)
            time.sleep(wait)
            continue

        return response.status_code, response.content, response.url

    raise RuntimeError("fetch: no attempts were made")  # max_attempts < 1


def load_partition(url: str, params: dict, partition: Path, extra_meta: dict,
                   *, force: bool = False) -> str:
    """Fetch one partition and store it. Returns 'skipped', 'fetched' or 'failed'.

    1. Skip if the partition is complete and was fetched with the same inputs.
    2. Fetch. If anything goes wrong, write NOTHING and return 'failed'.
    3. Write response.json first and meta.json last.
    """
    partition = Path(partition)
    if not force and is_up_to_date(partition, params):
        return "skipped"

    try:
        status, body, final_url = fetch(url, params)
    except requests.RequestException as error:
        log.error("%s: request failed (%s)", partition, type(error).__name__)
        return "failed"

    if status != 200:
        log.error("%s: HTTP %s %s", partition, status, body[:200])
        return "failed"

    try:
        json.loads(body)  # bronze keeps the bytes as they are, but they must be JSON
    except ValueError:
        log.error("%s: the response was not valid JSON", partition)
        return "failed"

    meta = {
        **extra_meta,
        "request_params": params,
        "url": final_url,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "http_status": status,
    }
    write_partition(partition, body, meta)
    return "fetched"