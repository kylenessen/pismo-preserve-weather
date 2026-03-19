"""
Pismo Preserve Weather Data Fetcher
====================================
Fetches historical weather data from Weather Underground personal weather stations
near the Pismo Preserve. Designed for Emily Taylor's lab (Cal Poly) — Sam Russell's
project needing temperature data from 2021 to present.

Data is stored in a local SQLite database. The script is idempotent — it skips
dates already fetched, so you can safely re-run to fill gaps or extend the range.

Usage:
    python fetch_weather.py

API Key: Uses the Weather Underground API (free tier via IBM).
"""

import requests
import sqlite3
import time
import csv
import os
from datetime import datetime, timedelta

# --- Configuration ---
API_KEY = "e1f10a1e78da46f5b10a1e78da96f525"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "pismo_weather.db")
EXPORT_DIR = os.path.join(SCRIPT_DIR, "exports")

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 0.5
API_BACKOFF_SECONDS = 1

# Stations near Pismo Preserve, ordered roughly by proximity
# Pismo Preserve is at approx 35.16°N, 120.63°W
STATIONS = [
    "KCAPISMO28",   # Pismo Beach
    "KCAPISMO33",   # Pismo Beach
    "KCAPISMO20",   # Pismo Beach
    "KCAPISMO23",   # Pismo Beach
    "KCAPISMO41",   # Pismo Beach
    "KCAPISMO45",   # Pismo Beach
    "KCASHELL2",    # Shell Beach (nearby)
    "KCAGROVE128",  # Grover Beach
    "KCAGROVE94",   # Grover Beach
    "KCAGROVE80",   # Grover Beach
]

# Full date range: 2021-01-01 to today
DATE_START = "2021-01-01"
DATE_END = datetime.now().strftime("%Y-%m-%d")


# --- Database ---

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS observations (
        station_id TEXT,
        fetched_date TEXT,
        obs_time_utc TEXT,
        obs_time_local TEXT,
        epoch INTEGER,
        lat REAL,
        lon REAL,
        temp_high REAL,
        temp_low REAL,
        temp_avg REAL,
        humidity_high INTEGER,
        humidity_low INTEGER,
        humidity_avg INTEGER,
        windspeed_high REAL,
        windspeed_low REAL,
        windspeed_avg REAL,
        winddir_avg INTEGER,
        windgust_high REAL,
        dewpt_high REAL,
        dewpt_low REAL,
        dewpt_avg REAL,
        pressure_max REAL,
        pressure_min REAL,
        precip_rate REAL,
        precip_total REAL,
        solar_radiation_high REAL,
        uv_high REAL,
        PRIMARY KEY (station_id, epoch)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS checked_dates (
        station_id TEXT,
        fetched_date TEXT,
        had_data INTEGER,
        PRIMARY KEY (station_id, fetched_date)
    )
    """)
    conn.commit()
    return conn


def date_already_checked(conn, station_id, date_str):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM checked_dates WHERE station_id = ? AND fetched_date = ?",
        (station_id, date_str)
    )
    return cursor.fetchone()[0] > 0


def mark_date_checked(conn, station_id, date_str, had_data):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO checked_dates (station_id, fetched_date, had_data) VALUES (?, ?, ?)",
        (station_id, date_str, 1 if had_data else 0)
    )
    conn.commit()


def save_observations(conn, station_id, date_str, observations):
    cursor = conn.cursor()
    records = []
    for obs in observations:
        m = obs.get("metric", {})
        records.append((
            station_id, date_str,
            obs.get("obsTimeUtc"), obs.get("obsTimeLocal"), obs.get("epoch"),
            obs.get("lat"), obs.get("lon"),
            m.get("tempHigh"), m.get("tempLow"), m.get("tempAvg"),
            obs.get("humidityHigh"), obs.get("humidityLow"), obs.get("humidityAvg"),
            m.get("windspeedHigh"), m.get("windspeedLow"), m.get("windspeedAvg"),
            obs.get("winddirAvg"),
            m.get("windgustHigh"),
            m.get("dewptHigh"), m.get("dewptLow"), m.get("dewptAvg"),
            m.get("pressureMax"), m.get("pressureMin"),
            m.get("precipRate"), m.get("precipTotal"),
            obs.get("solarRadiationHigh"), obs.get("uvHigh"),
        ))
    if records:
        cursor.executemany("""
        INSERT OR IGNORE INTO observations (
            station_id, fetched_date, obs_time_utc, obs_time_local, epoch,
            lat, lon, temp_high, temp_low, temp_avg,
            humidity_high, humidity_low, humidity_avg,
            windspeed_high, windspeed_low, windspeed_avg, winddir_avg,
            windgust_high, dewpt_high, dewpt_low, dewpt_avg,
            pressure_max, pressure_min, precip_rate, precip_total,
            solar_radiation_high, uv_high
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, records)
        conn.commit()
    return len(records)


# --- API ---

def fetch_day(station_id, date_str):
    url = "https://api.weather.com/v2/pws/history/all"
    params = {
        "stationId": station_id,
        "format": "json",
        "units": "m",
        "date": date_str,
        "apiKey": API_KEY,
        "numericPrecision": "decimal",
    }
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {"observations": []}
            print(f"    HTTP {e.response.status_code} for {station_id}/{date_str} (attempt {attempt+1})")
        except requests.exceptions.RequestException as e:
            print(f"    Request error for {station_id}/{date_str}: {e} (attempt {attempt+1})")
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY_SECONDS)
    return None


