import streamlit as st
import requests

st.set_page_config(page_title="ForecastFlow - Auth Forecast")

API_URL = "http://localhost:8000"
if "token" not in st.session_state:
    st.session_state.token = None

st.title("🔐 ForecastFlow – Authenticated Forecasting")

auth_mode = st.radio("Choose action", ["Login", "Register"])
email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Submit"):
    if auth_mode == "Register":
        res = requests.post(f"{API_URL}/register/", data={"email": email, "password": password})
        if res.status_code == 200:
            st.success("Registered. Please log in.")
        else:
            try:
                st.error(res.json()["detail"])
            except:
                st.error("Registration error.")
    else:
        res = requests.post(f"{API_URL}/token/", data={"email": email, "password": password})
        if res.status_code == 200:
            st.session_state.token = res.json()["access_token"]
            st.success("Logged in!")
        else:
            st.error("Invalid credentials")

if st.session_state.token:
    st.markdown("---")
    st.subheader("📤 Upload CSV/XLSX + Forecast")
    uploaded_file = st.file_uploader("Upload your file", type=["csv", "xlsx"])
    target_column = st.text_input("Target Column", value="sales")
    model_type = st.selectbox("Select Model", ["prophet", "arima", "auto"])

    if uploaded_file and st.button("Run Forecast"):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
        data = {
            "target_column": target_column,
            "model_type": model_type
        }
        headers = {"Authorization": f"Bearer {st.session_state.token}"}

        res = requests.post(f"{API_URL}/upload/", files=files, data=data, headers=headers)

        if res.ok:
            r = res.json()
            st.image(r["plot"], caption=f"{model_type.upper()} Forecast Plot")

            st.subheader("📊 Summary Statistics")
            st.write(f"**Mean:** {r['mean']} | **Median:** {r['median']} | **Trend:** {r['trend']}")

            st.subheader("📈 YoY / MoM Comparison")
            st.write(r["comparison"])

            st.subheader("🧠 LLM Insight")
            st.text_area("Changepoint Explanation", r["summary"], height=180)

            st.subheader("📄 Download Report")
            with open(r["pdf_report"], "rb") as f:
                st.download_button("📥 Download PDF", f, file_name="forecast_report.pdf")

        else:
            try:
                error_detail = res.json().get("detail", "Upload failed.")
            except:
                error_detail = res.text or "Unknown error"
            st.error(error_detail)

    st.markdown("---")
    if st.button("📜 View My Forecast History"):
        res = requests.get(f"{API_URL}/history/", headers={"Authorization": f"Bearer {st.session_state.token}"})
        if res.ok:
            for h in res.json():
                st.markdown(f"**{h['filename']}** | {h['timestamp']} | Model: {h['model']}")
                st.image(h["plot"], width=300)
                st.text(h["summary"])
        else:
            st.error("Could not load history")

    if st.button("🔓 Logout"):
        st.session_state.token = None
        st.experimental_rerun()
