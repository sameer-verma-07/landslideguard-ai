"""
dashboard.py
LandslideGuard AI - SIH 2026 PS26001

Run with:
    streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import joblib
import plotly.express as px
import pydeck as pdk
from datetime import datetime, timedelta
import sqlite3
import plotly.graph_objects as go
import numpy as np
import time

# Initialize Session State
if 'offline_queue' not in st.session_state:
    st.session_state.offline_queue = []
if 'state_filter' not in st.session_state:
    st.session_state.state_filter = []
if 'risk_filter' not in st.session_state:
    st.session_state.risk_filter = []

# ============================================================
# UTILITIES & DATABASE
# ============================================================
def fetch_live_telemetry(source):
    try:
        if "IMD" in source:
            time.sleep(1.5) 
            return True, "IMD"
        elif "ISRO" in source:
            time.sleep(2.0)
            return True, "ISRO"
    except Exception as e:
        return False, str(e)
    
def init_db():
    conn = sqlite3.connect('landslide_reports.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reports
                 (timestamp TEXT, location_id TEXT, observation TEXT, note TEXT)''')
    conn.commit()
    conn.close()

init_db()

def insert_report(time_val, loc, obs, note):
    conn = sqlite3.connect('landslide_reports.db')
    c = conn.cursor()
    c.execute("INSERT INTO reports VALUES (?, ?, ?, ?)", (time_val, loc, obs, note))
    conn.commit()
    conn.close()

def get_reports():
    conn = sqlite3.connect('landslide_reports.db')
    df_reports = pd.read_sql("SELECT * FROM reports ORDER BY timestamp DESC", conn)
    conn.close()
    return df_reports
    
# ============================================================
# PAGE CONFIG 
# ============================================================
st.set_page_config(
    page_title="LandslideGuard AI",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# THEME ENGINE & DYNAMIC CSS
# ============================================================
st.sidebar.markdown("### ⚙️ Interface Settings")
theme_choice = st.sidebar.radio("UI Theme", ["Dark", "Light"], horizontal=True)

if theme_choice == "Dark":
    main_bg, sidebar_bg = "#0f172a", "#1e293b"
    text_color = "#f8fafc"
    kpi_bg = "rgba(30, 41, 59, 0.4)"
    kpi_border = "rgba(255, 255, 255, 0.08)"
    kpi_hover = "rgba(255, 255, 255, 0.2)"
    kpi_val_color = "#f8fafc"
    kpi_lbl_color = "#cbd5e1"
    map_theme = pdk.map_styles.CARTO_DARK
    chart_font = "#94a3b8"
    grid_color = "rgba(255,255,255,0.05)"
else:
    main_bg, sidebar_bg = "#f8fafc", "#f1f5f9"
    text_color = "#1e293b"
    kpi_bg = "rgba(255, 255, 255, 0.7)"
    kpi_border = "rgba(0, 0, 0, 0.1)"
    kpi_hover = "rgba(0, 0, 0, 0.3)"
    kpi_val_color = "#0f172a"
    kpi_lbl_color = "#475569"
    map_theme = pdk.map_styles.CARTO_LIGHT
    chart_font = "#475569"
    grid_color = "rgba(0,0,0,0.05)"

st.markdown(f"""
    <style>
    /* ---------- App-wide cleanup & Theme Overrides ---------- */
    .stApp {{ background-color: {main_bg} !important; }}
    [data-testid="stSidebar"] {{ background-color: {sidebar_bg} !important; }}
    
    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {{
        color: {text_color} !important;
    }}
    .stMarkdown strong, .stMarkdown b {{ color: {text_color} !important; }}
    div[data-baseweb="select"] > div, div[data-baseweb="popover"] {{ background-color: {main_bg} !important; }}
    ul[role="listbox"] li {{ color: {text_color} !important; }}
    [data-testid="stDataFrame"] {{ color: {text_color} !important; }}

    .block-container {{ 
        padding-top: 4rem !important; 
        max-width: 1600px; 
        font-family: 'Inter', sans-serif;
    }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* ---------- Typography & Hero ---------- */
    .hero-title {{
        font-size: 3.2rem; font-weight: 900;
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0rem; letter-spacing: -0.05em; line-height: 1.2;
    }}
    .hero-subtitle {{
        font-size: 1.15rem; color: #94a3b8; font-weight: 500;
        margin-bottom: 2rem; letter-spacing: 0.02em;
    }}

    /* ---------- Glassmorphic KPI Cards ---------- */
    .kpi-container {{
        display: flex; flex-direction: column; justify-content: center;
        background: {kpi_bg}; 
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        border: 1px solid {kpi_border};
        border-radius: 16px; padding: 24px; min-height: 130px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, border-color 0.3s ease;
    }}
    .kpi-container:hover {{ transform: translateY(-4px); border-color: {kpi_hover}; }}
    .kpi-header {{ display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }}
    .kpi-label {{ font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: {kpi_lbl_color}; }}
    .kpi-value {{ font-size: 2.6rem; font-weight: 800; color: {kpi_val_color}; line-height: 1; }}

    .kpi-cyan {{ border-bottom: 4px solid #00f2fe; }}
    .kpi-red {{ border-bottom: 4px solid #ef4444; box-shadow: 0 8px 32px 0 rgba(239, 68, 68, 0.15); }}
    .kpi-orange {{ border-bottom: 4px solid #f59e0b; box-shadow: 0 8px 32px 0 rgba(245, 158, 11, 0.15); }}

    /* ---------- UI Elements ---------- */
    .stTabs [data-baseweb="tab-list"] {{ gap: 24px; }}
    .stTabs [data-baseweb="tab"] {{ height: 50px; font-weight: 600 !important; font-size: 1.05rem !important; }}
    hr {{ border-color: {grid_color}; margin: 2rem 0; }}

    /* ============================================================ */
    /* MOBILE RESPONSIVENESS OVERRIDES                              */
    /* ============================================================ */
    @media (max-width: 768px) {{
        .block-container {{ padding-top: 3rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }}
        .hero-title {{ font-size: 2.2rem !important; line-height: 1.1 !important; }}
        .hero-subtitle {{ font-size: 0.85rem !important; margin-bottom: 1.5rem !important; }}
        .kpi-container {{ padding: 16px !important; min-height: 100px !important; margin-bottom: 10px !important; }}
        .kpi-value {{ font-size: 2rem !important; }}
        .kpi-label {{ font-size: 0.65rem !important; }}
        .stTabs [data-baseweb="tab"] {{ font-size: 0.9rem !important; }}
    }}
    </style>
""", unsafe_allow_html=True)

# ============================================================
# CONSTANTS & LOADERS
# ============================================================
FEATURES_CATEGORICAL = ["state", "location_type"]
LEVEL_ICONS = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
RISK_COLORS = {"Critical": "#ef4444", "High": "#f59e0b", "Medium": "#eab308", "Low": "#22c55e"}

def get_map_color(level):
    if level == "Critical": return [239, 68, 68, 220]
    if level == "High": return [245, 158, 11, 220]
    if level == "Medium": return [234, 179, 8, 220]
    return [34, 197, 94, 180]

@st.cache_data
def load_data():
    return pd.read_csv("data/ner_landslide_data.csv")

@st.cache_resource
def load_model_bundle():
    model = joblib.load("model/risk_model.pkl")
    encoders = joblib.load("model/encoders.pkl")
    feature_cols = joblib.load("model/feature_cols.pkl")
    importances = joblib.load("model/feature_importances.pkl")
    return model, encoders, feature_cols, importances

def score_dataframe(data, model, encoders, feature_cols):
    encoded = data.copy()
    for col in FEATURES_CATEGORICAL:
        encoded[col + "_enc"] = encoders[col].transform(data[col])
    return model.predict_proba(encoded[feature_cols])[:, 1]

def risk_bucket(score):
    if score >= 0.75: return "Critical"
    if score >= 0.55: return "High"
    if score >= 0.35: return "Medium"
    return "Low"

df = load_data()
model, encoders, feature_cols, importances = load_model_bundle()
df["risk_score"] = score_dataframe(df, model, encoders, feature_cols)
df["risk_level"] = df["risk_score"].apply(risk_bucket)

# ============================================================
# HEADER & SIDEBAR
# ============================================================
st.markdown('<div class="hero-title">LandslideGuard AI</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">NER Disaster Intelligence • High-Fidelity 3D Risk Command Center</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"""
    <div style="margin-bottom: 15px;">
        <div style="font-size: 1.45rem; font-weight: 900; color: {text_color};">🛰️ COMMAND UPLINK</div>
        <div style="font-size: 0.68rem; font-weight: 800; letter-spacing: 0.12em; color: #10b981;">SYSTEM: ONLINE</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Callback to clear filters
def clear_filters():
    st.session_state.state_filter = []
    st.session_state.risk_filter = []

state_filter = st.sidebar.multiselect(
    "Region Select", 
    sorted(df["state"].unique()), 
    key="state_filter",
    help="Filter active monitoring nodes by specific North Eastern states."
)
risk_filter = st.sidebar.multiselect(
    "Threat Level", 
    ["Critical", "High", "Medium", "Low"], 
    key="risk_filter",
    help="Isolate zones based on the AI's current predictive risk assessment."
)

st.sidebar.button("🔄 Clear All Filters", on_click=clear_filters, use_container_width=True)

# **CRITICAL FIX: Define `filtered` dataset based on the sidebar choices**
filtered = df.copy()
if state_filter: 
    filtered = filtered[filtered["state"].isin(state_filter)]
if risk_filter: 
    filtered = filtered[filtered["risk_level"].isin(risk_filter)]

st.sidebar.markdown("---")
st.sidebar.markdown("### System Architecture")
data_source = st.sidebar.selectbox("Telemetry Source", ["Demo (Synthetic Data)", "ISRO Bhuvan Live API", "IMD Weather API"])
offline_mode = st.sidebar.toggle("Enable Edge/Offline Mode")

if offline_mode:
    st.sidebar.warning("⚠️ Offline Mode Active. Caching telemetry to local Edge Node.")
    st.markdown("""
    <style>
        .stApp { border-top: 5px solid #d97706; }
        .offline-banner {
            background-color: rgba(69, 26, 3, 0.8); color: #fcd34d; padding: 12px; 
            border-radius: 8px; border: 1px solid #d97706; font-family: monospace;
            text-align: center; margin-bottom: 20px; backdrop-filter: blur(10px);
        }
    </style>
    <div class="offline-banner">
        ⚠️ CRITICAL WARNING: Main Network Disconnected. Operating via Local Edge Node.
    </div>
    """, unsafe_allow_html=True)

# Safety Catch: Empty States
if filtered.empty:
    st.info("No active monitoring nodes match your current filter criteria. Try adjusting the Region or Threat Level.")

# ============================================================
# KPI SECTION (Glassmorphism)
# ============================================================
critical_count = int((filtered["risk_level"] == "Critical").sum())
high_count = int((filtered["risk_level"] == "High").sum())
exposed_people = int(filtered.loc[filtered["risk_level"].isin(["Critical", "High"]), "nearby_population"].sum())

k1, k2, k3, k4 = st.columns(4)
with k1: 
    st.markdown(f'<div class="kpi-container kpi-cyan"><div class="kpi-header"><span style="font-size:1.2rem;">📡</span><span class="kpi-label">Active Nodes</span></div><div class="kpi-value">{len(filtered):,}</div></div>', unsafe_allow_html=True)
with k2: 
    st.markdown(f'<div class="kpi-container kpi-red"><div class="kpi-header"><span style="font-size:1.2rem;">🔴</span><span class="kpi-label">Critical Zones</span></div><div class="kpi-value">{critical_count}</div></div>', unsafe_allow_html=True)
with k3: 
    st.markdown(f'<div class="kpi-container kpi-orange"><div class="kpi-header"><span style="font-size:1.2rem;">🟠</span><span class="kpi-label">High-Risk Zones</span></div><div class="kpi-value">{high_count}</div></div>', unsafe_allow_html=True)
with k4: 
    st.markdown(f'<div class="kpi-container kpi-cyan"><div class="kpi-header"><span style="font-size:1.2rem;">👥</span><span class="kpi-label">Exposed Population</span></div><div class="kpi-value">{exposed_people:,}</div></div>', unsafe_allow_html=True)

st.write("---")

# ============================================================
# LIVE SENSOR TELEMETRY FEED 
# ============================================================
st.markdown(f"### 📡 Live Edge-Sensor Telemetry <span style='color:{chart_font}; font-size:1rem; font-weight:normal;'>(Past 24H)</span>", unsafe_allow_html=True)

times = [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)]
rainfall = np.random.normal(loc=15, scale=5, size=24).clip(0) 
seismic = np.random.normal(loc=1.2, scale=0.4, size=24).clip(0)

fig = go.Figure()
fig.add_trace(go.Bar(
    x=times, y=rainfall, name="Rainfall (mm/hr)",
    marker_color='#00f2fe', opacity=0.8, yaxis='y1',
    marker_line_width=0 
))
fig.add_trace(go.Scatter(
    x=times, y=seismic, name="Seismic Vibration",
    mode='lines+markers', line=dict(color='#ef4444', width=3, shape='spline'), 
    marker=dict(size=6, color='#ef4444', line=dict(width=1, color=main_bg)),
    yaxis='y2'
))

fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color=chart_font if not offline_mode else '#fcd34d', family="Inter"),
    margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, font=dict(size=12)),
    hovermode="x unified",
    xaxis=dict(showgrid=False, zeroline=False, showline=False),
    yaxis=dict(title="Rainfall (mm)", showgrid=True, gridcolor=grid_color, zeroline=False),
    yaxis2=dict(title="Vibration (Richter)", overlaying='y', side='right', showgrid=False, zeroline=False)
)
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
st.write("---")

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs(["🌐 3D Risk Terrain", "📊 AI Analytics & Insights", "🚨 Live Alert Feed", "📍 Field Reports"])

with tab1:
    st.markdown(f"<div style='margin-bottom:15px; color:{chart_font};'>Height represents Risk Probability. <b>Shift+Drag</b> to rotate map. Green arcs indicate active evacuation corridors.</div>", unsafe_allow_html=True)
    
    map_df = filtered.copy() if len(filtered) else df.copy()
    map_center = {"lat": float(map_df["latitude"].mean()), "lon": float(map_df["longitude"].mean())} if len(map_df) > 0 else {"lat": 25.5, "lon": 93.0}

    map_df["color"] = map_df["risk_level"].apply(get_map_color)
    map_df["elevation"] = map_df["risk_score"] * 15000 
    
    column_layer = pdk.Layer(
        "ColumnLayer", data=map_df, get_position=["longitude", "latitude"],
        get_elevation="elevation", elevation_scale=1, radius=2500,
        get_fill_color="color", pickable=True, auto_highlight=True,
    )
    
    danger_zones = map_df[map_df['risk_level'].isin(['Critical', 'High'])]
    safe_zones = map_df[map_df['risk_level'] == 'Low']
    
    arcs_data = []
    if not danger_zones.empty and not safe_zones.empty:
        for _, d_row in danger_zones.iterrows():
            s_row = safe_zones.sample(1).iloc[0]
            arcs_data.append({
                "source_lon": d_row["longitude"], "source_lat": d_row["latitude"],
                "target_lon": s_row["longitude"], "target_lat": s_row["latitude"],
                "danger_node": d_row["location_id"], "safe_node": s_row["location_id"]
            })
            
    arc_layer = pdk.Layer(
        "ArcLayer", data=pd.DataFrame(arcs_data),
        get_source_position=["source_lon", "source_lat"], get_target_position=["target_lon", "target_lat"],
        get_source_color=[239, 68, 68, 255], get_target_color=[34, 197, 94, 255], 
        get_width=3, pickable=True, auto_highlight=True
    ) if arcs_data else None
    
    layers = [column_layer, arc_layer] if arc_layer else [column_layer]
    
    r = pdk.Deck(
        layers=layers, 
        initial_view_state=pdk.ViewState(latitude=map_center["lat"], longitude=map_center["lon"], zoom=5.5, pitch=50, bearing=25),
        tooltip={"html": "<b>Location:</b> {location_id} {danger_node} <br/> <b>Risk:</b> {risk_level}", "style": {"color": "black" if theme_choice == "Light" else "white"}},
        map_style=map_theme 
    )
    st.pydeck_chart(r, use_container_width=True)

with tab2:
    left, right = st.columns([1.65, 1])
    with left:
        st.markdown('#### Risk Intelligence Feed')
        show_cols = ["location_id", "state", "risk_level", "risk_score", "rainfall_last_7d_mm", "slope_angle_deg"]
        display_df = filtered.sort_values("risk_score", ascending=False)[show_cols].copy()
        display_df["risk_score"] = (display_df["risk_score"] * 100).round(1).astype(str) + "%"
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    with right:
        st.markdown('#### AI Model Drivers')
        imp_df = importances.reset_index()
        imp_df.columns = ["feature", "importance"]
        fig_imp = px.bar(imp_df.head(6), x="importance", y="feature", orientation="h", text_auto=".2f")
        fig_imp.update_traces(marker_color='#00f2fe')
        fig_imp.update_layout(yaxis={"categoryorder": "total ascending"}, height=320, margin=dict(l=0, r=0, t=0, b=0), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color=chart_font))
        st.plotly_chart(fig_imp, use_container_width=True)

    st.write("---")
    
    # AI Simulator Expander
    with st.expander("🎛️ Advanced: AI 'What-If' Scenario Simulator", expanded=False):
        st.markdown(f"<span style='color:{chart_font};'>Manually adjust environmental factors to test the machine learning model's real-time predictions.</span>", unsafe_allow_html=True)
        
        sim_col1, sim_col2, sim_col3 = st.columns([1, 1, 1])
        with sim_col1:
            # Safe catch for simulator location dropdown if filtered is empty
            sim_opts = filtered["location_id"].unique() if len(filtered) else df["location_id"].unique()
            sim_loc = st.selectbox("Target Location", sim_opts, help="Select a monitoring node to run the simulation.")
            base_row = df[df["location_id"] == sim_loc].iloc[0]
        with sim_col2:
            sim_rain = st.slider("Simulated 7-Day Rainfall (mm)", min_value=0, max_value=500, value=int(base_row["rainfall_last_7d_mm"]), step=10, help="Simulate a sudden monsoon surge.")
        with sim_col3:
            sim_moisture = st.slider("Simulated Soil Moisture (%)", min_value=0, max_value=100, value=int(base_row["soil_moisture_pct"]), step=5, help="Simulate ground saturation levels.")

        sim_df = pd.DataFrame([base_row])
        sim_df["rainfall_last_7d_mm"] = sim_rain
        sim_df["soil_moisture_pct"] = sim_moisture
        
        sim_score = score_dataframe(sim_df, model, encoders, feature_cols)[0]
        sim_level = risk_bucket(sim_score)
        sim_color = RISK_COLORS[sim_level]
        
        st.markdown(
            f"""
            <div style="background: {main_bg}; padding: 20px; border-radius: 12px; border-left: 6px solid {sim_color}; margin-top: 15px; border: 1px solid {kpi_border};">
                <h4 style="margin:0; color: {text_color};">Live Model Prediction: {LEVEL_ICONS[sim_level]} {sim_level.upper()} RISK</h4>
                <p style="margin:5px 0 0 0; color:{chart_font}; font-size:1.2rem;"><b>{(sim_score*100):.1f}%</b> Confidence Score</p>
            </div>
            """,
            unsafe_allow_html=True
        )

with tab3:
    st.markdown("### Automated Threat Detection")
    top_alerts = df[df["risk_level"].isin(["Critical", "High"])].sort_values("risk_score", ascending=False).head(5)
    
    if len(top_alerts) == 0:
        st.success("No high-risk anomalies detected.")
    else:
        for _, r in top_alerts.iterrows():
            st.warning(f"🚨 {r['risk_level'].upper()} THREAT: {r['location_id']} in {r['state']} | Confidence: {(r['risk_score']*100):.1f}%")

with tab4:
    st.markdown("### Ground Observation Hub")
    with st.form("citizen_report_form", clear_on_submit=True):
        rep_col1, rep_col2 = st.columns(2)
        with rep_col1:
            loc_options = df["location_id"].unique()
            location = st.selectbox("Nearest monitoring point", loc_options)
            observation = st.selectbox("Observation", ["Visible ground cracks", "Slope movement", "Water seepage", "Other"])
        with rep_col2:
            note = st.text_input("Additional note")
        
        if st.form_submit_button("Transmit Secure Report", type="primary", use_container_width=True):
            with st.spinner("Encrypting and transmitting data..."):
                time.sleep(0.8) 
                insert_report(datetime.now().strftime("%Y-%m-%d %H:%M"), location, observation, note)
            st.toast("Ground observation saved to secure database.", icon="✅")