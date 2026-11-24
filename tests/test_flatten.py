"""Tests for ingest/flatten.py, in the order you build the functions.

Run one step at a time while you build:
    python -m pytest tests/test_flatten.py -k step1
    python -m pytest tests/test_flatten.py -k step2
    ...
Then run them all:
    python -m pytest tests/test_flatten.py

Every test builds its own small raw-data folder in a temporary place, using the
same helper (common.write_partition) that the real loaders use, so the files look
exactly like real bronze files: response.json first, meta.json as the done marker.
"""
import json
from decimal import Decimal

import pytest

import common
import flatten


# --------------------------------------------------------------------------
# Helpers that build fake bronze data
# --------------------------------------------------------------------------
def days_of(month, n):
    """The first n days of a month as ISO dates."""
    return [f"{month}-{day:02d}" for day in range(1, n + 1)]


def weather_response(days):
    """An Open-Meteo-shaped response: one list per variable."""
    return {
        "latitude": 6.7, "longitude": -1.6, "generationtime_ms": 0.2,
        "daily": {
            "time": days,
            "temperature_2m_max": [30.0 + i % 5 for i in range(len(days))],
            "temperature_2m_min": [22.0 + i % 3 for i in range(len(days))],
            "precipitation_sum": [round((i % 7) * 0.5, 1) for i in range(len(days))],
            "weathercode": [i % 4 for i in range(len(days))],
        },
    }


def put_weather(root, city, month, days, finished=True):
    partition = common.partition_dir("weather", month, root, city=city)
    meta = {"city_slug": city, "month": month, "request_params": {}, "http_status": 200}
    common.write_partition(partition, json.dumps(weather_response(days)).encode("utf-8"), meta)
    if not finished:
        (partition / common.META_FILE).unlink()
    return partition


def fx_text(*records):
    """Raw FX JSON text. Each record is (date, rate_text). The rate text is written
    exactly as given, so '11.60' keeps its trailing zero."""
    items = ",".join('{"date":"%s","base":"USD","quote":"GHS","rate":%s}' % rec for rec in records)
    return "[" + items + "]"


def put_fx(root, month, *records, provider="bog", finished=True):
    partition = common.partition_dir("fx", month, root, provider=provider, pair="usd-ghs")
    meta = {"provider": provider, "pair": "usd-ghs", "month": month,
            "request_params": {}, "http_status": 200}
    common.write_partition(partition, fx_text(*records).encode("utf-8"), meta)
    if not finished:
        (partition / common.META_FILE).unlink()
    return partition


# --------------------------------------------------------------------------
# Step 1: columns_to_rows
# --------------------------------------------------------------------------
def test_step1_two_days_become_two_rows():
    daily = {"time": ["2026-11-01", "2026-11-02"],
             "temperature_2m_max": [31.3, 30.1], "temperature_2m_min": [22.9, 23.0],
             "precipitation_sum": [1.5, 0.0], "weathercode": [53, 1]}
    assert flatten.columns_to_rows(daily) == [
        {"time": "2026-11-01", "temperature_2m_max": 31.3, "temperature_2m_min": 22.9,
         "precipitation_sum": 1.5, "weathercode": 53},
        {"time": "2026-11-02", "temperature_2m_max": 30.1, "temperature_2m_min": 23.0,
         "precipitation_sum": 0.0, "weathercode": 1},
    ]


def test_step1_a_missing_value_stays_none():
    daily = {"time": ["2026-11-01"], "temperature_2m_max": [None], "temperature_2m_min": [22.9],
             "precipitation_sum": [None], "weathercode": [53]}
    row = flatten.columns_to_rows(daily)[0]
    assert row["temperature_2m_max"] is None and row["precipitation_sum"] is None


def test_step1_lists_of_different_lengths_raise():
    daily = {"time": ["2026-11-01", "2026-11-02"], "temperature_2m_max": [31.3],
             "temperature_2m_min": [22.9, 23.0], "precipitation_sum": [1.5, 0.0],
             "weathercode": [53, 1]}
    with pytest.raises(ValueError):
        flatten.columns_to_rows(daily)


def test_step1_no_days_gives_no_rows():
    daily = {"time": [], "temperature_2m_max": [], "temperature_2m_min": [],
             "precipitation_sum": [], "weathercode": []}
    assert flatten.columns_to_rows(daily) == []


# --------------------------------------------------------------------------
# Step 2: read_weather_partition
# --------------------------------------------------------------------------
def test_step2_every_row_has_the_city_slug_and_all_columns(tmp_path):
    partition = put_weather(tmp_path, "kumasi", "2025-03", days_of("2025-03", 3))
    rows = flatten.read_weather_partition(partition)
    assert len(rows) == 3
    assert all(set(row) == set(flatten.WEATHER_COLUMNS) for row in rows)
    assert {row["city_slug"] for row in rows} == {"kumasi"}


