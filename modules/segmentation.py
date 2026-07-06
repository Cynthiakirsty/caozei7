"""基于用户累计数据的画像与分层。"""
import numpy as np
import pandas as pd


def build_user_profiles(df: pd.DataFrame) -> pd.DataFrame:
    p = df.copy()
    today = pd.Timestamp.today().normalize()
    p["days_since_login"] = (today-p["last_login_date"].dt.normalize()).dt.days.fillna(999).clip(lower=0)
    p["account_age"] = (today-p["register_date"].dt.normalize()).dt.days.fillna(0).clip(lower=0)
    p["net_value"] = p["total_deposit"]-p["total_withdraw"]
    p["withdraw_ratio"] = np.divide(
        p["total_withdraw"], p["total_deposit"],
        out=np.zeros(len(p)), where=p["total_deposit"].ne(0),
    )
    p["balance"] = p["cash_balance"]+p["jcoin_balance"]
    return p


def segment_users(df: pd.DataFrame) -> pd.DataFrame:
    p = build_user_profiles(df)
    high = p["total_deposit"].quantile(.80)
    conditions = [
        p["days_since_login"].ge(14),
        (p["withdraw_ratio"] >= .9) & (p["jcoin_balance"] > 0),
        p["total_deposit"].ge(high) & p["net_value"].gt(0),
        (p["total_deposit"] >= p["total_deposit"].quantile(.60)) &
        (p["total_bet"] >= p["total_bet"].quantile(.75)),
        p["account_age"].le(7),
        p["first_deposit_date"].notna() & (p["account_age"] <= 14),
    ]
    p["segment"] = np.select(
        conditions,
        ["流失风险用户", "羊毛用户", "高价值用户", "VIP潜力用户", "新用户", "首充用户"],
        default="普通用户",
    )
    return p
