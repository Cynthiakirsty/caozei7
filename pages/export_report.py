import streamlit as st

from modules.report import build_excel_report
from modules.html_report import build_html_report
from pages.common import get_data, get_user_data

st.title("报告导出")
st.caption("导出指标摘要、每日趋势、活动分析、用户分层、流失预警和 AI 建议")
df = get_data()
user_df = get_user_data()
if df.empty:
    st.warning("当前日期范围内没有数据。"); st.stop()
st.info(f"报告范围：{df['date'].min():%Y-%m-%d} 至 {df['date'].max():%Y-%m-%d}，共 {len(df):,} 条记录")
st.download_button(
    "下载 HTML 可视化报告",
    build_html_report(df, user_df),
    "基础运营决策可视化报告.html",
    "text/html",
    type="primary",
    use_container_width=True,
)
if st.button("生成数据分析报告", type="primary", use_container_width=True):
    with st.spinner("正在生成报告…"):
        report = build_excel_report(df, user_df)
    st.download_button(
        "下载 Excel 报告", report, "AI游戏运营分析报告.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
