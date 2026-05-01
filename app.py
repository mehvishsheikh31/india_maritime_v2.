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

# ── LANGUAGE STRINGS ───────────────────────────────────────────────────────────
LANG = {
    "en": {
        # Sidebar
        "app_title": "⬡ MDA · IOR Command v2.0",
        "filters": "Filters",
        "min_fishing_hours": "Min Fishing Hours",
        "flag_state": "Flag State",
        "all_flags": "All flags",
        "vessel_type": "Vessel Type",
        "all_types": "All types",
        "severity_level": "Severity Level",
        "map_style": "Map Style",
        "column_color": "Column Color",
        "lang_toggle": "🇮🇳 Hinglish mein dekho",

        # Header
        "header_title": "⬡ MDA · IOR COMMAND",
        "header_sub": "INDIAN OCEAN REGION · GFW 2025 RELEASE",
        "live_feed": "●GFW 2025 DATA",
        "region": "5–25°N / 65–95°E",

        # Loading
        "loading_1": "🛰️  Initializing data pipeline...",
        "loading_2": "⚙️  Processing telemetry records...",
        "loading_3": "✅  Database online",
        "data_error": "❌ Dataset not found at `data/processed/india_v2_final.parquet`",
        "no_match": "No vessels match the current filters. Adjust filters in the sidebar.",

        # Tabs
        "tab_dashboard": "📡  Dashboard",
        "tab_about": "📖  How It Works",

        # KPI
        "kpi_ships": "Total Ships Tracked",
        "kpi_signals": "Satellite Signals Recorded",
        "kpi_country": "Most Active Country",
        "kpi_suspicious": "Suspicious Ships (>20h)",
        "kpi_filter": "Filter: ≥{}h",

        # Section labels
        "map_label": "◈ Where Are The Ships? (Indian Ocean Map)",
        "map_caption": "Each spike on the map = a fishing hotspot. Taller spike = more fishing hours recorded at that location.",
        "flags_label": "▶ Which Countries Are Fishing Here?",
        "flags_caption": "Country codes: LKA = Sri Lanka · IND = India · CHN = China · PAK = Pakistan",
        "trend_label": "↗ Fishing Activity by Month",
        "trend_caption": "Total fishing hours recorded each month across the Indian Ocean Region.",
        "gear_label": "◎ Types of Fishing Vessels",
        "gear_caption": "Trawlers drag nets along the sea floor. Longliners use lines with hundreds of hooks.",
        "hourly_label": "⏱ What Time of Day Do They Fish?",
        "hourly_caption": "Average fishing hours per UTC hour of day. Shows if fishing peaks at night or daytime.",
        "anomaly_label": "⚠ Suspicious Ships — Plotted by Location",
        "anomaly_caption": "🔴 Critical = fishing 20+ hrs non-stop · 🟠 High = 15–20 hrs · 🔵 Medium = 10–15 hrs. Larger dot = more hours.",
        "targets_label": "🕵 Most Active Ships",
        "targets_caption": "Ships with the highest total fishing hours. Bar length shows relative activity.",
        "summary_label": "⚡ Summary",
        "download_label": "📥 Download Report",
        "download_btn": "⬇ DOWNLOAD AS CSV",
        "registry_label": "📋  Full Ship Registry — Click to Expand",
        "registry_caption": "Complete list of all tracked vessels, sorted by fishing hours.",

        # Table columns
        "col_ship_id": "Ship ID",
        "col_ship_name": "Ship Name",
        "col_country": "Country",
        "col_vessel_type": "Vessel Type",
        "col_fishing_hrs": "Fishing Hours",
        "col_alert": "Alert Level",
        "col_month": "Month",
        "col_total_hrs": "Total Hrs",

        # Summary text
        "summary_text": "**{anomaly_count:,} ships** ({pct:.1f}% of all tracked vessels) were fishing for more than 20 hours continuously — a possible sign of illegal or unreported fishing. Ships from **{top_flag}** were the most active, making up {lka_pct:.1f}% of all satellite signals. Top 3 countries by activity: {top3}.",

        # Hour axis
        "hour_axis": "Hour (UTC)",

        # About tab
        "about_what_title": "⚓ What is this dashboard?",
        "about_what_body": "This is a <strong style='color:#e8f0fe;'>maritime surveillance dashboard</strong> that tracks fishing vessels in the <strong style='color:#e8f0fe;'>Indian Ocean</strong> using real satellite data. It processes over <strong style='color:#e8f0fe;'>1.3 million location signals</strong> from ships and turns them into visual maps and charts — helping identify <strong style='color:#e8f0fe;'>where fishing is happening, who is doing it, and whether any ships are behaving suspiciously.</strong>",
        "glossary_label": "📚 What Do These Words Mean?",
        "how_built_label": "🔧 How Was This Built?",
        "tech_label": "🛠️ Technologies Used",
        "built_by": "👩‍💻 BUILT BY",

        # Glossary
        "terms": [
            ("🛰️ AIS (Automatic Identification System)",
             "A tracking system every large ship is legally required to carry. It broadcasts the ship's location, speed, and identity every few seconds via satellite — like a GPS tracker that's always on."),
            ("📡 Telemetry Ping / Satellite Signal",
             "One single location broadcast from a ship. Think of it like one dot on a map saying 'I am here, right now.' This dataset has 1.3 million such dots."),
            ("🪪 MMSI (Maritime Mobile Service Identity)",
             "A unique 9-digit ID number assigned to every ship — like a vehicle registration plate, but for boats."),
            ("🎣 Fishing Hours",
             "The total number of hours a ship spent actively fishing, calculated from its movement patterns."),
            ("🚩 Flag State / Country Code",
             "The country a ship is registered in. LKA = Sri Lanka, IND = India, CHN = China, PAK = Pakistan."),
            ("⚓ Vessel Type",
             "The kind of fishing method the ship uses. Trawlers drag large nets. Longliners trail lines up to 100 km long with thousands of hooks."),
            ("⚠️ Anomaly / Suspicious Ship",
             "A ship flagged as suspicious because it fished for more than 20 hours in a single stretch without stopping."),
            ("🌊 IOR (Indian Ocean Region)",
             "The area this dashboard covers: Latitude 5°N to 25°N and Longitude 65°E to 95°E."),
            ("🗄️ Parquet File",
             "A highly efficient file format for storing large amounts of data. 10x faster to load than CSV."),
            ("🏭 IUU Fishing",
             "Illegal, Unreported, and Unregulated fishing — a global problem this dashboard is designed to help detect."),
        ],

        # Steps
        "steps": [
            ("Step 1 — Get the Raw Data",
             "Downloaded the Global Fishing Watch (GFW) 2025 public dataset — 355 daily CSV files. Total size: ~3.4 GB."),
            ("Step 2 — Filter to the Indian Ocean",
             "Wrote a Python script to read through all files in chunks (100,000 rows at a time) and kept only Indian Ocean signals."),
            ("Step 3 — Identify the Ships",
             "Used a vessel registry to match each MMSI to a real ship name, country flag, and vessel type."),
            ("Step 4 — Detect Suspicious Behaviour",
             "Applied a rule: any ship with more than 20 hours of continuous fishing was flagged as an anomaly."),
            ("Step 5 — Build the Dashboard",
             "Built using Streamlit, PyDeck for the 3D map, and Plotly for charts. Dark tactical theme built with custom CSS."),
        ],

        # Tech
        "techs": [
            ("Python", "Core programming language for all data processing."),
            ("Pandas", "Reading, cleaning, and transforming large datasets in chunks."),
            ("Streamlit", "Turns Python scripts into interactive web apps."),
            ("PyDeck", "Interactive 3D map with location spikes."),
            ("Plotly", "Interactive charts and graphs."),
            ("Apache Parquet", "Efficient file format — 10x faster loading."),
            ("Global Fishing Watch", "Public satellite dataset used as data source."),
            ("GitHub", "Used to store and share the code publicly."),
        ],

        # Footer
        "footer": "MDA · IOR COMMAND v2.0 · GFW 2025 PUBLIC DATA · B.TECH DATA SCIENCE · MEHVISH SHEIKH",
    },

    "hi": {
        # Sidebar
        "app_title": "⬡ MDA · IOR Command v2.0",
        "filters": "Filters (छानबीन करो)",
        "min_fishing_hours": "Minimum Fishing Hours (घंटे)",
        "flag_state": "Flag State (देश)",
        "all_flags": "Sab desh",
        "vessel_type": "Vessel Type (jahaaz ka type)",
        "all_types": "Sab types",
        "severity_level": "Severity Level (kitna suspicious)",
        "map_style": "Map Style",
        "column_color": "Column ka rang",
        "lang_toggle": "🇬🇧 Switch to English",

        # Header
        "header_title": "⬡ MDA · IOR COMMAND",
        "header_sub": "INDIAN OCEAN REGION · GFW 2025 DATA",
        "live_feed": "● GFW 2025 DATA",
        "region": "5–25°N / 65–95°E",

        # Loading
        "loading_1": "🛰️  Data load ho raha hai...",
        "loading_2": "⚙️  Records process ho rahe hain...",
        "loading_3": "✅  Dashboard ready hai",
        "data_error": "❌ Data file nahi mili: `data/processed/india_v2_final.parquet`",
        "no_match": "Koi bhi jahaaz filter se match nahi kiya. Sidebar mein filters change karo.",

        # Tabs
        "tab_dashboard": "📡  Dashboard",
        "tab_about": "📖  Kaise Bana?",

        # KPI
        "kpi_ships": "Total Jahaazon ki Ginti",
        "kpi_signals": "Satellite Signals Record Hue",
        "kpi_country": "Sabse Zyada Active Desh",
        "kpi_suspicious": "Suspicious Jahaaz (>20 ghante)",
        "kpi_filter": "Filter: ≥{}h",

        # Section labels
        "map_label": "◈ Jahaaz Kahan Hain? (Indian Ocean Map)",
        "map_caption": "Har spike ek fishing jagah hai. Jitna lamba spike, utne zyada fishing hours wahan hue.",
        "flags_label": "▶ Kaun Se Desh Yahan Fishing Kar Rahe Hain?",
        "flags_caption": "Country codes: LKA = Sri Lanka · IND = India · CHN = China · PAK = Pakistan",
        "trend_label": "↗ Har Mahine Fishing Activity",
        "trend_caption": "Indian Ocean mein har mahine kitne ghante fishing hui — yahan dekho.",
        "gear_label": "◎ Kis Type Ke Jahaaz Hain?",
        "gear_caption": "Trawlers bade jaal se machchli pakdte hain. Longliners 100 km lambi line daalta hain.",
        "hourly_label": "⏱ Din Mein Kab Fishing Hoti Hai?",
        "hourly_caption": "UTC time ke hisaab se average fishing hours. Raat mein zyada hoti hai ya din mein?",
        "anomaly_label": "⚠ Suspicious Jahaaz — Map Par Dikhaye",
        "anomaly_caption": "🔴 Critical = 20+ ghante lagaataar · 🟠 High = 15–20 ghante · 🔵 Medium = 10–15 ghante. Bada dot = zyada ghante.",
        "targets_label": "🕵 Sabse Zyada Active Jahaaz",
        "targets_caption": "Jinke sabse zyada fishing hours hain. Bar jitna lamba, utna zyada active.",
        "summary_label": "⚡ Kya Pata Chala?",
        "download_label": "📥 Report Download Karo",
        "download_btn": "⬇ CSV DOWNLOAD KARO",
        "registry_label": "📋  Pura Jahaaz Register — Click Karo",
        "registry_caption": "Sabhi track kiye gaye jahaazon ki poori list, fishing hours ke hisaab se sort ki gayi.",

        # Table columns
        "col_ship_id": "Jahaaz ID",
        "col_ship_name": "Jahaaz ka Naam",
        "col_country": "Desh",
        "col_vessel_type": "Type",
        "col_fishing_hrs": "Fishing Ghante",
        "col_alert": "Alert Level",
        "col_month": "Mahina",
        "col_total_hrs": "Total Ghante",

        # Summary text
        "summary_text": "**{anomaly_count:,} jahaaz** (sab tracked jahaazon mein se {pct:.1f}%) 20 ghante se zyada lagaataar fishing kar rahe the — yeh illegal ya unreported fishing ka sign ho sakta hai. **{top_flag}** ke jahaaz sabse zyada active the aur unhone {lka_pct:.1f}% satellite signals bheje. Top 3 active desh: {top3}.",

        # Hour axis
        "hour_axis": "Ghanta (UTC)",

        # About tab
        "about_what_title": "⚓ Yeh Dashboard Kya Hai?",
        "about_what_body": "Yeh ek <strong style='color:#e8f0fe;'>maritime surveillance dashboard</strong> hai jo <strong style='color:#e8f0fe;'>Indian Ocean</strong> mein fishing jahaazon ko track karta hai — real satellite data se. Isme <strong style='color:#e8f0fe;'>13 lakh se zyada location signals</strong> process ki gayi hain aur unhe visual maps aur charts mein convert kiya gaya hai — taaki pata chale <strong style='color:#e8f0fe;'>kahan fishing ho rahi hai, kaun kar raha hai, aur koi suspicious toh nahi.</strong>",
        "glossary_label": "📚 In Shabdon Ka Matlab Kya Hai?",
        "how_built_label": "🔧 Yeh Kaise Banaya?",
        "tech_label": "🛠️ Kaunsi Technologies Use Ki",
        "built_by": "👩‍💻 KISNE BANAYA",

        # Glossary
        "terms": [
            ("🛰️ AIS (Automatic Identification System)",
             "Har bade jahaaz mein legally ek tracking system hona chahiye. Yeh satellite se har kuch seconds mein jahaaz ki location, speed, aur pehchaan broadcast karta hai — bilkul GPS tracker ki tarah jo hamesha on rehta hai."),
            ("📡 Telemetry Ping / Satellite Signal",
             "Ek jahaaz ka ek single location broadcast. Samjho jaise map par ek dot jo bol raha ho 'Main yahan hoon, abhi.' Is dataset mein 13 lakh aise dots hain."),
            ("🪪 MMSI (Maritime Mobile Service Identity)",
             "Har jahaaz ko diya gaya ek unique 9-digit ID number — jaise gaadi ka registration number, but jahaaz ke liye."),
            ("🎣 Fishing Hours",
             "Ek jahaaz ne kitne ghante actively fishing ki — yeh uske movement patterns se calculate hota hai. Slow zigzag movement = fishing behaviour."),
            ("🚩 Flag State / Country Code",
             "Wo desh jisme jahaaz registered hai. LKA = Sri Lanka, IND = India, CHN = China, PAK = Pakistan."),
            ("⚓ Vessel Type",
             "Jahaaz kis tarah fishing karta hai. Trawlers bade jaal kheenchte hain. Longliners 100 km lambi line daalta hain hazaron hooks ke saath."),
            ("⚠️ Anomaly / Suspicious Jahaaz",
             "Woh jahaaz jo 20 ghante se zyada lagaataar fishing karta raha bina ruke. Legal fishing mein break hota hai. Non-stop fishing IUU fishing ka sign ho sakti hai."),
            ("🌊 IOR (Indian Ocean Region)",
             "Jis area ko yeh dashboard cover karta hai: Latitude 5°N se 25°N aur Longitude 65°E se 95°E — India, Sri Lanka, aur nearby countries ke aaspaas."),
            ("🗄️ Parquet File",
             "Data store karne ka ek bahut efficient format. 3.4 GB ke CSV files ko process karke Parquet mein save kiya gaya — jo 10 guna tezi se load hota hai."),
            ("🏭 IUU Fishing",
             "Illegal, Unreported, aur Unregulated fishing — ek global problem jisme jahaaz protected areas mein ya bina permission ke fishing karte hain. Yeh dashboard isko detect karne ke liye banaya gaya hai."),
        ],

        # Steps
        "steps": [
            ("Step 1 — Raw Data Lao",
             "Global Fishing Watch (GFW) 2025 public dataset download kiya — 355 daily CSV files, total size ~3.4 GB."),
            ("Step 2 — Indian Ocean Filter Karo",
             "Python script likhi jo 1 lakh rows at a time padhti thi aur sirf Indian Ocean ke signals rakhti thi — laptop crash na ho isliye."),
            ("Step 3 — Jahaazon Ko Pehchano",
             "Vessel registry use karke har MMSI ko real ship name, country flag, aur vessel type se match kiya — jaise phone number se contact dhundhna."),
            ("Step 4 — Suspicious Behavior Pakdo",
             "Rule lagaya: jo bhi jahaaz 20 ghante se zyada lagaataar fishing kare, use anomaly mark karo."),
            ("Step 5 — Dashboard Banao",
             "Streamlit se interface, PyDeck se 3D map, aur Plotly se charts banaye. Dark tactical theme custom CSS se design ki."),
        ],

        # Tech
        "techs": [
            ("Python", "Sab kuch is language mein likha gaya — processing se lekar dashboard tak."),
            ("Pandas", "Bade datasets ko chunks mein padhna, saaf karna, aur transform karna."),
            ("Streamlit", "Python script ko interactive web app mein badalta hai."),
            ("PyDeck", "3D interactive map jo location spikes dikhata hai."),
            ("Plotly", "Interactive charts aur graphs ke liye."),
            ("Apache Parquet", "Efficient data format — CSV se 10 guna tez load hota hai."),
            ("Global Fishing Watch", "Public satellite dataset jo data source hai."),
            ("GitHub", "Code publicly store aur share karne ke liye."),
        ],

        # Footer
        "footer": "MDA · IOR COMMAND v2.0 · GFW 2025 DATA · B.TECH DATA SCIENCE · MEHVISH SHEIKH",
    },
}


