import plotly.express as px
import streamlit as st

from modules.metrics import calculate_metrics, daily_metrics
from modules.segmentation import segment_users
from pages.common import get_data, get_user_data, metric_row, money, pct

st.title("首页仪表盘")
st.caption("核心经营表现与用户结构一屏掌握")
df = get_data()
if df.empty:
    st.warning("当前日期范围内没有数据。")
    st.stop()
metrics, daily = calculate_metrics(df), daily_metrics(df)
metric_row(metrics)
st.subheader("新增与首充指标")
extra_cols = st.columns(6)
extra_items = [
    ("新增用户数", f"{metrics['new_users']:,}"),
    ("新 ARPU", money(metrics["new_arpu"])),
    ("新 ARPPU", money(metrics["new_arppu"])),
    ("老 ARPPU", money(metrics["old_arppu"])),
    ("首充复充率", pct(metrics["first_recharge_rate"])),
    ("首充盈余率", pct(metrics["first_deposit_surplus_rate"])),
]
for col, item in zip(extra_cols, extra_items):
    col.metric(*item)
left, right = st.columns(2)
left.plotly_chart(px.line(daily, x="date", y="deposit", title="每日充值趋势", markers=True), use_container_width=True)
right.plotly_chart(px.line(daily, x="date", y="surplus", title="每日盈余趋势", markers=True), use_container_width=True)
left.plotly_chart(px.line(daily, x="date", y="surplus_rate", title="盈余率趋势", markers=True), use_container_width=True)
right.plotly_chart(px.line(daily, x="date", y="rtp", title="RTP 趋势", markers=True), use_container_width=True)
segments = segment_users(get_user_data())["segment"].value_counts().rename_axis("用户分层").reset_index(name="用户数")
st.plotly_chart(px.pie(segments, names="用户分层", values="用户数", hole=.55, title="用户分层占比"), use_container_width=True)
