"""Tests for ingest/common.py. No network and no real data folder is used."""
import json
import os

import pytest
import requests

import common


# --------------------------------------------------------------------------
# month_ranges
# --------------------------------------------------------------------------
def test_two_years_of_months_gives_25_tuples():
    ranges = common.month_ranges("2024-10", "2026-10")
    assert len(ranges) == 25
    assert ranges[0] == ("2024-10", "2024-10-01", "2024-10-31")
    assert ranges[-1] == ("2026-10", "2026-10-01", "2026-10-31")


def test_leap_year_february_ends_on_the_29th():
    assert common.month_ranges("2024-02", "2024-02") == [("2024-02", "2024-02-01", "2024-02-29")]


def test_normal_february_ends_on_the_28th():
    assert common.month_ranges("2026-02", "2026-02") == [("2026-02", "2026-02-01", "2026-02-28")]


def test_december_rolls_over_into_january():
    assert common.month_ranges("2024-12", "2025-01") == [
        ("2024-12", "2024-12-01", "2024-12-31"),
        ("2025-01", "2025-01-01", "2025-01-31"),
    ]


def test_same_start_and_end_gives_one_month():
    assert len(common.month_ranges("2025-06", "2025-06")) == 1


def test_start_after_end_raises():
    with pytest.raises(ValueError):
        common.month_ranges("2025-03", "2025-02")


def test_every_month_has_two_digit_parts():
    for label, first_day, last_day in common.month_ranges("2024-01", "2024-12"):
        assert len(first_day) == len(last_day) == 10
        assert first_day.startswith(label) and last_day.startswith(label)


# --------------------------------------------------------------------------
# partition_dir
# --------------------------------------------------------------------------
def test_weather_partition_path(tmp_path):
    path = common.partition_dir("weather", "2025-03", tmp_path, city="kumasi")
    assert path == tmp_path / "weather" / "city=kumasi" / "month=2025-03"


def test_fx_partition_path_keeps_key_order(tmp_path):
    path = common.partition_dir("fx", "2025-03", tmp_path, provider="bog", pair="usd-ghs")
    assert path == tmp_path / "fx" / "provider=bog" / "pair=usd-ghs" / "month=2025-03"


def test_same_inputs_give_the_same_path(tmp_path):
    first = common.partition_dir("weather", "2025-03", tmp_path, city="kumasi")
    second = common.partition_dir("weather", "2025-03", tmp_path, city="kumasi")
    assert first == second


# --------------------------------------------------------------------------
# write_atomic
# --------------------------------------------------------------------------
def test_write_atomic_writes_the_bytes_and_creates_folders(tmp_path):
    target = tmp_path / "a" / "b" / "file.json"
    common.write_atomic(target, b'{"x": 1}')
    assert target.read_bytes() == b'{"x": 1}'


def test_write_atomic_leaves_no_temporary_file(tmp_path):
    target = tmp_path / "file.json"
    common.write_atomic(target, b"data")
    assert [p.name for p in tmp_path.iterdir()] == ["file.json"]


def test_write_atomic_overwrites_an_existing_file(tmp_path):
    target = tmp_path / "file.json"
    common.write_atomic(target, b"old")
    common.write_atomic(target, b"new")
    assert target.read_bytes() == b"new"


def test_a_crash_keeps_the_old_file_and_removes_the_temporary_one(tmp_path, monkeypatch):
    target = tmp_path / "file.json"
    common.write_atomic(target, b"old")

    def broken_replace(src, dst):
        raise OSError("disk went away")

    monkeypatch.setattr(os, "replace", broken_replace)
    with pytest.raises(OSError):
        common.write_atomic(target, b"new")
    assert target.read_bytes() == b"old"
    assert [p.name for p in tmp_path.iterdir()] == ["file.json"]


# --------------------------------------------------------------------------
# is_up_to_date
# --------------------------------------------------------------------------
PARAMS = {"latitude": 6.6885, "longitude": -1.6244, "start_date": "2025-03-01",
          "end_date": "2025-03-31", "daily": "temperature_2m_max", "timezone": "Africa/Accra"}


def make_partition(folder, params=PARAMS, body=b'{"daily": {}}', **meta_overrides):
    meta = {"request_params": params, "http_status": 200}
    meta.update(meta_overrides)
    common.write_partition(folder, body, meta)
    return folder


def test_complete_partition_with_same_params_is_up_to_date(tmp_path):
    assert common.is_up_to_date(make_partition(tmp_path / "p"), PARAMS)


def test_missing_meta_means_not_up_to_date(tmp_path):
    folder = make_partition(tmp_path / "p")
    (folder / common.META_FILE).unlink()
    assert not common.is_up_to_date(folder, PARAMS)


def test_missing_response_means_not_up_to_date(tmp_path):
    folder = make_partition(tmp_path / "p")
    (folder / common.RESPONSE_FILE).unlink()
    assert not common.is_up_to_date(folder, PARAMS)


def test_changed_coordinates_mean_not_up_to_date(tmp_path):
    folder = make_partition(tmp_path / "p")
    assert not common.is_up_to_date(folder, {**PARAMS, "latitude": 6.7})


def test_changed_variables_mean_not_up_to_date(tmp_path):
    folder = make_partition(tmp_path / "p")
    assert not common.is_up_to_date(folder, {**PARAMS, "daily": "precipitation_sum"})


