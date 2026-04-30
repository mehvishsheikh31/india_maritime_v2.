# ⚓ Indian Ocean Maritime Analytics Dashboard (v2.0)

## 🌍 Overview

A geospatial analytics dashboard that monitors industrial fishing activity in the Indian Ocean Region (IOR) using Global Fishing Watch (GFW) public AIS data. It processes vessel telemetry data and transforms raw satellite pings into an interactive visual intelligence dashboard.

---

## 📁 Project Structure

```
app.py                          → Streamlit dashboard (main entry point)
src/ingest_india.py             → Chunk-based CSV ingestion & India-region filtering
src/merge_registry.py           → Merges activity data with vessel identity registry
requirements.txt                → Python dependencies
data/raw/                       → Raw AIS CSV files + vessel registry (mmsi-daily-*.csv, fishing-vessels-v3.csv)
data/processed/                 → Processed Parquet outputs
    india_2024_mmsi_combined.parquet   → Filtered & combined AIS data
    india_v2_final.parquet             → Final enriched dataset (used by dashboard)
```

---

## ⚙️ What Was Built

### 1. Data Ingestion — `src/ingest_india.py`

- Reads 355 daily GFW CSV files (`mmsi-daily-*.csv`) from `data/raw/` using **Pandas chunk-based loading** (100,000 rows per chunk) to avoid memory overflows
- Auto-detects and corrects scaled coordinates (divides by 100 if values exceed ±500)
- Filters records to the **Indian Ocean Region**: Latitude 5–25°N, Longitude 65–95°E
- Renames GFW v3.0 columns (`cell_ll_lat`, `cell_ll_lon`, `date`, `mmsi`) to standard names (`LAT`, `LON`, `BaseDateTime`, `MMSI`)
- Saves the combined result as `data/processed/india_2024_mmsi_combined.parquet`

---

### 2. Identity Enrichment — `src/merge_registry.py`

- Loads the activity Parquet and the vessel registry (`fishing-vessels-v3.csv`)
- Auto-detects MMSI, vessel name, flag state, and vessel type columns from the registry (case-insensitive column matching)
- Left-joins activity data with registry on MMSI to attach vessel identity
- Safely fills missing values: unknown vessels default to `"Unknown Vessel"`, `"Unknown"` flag, `"Unknown"` vessel type
- Saves the enriched dataset as `data/processed/india_v2_final.parquet`

---

### 3. Streamlit Dashboard — `app.py`

**Theme & UI**
- Full dark tactical theme built with custom CSS (`#080c10` background, teal `#00c8a0` accent)
- Google Fonts: Space Mono (monospace labels) + DM Sans (body text)
- Styled metrics, dataframes, buttons, selects, and alerts via injected CSS

**Sidebar Filters**
- Min Fishing Hours slider (0–24 h, step 0.1)
- Flag State multi-select
- Vessel Type multi-select
- Severity Level select (All / CRITICAL / HIGH / MEDIUM / NORMAL)
- Map column color switcher (Teal / Heat / Blue)

**KPI Strip (4 metrics)**
- Total unique vessels tracked (filtered)
- Total satellite signals recorded (filtered)
- Most active flag state
- Suspicious ships count (fishing hours > 20 h), highlighted in orange

**3D Geospatial Map (PyDeck ColumnLayer)**
- Dark Mapbox basemap, pitched 45°, centered on Indian Ocean
- Each column represents a fishing location; height = fishing hours; radius = 4,500 m, elevation scale = 5,000
- Hover tooltip shows coordinates and total fishing hours
- Color driven by sidebar map style selection

**Charts (Plotly)**
- Monthly fishing-hour trend (area line chart, sorted by month number)
- Top 8 flag states by ping count (horizontal bar chart)
- Top 5 vessel types by count (donut chart, hole = 0.65)
- Average fishing hours by UTC hour of day (vertical bar chart)
- Anomaly scatter plot: vessels with > 10 fishing hours, colored by severity (CRITICAL / HIGH / MEDIUM), sized by fishing hours — sampled to 3,000 points

**Severity Classification**
- CRITICAL: fishing hours > 20
- HIGH: > 15
- MEDIUM: > 10
- NORMAL: ≤ 10

**Top 10 Most Active Ships Table**
- Grouped by vessel name, flag, and vessel type
- `ProgressColumn` for total fishing hours
- Alert Level column (🔴 Critical / 🟠 High / 🟡 Medium)

**Auto-generated Summary**
- Inline `st.info` block reporting: anomaly count and percentage, most active flag state and its share of pings, top 3 countries by activity

**CSV Download**
- Exports filtered view of `MMSI`, `VesselName`, `Flag`, `VesselType`, `fishing_hours`, `Severity` as `IOR_Report.csv`

**Full Ship Registry Expander**
- Displays up to 200 vessels sorted by fishing hours
- `ProgressColumn` for fishing hours column

**How It Works Tab**
- Glossary of 10 domain terms (AIS, MMSI, Telemetry Ping, Fishing Hours, Flag State, Vessel Type, Anomaly, IOR, Parquet, IUU Fishing) in expandable sections
- 5-step numbered build walkthrough
- 8-card technology grid

---

## 🧠 Outputs

- Tracked **4,000+ unique vessels**
- Processed **1.3M+ telemetry pings**
- Flagged vessels with **> 20 continuous fishing hours** as anomalies (rule-based threshold)

---

## 🛠️ Tech Stack

| Layer | Tools |
|---|---|
| Data Processing | Python, Pandas (chunk loading), Apache Parquet (pyarrow / fastparquet) |
| Visualization | Streamlit, PyDeck (Deck.gl ColumnLayer), Plotly (Express + Graph Objects) |
| Data Source | Global Fishing Watch — GFW 2025 Public Data Release |

---

## 🚀 Run Locally

```bash
pip install -r requirements.txt

# Step 1 — Ingest and filter raw data
python src/ingest_india.py

# Step 2 — Enrich with vessel identity
python src/merge_registry.py

# Step 3 — Launch dashboard
streamlit run app.py
```

The dashboard expects `data/processed/india_v2_final.parquet` to exist before launch.

---

## 📌 Scope & Limitations

- Anomaly detection is rule-based (threshold > 20 h) — no ML models used
- Region fixed to Indian Ocean coordinates (5–25°N, 65–95°E)
- Built for analytics and portfolio demonstration purposes

---

## 👩‍💻 Author

Mehvish Sheikh — B.Tech, Data Science