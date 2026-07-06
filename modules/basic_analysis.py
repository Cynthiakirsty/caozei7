"""无需大模型的详细运营决策引擎。"""
from __future__ import annotations

import pandas as pd

from modules.churn import score_churn
from modules.metrics import calculate_metrics
from modules.segmentation import segment_users

HEALTH_STANDARDS = [
    ("盈余率", "20%–22%"),
    ("首充盈余率", "≥55%"),
    ("首充复充率", "≥20%"),
    ("D1留存", "≥60%"),
    ("D30留存", "≥8%"),
    ("RTP", "≤96.5%"),
    ("彩金/充值", "≤12%"),
    ("彩金发放/游戏收入", "≤40%"),
    ("充投比", "900%–1200%（9–12倍）"),
]


def _change(current: float, previous: float) -> float:
    return 0.0 if previous == 0 else (current - previous) / abs(previous)


def _money(value: float) -> str:
    return f"₹{value:,.0f}"


def _pct(value: float) -> str:
    return f"{value:.1%}"


def _status(value: float, warning: float, danger: float, higher_is_worse: bool = True) -> str:
    if higher_is_worse:
        return "高风险" if value >= danger else "需关注" if value >= warning else "健康"
    return "高风险" if value <= danger else "需关注" if value <= warning else "健康"


def _band_status(value: float, lower: float, upper: float, tolerance: float = .1) -> str:
    if lower <= value <= upper:
        return "健康"
    if lower*(1-tolerance) <= value <= upper*(1+tolerance):
        return "需关注"
    return "高风险"


def _item(category, title, status, priority, evidence, interpretation, impact,
          actions, target, observation="7天复盘，14天确认趋势", stop_condition="指标连续恶化3天时暂停方案并复核"):
    return {
        "category": category,
        "title": title,
        "status": status,
        "priority": priority,
        "evidence": evidence,
        "interpretation": interpretation,
        "impact": impact,
        "actions": actions,
        "target": target,
        "observation": observation,
        "stop_condition": stop_condition,
    }


