from pathlib import Path

import requests

URL = "https://api.frankfurter.dev/v2/rates"
PROVIDER = "bog"
BASE = "USD"
QUOTE = "GHS"
FROM_DATE = "2026-11-02"
TO_DATE = "2026-11-17"
OUTPUT_DIR = Path("ingest/samples")

params = {
    "from": FROM_DATE,
    "to": TO_DATE,
    "base": BASE,
    "quotes": QUOTE,
    "providers": PROVIDER,
}

response = requests.get(URL, params=params, timeout=30)
response.raise_for_status()

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
file_name = (
    f"frankfurter_{PROVIDER}_{BASE.lower()}_{QUOTE.lower()}"
    f"_{FROM_DATE}_to_{TO_DATE}.json"
)
output_file = OUTPUT_DIR / file_name
output_file.write_bytes(response.content)

records = response.json()
print(f"Saved {output_file}")
print(f"Records: {len(records)}, from {records[0]['date']} to {records[-1]['date']}")