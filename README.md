

# ⚓ Indian Ocean Maritime Analytics Dashboard (v2.0)

## 🌍 Overview

This project is a geospatial analytics dashboard that monitors industrial fishing activity in the Indian Ocean Region (IOR) using Global Fishing Watch (GFW) public AIS data.

It processes large-scale vessel telemetry data and transforms raw satellite pings into interactive visual intelligence — helping identify fishing hotspots, vessel activity trends, and suspicious long-duration behavior.

---

## 🎯 Problem Statement

Monitoring maritime activity requires:

* Processing millions of AIS telemetry records
* Identifying vessel concentrations in specific regions
* Detecting unusual long-duration fishing behavior
* Presenting insights in an interactive and interpretable format

Raw AIS data alone is difficult to analyze without structured processing and visualization.

---

## ⚙️ Solution Approach

The system consists of three main components:

### 1️⃣ Data Processing Pipeline

* Processed large CSV telemetry files using **Pandas chunk-based loading**
* Filtered India-region coordinates (5–25°N, 65–95°E)
* Standardized MMSI, timestamp, and location fields
* Stored optimized datasets using **Apache Parquet** format

---

### 2️⃣ Identity Enrichment

* Merged AIS activity data with vessel registry dataset
* Linked MMSI to:

  * Vessel Name
  * Flag State
  * Vessel Type
* Handled missing identity values safely

---

### 3️⃣ Interactive Intelligence Dashboard

Built using **Streamlit + PyDeck + Plotly**:

* 3D geospatial column visualization of fishing intensity
* Monthly fishing-hour trend analysis
* Fleet composition breakdown
* Top vessel activity leaderboard
* Rule-based anomaly detection (fishing hours threshold > 20 hrs)
* Downloadable filtered reports

---

## 🧠 Key Insights Generated

* Tracked 4,000+ unique vessels
* Processed 1.3M+ telemetry pings
* Identified regional fishing hotspots
* Flagged vessels exhibiting prolonged station-keeping behavior

Anomaly detection is implemented using rule-based fishing-hour thresholds.

---

## 🛠️ Tech Stack

**Backend & Processing:**
Python, Pandas (chunk processing), Apache Parquet

**Visualization & Interface:**
Streamlit, PyDeck (Deck.gl ColumnLayer), Plotly Express

**Data Source:**
Global Fishing Watch (GFW) Public Data Release

---

## 📁 Project Structure

```
/src                  → Data ingestion & merge logic
/data/raw             → Raw AIS & vessel registry files
/data/processed       → Optimized Parquet dataset
app.py                → Streamlit dashboard
```

---

## 🚀 Performance Optimizations

* Chunk-based CSV loading to handle large files efficiently
* Parquet storage for faster dashboard loading
* Cached data loading using Streamlit

---

## 📌 Scope & Limitations

* Rule-based anomaly detection (no ML models used)
* Region restricted to Indian Ocean coordinates
* Designed for analytics and visualization purposes

---

## 👩‍💻 Author

Mehvish Sheikh
B.Tech – Data Science

-