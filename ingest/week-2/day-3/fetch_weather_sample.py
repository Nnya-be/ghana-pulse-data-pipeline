from pathlib import Path

import requests as req


URL = 'https://archive-api.open-meteo.com/v1/archive'
CITY = 'Kumasi'
COUNTRY = 'Ghana'
LONGITUDE = -1.6244
LATITUDE = 6.6885
OUTPUT_DIR = Path("ingest/samples")
DAY = '2026-11-01'

VARIABLES = {
    'hourly': 'temperature_2m,weathercode',
    'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode',
}

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for granularity, variables in VARIABLES.items():
    params = {
        'latitude': LATITUDE,
        'longitude': LONGITUDE,
        'start_date': DAY,
        'end_date': DAY,
        granularity: variables,
        'timezone': 'Africa/Accra',
    }

    response = req.get(URL, params=params, timeout=30)
    response.raise_for_status()

    output_file = OUTPUT_DIR / f"open_meteo_{CITY.lower()}_{DAY}_{granularity}.json"
    output_file.write_bytes(response.content)

    print(f"{granularity.capitalize()} weather for {CITY} on {DAY} saved to {output_file}")
