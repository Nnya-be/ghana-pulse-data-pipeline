"""End-to-end tests for the loaders and verify.py, using a fake API.

The fake API builds a realistic response from the request parameters, so the
whole pipeline (request, skip check, write, verify) runs with no network.
"""
import json
from datetime import date, timedelta

import pytest

import common
import load_fx
import load_weather
import verify

CITIES_CSV = """city_slug,city,region,latitude,longitude,coordinate_source
kumasi,Kumasi,Ashanti,6.6885,-1.6244,test
accra,Accra,Greater Accra,5.5600,-0.2057,test
tamale,Tamale,Northern,9.4008,-0.8393,test
"""


class FakeResponse:
    def __init__(self, status_code, content, url="http://fake"):
        self.status_code, self.content, self.headers, self.url = status_code, content, {}, url


def daterange(first, last):
    start, end = date.fromisoformat(first), date.fromisoformat(last)
    return [(start + timedelta(days=n)).isoformat() for n in range((end - start).days + 1)]


class FakeApi:
    """Stands in for common.fetch. Counts calls and can be told to fail."""

    def __init__(self):
        self.calls = []
        self.fail_with = None  # an HTTP status to return instead of 200

    def __call__(self, url, params, **kwargs):
        self.calls.append((url, dict(params)))
        if self.fail_with:
            return self.fail_with, b'{"error": true}', url
        if url == load_weather.WEATHER_URL:
            days = daterange(params["start_date"], params["end_date"])
            seed = int(abs(params["latitude"]) * 1000)
            body = {
                "latitude": params["latitude"] + 0.02, "longitude": params["longitude"] + 0.03,
                "generationtime_ms": 0.1 + len(self.calls) / 1000,  # differs on every call
                "daily": {
                    "time": days,
                    "temperature_2m_max": [30.0 + (seed + i) % 5 for i in range(len(days))],
                    "temperature_2m_min": [22.0 + (seed + i) % 3 for i in range(len(days))],
                    "precipitation_sum": [round(((seed + i) % 7) * 0.5, 1) for i in range(len(days))],
                    "weathercode": [(seed + i) % 4 for i in range(len(days))],
                },
            }
        else:
            # business days only, like the Bank of Ghana
            body = [
                {"date": day, "base": params["base"], "quote": params["quotes"],
                 "rate": round(11.0 + date.fromisoformat(day).toordinal() % 50 / 100, 2)}
                for day in daterange(params["from"], params["to"])
                if date.fromisoformat(day).weekday() < 5
            ]
        return 200, json.dumps(body).encode("utf-8"), url


@pytest.fixture
def api(monkeypatch):
    fake = FakeApi()
    monkeypatch.setattr(common, "fetch", fake)
    return fake


@pytest.fixture
def cities_file(tmp_path):
    path = tmp_path / "cities.csv"
    path.write_text(CITIES_CSV, encoding="utf-8")
    return path


def run_weather(tmp_path, cities_file, *extra):
    argv = ["--cities-file", str(cities_file), "--root", str(tmp_path / "raw"),
            "--start", "2024-11", "--end", "2025-02", "--pause", "0", *extra]
    return load_weather.main(argv)


