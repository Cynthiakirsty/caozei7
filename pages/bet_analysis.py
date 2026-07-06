import plotly.express as px
import streamlit as st

from modules.metrics import calculate_metrics, daily_metrics
from pages.common import get_data, money, pct

st.title("投注 / RTP / 杀率分析")
df = get_data()
if df.empty:
    st.warning("当前日期范围内没有数据。"); st.stop()
metrics, daily = calculate_metrics(df), daily_metrics(df)
cols = st.columns(5)
items = [
    ("总投注", money(metrics["total_bet"])), ("总返奖", money(metrics["total_payout"])),
    ("RTP", pct(metrics["rtp"])), ("杀率", pct(metrics["kill_rate"])),
    ("充投比", f"{metrics['bet_deposit_ratio']:.2f}x"),
]
for col, item in zip(cols, items):
    col.metric(*item)
left, right = st.columns(2)
left.plotly_chart(px.line(daily, x="date", y="rtp", title="RTP 趋势", markers=True), use_container_width=True)
right.plotly_chart(px.line(daily, x="date", y=["bet", "payout"], title="投注与返奖趋势"), use_container_width=True)
st.subheader("每日投注指标")
st.dataframe(daily[["date", "bet", "rtp", "kill_rate", "deposit"]], use_container_width=True, hide_index=True)
