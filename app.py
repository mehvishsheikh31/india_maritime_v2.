import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="MDA STRATEGIC COMMAND", layout="wide")

# --- ULTIMATE BLACKOUT CSS: REFINED FONT & PURE BLACK ---
st.markdown("""
    <style>
    /* Absolute Black Background */
    .stApp, .main, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] {
        background-color: #000000 !important;
    }

    /* Force Pure White Typography */
    h1, h2, h3, h4, p, span, label, [data-testid="stMetricLabel"] {
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
    }

    /* Refined Metric Font Size (45px) */
    [data-testid="stMetricValue"] {
        font-size: 45px !important;
        font-weight: 900 !important;
        color: #FFFFFF !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 16px !important;
        font-weight: 700 !important;
        color: #888888 !important;
        text-transform: uppercase;
    }

    /* Command Sidebar & Button */
    section[data-testid="stSidebar"] { border-right: 1px solid #333333; }
    .stDownloadButton button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        font-weight: 900 !important;
        border-radius: 0px !important;
        width: 100%;
        padding: 15px;
    }
    
    /* Insight Panel Styling */
    .stAlert {
        background-color: #111111 !important;
        color: #FFFFFF !important;
        border: 1px solid #FFFFFF !important;
    }

    hr { border: 1px solid #333333; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    path = 'data/processed/india_v2_final.parquet'
    if os.path.exists(path):
        df = pd.read_parquet(path)
        df['BaseDateTime'] = pd.to_datetime(df['BaseDateTime'])
        df['Month'] = df['BaseDateTime'].dt.strftime('%b')
        return df
    return None

def main():
    # --- 1. HEADER SECTION ---
    st.markdown("# ⚓ IOR STRATEGIC COMMAND")
    st.markdown("#### TACTICAL SURVEILLANCE | GFW 2025 DATA RELEASE")
    
    df = load_data()
    if df is None:
        st.error("DATABASE OFFLINE")
        return

    # --- 2. KPI STRIP (Refined Metrics) ---
    st.write("---")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("TOTAL TARGETS", f"{df['MMSI'].nunique():,}")
    k2.metric("TELEMETRY PINGS", f"{len(df):,}")
    k3.metric("IOR ZONE", "ACTIVE")
    k4.metric("ANOMALIES", f"{len(df[df['fishing_hours'] > 18]):,}")

    # --- 3. MAIN ANALYTICS ROW: MAP & TRENDS ---
    st.write("---")
    col_map, col_stats = st.columns([2, 1])

    with col_map:
        st.markdown("### 🗺️ TACTICAL SPATIAL PROJECTION")
        hr_filter = st.sidebar.slider("ACTIVITY FILTER (HRS)", 0.0, 24.0, 1.0)
        p_df = df[df['fishing_hours'] >= hr_filter]

        # White Pillars View
        view = pdk.ViewState(latitude=14.0, longitude=79.0, zoom=4.8, pitch=45)
        layer = pdk.Layer(
            "ColumnLayer", p_df, get_position="[LON, LAT]",
            get_elevation="fishing_hours", elevation_scale=6000,
            radius=4000, get_fill_color=[255, 255, 255, 255], pickable=True
        )
        st.pydeck_chart(pdk.Deck(map_style='mapbox://styles/mapbox/dark-v11', initial_view_state=view, layers=[layer]))

    with col_stats:
        st.markdown("### 📈 TEMPORAL TRENDS")
        monthly = df.groupby('Month')['fishing_hours'].sum().reset_index()
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        monthly['Month'] = pd.Categorical(monthly['Month'], categories=months, ordered=True)
        monthly = monthly.sort_values('Month')
        
        fig_line = px.line(monthly, x='Month', y='fishing_hours', markers=True, color_discrete_sequence=['#FFFFFF'])
        fig_line.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='white', xaxis_title="", yaxis_title="", height=250)
        st.plotly_chart(fig_line, use_container_width=True)

        st.markdown("### 🏗️ FLEET COMPOSITION")
        fig_pie = px.pie(df, names='VesselType', hole=0.6, color_discrete_sequence=['#FFFFFF', '#888888', '#444444'])
        fig_pie.update_layout(showlegend=False, plot_bgcolor='black', paper_bgcolor='black', font_color='white', height=250)
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- 4. DATA INSIGHTS ROW: TARGETS & FLAGS ---
    st.write("---")
    i1, i2, i3 = st.columns([1, 1, 1])

    with i1:
        st.markdown("### 🕵️ TOP TARGETS")
        suspects = df.groupby('VesselName')['fishing_hours'].sum().nlargest(5).reset_index()
        st.table(suspects)

    with i2:
        st.markdown("### 🚩 OPERATING FLAGS")
        top_flags = df['Flag'].value_counts().head(5)
        st.table(top_flags)

    with i3:
        st.markdown("### 🧠 COMMAND INSIGHTS")
        st.info(f"Analysis: {len(df[df['fishing_hours'] > 20])} vessels exceeded 20h fishing pings, indicating illegal station-keeping.")
        csv = p_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 DOWNLOAD TACTICAL REPORT", csv, "IOR_Report.csv", "text/csv")

    # --- 5. TARGET REGISTRY ---
    st.write("---")
    st.markdown("### 📋 FULL TARGET REGISTRY")
    st.dataframe(p_df[['MMSI', 'VesselName', 'Flag', 'VesselType', 'fishing_hours']].head(100), use_container_width=True)

if __name__ == "__main__":
    main()