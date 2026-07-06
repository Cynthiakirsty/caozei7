"""曹贼运营分析平台入口。"""
from pathlib import Path

import streamlit as st

from modules.data_loader import ensure_sample_files, load_full_excel, load_user_excel

st.set_page_config(page_title="曹贼运营分析平台", page_icon="🎮", layout="wide")
st.markdown(
    """<style>
    .stApp{background:#f5f7fb}.block-container{padding-top:1.6rem;max-width:1500px}
    [data-testid="stSidebar"]{background:linear-gradient(180deg,#111827,#1e293b)}
    [data-testid="stSidebar"] *{color:#f8fafc}
    [data-testid="stMetric"]{background:white;border:1px solid #e5e7eb;padding:16px;
    border-radius:14px;box-shadow:0 3px 12px rgba(15,23,42,.05)}
    </style>""",
    unsafe_allow_html=True,
)

full_path, user_path = ensure_sample_files(Path("data"))
if "full_data" not in st.session_state:
    st.session_state.full_data = load_full_excel(full_path)
    st.session_state.user_data = load_user_excel(user_path)
    st.session_state.full_source_name = "sample_full_data.xlsx（演示）"
    st.session_state.user_source_name = "sample_user_data.xlsx（演示）"

with st.sidebar:
    st.title("🎮 曹贼运营平台")
    st.caption("数据驱动 · 风险预警 · 决策建议")
    st.divider()
    st.caption("当前全盘数据")
    st.success(st.session_state.full_source_name)
    st.caption("当前用户明细")
    st.success(st.session_state.user_source_name)

pages = {
    "数据总览": [
        st.Page("pages/dashboard.py", title="首页仪表盘", icon="📊", default=True),
        st.Page("pages/upload.py", title="Excel 数据上传", icon="📤"),
    ],
    "数据分析": [
        st.Page("pages/deposit_analysis.py", title="充值 / 提现分析", icon="💳"),
        st.Page("pages/bet_analysis.py", title="投注 / RTP / 杀率", icon="🎯"),
        st.Page("pages/retention.py", title="留存分析", icon="🔁"),
        st.Page("pages/activity_cost.py", title="活动成本分析", icon="🎁"),
        st.Page("pages/bonus_multiplier.py", title="彩金成本明细", icon="🪙"),
    ],
    "用户洞察": [
        st.Page("pages/user_segments.py", title="用户分层分析", icon="👥"),
        st.Page("pages/churn_warning.py", title="流失预警", icon="⚠️"),
    ],
    "智能决策": [
        st.Page("pages/ai_advice.py", title="运营建议", icon="📋"),
        st.Page("pages/export_report.py", title="报告导出", icon="📥"),
    ],
}
st.navigation(pages).run()
