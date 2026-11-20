# Ingest: source tests (week 2, day 3)

Tested on 18 November 2026, with Python 3.14.4 on Linux and `requests` 2.34.2.

Every statement below comes from a request I ran, from a provider's own record or documentation, or is a decision about the pipeline. Anything not yet checked is listed at the end.

The saved raw samples are in `ingest/samples/`. They are the first files of the bronze layer.

## Files

| File | What it is |
|---|---|
| `week-2/day-3/fetch_weather_sample.py` | Fetches hourly and daily Open-Meteo weather for Kumasi on 2026-11-01 and saves the raw response bytes |
| `week-2/day-3/fetch_fx_rates_sample.py` | Fetches Bank of Ghana USD/GHS rates from Frankfurter for 2026-11-02 to 2026-11-17 and saves the raw response bytes |
| `samples/open_meteo_kumasi_2026-11-01_hourly.json` | Raw Open-Meteo hourly response, written by `fetch_weather_sample.py` |
| `samples/open_meteo_kumasi_2026-11-01_daily.json` | Raw Open-Meteo daily response, written by `fetch_weather_sample.py` |
| `samples/frankfurter_bog_usd_ghs_2026-11-02_to_2026-11-17.json` | Raw Frankfurter response (`providers=bog`), written by `fetch_fx_rates_sample.py` |

## How to run

```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python ingest/week-2/day-3/fetch_weather_sample.py
python ingest/week-2/day-3/fetch_fx_rates_sample.py
```

Run the scripts from the repository root. `.venv/` is in `.gitignore`.

## Weather: Open-Meteo

Endpoint that worked: `https://archive-api.open-meteo.com/v1/archive`.

A request to `https://api.open-meteo.com/v1/archive` returned `404 Not Found`. The archive endpoint is on the `archive-api` host.

### Requests

| Sample | Parameters |
|---|---|
| Hourly | `latitude=6.6885`, `longitude=-1.6244`, `start_date=2026-11-01`, `end_date=2026-11-01`, `hourly=temperature_2m,weathercode`, `timezone=Africa/Accra` |
| Daily | the same location, dates and time zone, with `daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode` |

### Observations (Kumasi, 2026-11-01)

- **The returned coordinates differ from the requested ones.** I requested 6.6885, -1.6244 and the response says 6.7135324, -1.5895691, which is roughly 5 km away. The response also gives elevation 275.0. I have not looked up why they differ.
- **The JSON is column-shaped.** Under `hourly` and `daily`, each variable is a list, and `time` is a list too. The hourly response has 24 entries in `time`, and 24 values per variable.
- **The response does not name the city.** The only location information is the returned latitude and longitude.
- **`generationtime_ms` changed on every call:** 0.1833, 0.1824 and 0.1402 across three responses. Two downloads of the same day are therefore not byte-for-byte identical.
- **Time zone:** the response reports `Africa/Accra`, abbreviation `GMT`, `utc_offset_seconds` 0.
- **Units in the response:** `°C` for temperatures, `mm` for `precipitation_sum`, and `wmo code` for `weathercode`.
- **Daily values for 2026-11-01:** maximum 31.3, minimum 22.9, precipitation 1.5 mm, weather code 53.
- **Hourly against daily:** the highest hourly temperature is 31.2 (14:00) and the lowest is 22.9 (05:00). The daily minimum matches the hourly minimum, and the daily maximum is 0.1 higher than the highest hourly value. I have not checked why.
- **Weather code:** the daily code (53) equals the highest of the 24 hourly codes in this sample. The hourly codes include 0, 1, 2, 3, 51 and 53.

### Consequences for the pipeline

- Each raw weather file must be stored together with the city name, the coordinates I requested, and the fetch time, because the response does not hold them.
- `dim_city` holds my own coordinates for each city.
- A check that a rerun created no duplicates must compare the data (city and date), not whole files, because `generationtime_ms` differs between calls.

## Exchange rates: Frankfurter

Endpoint: `https://api.frankfurter.dev/v2/rates`, with the parameters `from`, `to`, `base`, `quotes` and `providers`. No API key was needed for any request.

### Tests on the blended series (no `providers` parameter)

| Request | Result |
|---|---|
| `from=2026-11-01&to=2026-11-10&base=usd&quotes=ghs` | 9 records. 2026-11-07 is missing. The records for 2026-11-01 and 2026-11-08 exist |
| `date=2024-11-13&base=usd&quotes=ghs` | One record dated 2024-11-13, rate 16.1992 |
| `date=2026-11-07&base=usd&quotes=ghs` | One record dated **2026-11-06**, rate 11.6913 |

### Providers behind the blended rate (`expand=providers`, 2026-11-01 to 2026-11-10)

