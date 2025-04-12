import streamlit as st
import requests

st.set_page_config(page_title="ForecastFlow Login")

API_URL = "http://localhost:8000"
if "token" not in st.session_state:
    st.session_state.token = None

st.title("🔐 ForecastFlow – User Login & Forecast History")

# === Auth section ===
auth_mode = st.radio("Choose action", ["Login", "Register"])
email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Submit"):
    if auth_mode == "Register":
        res = requests.post(f"{API_URL}/register/", data={"email": email, "password": password})
        if res.status_code == 200:
            st.success("Registration successful! Please log in.")
        else:
            st.error(res.json()["detail"])
    else:
        res = requests.post(f"{API_URL}/token/", data={"email": email, "password": password})
        if res.status_code == 200:
            st.session_state.token = res.json()["access_token"]
            st.success("Login successful!")
        else:
            st.error("Login failed.")

# === Upload forecast ===
if st.session_state.token:
    st.markdown("---")
    st.subheader("📤 Upload CSV/XLSX for Forecast")
    uploaded_file = st.file_uploader("Upload your file", type=["csv", "xlsx"])
    model = st.selectbox("Model Used", ["prophet", "arima", "lstm", "auto"])

    if uploaded_file and st.button("Upload Forecast"):
        files = {"file": uploaded_file.getvalue()}
        res = requests.post(
            f"{API_URL}/upload/",
            files={"file": uploaded_file},
            data={"model_used": model},
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if res.status_code == 200:
            st.success("Forecast uploaded and saved")
        else:
            st.error(res.json().get("detail", "Upload failed"))

    # === View forecast history ===
    if st.button("📜 View My Forecast History"):
        res = requests.get(
            f"{API_URL}/history/",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if res.ok:
            st.table(res.json())
        else:
            st.error("Could not load history")

    if st.button("🔓 Logout"):
        st.session_state.token = None
        st.experimental_rerun()
