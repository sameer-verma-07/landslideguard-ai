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
from datetime import datetime

import sqlite3
import requests
import json

# Initialize local database

import time

def fetch_live_telemetry(source):
    """
    Scaffolding for actual API integration. 
    Replace time.sleep with real requests.get() calls when keys are acquired.
    """
    try:
        if "IMD" in source:
            # TODO: req = requests.get("https://api.imd.gov.in/v1/weather", headers={"Token": "YOUR_IMD_KEY"})
            # df_live = pd.DataFrame(req.json())
            time.sleep(1.5) # Simulate network latency
            return True, "IMD"
            
        elif "ISRO" in source:
            # TODO: req = requests.get("https://bhuvan.nrsc.gov.in/wfs/landslide", auth=('user', 'pass'))
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

def insert_report(time, loc, obs, note):
    conn = sqlite3.connect('landslide_reports.db')
    c = conn.cursor()
    c.execute("INSERT INTO reports VALUES (?, ?, ?, ?)", (time, loc, obs, note))
    conn.commit()
    conn.close()

def get_reports():
    conn = sqlite3.connect('landslide_reports.db')
    df = pd.read_sql("SELECT * FROM reports ORDER BY timestamp DESC", conn)
    conn.close()
    return df

def trigger_emergency_webhook(location, risk, score):
    # Mock payload for Zapier / Twilio / Custom API
    payload = {"location": location, "risk_level": risk, "confidence": score}
    try:
        # requests.post("https://your-webhook.endpoint/alerts", json=payload)
        return True
    except:
        return False
    
    
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
# ADVANCED CUSTOM CSS (Animations & 3D Feel)
# ============================================================

