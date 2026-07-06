"""规则兜底与 OpenAI Responses API 运营建议引擎。"""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from modules.churn import score_churn
from modules.metrics import calculate_metrics
from modules.segmentation import segment_users


def generate_advice(df) -> list[dict]:
    m, advice = calculate_metrics(df), []
    def add(level, title, detail):
        advice.append({"level": level, "title": title, "detail": detail})
    if m["surplus_rate"] < .15:
        add("高", "盈余率偏低", "检查彩金成本、整体 RTP 与异常提现用户，并按渠道拆解盈余。")
    if m["activity_cost_ratio"] > .12:
        add("高", "活动成本占比过高", "降低奖励比例、提高有效流水倍数，优先收紧低净值人群优惠。")
    if m["retention_d7"] < .25:
        add("中", "7日留存偏低", "增加次日复充、连续签到和 VIP 召回活动，对新客前 7 日分层触达。")
    if m["rtp"] > .96:
        add("高", "RTP 偏高", "检查游戏配置、渠道及高返奖用户，确认短期波动或异常套利。")
    if m["bet_deposit_ratio"] < 3:
        add("中", "充投比偏低", "优化充值后的投注引导、首局任务和产品路径，减少充值后未投注用户。")
    if (df["bonus_ratio"] > .12).mean() > .25:
        add("中", "高彩金成本日期较多", "超过四分之一日期的彩金占比高于 12%，建议拆分渠道和活动明细进一步定位。")
    if not advice:
        add("低", "核心指标整体健康", "当前未触发高风险规则，继续按渠道、活动和用户层级监控趋势。")
    return advice


def build_analysis_context(full_df, user_df) -> dict:
    """仅构建匿名聚合上下文，绝不包含 UID 或逐用户记录。"""
    metrics = calculate_metrics(full_df)
    ordered = full_df.sort_values("date")
    recent, previous = ordered.tail(14), ordered.iloc[-28:-14]
    segments = segment_users(user_df)["segment"].value_counts().to_dict()
    risks = score_churn(user_df)["risk_level"].astype(str).value_counts().to_dict()

    def period_summary(data):
        if data.empty:
            return {}
        values = calculate_metrics(data)
        keys = [
            "total_deposit", "total_withdraw", "surplus", "surplus_rate",
            "rtp", "kill_rate", "activity_cost_ratio", "new_users",
            "new_arpu", "new_arppu", "old_arppu", "first_recharge_rate",
            "retention_d1", "retention_d7", "retention_d15", "retention_d30",
        ]
        return {key: round(float(values[key]), 4) for key in keys}

    safe_metric_keys = [
        "total_deposit", "total_withdraw", "surplus", "surplus_rate",
        "total_bet", "rtp", "kill_rate", "activity_cost",
        "activity_cost_ratio", "arppu", "new_arpu", "new_arppu",
        "first_recharge_rate", "old_arppu", "first_deposit_surplus_rate",
        "new_users", "retention_d1", "retention_d3", "retention_d7",
        "retention_d15", "retention_d30",
    ]
    return {
        "analysis_period": {
            "start": str(ordered["date"].min().date()),
            "end": str(ordered["date"].max().date()),
            "days": len(ordered),
        },
        "overall_metrics": {key: round(float(metrics[key]), 4) for key in safe_metric_keys},
        "recent_14_days": period_summary(recent),
        "previous_14_days": period_summary(previous),
        "user_segment_counts": segments,
        "churn_risk_counts": risks,
        "vip_level_counts": user_df["vip_level"].value_counts().head(10).to_dict(),
        "channel_user_counts": user_df["channel"].value_counts().head(10).to_dict(),
    }


def _advice_instructions() -> str:
    return """
你是一名资深游戏平台数据策略与风险治理顾问。根据匿名聚合数据生成中文运营决策报告。
只能引用输入中存在的数字，不能编造活动、渠道表现、用户动机或因果关系。
明确区分“数据事实”“合理推测”“待验证假设”。百分比保留一位小数，金额使用千分位。

报告必须包含：
1. 执行摘要：3至5条关键结论，分别标明高、中、低优先级；
2. 指标诊断：充值提现、盈余、RTP/杀率、彩金成本、新老用户、首充复充和留存；
3. 趋势对比：最近14天与此前14天，计算变化幅度并解释经营影响；
4. 用户策略：根据用户分层、VIP分布、渠道人数和流失风险制定差异化动作；
5. 行动清单：每项包含负责人角色、具体动作、目标指标、建议目标区间、观察周期和停止条件；
6. 风险与验证：数据局限、需要补充的数据、A/B测试方案及判定标准；
7. 未来7天与30天行动计划。

必须遵守负责任运营原则：不得诱导高风险或疑似成瘾用户增加投注；对高风险人群优先建议
风险识别、限额、自我排除提醒和客服关怀。不得把相关性写成因果。输出清晰 Markdown。
"""


def _advice_prompt(full_df, user_df, focus: str) -> str:
    context = build_analysis_context(full_df, user_df)
    return (
        f"本次分析重点：{focus}\n\n"
        "以下内容全部是匿名聚合数据，不含UID或逐用户记录：\n"
        f"{json.dumps(context, ensure_ascii=False, indent=2)}"
    )