Each blended record lists six providers: BDI, BOG, CBG, CBKKW, CBSL and NBP. Only BOG is identified here, as the Bank of Ghana, by its provider record below.

- **On 2026-11-01 and 2026-11-08, only CBKKW has a quote dated that day.** The other five providers carry earlier dates. On 2026-11-08 they carry 2026-11-06, except NBP, which carries 2026-11-04.
- **NBP's quote is dated 2026-10-28 on the records for 2026-11-01, 2026-11-02 and 2026-11-03.**
- **The providers' rates differ on the same day.** On 2026-11-10 the six values ran from 11.6649 to 11.9112 (CBG). The blended rate for that day was 11.7217.

### The Bank of Ghana as the only provider (`providers=bog`)

The provider record returned by Frankfurter states:

| Field | Value |
|---|---|
| Name | Bank of Ghana |
| Rate type | interbank middle rate |
| Cadence | daily |
| Start date | 1996-01-02 |
| End date (when queried) | 2026-11-17 |
| Currencies listed | include USD, EUR, GBP, GHS and GHC |

| Request | Result |
|---|---|
| `from=2026-11-01&to=2026-11-10&base=usd&quotes=ghs&providers=bog` | 8 records, from **2026-10-30** to 2026-11-10. No records for 2026-11-01, 2026-11-07 or 2026-11-08 |
| `from=2026-11-02&to=2026-11-10&...&providers=bog` | 7 records, from 2026-11-02 to 2026-11-10. No earlier record |
| `from=2026-11-02&to=2026-11-17&...&providers=bog` (saved by the script) | 12 records, from 2026-11-02 to 2026-11-17. No records for 7, 8, 14 and 15 November |
| `date=2024-11-13&base=usd&quotes=ghs&providers=bog` | One record dated 2024-11-13, rate 16.15 |

### Observations

- **The Bank of Ghana records have two decimals.** The blended records have four.
- **Three requests gave the same rates for 2026-11-02 to 2026-11-10.** Values in that period: 11.66, 11.66, 11.66, 11.66, 11.64, 11.69 and 11.70.
- **Bank of Ghana against the blend:** 11.70 against 11.7217 on 2026-11-10, and 16.15 against 16.1992 on 2024-11-13.
- **A range starting on Sunday 2026-11-01 returned a record dated 2026-10-30.** Ranges starting on Monday 2026-11-02 returned no earlier record. I have not established why.
- **When I fetched on 18 November, the latest record was dated 17 November.**
- **Weekends:** in every Bank of Ghana range I ran, the missing dates were weekend days.

### Decision

The source is Frankfurter with `providers=bog`, the Bank of Ghana interbank middle rate.

Reasons, each from the tests above:
- it returns the cedi
- it returned daily records on business days
- it returned a rate for a date two years back
- its provider record states a start date of 1996-01-02
- a date-range request works
- it is a single named provider, so every rate has one known origin

The blended series is kept as a cross-check, not as the source.

### Rules for the pipeline