st.markdown(
    """
    <style>
    /* ---------- Mobile Optimization ---------- */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .hero-title {
            font-size: 1.8rem;
        }
        .hero-subtitle {
            font-size: 0.9rem;
        }
        .kpi-card {
            min-height: 80px;
            padding: 12px;
            margin-bottom: 10px;
        }
        .kpi-value {
            font-size: 1.6rem;
        }
        button[data-baseweb="tab"] {
            font-size: 0.9rem !important;
            padding-left: 8px !important;
            padding-right: 8px !important;
        }
    }

    /* ---------- Global ---------- */
    .block-container {
        max-width: 1500px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    /* ---------- Headings with Gradient ---------- */
    .hero-title {
        font-size: 2.8rem;
        font-weight: 900;
        background: -webkit-linear-gradient(45deg, #3b82f6, #8b5cf6, #ef4444);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.15rem;
        letter-spacing: -0.04em;
    }

    .hero-subtitle {
        font-size: 1.1rem;
        color: var(--text-color);
        opacity: 0.8;
        margin-bottom: 1.5rem;
        font-weight: 500;
    }

    /* ---------- Animated KPI cards ---------- */
    .kpi-card {
        background: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 18px;
        padding: 18px 20px;
        min-height: 118px;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.045);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        cursor: default;
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
        border-color: rgba(128, 128, 128, 0.4);
    }

    .kpi-label {
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-color);
        opacity: 0.7;
    }

    .kpi-value {
        font-size: 2.2rem;
        font-weight: 900;
        color: var(--text-color);
        margin-top: 7px;
    }

    /* ---------- Pulsing Alert Cards ---------- */
    @keyframes pulse-border {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }

    .alert-card {
        background: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-left: 5px solid #ef4444;
        border-radius: 14px;
        padding: 13px 16px;
        margin-bottom: 12px;
        transition: transform 0.2s;
    }

    .alert-card.critical {
        animation: pulse-border 2s infinite;
        border-left: 6px solid #b91c1c;
    }
    
    .alert-card:hover {
        transform: translateX(5px);
    }

    .alert-title {
        font-weight: 800;
        color: var(--text-color);
    }

    /* ---------- Info card ---------- */
    .info-card {
        background: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.045);
        transition: box-shadow 0.3s ease;
    }
    .info-card:hover {
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
    }

    /* Streamlit Tabs Styling to look like buttons */
    button[data-baseweb="tab"] {
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }
    
    /* ---------- Footer ---------- */
    .footer {
        text-align: center;
        color: var(--text-color);
        opacity: 0.7;
        font-size: 0.78rem;
        padding: 20px 0 5px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# CONSTANTS & LOADERS
# ============================================================
FEATURES_CATEGORICAL = ["state", "location_type"]
LEVEL_ICONS = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
RISK_COLORS = {
    "Critical": "#b91c1c",
    "High": "#ea580c",
    "Medium": "#ca8a04",
    "Low": "#16a34a",
}

# Helper to assign RGB colors for the 3D Map
def get_map_color(level):
    if level == "Critical": return [185, 28, 28, 200]  # Deep Red
    if level == "High": return [234, 88, 12, 200]      # Orange
    if level == "Medium": return [202, 138, 4, 200]    # Yellow
    return [22, 163, 74, 150]                          # Green

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

if "citizen_reports" not in st.session_state:
    st.session_state.citizen_reports = []

# ============================================================
# HEADER
# ============================================================

st.markdown('<div class="hero-title">🏔️ LandslideGuard AI </div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">NER Disaster Intelligence • High-Fidelity 3D Risk Command Center</div>', unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================

# Uses a native emoji/text combo instead of an external image link for reliability
st.sidebar.markdown(
    """
    <div style="margin-bottom: 28px;">
        <div style="font-size: 1.45rem; font-weight: 900; color: var(--text-color);">
            🛰️ COMMAND UPLINK
        </div>
        <div style="font-size: 0.68rem; font-weight: 800; letter-spacing: 0.12em; color: var(--text-color); opacity: 0.7;">
            SYSTEM: ONLINE
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

state_filter = st.sidebar.multiselect("Region Select", sorted(df["state"].unique()))
risk_filter = st.sidebar.multiselect("Threat Level", ["Critical", "High", "Medium", "Low"])
st.sidebar.markdown("### System Architecture")

data_source = st.sidebar.selectbox(
    "Telemetry Source",
    ["Demo (Synthetic Data)", "ISRO Bhuvan Live API", "IMD Weather API"]
)

offline_mode = st.sidebar.toggle("Enable Edge/Offline Mode")

if offline_mode:
    st.sidebar.warning("⚠️ Offline Mode Active. Caching telemetry to local SQLite. Webhooks paused.")
elif data_source != "Demo (Synthetic Data)":
    is_success, message = fetch_live_telemetry(data_source)
    if is_success:
        st.sidebar.success(f"✅ {message} API Connected.")
    else:
        st.sidebar.error(f"❌ Error connecting to {message} API.")

filtered = df.copy()
if state_filter: filtered = filtered[filtered["state"].isin(state_filter)]
if risk_filter: filtered = filtered[filtered["risk_level"].isin(risk_filter)]

# ============================================================
# KPI SECTION (Animated)
# ============================================================

critical_count = int((filtered["risk_level"] == "Critical").sum())
high_count = int((filtered["risk_level"] == "High").sum())
exposed_people = int(filtered.loc[filtered["risk_level"].isin(["Critical", "High"]), "nearby_population"].sum())

k1, k2, k3, k4 = st.columns(4)
with k1: st.markdown(f'<div class="kpi-card"><div class="kpi-label">Active Nodes</div><div class="kpi-value">{len(filtered):,}</div></div>', unsafe_allow_html=True)
with k2: st.markdown(f'<div class="kpi-card" style="border-bottom: 4px solid #b91c1c;"><div class="kpi-label">Critical Zones</div><div class="kpi-value">{critical_count}</div></div>', unsafe_allow_html=True)
with k3: st.markdown(f'<div class="kpi-card" style="border-bottom: 4px solid #ea580c;"><div class="kpi-label">High-Risk Zones</div><div class="kpi-value">{high_count}</div></div>', unsafe_allow_html=True)
with k4: st.markdown(f'<div class="kpi-card"><div class="kpi-label">Exposed Population</div><div class="kpi-value">{exposed_people:,}</div></div>', unsafe_allow_html=True)

st.write("---")

# ============================================================
# TABS FOR CLEANER UI
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs(["🌐 3D Risk Terrain", "📊 AI Analytics & Insights", "🚨 Live Alert Feed", "📍 Field Reports"])

with tab1:
    st.markdown("### Interactive 3D Spatial Assessment")
    st.markdown("<span style='opacity:0.7;'>Height represents Risk Probability. Color indicates Threat Level. <b>Shift+Drag</b> to rotate map.</span>", unsafe_allow_html=True)
    
    map_df = filtered.copy() if len(filtered) else df.copy()
    
    if len(map_df) > 0:
        map_center = {"lat": float(map_df["latitude"].mean()), "lon": float(map_df["longitude"].mean())}
    else:
        map_center = {"lat": 25.5, "lon": 93.0}

    # Prepare data for 3D map
    map_df["color"] = map_df["risk_level"].apply(get_map_color)
    map_df["elevation"] = map_df["risk_score"] * 15000  # Scale height based on score

    # PyDeck 3D Column Layer
    layer = pdk.Layer(
        "ColumnLayer",
        data=map_df,
        get_position=["longitude", "latitude"],
        get_elevation="elevation",
        elevation_scale=1,
        radius=2500, # Size of the 3D columns
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
    )

    # Set the initial 3D angled view
    view_state = pdk.ViewState(
        latitude=map_center["lat"],
        longitude=map_center["lon"],
        zoom=5.5,
        pitch=45,  # Angles the map to make it 3D
        bearing=15, # Rotates the map slightly
    )

    # Render map
    # Render map
    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "Location ID: {location_id}\nRisk Level: {risk_level}\nProbability: {risk_score}"},
        map_style="dark" # Switched to a free native dark base map (no API key needed)
    )
    st.pydeck_chart(r, use_container_width=True)
    