def generate_llm_advice(full_df, user_df, api_key: str,
                        model: str = "gpt-5.4-mini",
                        focus: str = "综合经营优化") -> str:
    """调用真实模型生成结构化运营决策报告。"""
    if not api_key or not api_key.strip():
        raise ValueError("请先输入 OpenAI API Key。")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("尚未安装 openai，请运行：python -m pip install -r requirements.txt") from exc

    client = OpenAI(api_key=api_key.strip())
    response = client.responses.create(
        model=model,
        instructions=_advice_instructions(),
        input=_advice_prompt(full_df, user_df, focus),
    )
    if not response.output_text:
        raise RuntimeError("模型没有返回文本，请稍后重试。")
    return response.output_text


def generate_groq_advice(full_df, user_df, api_key: str,
                         model: str = "qwen/qwen3-32b",
                         focus: str = "综合经营优化") -> str:
    """通过 Groq 的 OpenAI 兼容接口生成匿名聚合数据分析。"""
    if not api_key or not api_key.strip():
        raise ValueError("请先输入 Groq API Key。")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("尚未安装 openai，请运行：python -m pip install -r requirements.txt") from exc
    client = OpenAI(
        api_key=api_key.strip(),
        base_url="https://api.groq.com/openai/v1",
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _advice_instructions()},
            {"role": "user", "content": _advice_prompt(full_df, user_df, focus)},
        ],
        temperature=0.2,
        max_tokens=6000,
    )
    content = response.choices[0].message.content if response.choices else ""
    if not content:
        raise RuntimeError("Groq 没有返回文本内容，请稍后重试。")
    return content


def generate_huggingface_advice(
    full_df, user_df, api_key: str,
    model: str = "deepseek-ai/DeepSeek-V4-Flash:novita",
    focus: str = "综合经营优化",
) -> str:
    """通过 Hugging Face Router 调用指定推理提供商。"""
    if not api_key or not api_key.strip():
        raise ValueError("请先输入 Hugging Face Token。")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("尚未安装 openai，请运行：python -m pip install -r requirements.txt") from exc
    client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=api_key.strip(),
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _advice_instructions()},
            {"role": "user", "content": _advice_prompt(full_df, user_df, focus)},
        ],
        temperature=0.2,
        max_tokens=6000,
    )
    content = response.choices[0].message.content if response.choices else ""
    if not content:
        raise RuntimeError("Hugging Face Router 没有返回文本内容。")
    return content


def list_ollama_models(base_url: str = "http://localhost:11434") -> list[str]:
    """读取本地 Ollama 已安装模型。"""
    try:
        with urlopen(f"{base_url.rstrip('/')}/api/tags", timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return [item.get("name") or item.get("model") for item in payload.get("models", [])]
    except (URLError, TimeoutError, OSError, json.JSONDecodeError):
        return []


def generate_ollama_advice(full_df, user_df, model: str = "qwen3:8b",
                           focus: str = "综合经营优化",
                           base_url: str = "http://localhost:11434") -> str:
    """通过本机 Ollama Chat API 免费生成建议，数据不离开电脑。"""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _advice_instructions()},
            {"role": "user", "content": _advice_prompt(full_df, user_df, focus)},
        ],
        "stream": False,
        "options": {"temperature": 0.2, "num_ctx": 16384},
    }
    request = Request(
        f"{base_url.rstrip('/')}/api/chat",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=600) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code == 404:
            raise RuntimeError(f"未找到模型 {model}，请先运行：ollama pull {model}") from exc
        raise RuntimeError(f"Ollama 返回 HTTP {exc.code}：{body}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(
            "无法连接本机 Ollama。请先安装并启动 Ollama，然后运行："
            f"ollama pull {model}"
        ) from exc
    content = result.get("message", {}).get("content", "").strip()
    if not content:
        raise RuntimeError("Ollama 没有返回文本内容。")
    return content


def friendly_api_error(exc: Exception) -> tuple[str, str]:
    """将常见 OpenAI API 异常转换为运营人员可理解的提示。"""
    text = str(exc).lower()
    if "insufficient_quota" in text or "exceeded your current quota" in text:
        return (
            "OpenAI API 额度不足",
            "当前 API 账户没有可用额度，或组织/项目月度预算已达到上限。"
            "请检查 API 用量与 Billing，充值或提高项目预算后再试。重复点击不会恢复额度。",
        )
    if "rate_limit" in text or "rate limit" in text or "too many requests" in text:
        return (
            "API 请求过于频繁",
            "当前触发了免费额度或速率限制，请根据响应时间稍后重试；免费平台也可能达到每日上限。",
        )
    if "authentication" in text or "incorrect api key" in text or "401" in text:
        return (
            "API Key 无效",
            "请检查 Key 是否完整、是否已被删除，以及它是否属于当前有额度的 OpenAI API 项目。",
        )
    if "connection" in text or "timeout" in text:
        return ("网络连接失败", "无法连接 OpenAI API，请检查网络、代理或防火墙设置后重试。")
    return ("AI 调用失败", str(exc))
