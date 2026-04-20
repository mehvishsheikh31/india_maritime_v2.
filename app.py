import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
import os

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MDA · IOR Command",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── GLOBAL CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap');

/* ── Base ── */
.stApp, .main, [data-testid="stAppViewContainer"],
[data-testid="stHeader"], [data-testid="stSidebar"] {
    background-color: #080c10 !important;
}
html, body, * { font-family: 'DM Sans', sans-serif; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background-color: #0d1420 !important;
    border-right: 1px solid rgba(0,200,160,0.15) !important;
}
section[data-testid="stSidebar"] * { color: #e8f0fe !important; }
section[data-testid="stSidebar"] .stSlider > label { font-size: 11px !important; letter-spacing: 2px; }

/* ── Typography ── */
h1, h2, h3, h4, p, span, label, div {
    color: #e8f0fe !important;
}
.stMarkdown p { color: #9ab0c8 !important; }

/* ── Metrics ── */
[data-testid="stMetricValue"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 28px !important;
    font-weight: 700 !important;
    color: #e8f0fe !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 2px !important;
    color: #6b8099 !important;
    text-transform: uppercase !important;
}
[data-testid="metric-container"] {
    background: #0d1420 !important;
    border: 1px solid rgba(0,200,160,0.15) !important;
    border-top: 2px solid #00c8a0 !important;
    border-radius: 8px !important;
    padding: 16px !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    background: #0d1420 !important;
    border: 1px solid rgba(0,200,160,0.15) !important;
    border-radius: 8px !important;
}
.dvn-scroller { background: #0d1420 !important; }

/* ── Buttons ── */
.stDownloadButton > button, .stButton > button {
    background-color: transparent !important;
    color: #00c8a0 !important;
    border: 1px solid #00c8a0 !important;
    border-radius: 6px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 1px !important;
    width: 100% !important;
    padding: 10px !important;
    transition: all 0.2s !important;
}
.stDownloadButton > button:hover, .stButton > button:hover {
    background-color: rgba(0,200,160,0.1) !important;
}

/* ── Alerts / Info boxes ── */
.stAlert {
    background-color: rgba(0,136,255,0.08) !important;
    border: 1px solid rgba(0,136,255,0.25) !important;
    border-radius: 8px !important;
    color: #9ab0c8 !important;
}

/* ── Select/Multiselect ── */
[data-baseweb="select"] div {
    background-color: #111a28 !important;
    border-color: rgba(0,200,160,0.2) !important;
    color: #e8f0fe !important;
}
.stMultiSelect span { background-color: rgba(0,200,160,0.15) !important; color: #00c8a0 !important; }

hr { border-color: rgba(0,200,160,0.1) !important; }

/* ── Section headers ── */
.section-label {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    letter-spacing: 3px;
    color: #00c8a0 !important;
    text-transform: uppercase;
    margin-bottom: 12px;
    display: block;
}

/* ── KPI anomaly override ── */
.anomaly-metric [data-testid="metric-container"] {
    border-top-color: #ff6b35 !important;
}

/* ── Progress bar ── */
.stProgress > div > div { background-color: #00c8a0 !important; }
</style>
""", unsafe_allow_html=True)


# ── DATA LOADING ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data():
    path = "data/processed/india_v2_final.parquet"
    if not os.path.exists(path):
        return None
    df = pd.read_parquet(path)
    df["BaseDateTime"] = pd.to_datetime(df["BaseDateTime"])
    df["Month"] = df["BaseDateTime"].dt.strftime("%b")
    df["MonthNum"] = df["BaseDateTime"].dt.month
    df["Hour"] = df["BaseDateTime"].dt.hour

    # Severity classification
    def classify(h):
        if h > 20: return "CRITICAL"
        elif h > 15: return "HIGH"
        elif h > 10: return "MEDIUM"
        return "NORMAL"
    df["Severity"] = df["fishing_hours"].apply(classify)
    return df

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
PLOTLY_BASE = dict(
    plot_bgcolor="#080c10",
    paper_bgcolor="#080c10",
    font_color="#9ab0c8",
    font_family="DM Sans",
    margin=dict(l=0, r=0, t=10, b=0),
)
GRID_STYLE = dict(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.05)")


# ── CHART HELPERS ──────────────────────────────────────────────────────────────
def make_trend_chart(df):
    monthly = (
        df.groupby(["Month", "MonthNum"])["fishing_hours"]
        .sum().reset_index()
        .sort_values("MonthNum")
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["Month"], y=monthly["fishing_hours"],
        mode="lines+markers",
        line=dict(color="#00c8a0", width=2),
        marker=dict(size=5, color="#00c8a0"),
        fill="tozeroy",
        fillcolor="rgba(0,200,160,0.07)",
    ))
    fig.update_layout(**PLOTLY_BASE, height=220,
                      xaxis=dict(title="", **GRID_STYLE),
                      yaxis=dict(title="", tickformat=".2s", **GRID_STYLE))
    return fig


def make_flag_chart(df):
    flags = df["Flag"].value_counts().head(8).reset_index()
    flags.columns = ["Flag", "Count"]
    colors = ["#00c8a0","#0088ff","#a78bfa","#ff6b35","#fbbf24",
              "#6b8099","#6b8099","#6b8099"]
    fig = go.Figure(go.Bar(
        x=flags["Count"], y=flags["Flag"], orientation="h",
        marker_color=colors[:len(flags)],
        text=flags["Count"].apply(lambda x: f"{x:,}"),
        textposition="outside", textfont=dict(size=10, color="#9ab0c8"),
    ))
    fig.update_layout(**PLOTLY_BASE, height=260,
                      xaxis=dict(title="", **GRID_STYLE, tickformat=".2s"),
                      yaxis=dict(title="", autorange="reversed"),
                      bargap=0.35)
    return fig


def make_gear_chart(df):
    gear = df["VesselType"].value_counts().head(5).reset_index()
    gear.columns = ["Type", "Count"]
    colors = ["#00c8a0","#0088ff","#a78bfa","#ff6b35","#6b8099"]
    fig = go.Figure(go.Pie(
        labels=gear["Type"], values=gear["Count"],
        hole=0.65,
        marker_colors=colors[:len(gear)],
        textinfo="percent",
        textfont_size=11,
    ))
    fig.update_layout(**PLOTLY_BASE, height=220, showlegend=True,
                      legend=dict(font=dict(size=11, color="#9ab0c8"),
                                  bgcolor="rgba(0,0,0,0)", x=1.0))
    return fig


def make_hourly_chart(df):
    hourly = df.groupby("Hour")["fishing_hours"].mean().reset_index()
    fig = go.Figure(go.Bar(
        x=hourly["Hour"], y=hourly["fishing_hours"],
        marker_color="#0088ff",
        marker_opacity=0.8,
    ))
    fig.update_layout(**PLOTLY_BASE, height=180,
                      xaxis=dict(title="Hour (UTC)", tickmode="linear", dtick=4, **GRID_STYLE),
                      yaxis=dict(title="", **GRID_STYLE),
                      bargap=0.1)
    return fig


def make_anomaly_scatter(df):
    sample = df[df["fishing_hours"] > 10].sample(min(3000, len(df[df["fishing_hours"] > 10])), random_state=42)
    color_map = {"CRITICAL": "#ff6b35", "HIGH": "#fbbf24", "MEDIUM": "#0088ff", "NORMAL": "#00c8a0"}
    fig = px.scatter(
        sample, x="LON", y="LAT", color="Severity",
        color_discrete_map=color_map,
        size="fishing_hours", size_max=12,
        opacity=0.7,
        hover_data=["VesselName", "Flag", "fishing_hours"],
    )
    fig.update_layout(**PLOTLY_BASE, height=300,
                      legend=dict(font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
                      xaxis=dict(title="Longitude", **GRID_STYLE),
                      yaxis=dict(title="Latitude", **GRID_STYLE))
    return fig


# ── SIDEBAR ────────────────────────────────────────────────────────────────────
def build_sidebar(df):
    st.sidebar.markdown(
        '<span class="section-label">⬡ MDA · IOR Command v2.0</span>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")

    st.sidebar.markdown('<span class="section-label">Filters</span>', unsafe_allow_html=True)

    hr_filter = st.sidebar.slider("Min Fishing Hours", 0.0, 24.0, 1.0, 0.1)

    all_flags = sorted(df["Flag"].dropna().unique().tolist())
    selected_flags = st.sidebar.multiselect("Flag State", all_flags, placeholder="All flags")

    all_types = sorted(df["VesselType"].dropna().unique().tolist())
    selected_types = st.sidebar.multiselect("Vessel Type", all_types, placeholder="All types")

    severity_filter = st.sidebar.selectbox(
        "Severity Level", ["All", "CRITICAL", "HIGH", "MEDIUM", "NORMAL"]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown('<span class="section-label">Map Style</span>', unsafe_allow_html=True)
    map_color = st.sidebar.selectbox("Column Color", ["Teal (Default)", "Heat (Red→Yellow)", "Blue"])

    return hr_filter, selected_flags, selected_types, severity_filter, map_color


def apply_filters(df, hr_filter, selected_flags, selected_types, severity_filter):
    filtered = df[df["fishing_hours"] >= hr_filter]
    if selected_flags:
        filtered = filtered[filtered["Flag"].isin(selected_flags)]
    if selected_types:
        filtered = filtered[filtered["VesselType"].isin(selected_types)]
    if severity_filter != "All":
        filtered = filtered[filtered["Severity"] == severity_filter]
    return filtered


def get_map_color(choice):
    if choice == "Heat (Red→Yellow)":
        return [255, 100, 50, 200]
    elif choice == "Blue":
        return [0, 136, 255, 200]
    return [0, 200, 160, 200]


# ── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    # ── Header ──
    st.markdown(
        """
        <div style="display:flex; align-items:center; justify-content:space-between;
                    border-bottom:1px solid rgba(0,200,160,0.15); padding-bottom:14px; margin-bottom:20px;">
            <div>
                <span style="font-family:'Space Mono',monospace; font-size:22px;
                             font-weight:700; color:#00c8a0; letter-spacing:3px;">
                    ⬡ MDA · IOR COMMAND
                </span>
                <span style="font-family:'Space Mono',monospace; font-size:10px;
                             color:#6b8099; margin-left:16px; letter-spacing:2px;">
                    INDIAN OCEAN REGION · GFW 2025 RELEASE
                </span>
            </div>
            <div style="display:flex; gap:20px; align-items:center;">
                <span style="font-family:'Space Mono',monospace; font-size:10px; color:#00c8a0;">
                    ● LIVE FEED
                </span>
                <span style="font-family:'Space Mono',monospace; font-size:10px; color:#6b8099;">
                    5–25°N / 65–95°E
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Load Data with Progress ──
    with st.spinner(""):
        progress = st.progress(0, text="🛰️  Initializing data pipeline...")
        df = load_data()
        progress.progress(50, text="⚙️  Processing telemetry records...")
        if df is None:
            progress.empty()
            st.error("❌ Dataset not found at `data/processed/india_v2_final.parquet`")
            return
        progress.progress(100, text="✅  Database online")
        import time; time.sleep(0.4)
        progress.empty()

    # ── Tabs ──
    tab_dashboard, tab_about = st.tabs(["📡  Dashboard", "📖  How It Works"])

    # ════════════════════════════════════════════════════════════
    # TAB 1 — DASHBOARD
    # ════════════════════════════════════════════════════════════
    with tab_dashboard:

        # ── Sidebar & Filters ──
        hr_filter, sel_flags, sel_types, sev_filter, map_color = build_sidebar(df)
        fdf = apply_filters(df, hr_filter, sel_flags, sel_types, sev_filter)

        if len(fdf) == 0:
            st.warning("No vessels match the current filters. Adjust filters in the sidebar.")
            return

        # ── KPI Strip ──
        anomaly_count = len(fdf[fdf["fishing_hours"] > 20])
        unique_vessels = fdf["MMSI"].nunique()
        total_pings = len(fdf)
        top_flag = fdf["Flag"].value_counts().idxmax() if len(fdf) > 0 else "—"

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Ships Tracked", f"{unique_vessels:,}", delta=f"Filter: ≥{hr_filter}h")
        k2.metric("Satellite Signals Recorded", f"{total_pings:,}")
        k3.metric("Most Active Country", top_flag)

        with k4:
            st.markdown(
                f"""
                <div style="background:#0d1420; border:1px solid rgba(0,200,160,0.15);
                            border-top:2px solid #ff6b35; border-radius:8px; padding:16px;">
                    <div style="font-family:'Space Mono',monospace; font-size:10px;
                                 letter-spacing:2px; color:#6b8099; text-transform:uppercase;">
                        Suspicious Ships (&gt;20h)
                    </div>
                    <div style="font-family:'Space Mono',monospace; font-size:28px;
                                 font-weight:700; color:#ff6b35; margin-top:4px;">
                        {anomaly_count:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Row 1: Map + Flag Chart ──
        col_map, col_flags = st.columns([3, 2])

        with col_map:
            st.markdown('<span class="section-label">◈ Where Are The Ships? (Indian Ocean Map)</span>', unsafe_allow_html=True)
            st.caption("Each spike on the map = a fishing hotspot. Taller spike = more fishing hours recorded at that location.")
            view = pdk.ViewState(latitude=14.0, longitude=79.0, zoom=4.5, pitch=45, bearing=0)
            fill = get_map_color(map_color)
            layer = pdk.Layer(
                "ColumnLayer",
                fdf[["LON", "LAT", "fishing_hours"]].dropna(),
                get_position="[LON, LAT]",
                get_elevation="fishing_hours",
                elevation_scale=5000,
                radius=4500,
                get_fill_color=fill,
                pickable=True,
                auto_highlight=True,
            )
            deck = pdk.Deck(
                map_style="mapbox://styles/mapbox/dark-v11",
                initial_view_state=view,
                layers=[layer],
                tooltip={"text": "📍 Location: {LAT}°N, {LON}°E\n🎣 Total fishing time: {fishing_hours} hours"},
            )
            st.pydeck_chart(deck)

        with col_flags:
            st.markdown('<span class="section-label">▶ Which Countries Are Fishing Here?</span>', unsafe_allow_html=True)
            st.caption("Country codes: LKA = Sri Lanka · IND = India · CHN = China · PAK = Pakistan")
            st.plotly_chart(make_flag_chart(fdf), width='stretch')

        # ── Row 2: Trends + Gear + Hourly ──
        st.markdown("---")
        c1, c2, c3 = st.columns([2, 1.2, 1.2])

        with c1:
            st.markdown('<span class="section-label">↗ Fishing Activity by Month</span>', unsafe_allow_html=True)
            st.caption("Total fishing hours recorded each month across the Indian Ocean Region.")
            st.plotly_chart(make_trend_chart(fdf), width='stretch')

        with c2:
            st.markdown('<span class="section-label">◎ Types of Fishing Vessels</span>', unsafe_allow_html=True)
            st.caption("Trawlers drag nets along the sea floor. Longliners use lines with hundreds of hooks.")
            st.plotly_chart(make_gear_chart(fdf), width='stretch')

        with c3:
            st.markdown('<span class="section-label">⏱ What Time of Day Do They Fish?</span>', unsafe_allow_html=True)
            st.caption("Average fishing hours per UTC hour of day. Shows if fishing peaks at night or daytime.")
            st.plotly_chart(make_hourly_chart(fdf), width='stretch')

        # ── Row 3: Anomaly Scatter + Top Targets ──
        st.markdown("---")
        col_scatter, col_targets = st.columns([3, 2])

        with col_scatter:
            st.markdown('<span class="section-label">⚠ Suspicious Ships — Plotted by Location</span>', unsafe_allow_html=True)
            st.caption("🔴 Critical = fishing 20+ hrs non-stop · 🟠 High = 15–20 hrs · 🔵 Medium = 10–15 hrs. Larger dot = more hours.")
            st.plotly_chart(make_anomaly_scatter(fdf), width='stretch')

        with col_targets:
            st.markdown('<span class="section-label">🕵 Most Active Ships</span>', unsafe_allow_html=True)
            st.caption("Ships with the highest total fishing hours. Bar length shows relative activity.")
            suspects = (
                fdf.groupby(["VesselName", "Flag", "VesselType"])["fishing_hours"]
                .sum().reset_index().nlargest(10, "fishing_hours")
                .rename(columns={"VesselName": "Ship Name", "Flag": "Country",
                                  "VesselType": "Vessel Type", "fishing_hours": "Total Hrs"})
            )
            suspects["Total Hrs"] = suspects["Total Hrs"].round(1)
            suspects["Alert Level"] = suspects["Total Hrs"].apply(
                lambda h: "🔴 Critical" if h > 20 else ("🟠 High" if h > 15 else "🟡 Medium")
            )
            st.dataframe(
                suspects.reset_index(drop=True),
                width='stretch',
                column_config={
                    "Total Hrs": st.column_config.ProgressColumn(
                        "Total Hrs", min_value=0,
                        max_value=float(suspects["Total Hrs"].max()),
                        format="%.1f",
                    ),
                },
                hide_index=True,
            )

        # ── Row 4: Insight + Download ──
        st.markdown("---")
        i1, i2 = st.columns([3, 1])

        with i1:
            st.markdown('<span class="section-label">⚡ Summary</span>', unsafe_allow_html=True)
            pct_anomaly = anomaly_count / unique_vessels * 100 if unique_vessels > 0 else 0
            top5_flags = fdf["Flag"].value_counts().head(3).index.tolist()
            lka_pct = (fdf["Flag"] == top_flag).sum() / len(fdf) * 100
            st.info(
                f"**{anomaly_count:,} ships** ({pct_anomaly:.1f}% of all tracked vessels) were fishing for more than 20 hours "
                f"continuously — a possible sign of illegal or unreported fishing. "
                f"Ships from **{top_flag}** were the most active, making up {lka_pct:.1f}% of all satellite signals. "
                f"Top 3 countries by activity: {', '.join(top5_flags)}."
            )

        with i2:
            st.markdown('<span class="section-label">📥 Download Report</span>', unsafe_allow_html=True)
            csv = fdf[["MMSI", "VesselName", "Flag", "VesselType", "fishing_hours", "Severity"]].to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇ DOWNLOAD AS CSV",
                data=csv,
                file_name="IOR_Report.csv",
                mime="text/csv",
            )

        # ── Full Registry ──
        st.markdown("---")
        with st.expander("📋  Full Ship Registry — Click to Expand", expanded=False):
            st.caption("Complete list of all tracked vessels, sorted by fishing hours. Bar shows activity level relative to the most active ship.")
            display_cols = ["MMSI", "VesselName", "Flag", "VesselType", "fishing_hours", "Severity", "Month"]
            display_cols = [c for c in display_cols if c in fdf.columns]
            rename_map = {"MMSI": "Ship ID", "VesselName": "Ship Name", "Flag": "Country",
                          "VesselType": "Vessel Type", "fishing_hours": "Fishing Hours",
                          "Severity": "Alert Level", "Month": "Month"}
            show_df = fdf[display_cols].sort_values("fishing_hours", ascending=False).head(200).reset_index(drop=True)
            show_df = show_df.rename(columns=rename_map)
            st.dataframe(
                show_df,
                width='stretch',
                column_config={
                    "Fishing Hours": st.column_config.ProgressColumn(
                        "Fishing Hours", min_value=0,
                        max_value=float(show_df["Fishing Hours"].max()),
                        format="%.1f",
                    ),
                },
                hide_index=True,
            )

    # ════════════════════════════════════════════════════════════
    # TAB 2 — HOW IT WORKS
    # ════════════════════════════════════════════════════════════
    with tab_about:
        st.markdown("<br>", unsafe_allow_html=True)

        # Hero
        st.markdown("""
        <div style="background:#0d1420; border:1px solid rgba(0,200,160,0.2); border-radius:12px;
                    padding:28px 32px; margin-bottom:28px;">
            <div style="font-family:'Space Mono',monospace; font-size:20px; font-weight:700;
                        color:#00c8a0; margin-bottom:10px;">
                ⚓ What is this dashboard?
            </div>
            <p style="font-size:15px; line-height:1.8; color:#9ab0c8 !important;">
                This is a <strong style="color:#e8f0fe;">maritime surveillance dashboard</strong> that tracks
                fishing vessels in the <strong style="color:#e8f0fe;">Indian Ocean</strong> using real
                satellite data. It processes over <strong style="color:#e8f0fe;">1.3 million location signals</strong>
                from ships and turns them into visual maps and charts — helping identify
                <strong style="color:#e8f0fe;">where fishing is happening, who is doing it, and whether any ships
                are behaving suspiciously.</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Glossary
        st.markdown('<span class="section-label">📚 What Do These Words Mean?</span>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        terms = [
            ("🛰️ AIS (Automatic Identification System)",
             "A tracking system every large ship is legally required to carry. It broadcasts the ship's location, speed, and identity every few seconds via satellite — like a GPS tracker that's always on. This dashboard uses those signals to know where every ship is."),
            ("📡 Telemetry Ping / Satellite Signal",
             "One single location broadcast from a ship. Think of it like one dot on a map saying 'I am here, right now.' This dataset has 1.3 million such dots, collected from thousands of ships over a full year."),
            ("🪪 MMSI (Maritime Mobile Service Identity)",
             "A unique 9-digit ID number assigned to every ship — like an Aadhaar number or a vehicle registration plate, but for boats. Every ship has one. We use it to identify and track individual vessels."),
            ("🎣 Fishing Hours",
             "The total number of hours a ship spent actively fishing, calculated from its movement patterns. When a ship moves slowly in a zigzag pattern, the algorithm classifies that as 'fishing behaviour'. This is how we measure how active each vessel is."),
            ("🚩 Flag State / Country Code",
             "The country a ship is registered in — not necessarily where the crew is from. LKA = Sri Lanka, IND = India, CHN = China, PAK = Pakistan. A ship 'flying the Sri Lankan flag' means it's registered there."),
            ("⚓ Vessel Type",
             "The kind of fishing method the ship uses. Trawlers drag large nets behind them along the ocean floor. Longliners trail lines up to 100 km long with thousands of baited hooks. Different tools, different fish."),
            ("⚠️ Anomaly / Suspicious Ship",
             "A ship flagged as suspicious because it fished for more than 20 hours in a single stretch without stopping. Legal fishing operations usually have breaks. Non-stop fishing can indicate IUU fishing — illegal, unreported, or unregulated activity."),
            ("🌊 IOR (Indian Ocean Region)",
             "The area of ocean this dashboard covers, defined by coordinates: Latitude 5°N to 25°N and Longitude 65°E to 95°E. This covers the waters around India, Sri Lanka, and nearby countries."),
            ("🗄️ Parquet File",
             "A highly efficient file format for storing large amounts of data. The raw data was 3.4 GB of CSV files. After processing and converting to Parquet, it loads 10x faster — which is why the dashboard loads in seconds instead of minutes."),
            ("🏭 IUU Fishing",
             "Illegal, Unreported, and Unregulated fishing — a global problem where ships fish in protected areas, beyond their quota, or without reporting their catch. It damages fish populations and the ocean ecosystem. This dashboard is designed to help detect it."),
        ]

        for title, desc in terms:
            with st.expander(title):
                st.markdown(
                    f'<p style="font-size:14px; line-height:1.8; color:#9ab0c8 !important;">{desc}</p>',
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)

        # How it was built
        st.markdown('<span class="section-label">🔧 How Was This Built?</span>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        steps = [
            ("Step 1 — Get the Raw Data",
             "Downloaded the Global Fishing Watch (GFW) 2025 public dataset — 355 daily CSV files containing billions of satellite signals from fishing vessels all over the world. Total size: ~3.4 GB."),
            ("Step 2 — Filter to the Indian Ocean",
             "Wrote a Python script to read through all those files in chunks (50,000 rows at a time) without crashing the laptop, and kept only the signals from the Indian Ocean region. This reduced the data to a manageable size."),
            ("Step 3 — Identify the Ships",
             "The raw data only had anonymous ship ID numbers (MMSI). Used a vessel registry dataset to match each ID to a real ship name, country flag, and vessel type — like looking up a phone number in a contact book."),
            ("Step 4 — Detect Suspicious Behaviour",
             "Applied a rule: any ship with more than 20 hours of continuous fishing was flagged as an anomaly. This is the basis of the anomaly detection — simple but effective for spotting unusual activity."),
            ("Step 5 — Build the Dashboard",
             "Built this interactive web dashboard using Streamlit (for the interface), PyDeck (for the 3D map), and Plotly (for the charts). The dark tactical theme was custom-built using CSS."),
        ]

        for i, (title, desc) in enumerate(steps):
            st.markdown(
                f"""
                <div style="display:flex; gap:16px; margin-bottom:16px; align-items:flex-start;">
                    <div style="background:rgba(0,200,160,0.1); border:1px solid rgba(0,200,160,0.3);
                                border-radius:50%; width:36px; height:36px; flex-shrink:0;
                                display:flex; align-items:center; justify-content:center;
                                font-family:'Space Mono',monospace; font-size:13px; color:#00c8a0;">
                        {i+1}
                    </div>
                    <div>
                        <div style="font-weight:600; font-size:14px; color:#e8f0fe; margin-bottom:4px;">{title}</div>
                        <div style="font-size:13px; color:#9ab0c8; line-height:1.7;">{desc}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Tech stack
        st.markdown('<span class="section-label">🛠️ Technologies Used</span>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        tech_cols = st.columns(4)
        techs = [
            ("Python", "Core programming language used for all data processing and logic."),
            ("Pandas", "Python library for reading, cleaning, and transforming large datasets."),
            ("Streamlit", "Framework that turns Python scripts into interactive web apps."),
            ("PyDeck", "Library for rendering the interactive 3D map with location spikes."),
            ("Plotly", "Library for creating the interactive charts and graphs."),
            ("Apache Parquet", "Efficient file format that makes the data load 10x faster."),
            ("Global Fishing Watch", "The public satellite dataset used as the data source."),
            ("GitHub", "Used to store and share the code publicly for portfolio purposes."),
        ]
        for i, (name, desc) in enumerate(techs):
            with tech_cols[i % 4]:
                st.markdown(
                    f"""
                    <div style="background:#0d1420; border:1px solid rgba(0,200,160,0.15);
                                border-radius:8px; padding:14px; margin-bottom:12px; min-height:100px;">
                        <div style="font-family:'Space Mono',monospace; font-size:12px;
                                    color:#00c8a0; margin-bottom:6px;">{name}</div>
                        <div style="font-size:12px; color:#6b8099; line-height:1.6;">{desc}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)

        # About the author
        st.markdown(
            """
            <div style="background:#0d1420; border:1px solid rgba(0,136,255,0.2); border-radius:12px;
                        padding:24px 28px; margin-top:8px;">
                <div style="font-family:'Space Mono',monospace; font-size:13px;
                            color:#0088ff; margin-bottom:10px; letter-spacing:2px;">
                    👩‍💻 BUILT BY
                </div>
                <div style="font-size:16px; font-weight:600; color:#e8f0fe; margin-bottom:6px;">
                    Mehvish Sheikh
                </div>
                <div style="font-size:13px; color:#9ab0c8; line-height:1.8;">
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Footer ──
    st.markdown(
        """
        <div style="text-align:center; padding:24px 0 8px;
                    font-family:'Space Mono',monospace; font-size:10px;
                    color:#3a4a5a; letter-spacing:2px; border-top:1px solid rgba(0,200,160,0.08);">
            MDA · IOR COMMAND v2.0 · GFW 2025 PUBLIC DATA · B.TECH DATA SCIENCE · MEHVISH SHEIKH
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()