def test_wrong_size_means_not_up_to_date(tmp_path):
    folder = make_partition(tmp_path / "p")
    (folder / common.RESPONSE_FILE).write_bytes(b"truncated")
    assert not common.is_up_to_date(folder, PARAMS)


def test_same_size_but_different_content_means_not_up_to_date(tmp_path):
    folder = make_partition(tmp_path / "p", body=b"aaaa")
    (folder / common.RESPONSE_FILE).write_bytes(b"bbbb")
    assert not common.is_up_to_date(folder, PARAMS)


def test_corrupt_meta_means_not_up_to_date(tmp_path):
    folder = make_partition(tmp_path / "p")
    (folder / common.META_FILE).write_text("{ not json", encoding="utf-8")
    assert not common.is_up_to_date(folder, PARAMS)


def test_a_failed_status_in_meta_means_not_up_to_date(tmp_path):
    folder = make_partition(tmp_path / "p", http_status=500)
    assert not common.is_up_to_date(folder, PARAMS)


def test_results_that_change_every_run_are_ignored(tmp_path):
    folder = make_partition(tmp_path / "p", fetched_at="2020-01-01T00:00:00+00:00")
    meta = json.loads((folder / common.META_FILE).read_text())
    meta["fetched_at"] = "2026-11-20T10:00:00+00:00"
    (folder / common.META_FILE).write_text(json.dumps(meta))
    assert common.is_up_to_date(folder, PARAMS)


# --------------------------------------------------------------------------
# fetch (the network is replaced by a fake)
# --------------------------------------------------------------------------
class FakeResponse:
    def __init__(self, status_code, content=b"{}", headers=None, url="http://x"):
        self.status_code, self.content, self.headers, self.url = status_code, content, headers or {}, url


@pytest.fixture
def no_sleep(monkeypatch):
    waits = []
    monkeypatch.setattr(common.time, "sleep", waits.append)
    return waits


def test_fetch_returns_status_body_and_url(monkeypatch, no_sleep):
    monkeypatch.setattr(common.requests, "get",
                        lambda url, params, timeout: FakeResponse(200, b'{"ok": 1}', url="http://x?a=1"))
    assert common.fetch("http://x", {"a": 1}) == (200, b'{"ok": 1}', "http://x?a=1")


def test_fetch_retries_on_429_then_succeeds(monkeypatch, no_sleep):
    answers = iter([FakeResponse(429), FakeResponse(200)])
    monkeypatch.setattr(common.requests, "get", lambda url, params, timeout: next(answers))
    status, _, _ = common.fetch("http://x", {})
    assert status == 200
    assert len(no_sleep) == 1


def test_fetch_waits_longer_each_time(monkeypatch, no_sleep):
    answers = iter([FakeResponse(503), FakeResponse(503), FakeResponse(200)])
    monkeypatch.setattr(common.requests, "get", lambda url, params, timeout: next(answers))
    common.fetch("http://x", {}, base_wait=2.0)
    assert no_sleep == [2.0, 4.0]


def test_fetch_honours_retry_after(monkeypatch, no_sleep):
    answers = iter([FakeResponse(429, headers={"Retry-After": "7"}), FakeResponse(200)])
    monkeypatch.setattr(common.requests, "get", lambda url, params, timeout: next(answers))
    common.fetch("http://x", {})
    assert no_sleep == [7]


def test_fetch_does_not_retry_a_400(monkeypatch, no_sleep):
    calls = []

    def fake_get(url, params, timeout):
        calls.append(1)
        return FakeResponse(400, b'{"error": true}')

    monkeypatch.setattr(common.requests, "get", fake_get)
    status, _, _ = common.fetch("http://x", {})
    assert status == 400 and len(calls) == 1 and no_sleep == []


def test_fetch_gives_up_after_max_attempts_and_returns_the_last_status(monkeypatch, no_sleep):
    monkeypatch.setattr(common.requests, "get", lambda url, params, timeout: FakeResponse(500))
    status, _, _ = common.fetch("http://x", {}, max_attempts=3)
    assert status == 500
    assert len(no_sleep) == 2


def test_fetch_raises_when_it_never_connects(monkeypatch, no_sleep):
    def fake_get(url, params, timeout):
        raise requests.ConnectionError("no network")

    monkeypatch.setattr(common.requests, "get", fake_get)
    with pytest.raises(requests.ConnectionError):
        common.fetch("http://x", {}, max_attempts=2)


# --------------------------------------------------------------------------
# write order: response first, meta last
# --------------------------------------------------------------------------
def test_response_is_written_before_meta(tmp_path, monkeypatch):
    order = []
    real_write = common.write_atomic

    def recording_write(path, data):
        order.append(path.name)
        real_write(path, data)

    monkeypatch.setattr(common, "write_atomic", recording_write)
    common.write_partition(tmp_path / "p", b"{}", {"request_params": {}, "http_status": 200})
    assert order == [common.RESPONSE_FILE, common.META_FILE]


def test_a_crash_after_the_response_leaves_the_partition_unfinished(tmp_path, monkeypatch):
    real_write = common.write_atomic

    def crash_on_meta(path, data):
        if path.name == common.META_FILE:
            raise OSError("crashed before the done marker")
        real_write(path, data)

    monkeypatch.setattr(common, "write_atomic", crash_on_meta)
    folder = tmp_path / "p"
    with pytest.raises(OSError):
        common.write_partition(folder, b"{}", {"request_params": PARAMS, "http_status": 200})
    assert (folder / common.RESPONSE_FILE).is_file()
    assert not common.is_up_to_date(folder, PARAMS)