def test_step2_values_match_the_response(tmp_path):
    days = days_of("2025-03", 3)
    partition = put_weather(tmp_path, "kumasi", "2025-03", days)
    rows = flatten.read_weather_partition(partition)
    daily = weather_response(days)["daily"]
    assert [row["time"] for row in rows] == days
    assert rows[1]["temperature_2m_max"] == daily["temperature_2m_max"][1]
    assert rows[2]["precipitation_sum"] == daily["precipitation_sum"][2]


# --------------------------------------------------------------------------
# Step 3: flatten_weather
# --------------------------------------------------------------------------
def test_step3_collects_every_city_and_month(tmp_path):
    for city in ("accra", "kumasi"):
        for month in ("2025-01", "2025-02"):
            put_weather(tmp_path, city, month, days_of(month, 3))
    rows, skipped = flatten.flatten_weather(tmp_path)
    assert len(rows) == 2 * 2 * 3
    assert skipped == 0


def test_step3_rows_are_sorted_by_city_then_time(tmp_path):
    put_weather(tmp_path, "kumasi", "2025-02", days_of("2025-02", 2))
    put_weather(tmp_path, "accra", "2025-02", ["2025-02-03", "2025-02-01", "2025-02-02"])  # out of order
    put_weather(tmp_path, "kumasi", "2025-01", days_of("2025-01", 2))
    rows, _ = flatten.flatten_weather(tmp_path)
    keys = [(row["city_slug"], row["time"]) for row in rows]
    assert keys == sorted(keys)
    assert keys[0] == ("accra", "2025-02-01")


def test_step3_a_partition_without_meta_is_skipped_and_counted(tmp_path):
    put_weather(tmp_path, "accra", "2025-01", days_of("2025-01", 3))
    put_weather(tmp_path, "accra", "2025-02", days_of("2025-02", 3), finished=False)
    rows, skipped = flatten.flatten_weather(tmp_path)
    assert skipped == 1
    assert len(rows) == 3
    assert not any(row["time"].startswith("2025-02") for row in rows)


def test_step3_an_empty_folder_gives_nothing(tmp_path):
    assert flatten.flatten_weather(tmp_path) == ([], 0)


# --------------------------------------------------------------------------
# Step 4: flatten_fx
# --------------------------------------------------------------------------
def test_step4_every_record_becomes_a_row(tmp_path):
    put_fx(tmp_path, "2025-01", ("2025-01-02", "11.60"), ("2025-01-03", "11.62"), ("2025-01-06", "11.70"))
    rows, skipped = flatten.flatten_fx(tmp_path)
    assert skipped == 0 and len(rows) == 3
    assert all(set(row) == set(flatten.FX_COLUMNS) for row in rows)
    assert rows[0]["base"] == "USD" and rows[0]["quote"] == "GHS"


def test_step4_the_rate_is_a_decimal_with_its_exact_text(tmp_path):
    put_fx(tmp_path, "2025-01", ("2025-01-02", "11.60"))
    rows, _ = flatten.flatten_fx(tmp_path)
    assert isinstance(rows[0]["rate"], Decimal)
    assert str(rows[0]["rate"]) == "11.60"  # a float would have lost the trailing zero


def test_step4_a_record_in_two_neighbouring_partitions_appears_once(tmp_path):
    put_fx(tmp_path, "2024-12", ("2024-12-30", "11.50"), ("2024-12-31", "11.55"))
    put_fx(tmp_path, "2025-01", ("2024-12-31", "11.55"), ("2025-01-02", "11.60"))
    rows, _ = flatten.flatten_fx(tmp_path)
    assert [row["date"] for row in rows] == ["2024-12-30", "2024-12-31", "2025-01-02"]


def test_step4_two_different_rates_for_one_date_raise(tmp_path):
    put_fx(tmp_path, "2024-12", ("2024-12-31", "11.55"))
    put_fx(tmp_path, "2025-01", ("2024-12-31", "11.99"))
    with pytest.raises(ValueError):
        flatten.flatten_fx(tmp_path)


def test_step4_rows_are_sorted_by_date(tmp_path):
    put_fx(tmp_path, "2025-02", ("2025-02-03", "11.70"))
    put_fx(tmp_path, "2025-01", ("2025-01-06", "11.65"), ("2025-01-02", "11.60"))  # out of order
    rows, _ = flatten.flatten_fx(tmp_path)
    assert [row["date"] for row in rows] == ["2025-01-02", "2025-01-06", "2025-02-03"]


