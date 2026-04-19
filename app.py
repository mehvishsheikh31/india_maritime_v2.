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
.dvn-scroller * { color: #e8f0fe !important; }
[data-testid="stDataFrame"] * { color: #e8f0fe !important; }
[data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
    color: #e8f0fe !important;
    background-color: #0d1420 !important;
}

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

/* Dropdown options panel */
[data-baseweb="popover"] * { 
    background-color: #111a28 !important; 
    color: #e8f0fe !important; 
}
[data-baseweb="menu"] * { 
    background-color: #111a28 !important; 
    color: #e8f0fe !important; 
}
[data-baseweb="option"]:hover {
    background-color: rgba(0,200,160,0.15) !important;
}
/* Selected tag text inside multiselect */
[data-baseweb="tag"] span { color: #00c8a0 !important; }
/* Selectbox current value text */
[data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
[data-baseweb="select"] span { color: #e8f0fe !important; }
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
    k1.metric("Total Targets", f"{unique_vessels:,}", delta=f"Filter: ≥{hr_filter}h")
    k2.metric("Telemetry Pings", f"{total_pings:,}")
    k3.metric("Dominant Flag", top_flag)

    # Anomaly metric with orange accent (via container hack)
    with k4:
        st.markdown(
            f"""
            <div style="background:#0d1420; border:1px solid rgba(0,200,160,0.15);
                        border-top:2px solid #ff6b35; border-radius:8px; padding:16px;">
                <div style="font-family:'Space Mono',monospace; font-size:10px;
                             letter-spacing:2px; color:#6b8099; text-transform:uppercase;">
                    Anomalies (&gt;20h)
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
        st.markdown('<span class="section-label">◈ Tactical Spatial Projection</span>', unsafe_allow_html=True)
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
            tooltip={"text": "Lat: {LAT}\nLon: {LON}\nFishing hrs: {fishing_hours}"},
        )
        st.pydeck_chart(deck)

    with col_flags:
        st.markdown('<span class="section-label">▶ Operating Flags</span>', unsafe_allow_html=True)
        st.plotly_chart(make_flag_chart(fdf), width='stretch')

    # ── Row 2: Trends + Gear + Hourly ──
    st.markdown("---")
    c1, c2, c3 = st.columns([2, 1.2, 1.2])

    with c1:
        st.markdown('<span class="section-label">↗ Monthly Activity Trend</span>', unsafe_allow_html=True)
        st.plotly_chart(make_trend_chart(fdf), width='stretch')

    with c2:
        st.markdown('<span class="section-label">◎ Fleet Composition</span>', unsafe_allow_html=True)
        st.plotly_chart(make_gear_chart(fdf), width='stretch')

    with c3:
        st.markdown('<span class="section-label">⏱ Hourly Activity Pattern</span>', unsafe_allow_html=True)
        st.plotly_chart(make_hourly_chart(fdf), width='stretch')

    # ── Row 3: Anomaly Scatter + Top Targets ──
    st.markdown("---")
    col_scatter, col_targets = st.columns([3, 2])

    with col_scatter:
        st.markdown('<span class="section-label">⚠ Anomaly Scatter · IOR</span>', unsafe_allow_html=True)
        st.plotly_chart(make_anomaly_scatter(fdf), width='stretch')

    with col_targets:
        st.markdown('<span class="section-label">🕵 Top Targets by Fishing Hours</span>', unsafe_allow_html=True)
        suspects = (
            fdf.groupby(["VesselName", "Flag", "VesselType"])["fishing_hours"]
            .sum().reset_index().nlargest(10, "fishing_hours")
            .rename(columns={"fishing_hours": "Total Hrs"})
        )
        suspects["Total Hrs"] = suspects["Total Hrs"].round(1)
        suspects["Severity"] = suspects["Total Hrs"].apply(
            lambda h: "🔴 CRITICAL" if h > 20 else ("🟠 HIGH" if h > 15 else "🟡 MEDIUM")
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
        st.markdown('<span class="section-label">⚡ Command Insights</span>', unsafe_allow_html=True)
        pct_anomaly = anomaly_count / unique_vessels * 100 if unique_vessels > 0 else 0
        top5_flags = fdf["Flag"].value_counts().head(3).index.tolist()
        lka_pct = (fdf["Flag"] == top_flag).sum() / len(fdf) * 100

        st.info(
            f"**{anomaly_count:,} vessels** ({pct_anomaly:.1f}%) exceeded the 20h station-keeping threshold — "
            f"possible IUU fishing indicators. "
            f"**{top_flag}** dominates with {lka_pct:.1f}% of total pings. "
            f"Top 3 operating flags: {', '.join(top5_flags)}."
        )

    with i2:
        st.markdown('<span class="section-label">📥 Export</span>', unsafe_allow_html=True)
        csv = fdf[["MMSI", "VesselName", "Flag", "VesselType", "fishing_hours", "Severity"]].to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ DOWNLOAD TACTICAL REPORT",
            data=csv,
            file_name="IOR_Report.csv",
            mime="text/csv",
        )

    # ── Full Registry ──
    st.markdown("---")
    with st.expander("📋  FULL TARGET REGISTRY", expanded=False):
        display_cols = ["MMSI", "VesselName", "Flag", "VesselType", "fishing_hours", "Severity", "Month"]
        display_cols = [c for c in display_cols if c in fdf.columns]
        st.dataframe(
            fdf[display_cols].sort_values("fishing_hours", ascending=False).head(200).reset_index(drop=True),
            width='stretch',
            column_config={
                "fishing_hours": st.column_config.ProgressColumn(
                    "Fishing Hours", min_value=0,
                    max_value=float(fdf["fishing_hours"].max()),
                    format="%.1f",
                ),
            },
            hide_index=True,
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