import pandas as pd
from statsmodels.tsa.stattools import adfuller

def calculate_summary_stats(series):
    return {
        "mean": round(series.mean(), 2),
        "median": round(series.median(), 2),
        "trend": "increasing" if series.iloc[-1] > series.iloc[0] else "decreasing"
    }

def compare_periods(df, col):
    mid = len(df) // 2
    current = df[col].iloc[mid:].mean()
    previous = df[col].iloc[:mid].mean()
    yoy = ((current - previous) / previous) * 100 if previous != 0 else 0
    return round(current, 2), round(previous, 2), round(yoy, 2)

def is_stationary(series):
    result = adfuller(series)
    return result[1] < 0.05
