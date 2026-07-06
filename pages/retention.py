import pandas as pd
import plotly.express as px
import streamlit as st

from modules.metrics import calculate_metrics
from pages.common import get_data, pct

st.title("留存分析")
df = get_data()
if df.empty:
    st.warning("当前日期范围内没有数据。"); st.stop()
metrics = calculate_metrics(df)
days = [1, 3, 7, 15, 30]
values = [metrics[f"retention_d{x}"] for x in days]
for col, day, value in zip(st.columns(5), days, values):
    col.metric("次日留存" if day == 1 else f"{day}日留存", pct(value))
curve = pd.DataFrame({"留存周期":[f"D{x}" for x in days], "留存率":values})
st.plotly_chart(px.line(curve, x="留存周期", y="留存率", markers=True, title="整体留存曲线"), use_container_width=True)
columns = [f"retention_d{x}" for x in days]
st.plotly_chart(px.line(df, x="date", y=columns, title="每日新增用户留存趋势"), use_container_width=True)
