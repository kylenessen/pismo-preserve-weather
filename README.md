# Pismo Preserve Weather Data

Temperature and weather data from Weather Underground personal weather stations near the Pismo Preserve, 2021–present.

## Setup

```bash
pip install requests
python fetch_weather.py
```

The script fetches 5-minute interval data from 10 weather stations near the Pismo Preserve. Data is stored in `pismo_weather.db` (SQLite) and automatically exported to `exports/pismo_temperature_data.csv`.

## Data

- **Source:** Weather Underground Personal Weather Stations (PWS)
- **Date range:** 2021-01-01 to present
- **Resolution:** 5-minute intervals
- **Units:** Metric (°C, km/h, hPa)
- **Stations:** 10 stations in Pismo Beach, Shell Beach, and Grover Beach

## Output

`exports/pismo_temperature_data.csv` contains:
- `station_id` — Weather Underground station identifier
- `datetime_local` — Local timestamp
- `temp_high_c`, `temp_low_c`, `temp_avg_c` — Temperature (°C) per 5-min interval
- `humidity_avg_pct` — Average humidity (%)
- `windspeed_avg_kmh` — Average wind speed (km/h)
- `solar_radiation_high_wm2` — Peak solar radiation (W/m²)

## Notes

- The script is idempotent — re-run to fill gaps or extend the date range
- Each station/date combination is only fetched once
- Not all stations have data for the full date range
- The API key is from Weather Underground's free tier
