import plotly.express as px
import streamlit as st

from modules.segmentation import segment_users
from pages.common import get_user_data

st.title("用户分层分析")
segments = segment_users(get_user_data())
counts = segments["segment"].value_counts().rename_axis("用户分层").reset_index(name="用户数")
left, right = st.columns([1, 2])
left.plotly_chart(px.pie(counts, names="用户分层", values="用户数", hole=.5, title="用户分层占比"), use_container_width=True)
right.plotly_chart(px.bar(counts, x="用户分层", y="用户数", color="用户分层", title="各层用户规模"), use_container_width=True)
selected = st.multiselect("筛选分层", counts["用户分层"].tolist(), default=counts["用户分层"].tolist())
st.dataframe(segments[segments["segment"].isin(selected)].sort_values("total_deposit", ascending=False), use_container_width=True, hide_index=True)
