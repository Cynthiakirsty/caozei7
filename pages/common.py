"""页面共享筛选器与展示函数。"""
import streamlit as st


def get_data():
    df = st.session_state.full_data
    if df.empty:
        st.info("当前没有全盘数据。请先前往“Excel 数据上传”页面上传两张数据表。")
        st.stop()
    with st.sidebar:
        st.divider()
        st.caption("分析日期范围")
        start, end = df["date"].min().date(), df["date"].max().date()
        selected = st.date_input(
            "日期", value=(start, end), min_value=start, max_value=end,
            label_visibility="collapsed",
        )
    if isinstance(selected, (tuple, list)) and len(selected) == 2:
        return df[df["date"].between(str(selected[0]), str(selected[1]))].copy()
    return df.copy()


def get_user_data():
    df = st.session_state.user_data
    if df.empty:
        st.info("当前没有用户明细数据。请先前往“Excel 数据上传”页面上传两张数据表。")
        st.stop()
    return df.copy()


def money(value): return f"₹{value:,.0f}"
def pct(value): return f"{value:.1%}"


def metric_row(metrics):
    cols = st.columns(6)
    values = [
        ("总充值", money(metrics["total_deposit"])),
        ("总提现", money(metrics["total_withdraw"])),
        ("盈余", money(metrics["surplus"])),
        ("盈余率", pct(metrics["surplus_rate"])),
        ("RTP", pct(metrics["rtp"])),
        ("ARPPU", money(metrics["arppu"])),
    ]
    for col, (label, value) in zip(cols, values):
        col.metric(label, value)
