"""生成可离线打开的自包含 HTML 可视化运营报告。"""
from html import escape

import plotly.express as px
import plotly.io as pio

from modules.basic_analysis import HEALTH_STANDARDS, generate_detailed_analysis
from modules.metrics import calculate_metrics


def _money(value):
    return f"₹{value:,.0f}"


def _pct(value):
    return f"{value:.1%}"


def _card(label, value, note=""):
    return (
        '<div class="metric"><div class="metric-label">'
        f"{escape(label)}</div><div class=\"metric-value\">{escape(value)}</div>"
        f'<div class="metric-note">{escape(note)}</div></div>'
    )


def build_html_report(full_df, user_df) -> bytes:
    """构建包含指标、趋势图及行动建议的单文件 HTML。"""
    metrics = calculate_metrics(full_df)
    report = generate_detailed_analysis(full_df, user_df)
    ordered = full_df.sort_values("date").copy()

    money_fig = px.line(
        ordered, x="date", y=["deposit", "withdraw", "surplus"],
        title="每日充值、提现与盈余趋势",
        labels={"date":"日期", "value":"金额（₹）", "variable":"指标"},
    )
    money_fig.update_layout(template="plotly_white", legend_title_text="")
    rate_fig = px.line(
        ordered, x="date",
        y=["surplus_rate", "rtp", "bonus_ratio"],
        title="盈余率、RTP与彩金占比趋势",
        labels={"date":"日期", "value":"比例", "variable":"指标"},
    )
    rate_fig.update_layout(template="plotly_white", legend_title_text="", yaxis_tickformat=".0%")
    retention_fig = px.line(
        ordered, x="date",
        y=["retention_d1", "retention_d3", "retention_d7", "retention_d15", "retention_d30"],
        title="留存趋势",
        labels={"date":"日期", "value":"留存率", "variable":"周期"},
    )
    retention_fig.update_layout(template="plotly_white", legend_title_text="", yaxis_tickformat=".0%")

    metrics_html = "".join([
        _card("总充值", _money(metrics["total_deposit"])),
        _card("总提现", _money(metrics["total_withdraw"])),
        _card("盈余", _money(metrics["surplus"]), f"盈余率 {_pct(metrics['surplus_rate'])}"),
        _card("有效投注", _money(metrics["total_bet"])),
        _card("RTP", _pct(metrics["rtp"]), f"杀率 {_pct(metrics['kill_rate'])}"),
        _card("彩金成本", _money(metrics["activity_cost"]), f"占比 {_pct(metrics['activity_cost_ratio'])}"),
        _card("新增用户", f"{metrics['new_users']:,}", f"ARPU {_money(metrics['new_arpu'])}"),
        _card("高风险用户", f"{report['headline']['high_risk_users']:,}"),
    ])

    item_html = []
    status_class = {"高风险":"danger", "需关注":"warning", "健康":"healthy"}
    for item in report["items"]:
        actions = "".join(f"<li>{escape(action)}</li>" for action in item["actions"])
        item_html.append(
            f'<section class="decision {status_class[item["status"]]}">'
            f'<div class="decision-head"><h3>{escape(item["priority"])} · '
            f'{escape(item["category"])} · {escape(item["title"])}</h3>'
            f'<span>{escape(item["status"])}</span></div>'
            f'<div class="evidence"><b>数据证据：</b>{escape(item["evidence"])}</div>'
            f'<div class="two-col"><div><h4>判断说明</h4><p>{escape(item["interpretation"])}</p></div>'
            f'<div><h4>经营影响</h4><p>{escape(item["impact"])}</p></div></div>'
            f'<h4>建议动作</h4><ol>{actions}</ol>'
            f'<div class="two-col"><div><h4>目标与判定标准</h4><p>{escape(item["target"])}</p></div>'
            f'<div><h4>观察与停止条件</h4><p>{escape(item["observation"])}；'
            f'{escape(item["stop_condition"])}。</p></div></div></section>'
        )

    standards_html = "".join(
        f"<tr><td>{escape(name)}</td><td>{escape(value)}</td></tr>"
        for name, value in HEALTH_STANDARDS
    )
    chart1 = pio.to_html(money_fig, full_html=False, include_plotlyjs=True)
    chart2 = pio.to_html(rate_fig, full_html=False, include_plotlyjs=False)
    chart3 = pio.to_html(retention_fig, full_html=False, include_plotlyjs=False)
    html = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>游戏运营基础分析报告</title>
<style>
body{{margin:0;background:#f4f7fb;color:#172033;font-family:"Microsoft YaHei",Arial,sans-serif}}
.page{{max-width:1280px;margin:auto;padding:32px}} h1{{margin-bottom:8px}}
.sub{{color:#64748b;margin-bottom:24px}} .metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}
.metric,.chart,.decision{{background:#fff;border:1px solid #e2e8f0;border-radius:14px;box-shadow:0 3px 12px #0f172a0d}}
.metric{{padding:18px}} .metric-label,.metric-note{{color:#64748b;font-size:13px}}
.metric-value{{font-size:25px;font-weight:700;margin:7px 0}} .chart{{padding:10px;margin-top:18px}}
.section-title{{margin-top:34px}} .decision{{padding:22px;margin:16px 0;border-left:6px solid #22c55e}}
.decision.warning{{border-left-color:#f59e0b}} .decision.danger{{border-left-color:#ef4444}}
.decision-head{{display:flex;justify-content:space-between;gap:20px;align-items:center}}
.decision-head span{{background:#eef2ff;border-radius:20px;padding:7px 12px;white-space:nowrap}}
.evidence{{background:#f8fafc;padding:14px;border-radius:9px;line-height:1.7}}
.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:22px}} p,li{{line-height:1.75}}
footer{{color:#64748b;text-align:center;padding:28px}}
@media(max-width:800px){{.metrics{{grid-template-columns:1fr 1fr}}.two-col{{grid-template-columns:1fr}}}}
@media print{{body{{background:#fff}}.page{{max-width:none}}.metric,.chart,.decision{{box-shadow:none}}}}
</style></head><body><main class="page">
<h1>游戏运营基础分析报告</h1>
<div class="sub">分析区间：{escape(report["period"])}｜货币单位：印度卢比（₹）｜无需大模型</div>
<div class="metrics">{metrics_html}</div>
<h2 class="section-title">健康标准</h2>
<div class="chart"><table style="width:100%;border-collapse:collapse">
<thead><tr><th style="text-align:left;padding:10px;border-bottom:1px solid #ddd">指标</th>
<th style="text-align:left;padding:10px;border-bottom:1px solid #ddd">健康值</th></tr></thead>
<tbody>{standards_html}</tbody></table></div>
<div class="chart">{chart1}</div><div class="chart">{chart2}</div><div class="chart">{chart3}</div>
<h2 class="section-title">详细决策建议</h2>
{''.join(item_html)}
<footer>本报告由确定性指标与规则生成。建议结合业务基线、合规要求和人工复核使用。</footer>
</main></body></html>"""
    return html.encode("utf-8")
