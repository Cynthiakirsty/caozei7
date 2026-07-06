import plotly.express as px
import streamlit as st

from modules.metrics import calculate_metrics
from pages.common import get_data, money, pct

st.title("活动成本分析")
st.caption("当前全盘表以彩金金额代表活动成本。")
df = get_data()
metrics = calculate_metrics(df)
left, right = st.columns(2)
left.metric("彩金 / 活动成本", money(metrics["activity_cost"]))
right.metric("彩金占比", pct(metrics["activity_cost_ratio"]))
left.plotly_chart(px.bar(df, x="date", y="bonus", title="每日彩金成本"), use_container_width=True)
right.plotly_chart(px.line(df, x="date", y="bonus_ratio", markers=True, title="彩金占比趋势"), use_container_width=True)
st.dataframe(df[["date", "deposit", "bonus", "bonus_ratio", "surplus_rate"]],
             use_container_width=True, hide_index=True)