def t(key):
    """Get translation for current language."""
    lang = st.session_state.get("lang", "en")
    return LANG[lang].get(key, LANG["en"].get(key, key))


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

/* ── Lang toggle button special style ── */
.lang-btn > button {
    border-color: #fbbf24 !important;
    color: #fbbf24 !important;
    font-size: 12px !important;
    letter-spacing: 0.5px !important;
}
.lang-btn > button:hover {
    background-color: rgba(251,191,36,0.1) !important;
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

/* ── Progress bar ── */
.stProgress > div > div { background-color: #00c8a0 !important; }

/* ── Language badge ── */
.lang-badge {
    display: inline-block;
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    letter-spacing: 2px;
    color: #fbbf24 !important;
    border: 1px solid rgba(251,191,36,0.4);
    border-radius: 4px;
    padding: 2px 8px;
    margin-left: 10px;
    vertical-align: middle;
}
</style>
""", unsafe_allow_html=True)


# ── LANGUAGE INIT ──────────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state["lang"] = "en"


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
                      xaxis=dict(title=t("hour_axis"), tickmode="linear", dtick=4, **GRID_STYLE),
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
        f'<span class="section-label">{t("app_title")}</span>',
        unsafe_allow_html=True,
    )

    # ── Language Toggle ──
    lang_label = t("lang_toggle")
    st.sidebar.markdown("---")
    with st.sidebar:
        st.markdown('<div class="lang-btn">', unsafe_allow_html=True)
        if st.button(lang_label, key="lang_btn"):
            st.session_state["lang"] = "hi" if st.session_state["lang"] == "en" else "en"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown(f'<span class="section-label">{t("filters")}</span>', unsafe_allow_html=True)

    hr_filter = st.sidebar.slider(t("min_fishing_hours"), 0.0, 24.0, 1.0, 0.1)

    all_flags = sorted(df["Flag"].dropna().unique().tolist())
    selected_flags = st.sidebar.multiselect(t("flag_state"), all_flags, placeholder=t("all_flags"))

    all_types = sorted(df["VesselType"].dropna().unique().tolist())
    selected_types = st.sidebar.multiselect(t("vessel_type"), all_types, placeholder=t("all_types"))

    severity_filter = st.sidebar.selectbox(
        t("severity_level"), ["All", "CRITICAL", "HIGH", "MEDIUM", "NORMAL"]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown(f'<span class="section-label">{t("map_style")}</span>', unsafe_allow_html=True)
    map_color = st.sidebar.selectbox(t("column_color"), ["Teal (Default)", "Heat (Red→Yellow)", "Blue"])

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
    lang_badge = "हिंग्लिश" if st.session_state.get("lang") == "hi" else "ENG"

    # ── Header ──
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; justify-content:space-between;
                    border-bottom:1px solid rgba(0,200,160,0.15); padding-bottom:14px; margin-bottom:20px;">
            <div>
                <span style="font-family:'Space Mono',monospace; font-size:22px;
                             font-weight:700; color:#00c8a0; letter-spacing:3px;">
                    {t("header_title")}
                </span>
                <span class="lang-badge">{lang_badge}</span>
                <span style="font-family:'Space Mono',monospace; font-size:10px;
                             color:#6b8099; margin-left:16px; letter-spacing:2px;">
                    {t("header_sub")}
                </span>
            </div>
            <div style="display:flex; gap:20px; align-items:center;">
                <span style="font-family:'Space Mono',monospace; font-size:10px; color:#00c8a0;">
                </span>
                <span style="font-family:'Space Mono',monospace; font-size:10px; color:#6b8099;">
                    {t("region")}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Load Data ──
    with st.spinner(""):
        progress = st.progress(0, text=t("loading_1"))
        df = load_data()
        progress.progress(50, text=t("loading_2"))
        if df is None:
            progress.empty()
            st.error(t("data_error"))
            return
        progress.progress(100, text=t("loading_3"))
        import time; time.sleep(0.4)
        progress.empty()

    # ── Tabs ──
    tab_dashboard, tab_about = st.tabs([t("tab_dashboard"), t("tab_about")])

    # ════════════════════════════════════════════════════════════
    # TAB 1 — DASHBOARD
    # ════════════════════════════════════════════════════════════
    with tab_dashboard:

        hr_filter, sel_flags, sel_types, sev_filter, map_color = build_sidebar(df)
        fdf = apply_filters(df, hr_filter, sel_flags, sel_types, sev_filter)

        if len(fdf) == 0:
            st.warning(t("no_match"))
            return

        # ── KPI Strip ──
        anomaly_count = len(fdf[fdf["fishing_hours"] > 20])
        unique_vessels = fdf["MMSI"].nunique()
        total_pings = len(fdf)
        top_flag = fdf["Flag"].value_counts().idxmax() if len(fdf) > 0 else "—"

        k1, k2, k3, k4 = st.columns(4)
        k1.metric(t("kpi_ships"), f"{unique_vessels:,}", delta=t("kpi_filter").format(hr_filter))
        k2.metric(t("kpi_signals"), f"{total_pings:,}")
        k3.metric(t("kpi_country"), top_flag)

        with k4:
            st.markdown(
                f"""
                <div style="background:#0d1420; border:1px solid rgba(0,200,160,0.15);
                            border-top:2px solid #ff6b35; border-radius:8px; padding:16px;">
                    <div style="font-family:'Space Mono',monospace; font-size:10px;
                                 letter-spacing:2px; color:#6b8099; text-transform:uppercase;">
                        {t("kpi_suspicious")}
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
            st.markdown(f'<span class="section-label">{t("map_label")}</span>', unsafe_allow_html=True)
            st.caption(t("map_caption"))
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
            st.markdown(f'<span class="section-label">{t("flags_label")}</span>', unsafe_allow_html=True)
            st.caption(t("flags_caption"))
            st.plotly_chart(make_flag_chart(fdf), width='stretch')

        # ── Row 2: Trends + Gear + Hourly ──
        st.markdown("---")
        c1, c2, c3 = st.columns([2, 1.2, 1.2])

        with c1:
            st.markdown(f'<span class="section-label">{t("trend_label")}</span>', unsafe_allow_html=True)
            st.caption(t("trend_caption"))
            st.plotly_chart(make_trend_chart(fdf), width='stretch')

        with c2:
            st.markdown(f'<span class="section-label">{t("gear_label")}</span>', unsafe_allow_html=True)
            st.caption(t("gear_caption"))
            st.plotly_chart(make_gear_chart(fdf), width='stretch')

        with c3:
            st.markdown(f'<span class="section-label">{t("hourly_label")}</span>', unsafe_allow_html=True)
            st.caption(t("hourly_caption"))
            st.plotly_chart(make_hourly_chart(fdf), width='stretch')

        # ── Row 3: Anomaly Scatter + Top Targets ──
        st.markdown("---")
        col_scatter, col_targets = st.columns([3, 2])

        with col_scatter:
            st.markdown(f'<span class="section-label">{t("anomaly_label")}</span>', unsafe_allow_html=True)
            st.caption(t("anomaly_caption"))
            st.plotly_chart(make_anomaly_scatter(fdf), width='stretch')

        with col_targets:
            st.markdown(f'<span class="section-label">{t("targets_label")}</span>', unsafe_allow_html=True)
            st.caption(t("targets_caption"))
            suspects = (
                fdf.groupby(["VesselName", "Flag", "VesselType"])["fishing_hours"]
                .sum().reset_index().nlargest(10, "fishing_hours")
                .rename(columns={
                    "VesselName": t("col_ship_name"),
                    "Flag": t("col_country"),
                    "VesselType": t("col_vessel_type"),
                    "fishing_hours": t("col_total_hrs"),
                })
            )
            suspects[t("col_total_hrs")] = suspects[t("col_total_hrs")].round(1)
            suspects[t("col_alert")] = suspects[t("col_total_hrs")].apply(
                lambda h: "🔴 Critical" if h > 20 else ("🟠 High" if h > 15 else "🟡 Medium")
            )
            st.dataframe(
                suspects.reset_index(drop=True),
                width='stretch',
                column_config={
                    t("col_total_hrs"): st.column_config.ProgressColumn(
                        t("col_total_hrs"), min_value=0,
                        max_value=float(suspects[t("col_total_hrs")].max()),
                        format="%.1f",
                    ),
                },
                hide_index=True,
            )

        # ── Row 4: Summary + Download ──
        st.markdown("---")
        i1, i2 = st.columns([3, 1])

        with i1:
            st.markdown(f'<span class="section-label">{t("summary_label")}</span>', unsafe_allow_html=True)
            pct_anomaly = anomaly_count / unique_vessels * 100 if unique_vessels > 0 else 0
            top5_flags = fdf["Flag"].value_counts().head(3).index.tolist()
            lka_pct = (fdf["Flag"] == top_flag).sum() / len(fdf) * 100
            st.info(t("summary_text").format(
                anomaly_count=anomaly_count,
                pct=pct_anomaly,
                top_flag=top_flag,
                lka_pct=lka_pct,
                top3=", ".join(top5_flags),
            ))

        with i2:
            st.markdown(f'<span class="section-label">{t("download_label")}</span>', unsafe_allow_html=True)
            csv = fdf[["MMSI", "VesselName", "Flag", "VesselType", "fishing_hours", "Severity"]].to_csv(index=False).encode("utf-8")
            st.download_button(
                t("download_btn"),
                data=csv,
                file_name="IOR_Report.csv",
                mime="text/csv",
            )

        # ── Full Registry ──
        st.markdown("---")
        with st.expander(t("registry_label"), expanded=False):
            st.caption(t("registry_caption"))
            display_cols = ["MMSI", "VesselName", "Flag", "VesselType", "fishing_hours", "Severity", "Month"]
            display_cols = [c for c in display_cols if c in fdf.columns]
            rename_map = {
                "MMSI": t("col_ship_id"),
                "VesselName": t("col_ship_name"),
                "Flag": t("col_country"),
                "VesselType": t("col_vessel_type"),
                "fishing_hours": t("col_fishing_hrs"),
                "Severity": t("col_alert"),
                "Month": t("col_month"),
            }
            show_df = fdf[display_cols].sort_values("fishing_hours", ascending=False).head(200).reset_index(drop=True)
            show_df = show_df.rename(columns=rename_map)
            st.dataframe(
                show_df,
                width='stretch',
                column_config={
                    t("col_fishing_hrs"): st.column_config.ProgressColumn(
                        t("col_fishing_hrs"), min_value=0,
                        max_value=float(show_df[t("col_fishing_hrs")].max()),
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

        st.markdown(f"""
        <div style="background:#0d1420; border:1px solid rgba(0,200,160,0.2); border-radius:12px;
                    padding:28px 32px; margin-bottom:28px;">
            <div style="font-family:'Space Mono',monospace; font-size:20px; font-weight:700;
                        color:#00c8a0; margin-bottom:10px;">
                {t("about_what_title")}
            </div>
            <p style="font-size:15px; line-height:1.8; color:#9ab0c8 !important;">
                {t("about_what_body")}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Glossary
        st.markdown(f'<span class="section-label">{t("glossary_label")}</span>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        for title, desc in t("terms"):
            with st.expander(title):
                st.markdown(
                    f'<p style="font-size:14px; line-height:1.8; color:#9ab0c8 !important;">{desc}</p>',
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)

        # How it was built
        st.markdown(f'<span class="section-label">{t("how_built_label")}</span>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        for i, (title, desc) in enumerate(t("steps")):
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
        st.markdown(f'<span class="section-label">{t("tech_label")}</span>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        tech_cols = st.columns(4)
        for i, (name, desc) in enumerate(t("techs")):
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

        st.markdown(
            f"""
            <div style="background:#0d1420; border:1px solid rgba(0,136,255,0.2); border-radius:12px;
                        padding:24px 28px; margin-top:8px;">
                <div style="font-family:'Space Mono',monospace; font-size:13px;
                            color:#0088ff; margin-bottom:10px; letter-spacing:2px;">
                    {t("built_by")}
                </div>
                <div style="font-size:16px; font-weight:600; color:#e8f0fe; margin-bottom:6px;">
                    Mehvish Sheikh
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Footer ──
    st.markdown(
        f"""
        <div style="text-align:center; padding:24px 0 8px;
                    font-family:'Space Mono',monospace; font-size:10px;
                    color:#3a4a5a; letter-spacing:2px; border-top:1px solid rgba(0,200,160,0.08);">
            {t("footer")}
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()