def tree_bytes(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


# --------------------------------------------------------------------------
# Weather
# --------------------------------------------------------------------------
def test_first_run_fetches_every_partition(tmp_path, cities_file, api):
    assert run_weather(tmp_path, cities_file) == 0
    assert len(api.calls) == 3 * 4  # 3 cities x 4 months
    folder = tmp_path / "raw" / "weather" / "city=kumasi" / "month=2024-11"
    assert (folder / "response.json").is_file() and (folder / "meta.json").is_file()


def test_second_run_downloads_nothing_and_changes_nothing(tmp_path, cities_file, api):
    run_weather(tmp_path, cities_file)
    before = tree_bytes(tmp_path / "raw")
    calls_after_first_run = len(api.calls)

    assert run_weather(tmp_path, cities_file) == 0

    assert len(api.calls) == calls_after_first_run  # no new requests
    assert tree_bytes(tmp_path / "raw") == before  # every file byte-for-byte identical


def test_force_refetches_but_the_data_is_the_same(tmp_path, cities_file, api):
    run_weather(tmp_path, cities_file)
    cities = load_weather.read_cities(cities_file)
    first = verify.verify_weather(tmp_path / "raw", cities, "2024-11", "2025-02")

    run_weather(tmp_path, cities_file, "--force")
    second = verify.verify_weather(tmp_path / "raw", cities, "2024-11", "2025-02")

    assert len(api.calls) == 24
    assert first["fingerprint"] == second["fingerprint"]
    assert first["rows"] == second["rows"]


def test_a_corrected_coordinate_refetches_only_that_city(tmp_path, cities_file, api):
    run_weather(tmp_path, cities_file)
    before_calls = len(api.calls)

    cities_file.write_text(CITIES_CSV.replace("6.6885", "6.7000"), encoding="utf-8")
    run_weather(tmp_path, cities_file)

    assert len(api.calls) - before_calls == 4  # kumasi only, 4 months


def test_a_failed_request_writes_nothing_and_returns_a_nonzero_code(tmp_path, cities_file, api):
    api.fail_with = 500
    assert run_weather(tmp_path, cities_file) == 1
    assert not (tmp_path / "raw").exists() or not list((tmp_path / "raw").rglob("*.json"))


def test_failed_partitions_are_filled_by_the_next_run(tmp_path, cities_file, api):
    api.fail_with = 500
    run_weather(tmp_path, cities_file)
    api.fail_with = None
    assert run_weather(tmp_path, cities_file) == 0
    report = verify.verify_weather(tmp_path / "raw", load_weather.read_cities(cities_file),
                                   "2024-11", "2025-02")
    assert report["ok"]


def test_a_partition_without_meta_is_fetched_again(tmp_path, cities_file, api):
    run_weather(tmp_path, cities_file)
    (tmp_path / "raw" / "weather" / "city=accra" / "month=2025-01" / "meta.json").unlink()
    calls = len(api.calls)
    run_weather(tmp_path, cities_file)
    assert len(api.calls) - calls == 1


def test_the_loader_only_loads_the_cities_asked_for(tmp_path, cities_file, api):
    run_weather(tmp_path, cities_file, "--cities", "tamale")
    assert len(api.calls) == 4
    assert not (tmp_path / "raw" / "weather" / "city=kumasi").exists()


def test_unknown_city_is_rejected(tmp_path, cities_file, api):
    with pytest.raises(SystemExit):
        run_weather(tmp_path, cities_file, "--cities", "atlantis")


def test_the_request_keeps_the_negative_longitude():
    city = {"city_slug": "kumasi", "latitude": "6.6885", "longitude": "-1.6244"}
    params = load_weather.build_weather_request(city, "2025-03-01", "2025-03-31")
    assert params["longitude"] == -1.6244
    assert params["start_date"] == "2025-03-01" and params["end_date"] == "2025-03-31"


# --------------------------------------------------------------------------
# verify.py
# --------------------------------------------------------------------------
def test_verify_reports_the_expected_number_of_weather_rows(tmp_path, cities_file, api):
    run_weather(tmp_path, cities_file)
    report = verify.verify_weather(tmp_path / "raw", load_weather.read_cities(cities_file),
                                   "2024-11", "2025-02")
    days = 30 + 31 + 31 + 28  # Nov, Dec, Jan, Feb
    assert report["ok"]
    assert report["rows"] == report["rows_expected"] == 3 * days
    assert report["duplicates"] == 0 and report["partitions_ok"] == 12


def test_verify_finds_a_missing_partition(tmp_path, cities_file, api):
    run_weather(tmp_path, cities_file)
    (tmp_path / "raw" / "weather" / "city=accra" / "month=2024-12" / "response.json").unlink()
    report = verify.verify_weather(tmp_path / "raw", load_weather.read_cities(cities_file),
                                   "2024-11", "2025-02")
    assert not report["ok"]
    assert report["missing"] == ["accra 2024-12"]


def test_verify_finds_a_response_with_a_missing_day(tmp_path, cities_file, api):
    run_weather(tmp_path, cities_file)
    folder = tmp_path / "raw" / "weather" / "city=tamale" / "month=2025-01"
    data = json.loads((folder / "response.json").read_text())
    for values in data["daily"].values():
        values.pop()
    body = json.dumps(data).encode()
    meta = json.loads((folder / "meta.json").read_text())
    meta["bytes"], meta["sha256"] = len(body), common.sha256_bytes(body)
    (folder / "response.json").write_bytes(body)
    (folder / "meta.json").write_text(json.dumps(meta))
    report = verify.verify_weather(tmp_path / "raw", load_weather.read_cities(cities_file),
                                   "2024-11", "2025-02")
    assert not report["ok"]
    assert any("tamale 2025-01" in p for p in report["problems"])


# --------------------------------------------------------------------------
# FX
# --------------------------------------------------------------------------
def run_fx(tmp_path, *extra):
    return load_fx.main(["--root", str(tmp_path / "raw"), "--start", "2024-11",
                         "--end", "2025-02", "--pause", "0", *extra])


def test_fx_second_run_downloads_nothing(tmp_path, api):
    assert run_fx(tmp_path) == 0
    before = tree_bytes(tmp_path / "raw")
    calls = len(api.calls)
    assert run_fx(tmp_path) == 0
    assert len(api.calls) == calls
    assert tree_bytes(tmp_path / "raw") == before


def test_fx_partition_path_and_pairs(tmp_path, api):
    run_fx(tmp_path, "--pairs", "usd-ghs", "eur-ghs")
    assert len(api.calls) == 2 * 4
    assert (tmp_path / "raw" / "fx" / "provider=bog" / "pair=eur-ghs" / "month=2025-01"
            / "response.json").is_file()


def test_fx_request_uses_upper_case_codes_and_the_provider():
    params = load_fx.build_fx_request("usd-ghs", "bog", "2025-03-01", "2025-03-31")
    assert params == {"from": "2025-03-01", "to": "2025-03-31", "base": "USD",
                      "quotes": "GHS", "providers": "bog"}


def test_fx_verify_lists_no_gaps_when_every_weekday_has_a_rate(tmp_path, api):
    run_fx(tmp_path)
    report = verify.verify_fx(tmp_path / "raw", ["usd-ghs"], "bog", "2024-11", "2025-02")
    assert report["ok"]
    assert report["gaps"] == []  # the fake publishes every weekday, so no holidays


def test_fx_verify_finds_a_single_holiday_in_the_middle_of_a_week(tmp_path, api):
    run_fx(tmp_path)
    folder = tmp_path / "raw" / "fx" / "provider=bog" / "pair=usd-ghs" / "month=2025-01"
    records = json.loads((folder / "response.json").read_text())
    # remove Wednesday 2025-01-15: the neighbouring dates are only 2 days apart
    records = [r for r in records if r["date"] != "2025-01-15"]
    body = json.dumps(records).encode()
    meta = json.loads((folder / "meta.json").read_text())
    meta["bytes"], meta["sha256"] = len(body), common.sha256_bytes(body)
    (folder / "response.json").write_bytes(body)
    (folder / "meta.json").write_text(json.dumps(meta))
    report = verify.verify_fx(tmp_path / "raw", ["usd-ghs"], "bog", "2024-11", "2025-02")
    assert report["ok"]  # a holiday is information, not an error
    assert report["gaps"] == ["usd-ghs: no rate on 2025-01-15 (Wednesday)"]


def test_fx_verify_finds_conflicting_overlaps(tmp_path, api):
    run_fx(tmp_path)
    # put a record with a different rate for the same date into a second partition
    folder = tmp_path / "raw" / "fx" / "provider=bog" / "pair=usd-ghs" / "month=2025-01"
    records = json.loads((folder / "response.json").read_text())
    other = tmp_path / "raw" / "fx" / "provider=bog" / "pair=usd-ghs" / "month=2025-02"
    data = json.loads((other / "response.json").read_text())
    data.append({**records[0], "rate": 99.0})
    body = json.dumps(data).encode()
    meta = json.loads((other / "meta.json").read_text())
    meta["bytes"], meta["sha256"] = len(body), common.sha256_bytes(body)
    (other / "response.json").write_bytes(body)
    (other / "meta.json").write_text(json.dumps(meta))
    report = verify.verify_fx(tmp_path / "raw", ["usd-ghs"], "bog", "2024-11", "2025-02")
    assert not report["ok"]
    assert any("conflicting" in p for p in report["problems"])