with tab2:
    left, right = st.columns([1.65, 1])
    with left:
        st.markdown('<div class="info-card"><b>Risk Intelligence Feed</b><br><span style="opacity:0.7;font-size:0.85rem;">Ranked by AI probability score</span></div>', unsafe_allow_html=True)
        show_cols = ["location_id", "state", "risk_level", "risk_score", "rainfall_last_7d_mm", "slope_angle_deg"]
        display_df = filtered.sort_values("risk_score", ascending=False)[show_cols].copy()
        display_df["risk_score"] = (display_df["risk_score"] * 100).round(1).astype(str) + "%"
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    with right:
        st.markdown('<div class="info-card"><b>AI Model Drivers</b><br><span style="opacity:0.7;font-size:0.85rem;">What features are causing these alerts?</span></div>', unsafe_allow_html=True)
        imp_df = importances.reset_index()
        imp_df.columns = ["feature", "importance"]
        fig_imp = px.bar(imp_df.head(6), x="importance", y="feature", orientation="h", text_auto=".2f")
        fig_imp.update_traces(marker_color='#3b82f6') # Modern blue bars
        fig_imp.update_layout(yaxis={"categoryorder": "total ascending"}, height=320, margin=dict(l=0, r=0, t=20, b=0), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_imp, use_container_width=True)
        st.write("---")
    st.markdown("### 🎛️ AI 'What-If' Scenario Simulator")
    st.markdown("<span style='opacity:0.7;'>Manually adjust environmental factors to test the machine learning model's real-time predictions.</span>", unsafe_allow_html=True)
    
    sim_col1, sim_col2, sim_col3 = st.columns([1, 1, 1])
    
    with sim_col1:
        sim_loc = st.selectbox("Target Location", filtered["location_id"].unique() if len(filtered) else df["location_id"].unique())
        base_row = df[df["location_id"] == sim_loc].iloc[0]
        
    with sim_col2:
        # Let the user artificially increase rainfall
        sim_rain = st.slider(
            "Simulated 7-Day Rainfall (mm)", 
            min_value=0, max_value=500, 
            value=int(base_row["rainfall_last_7d_mm"]),
            step=10
        )
        
    with sim_col3:
        # Let the user artificially increase soil moisture
        sim_moisture = st.slider(
            "Simulated Soil Moisture (%)", 
            min_value=0, max_value=100, 
            value=int(base_row["soil_moisture_pct"]),
            step=5
        )

    # Create a dummy dataframe with the simulated values
    sim_df = pd.DataFrame([base_row])
    sim_df["rainfall_last_7d_mm"] = sim_rain
    sim_df["soil_moisture_pct"] = sim_moisture
    
    # Run the model live
    sim_score = score_dataframe(sim_df, model, encoders, feature_cols)[0]
    sim_level = risk_bucket(sim_score)
    sim_color = RISK_COLORS[sim_level]
    
    # Display the dynamic result
    st.markdown(
        f"""
        <div style="background: var(--secondary-background-color); padding: 20px; border-radius: 12px; border-left: 6px solid {sim_color}; margin-top: 15px;">
            <h4 style="margin:0; color: var(--text-color);">Live Model Prediction: {LEVEL_ICONS[sim_level]} {sim_level.upper()} RISK</h4>
            <p style="margin:5px 0 0 0; opacity:0.8; font-size:1.2rem;"><b>{(sim_score*100):.1f}%</b> Confidence Score</p>
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
            alert_class = "critical" if r["risk_level"] == "Critical" else ""
            icon = LEVEL_ICONS[r["risk_level"]]
            st.markdown(
                f"""
                <div class="alert-card {alert_class}">
                    <div class="alert-title">{icon} {r['location_id']} • {r['risk_level'].upper()} THREAT LEVEL DETECTED</div>
                    <div class="alert-meta">
                        Loc: {r['state']} ({r['location_type']}) &nbsp;|&nbsp; 
                        Confidence: {(r['risk_score']*100):.1f}% &nbsp;|&nbsp; 
                        Rainfall Surge: {r['rainfall_last_7d_mm']}mm
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            # Add webhook button for critical alerts
            if r["risk_level"] == "Critical":
                if st.button(f"📡 Broadcast Evacuation Alert for {r['location_id']}", key=f"btn_{r['location_id']}"):
                    trigger_emergency_webhook(r['location_id'], r['risk_level'], r['risk_score'])
                    st.toast(f"Emergency SMS/Webhook dispatched for {r['location_id']}!", icon="🚨")

with tab4:
    st.markdown("### Ground Observation Hub")
    st.markdown("<span style='opacity:0.7;'>Submit visible signs of slope instability. Data persists via local SQLite database.</span>", unsafe_allow_html=True)
    
    with st.form("citizen_report_form", clear_on_submit=True):
        rep_col1, rep_col2 = st.columns(2)
        with rep_col1:
            location = st.selectbox("Nearest monitoring point", df["location_id"])
            observation = st.selectbox("Observation", ["Visible ground cracks", "Slope movement / bulging", "Water seepage on slope", "Fallen trees / debris", "Road blockage", "Other"])
        with rep_col2:
            photo = st.file_uploader("Photo (optional)", type=["jpg", "jpeg", "png"])
            note = st.text_input("Additional note")
            
        submitted = st.form_submit_button("Submit ground report", type="primary", use_container_width=True)

        if submitted:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            insert_report(current_time, location, observation, note)
            st.success("Ground observation saved to secure database.")

    # Display persistent reports
    db_reports = get_reports()
    if not db_reports.empty:
        st.markdown('<div class="info-card"><b>Recent field reports (Database)</b><br></div>', unsafe_allow_html=True)
        st.dataframe(db_reports, use_container_width=True, hide_index=True)
# ============================================================
# FOOTER
# ============================================================
st.write("---")
st.markdown(
    """
    <div class="footer">
        <b>LandslideGuard AI</b> • SIH 2026 PS26001 • Prototype Command & Control System
    </div>
    """,
    unsafe_allow_html=True,
)

