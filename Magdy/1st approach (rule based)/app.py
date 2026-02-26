"""
Streamlit dashboard: Campaign Health — gauges, trend, radar, top actions.
Run: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import numpy as np

from campaign_health import run_pipeline, build_final_table

st.set_page_config(page_title="Campaign Health", layout="wide")
st.title("Campaign Health Score Dashboard")

@st.cache_data
def load_and_run():
    from campaign_health import load_data
    df = load_data("global")
    return run_pipeline(df), build_final_table(df)

df, final = load_and_run()

campaigns = df["campaign_name"].tolist()
selected = st.sidebar.selectbox("Select campaign", campaigns, index=0)
row = df[df["campaign_name"] == selected].iloc[0]

# --- Metrics row ---
c1, c2, c3, c4 = st.columns(4)
with c1:
    score = row["adjusted_health_score"]
    color = "🟢" if score > 75 else "🟡" if score >= 50 else "🔴"
    st.metric("Health Score", f"{score:.1f}", delta=None)
    st.caption(f"{color} {row['campaign_state']}")
with c2:
    st.metric("ROAS Trend", f"{row['roas_trend']:.2f}", delta="↑ Improving" if row["roas_trend"] > 1 else "↓ Declining")
with c3:
    st.metric("Confidence", f"{row['confidence']:.2f}", delta=None)
with c4:
    st.metric("Budget utilization", f"{row['budget_utilization']*100:.0f}%", delta=None)

# --- Gauge (simple bar) ---
st.subheader("Health score gauge")
st.progress(min(1.0, score / 100))

# --- Radar (metric percentiles) ---
st.subheader("Metric percentiles (relative strength)")
radar_cols = ["roas_p", "cvr_p", "ctr_p", "aov_p", "qs_p"]
# CPA: lower is better, so we show (1 - cpa_p)
radar_vals = [row["roas_p"], row["cvr_p"], row["ctr_p"], row["aov_p"], row["qs_p"], 1 - row["cpa_p"]]
radar_labels = ["ROAS", "CVR", "CTR", "AOV", "QS", "CPA (inv)"]
radar_df = pd.DataFrame({"metric": radar_labels, "value": [v * 100 for v in radar_vals]})
st.bar_chart(radar_df.set_index("metric"))

# --- Recommended actions ---
st.subheader("Recommended actions")
for i, action in enumerate([row["top_action_1"], row["top_action_2"], row["top_action_3"]], 1):
    if pd.notna(action) and str(action) != "nan":
        st.write(f"**{i}.** {action}")

# --- Diagnostics ---
with st.expander("Diagnostic signals"):
    st.write("- **Scaling signal:**", row["scaling_signal"])
    st.write("- **Efficiency problem:**", row["efficiency_problem_signal"])
    st.write("- **Creative problem:**", row["creative_problem_signal"])
    st.write("- **Landing page:**", row["landing_page_signal"])

st.divider()
st.subheader("All campaigns — final table")
st.dataframe(final, use_container_width=True)
