from io import BytesIO
import os
import pandas as pd
import streamlit as st

from modules.data_loader import (
    FULL_COLUMNS_CN, USER_COLUMNS_CN, save_to_sqlite,
    validate_full_data, validate_user_data,
)


def blank_template(columns):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(columns=columns).to_excel(writer, index=False, sheet_name="数据")
    return buffer.getvalue()


st.title("双表数据上传")
st.caption("全盘数据驱动数据分析；用户明细驱动用户分层与流失预警。两张表需同时上传并通过校验。")
if st.session_state.full_data.empty and st.session_state.user_data.empty:
    st.info("当前平台没有载入任何业务数据。上传并校验成功前，其他页面不会展示演示数据或分析结果。")
left, right = st.columns(2)
with left:
    st.subheader("① 全盘数据表")
    full_file = st.file_uploader("上传全盘日报 Excel", type=["xlsx"], key="full_upload")
    st.download_button("下载全盘数据模板", blank_template(FULL_COLUMNS_CN), "全盘数据模板.xlsx")
with right:
    st.subheader("② 用户明细表")
    user_file = st.file_uploader("上传用户 UID 明细 Excel", type=["xlsx"], key="user_upload")
    st.download_button("下载用户明细模板", blank_template(USER_COLUMNS_CN), "用户明细模板.xlsx")

if full_file and user_file:
    try:
        full_df, full_warnings = validate_full_data(pd.read_excel(full_file, engine="openpyxl"))
        user_df, user_warnings = validate_user_data(pd.read_excel(user_file, engine="openpyxl"))
        st.session_state.full_data = full_df
        st.session_state.user_data = user_df
        st.session_state.full_source_name = full_file.name
        st.session_state.user_source_name = user_file.name
        # 公共云部署默认只保存在当前访客会话中，避免不同访客共用磁盘数据。
        if os.getenv("PERSIST_UPLOADS", "false").lower() == "true":
            save_to_sqlite(full_df, user_df)
        st.success(f"上传成功：全盘 {len(full_df):,} 天，用户明细 {len(user_df):,} 人")
        for warning in full_warnings+user_warnings:
            st.warning(warning)
        tab1, tab2 = st.tabs(["全盘预览", "用户明细预览"])
        tab1.dataframe(full_df.head(100), use_container_width=True, hide_index=True)
        tab2.dataframe(user_df.head(100), use_container_width=True, hide_index=True)
    except Exception as exc:
        st.error(f"上传失败：{exc}")
elif full_file or user_file:
    st.info("请继续上传另一张表，系统会在两张表都就绪后统一校验。")

with st.expander("查看全盘数据字段"):
    st.write("、".join(FULL_COLUMNS_CN))
with st.expander("查看用户明细字段"):
    st.write("、".join(USER_COLUMNS_CN))