# --- Export ---

def export_temperature_csv(db_path, output_path):
    """Export temperature data to a clean CSV for analysis."""
    conn = sqlite3.connect(db_path)
    query = """
    SELECT
        station_id,
        obs_time_local,
        temp_high,
        temp_low,
        temp_avg,
        humidity_avg,
        windspeed_avg,
        solar_radiation_high
    FROM observations
    WHERE temp_avg IS NOT NULL
    ORDER BY station_id, obs_time_local
    """
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "station_id", "datetime_local",
            "temp_high_c", "temp_low_c", "temp_avg_c",
            "humidity_avg_pct", "windspeed_avg_kmh",
            "solar_radiation_high_wm2"
        ])
        writer.writerows(rows)
    return len(rows)


# --- Main ---

def generate_dates(start, end):
    dates = []
    current = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    while current <= end_dt:
        dates.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)
    return dates


def main():
    print(f"Pismo Preserve Weather Data Fetcher")
    print(f"Date range: {DATE_START} to {DATE_END}")
    print(f"Stations: {len(STATIONS)}")

    conn = init_db()
    dates = generate_dates(DATE_START, DATE_END)
    total = len(dates) * len(STATIONS)
    done = 0

    for station in STATIONS:
        print(f"\n--- {station} ---")
        for date_str in dates:
            done += 1
            if date_already_checked(conn, station, date_str):
                continue

            data = fetch_day(station, date_str)
            if data and "observations" in data:
                obs = data["observations"]
                if obs:
                    n = save_observations(conn, station, date_str, obs)
                    mark_date_checked(conn, station, date_str, had_data=True)
                    if done % 50 == 0:
                        print(f"  {done}/{total} — {date_str}: {n} obs")
                else:
                    mark_date_checked(conn, station, date_str, had_data=False)
            else:
                print(f"  Failed: {station} {date_str}")

            time.sleep(API_BACKOFF_SECONDS)

    conn.close()
    print(f"\nDone. Database at: {DB_PATH}")

    # Auto-export CSV
    csv_path = os.path.join(EXPORT_DIR, "pismo_temperature_data.csv")
    n = export_temperature_csv(DB_PATH, csv_path)
    print(f"Exported {n} rows to {csv_path}")


if __name__ == "__main__":
    main()
