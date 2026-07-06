import plotly.express as px
import streamlit as st

from modules.churn import score_churn
from pages.common import get_user_data

st.title("流失预警")
risk = score_churn(get_user_data())
for col, label in zip(st.columns(3), ["高风险", "中风险", "低风险"]):
    col.metric(label, f"{(risk['risk_level'].astype(str) == label).sum():,} 人")
st.plotly_chart(px.histogram(risk, x="churn_score", color="risk_level", nbins=20, title="用户流失风险分布"), use_container_width=True)
st.subheader("流失风险用户列表")
display = risk[risk["risk_level"].astype(str).isin(["高风险", "中风险"])]
st.dataframe(display[["user_id", "vip_level", "channel", "churn_score", "risk_level",
                      "days_since_login", "total_deposit", "total_bet", "balance"]],
             use_container_width=True, hide_index=True)
