# Pismo Preserve Weather Data

Temperature and weather data from Weather Underground personal weather stations near the Pismo Preserve, 2021–present. Built for Emily Taylor's lab at Cal Poly — Sam Russell's project.

## Quick Start (if you already have Python and Git)

```bash
git clone https://github.com/kylenessen/pismo-preserve-weather.git
cd pismo-preserve-weather
uv run fetch_weather.py
```

That's it. The script will fetch all data and export a CSV to `exports/pismo_temperature_data.csv`.

---

## Full Setup Guide (New Computer)

This section walks through setting up a brand new machine — no prior tools needed. If you're using an AI coding assistant (like Codex in VS Code), it can help you run these commands step by step.

### Step 1: Install Git

#### macOS
Open **Terminal** (search for it in Spotlight) and run:
```bash
xcode-select --install
```
Click "Install" in the popup. This installs Git along with other command-line tools.

#### Windows
1. Download Git from https://git-scm.com/download/win
2. Run the installer — **use all the default options** (just keep clicking Next)
3. After install, open **Git Bash** (it gets installed alongside Git) — use Git Bash for all commands below, not Command Prompt or PowerShell

### Step 2: Install uv (Python Manager)

[uv](https://docs.astral.sh/uv/) is the recommended way to manage Python. It installs Python for you and handles packages — no need to install Python separately.

#### macOS
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Then **restart your terminal** (close and reopen it) so the `uv` command is available.

#### Windows (in Git Bash)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Then **restart Git Bash**.

> **Note:** If `curl` isn't available on Windows, you can also install uv via PowerShell:
> ```powershell
> powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
> ```
> Then restart Git Bash.

### Step 3: Clone the Repository

```bash
git clone https://github.com/kylenessen/pismo-preserve-weather.git
cd pismo-preserve-weather
```

### Step 4: Run the Script

```bash
uv run fetch_weather.py
```

`uv run` automatically:
- Installs the right Python version if needed
- Installs the `requests` dependency
- Runs the script

**This will take a while** — it's fetching 5+ years of data from 10 weather stations, one day at a time, with a 1-second pause between API calls. Expect it to run for several hours on the first run. You can stop it at any time (Ctrl+C) and re-run later — it picks up where it left off.

### Step 5: Get Your Data

When the script finishes, your CSV file is at:
```
exports/pismo_temperature_data.csv
```

Open it in Excel, Google Sheets, R, or whatever you use for analysis.

---

## Setting Up VS Code with an AI Assistant

1. Download **VS Code** from https://code.visualstudio.com/
2. Open VS Code and install the **GitHub Copilot** extension (or **OpenAI Codex** extension)
   - Cal Poly students: sign in with your `.calpoly.edu` GitHub account for free Copilot access
3. Open a terminal in VS Code: **Terminal > New Terminal** (or Ctrl+`)
4. Use the AI assistant to help you run the setup commands above — just paste this README's URL and ask it to walk you through the setup

---

## Data Details

### Source
- **Weather Underground Personal Weather Stations (PWS)** — free API tier
- 10 stations near the Pismo Preserve in Pismo Beach, Shell Beach, and Grover Beach, CA

### Stations
| Station ID   | Location      |
|-------------|---------------|
| KCAPISMO28  | Pismo Beach   |
| KCAPISMO33  | Pismo Beach   |
| KCAPISMO20  | Pismo Beach   |
| KCAPISMO23  | Pismo Beach   |
| KCAPISMO41  | Pismo Beach   |
| KCAPISMO45  | Pismo Beach   |
| KCASHELL2   | Shell Beach   |
| KCAGROVE128 | Grover Beach  |
| KCAGROVE94  | Grover Beach  |
| KCAGROVE80  | Grover Beach  |

### Date Range
- 2021-01-01 to present (automatically extends each time you run the script)
- 5-minute observation intervals
- Not all stations have data for the full range

### CSV Output (`exports/pismo_temperature_data.csv`)
| Column | Description |
|--------|-------------|
| `station_id` | Weather Underground station ID |
| `datetime_local` | Local timestamp (Pacific time) |
| `temp_high_c` | High temperature (°C) for the 5-min interval |
| `temp_low_c` | Low temperature (°C) |
| `temp_avg_c` | Average temperature (°C) |
| `humidity_avg_pct` | Average humidity (%) |
| `windspeed_avg_kmh` | Average wind speed (km/h) |
| `solar_radiation_high_wm2` | Peak solar radiation (W/m²) |

### Full Database
All data (including dewpoint, pressure, precipitation, wind direction, UV index) is stored in `pismo_weather.db` (SQLite). The CSV export includes the most commonly needed fields. To export everything, you can ask your AI assistant to modify the export query in `fetch_weather.py`, or run a query directly against the database.

## Re-running

The script is **idempotent** — it tracks which station/date combinations have already been fetched and skips them. Safe to re-run anytime to:
- Resume after stopping (Ctrl+C)
- Fetch new days since the last run
- Fill in gaps from temporary API failures

## Troubleshooting

- **"uv: command not found"** — Restart your terminal after installing uv
- **"git: command not found"** — On Mac, run `xcode-select --install`. On Windows, make sure you're using Git Bash
- **Script seems stuck** — It pauses 1 second between API calls by design. Check the terminal output for progress
- **Permission errors on Mac** — Try prefixing commands with `sudo` if needed
- **Network errors** — The script retries automatically. If persistent, check your internet connection and re-run
