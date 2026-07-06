import plotly.express as px
import streamlit as st

from modules.metrics import calculate_metrics, daily_metrics
from pages.common import get_data, money, pct

st.title("充值 / 提现分析")
df = get_data()
if df.empty:
    st.warning("当前日期范围内没有数据。"); st.stop()
metrics, daily = calculate_metrics(df), daily_metrics(df)
cols = st.columns(4)
for col, item in zip(cols, [
    ("总充值", money(metrics["total_deposit"])), ("总提现", money(metrics["total_withdraw"])),
    ("盈余", money(metrics["surplus"])), ("盈余率", pct(metrics["surplus_rate"])),
]):
    col.metric(*item)
st.plotly_chart(
    px.line(daily, x="date", y=["deposit", "withdraw", "surplus"], title="充值、提现与盈余趋势"),
    use_container_width=True,
)
st.subheader("每日资金明细")
st.dataframe(
    daily[["date", "deposit", "withdraw", "surplus", "surplus_rate", "paying_users"]],
    use_container_width=True, hide_index=True,
)
