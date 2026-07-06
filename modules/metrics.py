"""全盘日报指标汇总口径。"""
import numpy as np
import pandas as pd


def safe_div(a, b):
    return 0.0 if b is None or float(b) == 0 else float(a)/float(b)


def _weighted(df, column, weight="deposit"):
    valid = df[weight].sum()
    return safe_div((df[column]*df[weight]).sum(), valid) if valid else float(df[column].mean() or 0)


def calculate_metrics(df: pd.DataFrame) -> dict:
    deposit, withdraw, bet = df["deposit"].sum(), df["withdraw"].sum(), df["bet"].sum()
    payout = bet*_weighted(df, "rtp", "bet")
    game_income = bet-payout
    result = {
        "total_deposit": deposit, "total_withdraw": withdraw,
        "surplus": df["surplus"].sum(), "surplus_rate": safe_div(df["surplus"].sum(), deposit),
        "total_bet": bet, "total_payout": payout, "game_income": game_income,
        "rtp": _weighted(df, "rtp", "bet"), "kill_rate": _weighted(df, "kill_rate"),
        "bet_deposit_ratio": safe_div(bet, deposit), "activity_cost": df["bonus"].sum(),
        "activity_cost_ratio": safe_div(df["bonus"].sum(), deposit),
        "bonus_game_income_ratio": safe_div(df["bonus"].sum(), game_income),
        "arppu": safe_div(deposit, df["paying_users"].sum()),
        "paying_users": int(df["paying_users"].sum()), "total_users": int(df["dau"].sum()),
        "new_arpu": safe_div(deposit, df["new_users"].sum()),
        "new_arppu": _weighted(df, "new_arppu", "first_deposit_users"),
        "first_recharge_rate": _weighted(df, "first_recharge_rate", "first_deposit_users"),
        "old_arppu": safe_div(df["old_deposit"].sum(), df["old_paying_users"].sum()),
        "first_deposit_surplus_rate": _weighted(df, "first_deposit_surplus_rate", "first_deposit"),
        "new_users": int(df["new_users"].sum()),
        "old_deposit": df["old_deposit"].sum(), "old_withdraw": df["old_withdraw"].sum(),
        "old_surplus": df["old_surplus"].sum(), "pay_rate": _weighted(df, "pay_rate", "dau"),
    }
    for day in (1, 3, 7, 15, 30):
        result[f"retention_d{day}"] = _weighted(df, f"retention_d{day}", "new_users")
    return result


def daily_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """全盘数据已经按日汇总，仅补齐页面兼容字段。"""
    result = df.copy()
    result["payout"] = result["bet"]*result["rtp"]
    result["activity_cost_ratio"] = result["bonus_ratio"]
    return result


def activity_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """无活动名称维度时，按日期输出彩金成本表现。"""
    result = df[["date", "deposit", "bonus", "bonus_ratio", "surplus"]].copy()
    result["activity_name"] = result["date"].dt.strftime("%Y-%m-%d")
    result["users"] = df["dau"]
    result["cost_ratio"] = result["bonus_ratio"]
    result["roi"] = np.divide(
        result["surplus"]-result["bonus"], result["bonus"],
        out=np.zeros(len(result)), where=result["bonus"].ne(0),
    )
    result["withdraw"] = df["withdraw"]
    result["bet"] = df["bet"]
    return result
