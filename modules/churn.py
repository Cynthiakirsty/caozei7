"""用户明细流失风险评分。"""
import numpy as np
import pandas as pd
from modules.segmentation import build_user_profiles


def _minmax(series):
    span = series.max()-series.min()
    return (series-series.min())/span if span else pd.Series(0.0, index=series.index)


def score_churn(df: pd.DataFrame) -> pd.DataFrame:
    p = build_user_profiles(df)
    inactivity = np.clip(p["days_since_login"]/30, 0, 1)
    low_value = 1-_minmax(p["total_deposit"])
    low_balance = 1-_minmax(p["balance"])
    no_first_pay = p["first_deposit_date"].isna().astype(float)
    p["churn_score"] = (100*(.55*inactivity+.20*low_value+.10*low_balance+.15*no_first_pay)).round(1)
    p["risk_level"] = pd.cut(p["churn_score"], [-1, 40, 70, 101], labels=["低风险", "中风险", "高风险"])
    return p.sort_values("churn_score", ascending=False)
