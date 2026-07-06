"""基础决策报告（默认）与可选大模型增强。"""
import os

import streamlit as st

from modules.ai_advisor import (
    friendly_api_error, generate_groq_advice, generate_huggingface_advice,
    generate_llm_advice, generate_ollama_advice, list_ollama_models,
)
from modules.basic_analysis import HEALTH_STANDARDS, generate_detailed_analysis
from modules.html_report import build_html_report
from modules.metrics import calculate_metrics
from pages.common import get_data, get_user_data, metric_row


def saved_secret(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or os.getenv(name, ""))


def render_analysis_item(item: dict) -> None:
    colors = {"高风险": "🔴", "需关注": "🟠", "健康": "🟢"}
    with st.container(border=True):
        title_col, status_col = st.columns([5, 1])
        title_col.subheader(f"{item['priority']} · {item['category']} · {item['title']}")
        status_col.metric("状态", f"{colors[item['status']]} {item['status']}")
        st.markdown("**数据证据**")
        st.write(item["evidence"])
        left, right = st.columns(2)
        with left:
            st.markdown("**判断说明**")
            st.write(item["interpretation"])
        with right:
            st.markdown("**可能影响**")
            st.write(item["impact"])
        st.markdown("**建议动作**")
        for index, action in enumerate(item["actions"], 1):
            st.write(f"{index}. {action}")
        target_col, cycle_col = st.columns(2)
        with target_col:
            st.markdown("**目标与判定标准**")
            st.write(item["target"])
        with cycle_col:
            st.markdown("**观察与停止条件**")
            st.write(f"{item['observation']}；{item['stop_condition']}。")


st.title("运营建议")
st.caption("默认使用本地确定性分析，无需 Token、无需大模型、数据不离开电脑")
full_df, user_df = get_data(), get_user_data()
metric_row(calculate_metrics(full_df))

basic_tab, model_tab = st.tabs(["📋 基础详细分析（默认）", "✨ 大模型增强（可选）"])

with basic_tab:
    report = generate_detailed_analysis(full_df, user_df)
    st.info(f"分析区间：{report['period']}。所有判断均由可解释规则和上传数据计算产生。")
    with st.expander("查看当前健康标准", expanded=False):
        st.dataframe(
            [{"指标": name, "健康值": value} for name, value in HEALTH_STANDARDS],
            use_container_width=True, hide_index=True,
        )

    p0, p1, p2, risk = st.columns(4)
    p0.metric("P0 立即处理", report["summary"]["P0"])
    p1.metric("P1 本周处理", report["summary"]["P1"])
    p2.metric("P2 持续观察", report["summary"]["P2"])
    risk.metric("高流失风险用户", f"{report['headline']['high_risk_users']:,}")

    st.subheader("最近14天经营变化")
    trend_cols = st.columns(3)
    trend_cols[0].metric("充值变化", f"{report['headline']['deposit_change']:+.1%}")
    trend_cols[1].metric("盈余变化", f"{report['headline']['surplus_change']:+.1%}")
    trend_cols[2].metric("新增用户变化", f"{report['headline']['new_user_change']:+.1%}")

    priority_filter = st.multiselect(
        "筛选优先级", ["P0", "P1", "P2"], default=["P0", "P1", "P2"],
    )
    for analysis_item in report["items"]:
        if analysis_item["priority"] in priority_filter:
            render_analysis_item(analysis_item)

    st.download_button(
        "下载基础分析可视化报告（HTML）",
        build_html_report(full_df, user_df),
        "基础运营决策可视化报告.html", "text/html",
        use_container_width=True,
    )

with model_tab:
    st.warning("此功能不是基础分析的必需项。只有点击生成时才会调用所选模型。")
    provider = st.selectbox(
        "AI 提供方",
        [
            "Hugging Face Router（Novita）",
            "Groq API（免费）",
            "本地 Ollama（免费）",
            "OpenAI API（付费）",
        ],
    )
    api_key, base_url = "", ""
    if provider.startswith("Hugging"):
        api_key = st.text_input(
            "Hugging Face Token", value=saved_secret("HF_TOKEN"), type="password",
        )
        model = st.text_input("模型", "deepseek-ai/DeepSeek-V4-Flash:novita")
    elif provider.startswith("Groq"):
        api_key = st.text_input(
            "Groq API Key", value=saved_secret("GROQ_API_KEY"), type="password",
        )
        model = st.selectbox(
            "模型", ["qwen/qwen3-32b", "llama-3.3-70b-versatile", "openai/gpt-oss-120b"],
        )
    elif provider.startswith("本地"):
        base_url = st.text_input("Ollama 地址", "http://localhost:11434")
        installed = list_ollama_models(base_url)
        model = st.selectbox("本地模型", installed) if installed else st.text_input("模型", "qwen3:8b")
        if not installed:
            st.info(f"未检测到 Ollama。安装后运行：ollama pull {model}")
    else:
        api_key = st.text_input(
            "OpenAI API Key", value=saved_secret("OPENAI_API_KEY"), type="password",
        )
        model = st.selectbox("模型", ["gpt-5.4-mini", "gpt-5.5"])

    focus = st.selectbox(
        "分析重点",
        ["综合经营优化", "盈余与成本控制", "新客首充与复充", "留存与流失治理", "RTP与风险控制"],
    )
    if st.button("生成大模型增强报告", type="primary", use_container_width=True):
        try:
            with st.spinner("模型正在分析匿名聚合数据…"):
                if provider.startswith("Hugging"):
                    result = generate_huggingface_advice(full_df, user_df, api_key, model, focus)
                elif provider.startswith("Groq"):
                    result = generate_groq_advice(full_df, user_df, api_key, model, focus)
                elif provider.startswith("本地"):
                    result = generate_ollama_advice(full_df, user_df, model, focus, base_url)
                else:
                    result = generate_llm_advice(full_df, user_df, api_key, model, focus)
            st.session_state["llm_advice"] = result
            st.session_state["llm_model"] = f"{provider} / {model}"
        except Exception as exc:
            title, detail = friendly_api_error(exc)
            st.error(f"{title}：{detail}")

    if st.session_state.get("llm_advice"):
        st.success(f"已由 {st.session_state.get('llm_model')} 生成")
        st.markdown(st.session_state["llm_advice"])
        st.download_button(
            "下载大模型报告",
            st.session_state["llm_advice"].encode("utf-8"),
            "大模型运营报告.md", "text/markdown",
        )