def generate_detailed_analysis(full_df: pd.DataFrame, user_df: pd.DataFrame) -> dict:
    """生成证据、判断、影响、动作、目标和观察周期完整的基础报告。"""
    ordered = full_df.sort_values("date")
    metrics = calculate_metrics(ordered)
    recent_df = ordered.tail(14)
    previous_df = ordered.iloc[-28:-14]
    recent = calculate_metrics(recent_df)
    previous = calculate_metrics(previous_df) if not previous_df.empty else recent
    segments = segment_users(user_df)
    churn = score_churn(user_df)

    high_risk = int((churn["risk_level"].astype(str) == "高风险").sum())
    medium_risk = int((churn["risk_level"].astype(str) == "中风险").sum())
    total_profiles = max(len(user_df), 1)
    high_value = int((segments["segment"] == "高价值用户").sum())
    wool = int((segments["segment"] == "羊毛用户").sum())

    deposit_change = _change(recent["total_deposit"], previous["total_deposit"])
    surplus_change = _change(recent["surplus"], previous["surplus"])
    new_user_change = _change(recent["new_users"], previous["new_users"])
    items = []

    surplus_status = _band_status(metrics["surplus_rate"], .20, .22, .15)
    if metrics["surplus_rate"] < .20:
        surplus_actions = [
            "财务运营按日期找出提现率最高的5天，并与RTP、彩金占比交叉核对。",
            "分别计算新客和老客盈余，确认拖累来自首充成本、老客提现还是游戏收入。",
            "先处理异常成本与提现结构，盈余率恢复到20%后再扩大投放。",
        ]
        surplus_interpretation = "当前盈余率低于20%健康下限，说明充值转化为可留存收入的效率不足。"
    elif metrics["surplus_rate"] > .22:
        surplus_actions = [
            "核对高盈余是否来自提现延迟、RTP下降或统计周期错配。",
            "检查用户投诉、提现处理时长和留存是否同步恶化。",
            "若体验指标稳定，可维持策略；不要为了继续抬高盈余而压低正常返奖。",
        ]
        surplus_interpretation = "当前盈余率高于22%标准上限，财务表现较强，但需要排除体验或提现时点造成的短期虚高。"
    else:
        surplus_actions = [
            "维持当前资金策略，并按周监控盈余率是否仍在20%–22%。",
            "复盘贡献最稳定的日期和渠道，将其作为后续投放基线。",
            "保留异常日预警，单日偏离区间超过5个百分点时人工复核。",
        ]
        surplus_interpretation = "当前盈余率位于20%–22%健康区间，重点应从纠偏转向稳定性管理。"
    items.append(_item(
        "资金健康", "盈余与提现结构", surplus_status,
        "P0" if surplus_status == "高风险" else "P1" if surplus_status == "需关注" else "P2",
        f"总充值 {_money(metrics['total_deposit'])}，总提现 {_money(metrics['total_withdraw'])}，"
        f"盈余 {_money(metrics['surplus'])}，盈余率 {_pct(metrics['surplus_rate'])}；"
        f"最近14天盈余较此前14天变化 {_pct(surplus_change)}。",
        surplus_interpretation,
        "盈余持续偏低会压缩活动预算和渠道投放空间，并放大短期资金波动。",
        surplus_actions,
        "整体盈余率保持在20%–22%。",
    ))

    rtp_status = _status(metrics["rtp"], .95, .965)
    ratio_status = _band_status(metrics["bet_deposit_ratio"], 9, 12, .15)
    if "高风险" in (rtp_status, ratio_status):
        rtp_status = "高风险"
    elif "需关注" in (rtp_status, ratio_status):
        rtp_status = "需关注"
    if metrics["rtp"] > .965:
        rtp_actions = [
            "定位最近14天RTP超过96.5%的日期，并核对其投注量是否足以排除小样本波动。",
            "补充游戏品类和渠道维度，确认是局部高返奖还是全盘配置问题。",
            "连续3天超标才进入配置复核，避免因单日波动频繁调整。",
        ]
    elif ratio_status != "健康":
        direction = "偏低" if metrics["bet_deposit_ratio"] < 9 else "偏高"
        rtp_actions = [
            f"当前充投比{direction}，先核对充值后投注链路、重复投注及统计口径。",
            "按新老用户拆分充投比，判断问题来自新客未转化还是老客高频循环投注。",
            "将充投比调整目标设为9–12倍，同时观察RTP和负责任运营风险。",
        ]
    else:
        rtp_actions = [
            "RTP和充投比处于标准范围，维持配置并继续监测异常日。",
            "将当前游戏及用户结构作为基准，不做无数据支持的参数调整。",
            "每周复核RTP、充投比、盈余率是否仍保持联动稳定。",
        ]
    items.append(_item(
        "游戏表现", "RTP与杀率", rtp_status,
        "P0" if rtp_status == "高风险" else "P1",
        f"加权RTP为 {_pct(metrics['rtp'])}，杀率为 {_pct(metrics['kill_rate'])}，"
        f"充投比为 {metrics['bet_deposit_ratio']:.2f} 倍（健康值9–12倍）。",
        "RTP应结合投注规模观察。单日RTP高可能是波动，连续多日高位才需要检查游戏、渠道或玩家结构。",
        "RTP持续偏高会侵蚀盈余；过低则可能影响体验与留存，因此不应只追求短期杀率。",
        rtp_actions,
        "RTP不高于96.5%，充投比保持900%–1200%（9–12倍）。",
    ))

    bonus_status = (
        "高风险" if metrics["activity_cost_ratio"] > .12 or metrics["bonus_game_income_ratio"] > .40
        else "需关注" if metrics["activity_cost_ratio"] > .10 or metrics["bonus_game_income_ratio"] > .32
        else "健康"
    )
    high_bonus_days = int((ordered["bonus_ratio"] >= .12).sum())
    items.append(_item(
        "成本控制", "彩金成本效率", bonus_status,
        "P0" if bonus_status == "高风险" else "P1",
        f"彩金总额 {_money(metrics['activity_cost'])}，彩金占充值 {_pct(metrics['activity_cost_ratio'])}，"
        f"彩金发放占游戏收入 {_pct(metrics['bonus_game_income_ratio'])}；"
        f"彩金占比达到或超过12%的日期共 {high_bonus_days} 天。",
        "彩金占比反映直接奖励成本，但当前数据没有活动名称和活动用户明细，无法直接判断单个活动ROI。",
        "高成本若未带来复充或留存改善，会直接降低盈余；过度削减也可能损害有效活动。",
        (
            [
                "列出彩金/充值超过12%或彩金/游戏收入超过40%的日期并优先复核。",
                "比较这些日期的首充复充率、D1和D30留存，确认彩金是否带来真实增量。",
                "未带来增量的奖励先降低覆盖或额度；有效活动保持并设置成本上限。",
            ] if bonus_status != "健康" else [
                "彩金两项成本指标均在健康线内，维持预算并观察留存产出。",
                "识别低成本高留存日期，沉淀为后续活动设计基线。",
                "新增活动上线前设置彩金/充值12%和彩金/游戏收入40%的硬性预警。",
            ]
        ),
        "彩金/充值≤12%，彩金发放/游戏收入≤40%。",
    ))

    retention_status = (
        "高风险" if metrics["retention_d1"] < .48 or metrics["retention_d30"] < .064
        else "需关注" if metrics["retention_d1"] < .60 or metrics["retention_d30"] < .08
        else "健康"
    )
    if retention_status == "健康":
        retention_actions = [
            "D1和D30均达到标准，维持当前新手路径和用户服务节奏。",
            "按渠道寻找持续高于全盘留存的来源，作为新增投放质量基线。",
            "关注D3至D15的衰减拐点，避免只看首尾指标忽略中期流失。",
        ]
    elif metrics["retention_d1"] < .60 and metrics["retention_d30"] >= .08:
        retention_actions = [
            "D1未达60%但D30达标，重点优化注册后24小时的新手路径和首次回访。",
            "按渠道比较注册到次日登录漏斗，优先修复流量大且D1低的渠道。",
            "不扩大长期召回预算，先解决首日体验问题并观察7天。",
        ]
    elif metrics["retention_d1"] >= .60 and metrics["retention_d30"] < .08:
        retention_actions = [
            "D1达标但D30不足8%，说明首日承接尚可、长期价值维系不足。",
            "分析D7至D30的流失时间段，优化内容节奏、服务权益和风险关怀。",
            "以30日活跃而非短期复充作为实验主指标，观察至少一个完整周期。",
        ]
    else:
        retention_actions = [
            "D1和D30均未达标，先暂停扩大低质量渠道投放。",
            "拆解注册、首充、D1、D7、D30漏斗，优先修复损失最大的一段。",
            "分别测试新手引导和长期服务，避免用单一奖励同时解决所有留存问题。",
        ]
    items.append(_item(
        "用户质量", "新增与留存质量", retention_status,
        "P0" if retention_status == "高风险" else "P1",
        f"新增用户 {metrics['new_users']:,}，新增ARPU {_money(metrics['new_arpu'])}，"
        f"次日/7日/15日/30日留存分别为 {_pct(metrics['retention_d1'])}/"
        f"{_pct(metrics['retention_d7'])}/{_pct(metrics['retention_d15'])}/"
        f"{_pct(metrics['retention_d30'])}；最近14天新增变化 {_pct(new_user_change)}。",
        "新增规模与留存应同时判断。新增增长但7日留存下降，通常意味着流量质量或新手路径需要复核。",
        "低留存会使获客投入难以沉淀为活跃和付费用户，后续ARPU也容易失真。",
        retention_actions,
        "D1留存≥60%，D30留存≥8%；D3、D7和D15用于观察衰减路径。",
    ))

    first_surplus_ok = metrics["first_deposit_surplus_rate"] >= .55
    recharge_ok = metrics["first_recharge_rate"] >= .20
    recharge_status = "健康" if first_surplus_ok and recharge_ok else (
        "高风险" if metrics["first_deposit_surplus_rate"] < .44 or metrics["first_recharge_rate"] < .16
        else "需关注"
    )
    items.append(_item(
        "付费转化", "首充与复充质量", recharge_status,
        "P1" if recharge_status != "健康" else "P2",
        f"首充复充率 {_pct(metrics['first_recharge_rate'])}，首充盈余率 "
        f"{_pct(metrics['first_deposit_surplus_rate'])}，新增ARPPU {_money(metrics['new_arppu'])}。",
        "复充率需要与首充盈余率共同评估。复充高但盈余低，可能是奖励成本或提现结构问题。",
        "首充后未形成健康活跃会造成获客成本浪费；激进刺激复充则可能带来合规和用户风险。",
        (
            [
                "若首充盈余率低于55%，先检查首充提现与首充奖励成本；若复充率低于20%，再检查首充后体验。",
                "分别建立“盈余不足”和“复充不足”两个实验，不把两类问题混在同一活动中。",
                "7天后同时观察首充盈余率、复充率和投诉率，任一恶化即停止扩大。",
            ] if recharge_status != "健康" else [
                "首充盈余与复充均达到标准，保持当前首充策略。",
                "按渠道识别稳定达标来源，增加优质渠道占比而非普遍加奖。",
                "继续监测首充提现占比，防止健康指标被短期活动透支。",
            ]
        ),
        "首充盈余率≥55%，首充复充率≥20%。",
    ))

    old_status = _status(safe_value := metrics["old_arppu"], metrics["arppu"]*.8, metrics["arppu"]*.6, higher_is_worse=False)
    items.append(_item(
        "老客经营", "老用户价值稳定性", old_status,
        "P1" if old_status != "健康" else "P2",
        f"老用户充值 {_money(metrics['old_deposit'])}，老用户提现 {_money(metrics['old_withdraw'])}，"
        f"老用户盈余 {_money(metrics['old_surplus'])}，老用户ARPPU {_money(safe_value)}，"
        f"整体ARPPU {_money(metrics['arppu'])}。",
        "老用户ARPPU明显低于整体水平时，应区分自然成熟、活跃下降与高价值用户流失。",
        "老客价值下滑会提高平台对新增投放的依赖，使收入质量变得不稳定。",
        [
            "按VIP等级观察累计充值、最后登录和余额，识别价值下降而非单纯未登录。",
            "高价值流失风险用户优先客服关怀和产品反馈，不使用强刺激奖励。",
            "复盘老客权益使用率，移除无感知权益，保留高使用率服务权益。",
        ],
        "老用户ARPPU至少达到整体ARPPU的80%，并保持14天趋势不连续下滑。",
    ))

    risk_ratio = high_risk / total_profiles
    risk_status = _status(risk_ratio, .15, .25)
    items.append(_item(
        "风险治理", "用户流失与分层结构", risk_status,
        "P0" if risk_status == "高风险" else "P1",
        f"用户明细 {len(user_df):,} 人，其中高风险 {high_risk:,} 人、中风险 {medium_risk:,} 人，"
        f"高风险占比 {_pct(risk_ratio)}；高价值用户 {high_value:,} 人，羊毛用户 {wool:,} 人。",
        "风险评分基于最后登录、累计充值、余额和首充状态，是运营筛查工具，不代表用户真实意图。",
        "高风险用户积累会拖累活跃与收入稳定性；错误召回则可能造成打扰或负责任运营风险。",
        [
            "将高风险名单按VIP、渠道和最近登录天数排序，分批人工复核。",
            "区分服务型关怀、产品反馈和风险提醒，不对全部流失用户统一发奖。",
            "记录触达、回访和投诉结果，7天后更新规则阈值。",
        ],
        "高风险用户占比控制在15%以内；更重要的是连续4周下降。",
    ))

    priorities = {"P0": 0, "P1": 1, "P2": 2}
    items.sort(key=lambda x: (priorities[x["priority"]], x["category"]))
    return {
        "period": f"{ordered['date'].min():%Y-%m-%d} 至 {ordered['date'].max():%Y-%m-%d}",
        "headline": {
            "deposit_change": deposit_change,
            "surplus_change": surplus_change,
            "new_user_change": new_user_change,
            "high_risk_users": high_risk,
        },
        "items": items,
        "summary": {
            "P0": sum(item["priority"] == "P0" for item in items),
            "P1": sum(item["priority"] == "P1" for item in items),
            "P2": sum(item["priority"] == "P2" for item in items),
        },
    }


def analysis_to_rows(report: dict) -> pd.DataFrame:
    """转换为适合 Excel 导出的平面表格。"""
    return pd.DataFrame([
        {
            "优先级": item["priority"], "分析模块": item["category"],
            "结论": item["title"], "状态": item["status"],
            "数据证据": item["evidence"], "判断说明": item["interpretation"],
            "经营影响": item["impact"], "建议动作": "；".join(item["actions"]),
            "目标与判定": item["target"], "观察周期": item["observation"],
            "停止条件": item["stop_condition"],
        }
        for item in report["items"]
    ])
