import streamlit as st
import requests

st.set_page_config(page_title="LLM Forecast")

st.title("ForecastFlow (Beta) – LLM-Assisted Forecasting for SMEs")

st.markdown("""
Welcome to **ForecastFlow (Beta)** – an AI-powered forecasting assistant built for small and medium businesses.  
Upload your sales or demand data and get:
- 30-day forecasts using advanced models (Prophet, ARIMA, LSTM)
- Natural language explanations powered by Mistral (LLM)
- Seasonality insights, anomaly detection, and downloadable PDF reports

---
""")

st.sidebar.markdown("🔧 **Available Models:**")
st.sidebar.markdown("- auto (recommended)")
st.sidebar.markdown("- prophet")
st.sidebar.markdown("- arima")
st.sidebar.markdown("- lstm")

uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
target_column = st.text_input("Target Column", value="sales")
model_type = st.selectbox("Select Model", options=["auto", "prophet", "arima", "lstm"])

if uploaded_file and st.button("Run Forecast"):
    files = {"file": uploaded_file}
    data = {
        "target_column": target_column,
        "model_type": model_type
    }

    res = requests.post("http://localhost:8000/forecast/", files=files, data=data)
    if res.ok:
        result = res.json()
        st.image(result["plot_path"], caption=f"{result['model_used'].upper()} Forecast Plot")
        st.subheader("Summary Stats")
        st.json(result["summary_stats"])

        st.subheader("YoY / MoM Comparison")
        st.json(result["comparison"])

        st.subheader("Detected Anomalies")
        st.write(f"{result['anomaly_count']} anomalies found")

        st.subheader("Changepoint Explanation")
        st.write(result["changepoints_explanation"])

        st.subheader("Cross-Validation Results")
        st.table(result["cross_validation"])

        st.download_button("📄 Download PDF Report", data=open(result["pdf_report"], "rb").read(), file_name="forecast_report.pdf")
    else:
        st.error(res.json().get("error", "Something went wrong."))

st.markdown("---")
st.markdown("Built by **Hazim** | Contact: alhaidarihazim@gmail.com")
