from prophet import Prophet
from statsmodels.tsa.arima.model import ARIMA
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import uuid
from utils import is_stationary

def generate_forecast(df: pd.DataFrame, target_col: str, model_type="auto", periods: int = 30):
    df = df.rename(columns={target_col: "y"})
    df["ds"] = pd.to_datetime(df[df.columns[0]])

    original_df = df.copy()
    forecast = None
    model_used = model_type

    if model_type == "auto":
        stationary = is_stationary(df["y"])
        model_used = "arima" if stationary else "prophet"

    fig, ax = plt.subplots()

    if model_used == "prophet":
        model = Prophet()
        model.fit(df[["ds", "y"]])
        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)

        ax.plot(df["ds"], df["y"], label="Original", color="blue")
        ax.plot(forecast["ds"], forecast["yhat"], label="Forecast", color="red")
        ax.fill_between(forecast["ds"], forecast["yhat_lower"], forecast["yhat_upper"], color="red", alpha=0.2)
        ax.set_title("Prophet Forecast")
        ax.legend()

    elif model_used == "arima":
        df.set_index("ds", inplace=True)
        model = ARIMA(df["y"], order=(5, 1, 0)).fit()
        pred = model.get_forecast(steps=periods)
        forecast_df = pred.summary_frame()
        f_index = pd.date_range(start=df.index[-1], periods=periods+1, freq="D")[1:]
        forecast = pd.DataFrame({"ds": f_index, "yhat": forecast_df["mean"]})

        ax.plot(df.index, df["y"], label="Original", color="blue")
        ax.plot(f_index, forecast_df["mean"], label="Forecast", color="red")
        ax.set_title("ARIMA Forecast")
        ax.legend()

    else:
        raise ValueError(f"Unsupported model type: {model_used}")

    plot_path = f"uploads/plot_{uuid.uuid4().hex}.png"
    fig.savefig(plot_path)
    plt.close(fig)

    return plot_path, forecast, model
