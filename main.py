from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import init_db, SessionLocal
from models import User, Forecast
from auth import hash_password, verify_password, create_access_token, decode_access_token
from forecast import generate_forecast
from utils import calculate_summary_stats, compare_periods
from llm_helper import summarize_changepoints
from report_generator import ForecastPDF
from datetime import datetime
import pandas as pd
import os

app = FastAPI()
init_db()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/register/")
def register(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    return {"msg": "Registered successfully"}

@app.post("/token/")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),
    target_column: str = Form(...),
    model_type: str = Form("prophet"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    safe_time = datetime.now().isoformat().replace(":", "-").replace(".", "-")
    filename = f"{safe_time}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f_out:
        f_out.write(await file.read())

    try:
        df = pd.read_excel(file_path) if filename.endswith(".xlsx") else pd.read_csv(file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    if target_column not in df.columns:
        raise HTTPException(status_code=400, detail="Target column not found in file.")

    try:
        plot_path, forecast_df, model = generate_forecast(df, target_column, model_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting failed: {str(e)}")

    stats = calculate_summary_stats(df[target_column])
    comparison = compare_periods(df, target_column)
    changepoint_prompt = f"""Explain the trend changes in this forecast data:
{forecast_df[['ds','yhat']].tail(10).to_string(index=False)}"""
    llm_summary = summarize_changepoints(changepoint_prompt)

    # Generate PDF report
    pdf = ForecastPDF()
    pdf.add_page()
    pdf.add_summary(stats, comparison, llm_summary)
    pdf.add_image(plot_path)
    pdf_path = f"uploads/report_{safe_time}.pdf"
    pdf.save_pdf(pdf_path)

    forecast_entry = Forecast(
        filename=filename,
        model_used=model_type,
        user_id=user.id,
        plot_path=plot_path,
        summary=llm_summary
    )
    db.add(forecast_entry)
    db.commit()

    return {
        "msg": "Forecast complete",
        "plot": plot_path,
        "summary": llm_summary,
        "mean": stats["mean"],
        "median": stats["median"],
        "trend": stats["trend"],
        "comparison": {
            "current_avg": comparison[0],
            "previous_avg": comparison[1],
            "yoy_change": comparison[2]
        },
        "pdf_report": pdf_path
    }

@app.get("/history/")
def get_user_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    history = db.query(Forecast).filter(Forecast.user_id == user.id).all()
    return [{
        "filename": h.filename,
        "model": h.model_used,
        "timestamp": h.timestamp.isoformat(),
        "plot": h.plot_path,
        "summary": h.summary
    } for h in history]