def test_step4_a_partition_without_meta_is_skipped_and_counted(tmp_path):
    put_fx(tmp_path, "2025-01", ("2025-01-02", "11.60"))
    put_fx(tmp_path, "2025-02", ("2025-02-03", "11.70"), finished=False)
    rows, skipped = flatten.flatten_fx(tmp_path)
    assert skipped == 1 and len(rows) == 1


def test_step4_only_the_requested_provider_is_read(tmp_path):
    put_fx(tmp_path, "2025-01", ("2025-01-02", "11.60"))
    put_fx(tmp_path, "2025-01", ("2025-01-02", "99.99"), provider="other")
    rows, _ = flatten.flatten_fx(tmp_path)
    assert len(rows) == 1 and str(rows[0]["rate"]) == "11.60"


# --------------------------------------------------------------------------
# Step 5: write_csv
# --------------------------------------------------------------------------
def test_step5_header_then_rows_in_column_order(tmp_path):
    path = tmp_path / "out.csv"
    flatten.write_csv(path, [{"b": 2, "a": 1}, {"a": 3, "b": 4}], ["a", "b"])
    assert path.read_bytes() == b"a,b\n1,2\n3,4\n"  # Unix line endings, no blank lines


def test_step5_none_becomes_an_empty_cell(tmp_path):
    path = tmp_path / "out.csv"
    flatten.write_csv(path, [{"a": None, "b": 1}], ["a", "b"])
    assert path.read_bytes() == b"a,b\n,1\n"


def test_step5_a_decimal_keeps_its_exact_text(tmp_path):
    path = tmp_path / "out.csv"
    flatten.write_csv(path, [{"rate": Decimal("11.60")}], ["rate"])
    assert path.read_bytes() == b"rate\n11.60\n"


def test_step5_a_comma_inside_a_value_is_quoted(tmp_path):
    path = tmp_path / "out.csv"
    flatten.write_csv(path, [{"a": "x,y"}], ["a"])
    assert path.read_bytes() == b'a\n"x,y"\n'


def test_step5_the_parent_folder_is_created(tmp_path):
    path = tmp_path / "flat" / "deeper" / "out.csv"
    flatten.write_csv(path, [{"a": 1}], ["a"])
    assert path.is_file()


# --------------------------------------------------------------------------
# Step 6: main
# --------------------------------------------------------------------------
def build_raw(root):
    for city in ("accra", "kumasi"):
        for month in ("2025-01", "2025-02"):
            put_weather(root, city, month, days_of(month, 3))
    put_weather(root, "tamale", "2025-01", days_of("2025-01", 3), finished=False)
    put_fx(root, "2024-12", ("2024-12-31", "11.55"))
    put_fx(root, "2025-01", ("2024-12-31", "11.55"), ("2025-01-02", "11.60"))


def run_main(raw, out, *extra):
    return flatten.main(["--root", str(raw), "--out", str(out), *extra])


def test_step6_writes_both_csv_files(tmp_path):
    raw, out = tmp_path / "raw", tmp_path / "flat"
    build_raw(raw)
    assert run_main(raw, out) == 0
    weather = (out / "weather_daily.csv").read_text(encoding="utf-8").splitlines()
    fx = (out / "fx_rates.csv").read_text(encoding="utf-8").splitlines()
    assert weather[0] == "city_slug,time,temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode"
    assert len(weather) == 1 + 12
    assert fx[0] == "date,base,quote,rate"
    assert fx[1:] == ["2024-12-31,USD,GHS,11.55", "2025-01-02,USD,GHS,11.60"]


def test_step6_reports_the_skipped_partitions(tmp_path, capsys):
    raw, out = tmp_path / "raw", tmp_path / "flat"
    build_raw(raw)
    run_main(raw, out)
    assert "skipped" in capsys.readouterr().out.lower()


def test_step6_running_twice_gives_identical_files(tmp_path):
    raw, out = tmp_path / "raw", tmp_path / "flat"
    build_raw(raw)
    run_main(raw, out)
    first = {p.name: p.read_bytes() for p in out.iterdir()}
    run_main(raw, out)
    second = {p.name: p.read_bytes() for p in out.iterdir()}
    assert first == second and len(first) == 2


def test_step6_conflicting_rates_make_it_return_1(tmp_path):
    raw, out = tmp_path / "raw", tmp_path / "flat"
    build_raw(raw)
    put_fx(raw, "2025-02", ("2024-12-31", "99.99"))
    assert run_main(raw, out) == 1