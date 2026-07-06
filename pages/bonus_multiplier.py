import plotly.express as px
import streamlit as st

from pages.common import get_data, money, pct

st.title("彩金成本分析")
st.caption("全盘日报未提供活动名称与流水倍数，本页展示每日彩金金额及彩金占比。")
df = get_data()
cols = st.columns(3)
cols[0].metric("彩金总额", money(df["bonus"].sum()))
cols[1].metric("平均彩金占比", pct(df["bonus_ratio"].mean()))
cols[2].metric("高成本天数", f"{(df['bonus_ratio'] > .12).sum():,}")
left, right = st.columns(2)
left.plotly_chart(px.bar(df, x="date", y="bonus", title="每日彩金金额"), use_container_width=True)
right.plotly_chart(px.line(df, x="date", y="bonus_ratio", markers=True, title="每日彩金占比"), use_container_width=True)
st.dataframe(df[["date", "deposit", "bonus", "bonus_ratio"]].sort_values("bonus_ratio", ascending=False),
             use_container_width=True, hide_index=True)