1. **Use the `date` field of each record, never the date I requested.** A single-date request for a Saturday returned a record dated Friday.
2. **Ingest with a range request.** A range returned only dates that have a rate.
3. **Load as an upsert keyed on `date`, `base` and `quote`.** A range can return a record from before its start date, so the same record can arrive twice.
4. **Bronze and silver keep exactly what arrived,** with no invented rows.
5. **Gold fills dates that have no rate** by carrying the last known rate forward, with an `is_carried_forward` flag, so that every date in `dim_date` has a rate and carried values are marked. The two-year load shows what gold has to fill: every weekend, plus the 28 weekdays listed under [FX: the two-year range](#fx-the-two-year-range).
6. **Parse rates as `Decimal`, never as floats.** Frankfurter's Python documentation also recommends this for money.
7. **Save the raw response bytes,** not parsed JSON written back out.
8. **The loader must accept a day with no rate yet.** The latest record was one day behind when I fetched.

## Load results

Loaded with `ingest/load_weather.py` and `ingest/load_fx.py`, and checked with `ingest/verify.py`, for October 2024 to October 2026. Weather covers 3 of the 16 cities so far: Kumasi, Accra and Tamale. FX covers USD/GHS from the Bank of Ghana.

### Idempotency

The test: run the loader, run `verify.py`, run the loader again, then run `verify.py` again. The counts and the fingerprint must not change. The fingerprint is a hash of the data values, keyed on (city, date) for weather and (date, base, quote) for FX. It does not hash whole files, because `generationtime_ms` changes on every call.

Second run of the loaders:

```
weather: 3 cities x 25 months = 75 partitions
  skipped: 75  fetched: 0  failed: 0

fx: 1 pairs x 25 months = 25 partitions
  skipped: 25  fetched: 0  failed: 0
```

`verify.py` gave the same result before and after that run:

| | Weather (3 cities) | FX (USD/GHS) |
|---|---|---|
| Partitions | 75 of 75 usable | 25 of 25 usable |
| Rows | 2,283 of 2,283 expected | 516 rates |
| Duplicates | 0 (city, day) rows | 13 records in two neighbouring partitions (see below) |
| Null values | none | not applicable |
| Fingerprint | `3b390a47bb867617` | `ad4fd3b2c7f02f8b` |

A rerun made no requests, wrote no files, and left the data unchanged.

### FX: the two-year range

`python ingest/verify.py fx` over 2024-10 to 2026-10:

- **516 rates.**
- **13 records appear in two neighbouring partitions.** Each time, the first day of a month had no rate (a weekend, 1 January or 1 May), and that month's response began with the previous month's last rate. Example: the 2024-12 partition holds 2024-11-29. The 13 copies carry identical rates, and none is dated outside the overall range. Rule 3 (upsert on `date`, `base` and `quote`) keeps one copy of each.
- **28 weekdays have no rate.** Bronze keeps these gaps as they are. Gold fills them under rule 5:

| Year | Weekdays with no rate |
|---|---|
| 2024 | 06 Dec (Fri), 25 Dec (Wed), 26 Dec (Thu) |
| 2025 | 01 Jan (Wed), 07 Jan (Tue), 06 Mar (Thu), 31 Mar (Mon), 01 Apr (Tue), 18 Apr (Fri), 21 Apr (Mon), 01 May (Thu), 06 Jun (Fri), 04 Jul (Fri), 22 Sep (Mon), 05 Dec (Fri), 25 Dec (Thu), 26 Dec (Fri) |
| 2026 | 01 Jan (Thu), 09 Jan (Fri), 06 Mar (Fri), 20 Mar (Fri), 23 Mar (Mon), 03 Apr (Fri), 06 Apr (Mon), 01 May (Fri), 27 May (Wed), 03 Jul (Fri), 21 Sep (Mon) |

Several of these dates look like Ghana public holidays, such as 25 December, 1 January, 6 March and 1 May. I have not checked the list against the official holiday calendar.

## Not yet checked

- Whether each of the 28 weekdays with no FX rate is a Ghana public holiday.
- The other currency pairs in the plan, with `providers=bog`.
- The terms of Open-Meteo, Frankfurter and the Bank of Ghana.
- A comparison of the hourly rainfall total with the daily `precipitation_sum` for 2026-11-01.
- A lookup table for weather code meanings.

## Ingestion design

### Period
October 2024 to October 2026 inclusive: 25 whole months. Every month in the range is closed, so a run has complete data to load. The current month is excluded and will be handled by the daily job (week 5).

Expected counts: 16 cities x 25 months = 400 weather files. FX: 25 files per currency pair.

### Weather granularity
Each weather file holds **daily values only**, one request per city per month with `daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode` and `timezone=Africa/Accra`. A file has one row per day of the month (28 to 31). Daily matches the one-row-per-day grain of `dim_date` and of the FX rates, so weather and rates join on date without aggregating. Hourly values are not ingested. The hourly sample in `ingest/samples/` stays as a test record only.

### Partitions
One file per city per month for weather. One file per pair per month for FX. A bad month can be refetched on its own, and one failure affects one file.

### Paths
```
data/raw/weather/city=<slug>/month=<YYYY-MM>/response.json
data/raw/weather/city=<slug>/month=<YYYY-MM>/meta.json
data/raw/fx/provider=<key>/pair=<base>-<quote>/month=<YYYY-MM>/response.json
data/raw/fx/provider=<key>/pair=<base>-<quote>/month=<YYYY-MM>/meta.json
```
The same city and month always map to the same path, so a rerun replaces a file and never adds a second one. City slugs come from `ingest/config/cities.csv` and never change.

### Skip or overwrite
A month is skipped only if `response.json` and `meta.json` both exist, the response size equals the size recorded in `meta.json`, the recorded status is 200, and the recorded request parameters equal this run's. Otherwise the month is fetched and overwritten. `--force` fetches every month.

### Write order
Each file is written under a temporary name and then renamed. `response.json` is written first and `meta.json` last, so a missing `meta.json` means the month is not finished.

### meta.json
City or pair and provider, request parameters, requested coordinates (weather), start and end dates, exact URL, fetch time, HTTP status, size in bytes, and a SHA-256 hash of the response.

### Not tracked in git
`data/` is in `.gitignore`. It can be rebuilt by running the loader. Only code, config and the small files in `ingest/samples/` are committed.
