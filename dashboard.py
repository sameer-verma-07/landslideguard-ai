"""
dashboard.py
Interactive early-warning dashboard for SIH PS 26001.
Run with: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import joblib
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="NER Landslide Early Warning", layout="wide")

FEATURES_CATEGORICAL = ["state", "location_type"]


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
    if score >= 0.75:
        return "Critical"
    if score >= 0.55:
        return "High"
    if score >= 0.35:
        return "Medium"
    return "Low"


RISK_COLORS = {"Critical": "#b91c1c", "High": "#ea580c", "Medium": "#ca8a04", "Low": "#16a34a"}

df = load_data()
model, encoders, feature_cols, importances = load_model_bundle()
df["risk_score"] = score_dataframe(df, model, encoders, feature_cols)
df["risk_level"] = df["risk_score"].apply(risk_bucket)

if "citizen_reports" not in st.session_state:
    st.session_state.citizen_reports = []

st.title("NER Landslide Early Warning Dashboard")
st.caption("SIH 2026 - PS 26001 | AI-based landslide risk monitoring, North Eastern Region")

# --- Sidebar filters ---
st.sidebar.header("Filters")
state_filter = st.sidebar.multiselect("State", sorted(df["state"].unique()))
risk_filter = st.sidebar.multiselect("Risk level", ["Critical", "High", "Medium", "Low"])

filtered = df.copy()
if state_filter:
    filtered = filtered[filtered["state"].isin(state_filter)]
if risk_filter:
    filtered = filtered[filtered["risk_level"].isin(risk_filter)]

# --- Top metrics ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Monitored locations", len(filtered))
col2.metric("Critical", int((filtered["risk_level"] == "Critical").sum()))
col3.metric("High risk", int((filtered["risk_level"] == "High").sum()))
col4.metric("People in high/critical zones", int(
    filtered.loc[filtered["risk_level"].isin(["Critical", "High"]), "nearby_population"].sum()
))

st.divider()

# --- Map ---
st.subheader("Risk map")
map_df = filtered if len(filtered) else df
fig_map = px.scatter_map(
    map_df, lat="latitude", lon="longitude",
    color="risk_level", size="nearby_population",
    hover_name="location_id",
    hover_data={"state": True, "location_type": True, "risk_score": ":.0%",
                "latitude": False, "longitude": False, "nearby_population": True},
    color_discrete_map=RISK_COLORS,
    category_orders={"risk_level": ["Critical", "High", "Medium", "Low"]},
    zoom=4.6, height=480,
)
fig_map.update_layout(
    map_style="open-street-map",
    margin=dict(l=0, r=0, t=0, b=0)
)
st.plotly_chart(fig_map, use_container_width=True)

st.divider()
left, right = st.columns([2, 1])

with left:
    st.subheader("Monitoring points, sorted by risk")
    show_cols = ["location_id", "state", "location_type", "slope_angle_deg",
                 "rainfall_last_7d_mm", "soil_moisture_pct", "risk_score", "risk_level"]
    st.dataframe(
        filtered.sort_values("risk_score", ascending=False)[show_cols],
        use_container_width=True, hide_index=True,
    )

with right:
    st.subheader("What's driving risk")
    imp_df = importances.reset_index()
    imp_df.columns = ["feature", "importance"]
    fig_imp = px.bar(imp_df.head(8), x="importance", y="feature", orientation="h")
    fig_imp.update_layout(yaxis={"categoryorder": "total ascending"}, height=350)
    st.plotly_chart(fig_imp, use_container_width=True)

st.divider()
st.subheader("Live alert feed (simulated)")
top_alerts = df[df["risk_level"].isin(["Critical", "High"])].sort_values("risk_score", ascending=False).head(5)
if len(top_alerts) == 0:
    st.info("No active high-risk alerts right now.")
else:
    for _, r in top_alerts.iterrows():
        icon = "🔴" if r["risk_level"] == "Critical" else "🟠"
        st.write(f"{icon} **{r['location_id']}** ({r['state']}, {r['location_type']}) — "
                 f"{r['risk_score']:.0%} risk. Rainfall last 7d: {r['rainfall_last_7d_mm']}mm, "
                 f"slope {r['slope_angle_deg']}°. ~{r['nearby_population']} people nearby.")

st.divider()
st.subheader("Report a ground observation")
st.caption("Citizens or field officials can flag visible cracks or slope movement here.")
with st.form("citizen_report_form", clear_on_submit=True):
    rep_col1, rep_col2 = st.columns(2)
    with rep_col1:
        location = st.selectbox("Nearest monitoring point", df["location_id"])
        observation = st.selectbox(
            "What did you observe?",
            ["Visible ground cracks", "Slope movement / bulging", "Water seepage on slope",
             "Fallen trees / debris", "Other"],
        )
    with rep_col2:
        photo = st.file_uploader("Photo (optional)", type=["jpg", "jpeg", "png"])
        note = st.text_input("Additional note")
    submitted = st.form_submit_button("Submit report")
    if submitted:
        st.session_state.citizen_reports.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "location_id": location,
            "observation": observation,
            "note": note,
            "has_photo": photo is not None,
        })
        st.success("Report submitted — added to the field-reports feed below.")

if st.session_state.citizen_reports:
    st.write("**Recent field reports (this session):**")
    st.dataframe(pd.DataFrame(st.session_state.citizen_reports), use_container_width=True, hide_index=True)

st.divider()
st.subheader("Inspect a single location")
options = filtered["location_id"] if len(filtered) else df["location_id"]
selected_id = st.selectbox("Location ID", options)
row = df[df["location_id"] == selected_id].iloc[0]

c1, c2 = st.columns(2)
with c1:
    st.write(f"**State:** {row['state']}  |  **Type:** {row['location_type']}")
    st.write(f"**Slope angle:** {row['slope_angle_deg']}°  |  **Elevation:** {row['elevation_m']}m")
    st.write(f"**Soil moisture:** {row['soil_moisture_pct']}%")
    st.write(f"**Rainfall (7d / 30d):** {row['rainfall_last_7d_mm']}mm / {row['rainfall_last_30d_mm']}mm")
    st.write(f"**Nearby population:** {row['nearby_population']}")
with c2:
    st.metric("Risk score", f"{row['risk_score']:.0%}")
    level_icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
    st.markdown(f"**Risk level:** {level_icon[row['risk_level']]} {row['risk_level']}")
    if row["risk_level"] in ["Critical", "High"]:
        st.error("Recommended action: alert district disaster authority and restrict access to the zone.")
    else:
        st.success("Normal - continue routine monitoring.")
