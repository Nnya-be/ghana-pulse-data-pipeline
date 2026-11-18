import io
import json
from pathlib import Path

import requests as req


URL= 'https://archive-api.open-meteo.com/v1/archive'
CITY= 'Kumasi'
COUNTRY= 'Ghana'
LONGITUDE = -1.6244
LATITUDE = 6.6885
OUTPUT_DIR = Path("ingest/samples")
DAY = '2026-11-01'


params = {
    'latitude': LATITUDE,
    'longitude': LONGITUDE,
    'start_date': DAY,
    'end_date': DAY,
    # 'hourly': 'temperature_2m,weathercode',
    'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode',
    'timezone': 'Africa/Accra'
}

response = req.get(URL, params=params, timeout=30)
response.raise_for_status()

data = response.json()

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
output_file = OUTPUT_DIR / f"open_meteo_{CITY}_{DAY}_daily.json"

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f,  indent=2)

print(f"Weather data for {CITY} on {DAY} saved to {output_file}")