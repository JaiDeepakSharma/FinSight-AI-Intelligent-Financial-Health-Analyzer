import os
import sys
from datetime import date, datetime
import pytest
import numpy as np

# Adjust path to find the app
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.utils.security import get_password_hash, verify_password, create_access_token
from app.services.parser import clean_amount, parse_date, BankStatementParser
from app.services.ml_pipeline import ml_pipeline

# --- Test Security ---
def test_password_security():
    password = "supersecretpassword123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_jwt_generation():
    data = {"sub": "test@example.com"}
    token = create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 20

# --- Test Parser Helpers ---
def test_clean_amount():
    assert clean_amount("$1,250.55") == 1250.55
    assert clean_amount("-€45.00") == -45.00
    assert clean_amount("12.5") == 12.5
    assert clean_amount(None) == 0.0
    assert clean_amount("") == 0.0

def test_parse_date():
    assert parse_date("2026-04-12") == date(2026, 4, 12)
    assert parse_date("04/12/2026") == date(2026, 4, 12)
    assert parse_date("12-Apr-2026") == date(2026, 4, 12)

# --- Test CSV Parser ---
def test_csv_parser():
    csv_data = (
        "Date,Description,Amount,Balance\n"
        "2026-05-01,Apartments Rent,-1500.00,3000.00\n"
        "2026-05-02,Starbucks Coffee,-6.50,2993.50\n"
        "2026-05-10,Salary Paycheck,4500.00,7493.50\n"
    ).encode('utf-8')
    
    transactions = BankStatementParser.parse_csv(csv_data)
    assert len(transactions) == 3
    
    # Verify mapping
    assert transactions[0]["date"] == date(2026, 5, 1)
    assert transactions[0]["description"] == "Apartments Rent"
    assert transactions[0]["amount"] == -1500.0
    assert transactions[0]["balance"] == 3000.0
    
    assert transactions[2]["amount"] == 4500.0

# --- Test ML Categorization ---
def test_ml_categorization():
    # Starbucks should map to Food & Dining via keywords or seed classifier
    cat1 = ml_pipeline.predict_category("Starbucks Coffee Shop")
    assert cat1 == "Food & Dining"
    
    # Netflix should map to Entertainment
    cat2 = ml_pipeline.predict_category("Netflix Streaming")
    assert cat2 == "Entertainment"
    
    # Direct deposit should map to Salary & Income
    cat3 = ml_pipeline.predict_category("Direct Deposit Payroll")
    assert cat3 == "Salary & Income"

# --- Test ML Anomaly Detection ---
def test_ml_anomaly_detection():
    txs = [
        {"date": date(2026, 5, 1), "description": "Rent", "amount": -1500.0, "balance": 3000.0},
        {"date": date(2026, 5, 2), "description": "Whole Foods", "amount": -100.0, "balance": 2900.0},
        {"date": date(2026, 5, 3), "description": "Starbucks", "amount": -5.0, "balance": 2895.0},
        # Duplicate Starbucks charge on the same day (Potential double charge anomaly)
        {"date": date(2026, 5, 4), "description": "Starbucks Coffee", "amount": -15.50, "balance": 2879.50},
        {"date": date(2026, 5, 4), "description": "Starbucks Coffee", "amount": -15.50, "balance": 2864.00},
    ]
    
    anomalies = ml_pipeline.detect_anomalies(txs)
    # The last element should be flagged as potential double charge
    flagged = [t for t in anomalies if t.get("is_anomaly")]
    assert len(flagged) > 0
    assert "double charge" in flagged[0]["anomaly_reason"].lower()

# --- Test ML Forecast ---
def test_forecast_spending():
    txs = [
        {"date": date(2026, 5, 1), "description": "Rent", "amount": -1500.0, "balance": 3000.0},
        {"date": date(2026, 5, 5), "description": "Groceries", "amount": -100.0, "balance": 2900.0},
        {"date": date(2026, 5, 10), "description": "Coffee", "amount": -5.0, "balance": 2895.0},
        {"date": date(2026, 5, 15), "description": "Utilities", "amount": -80.0, "balance": 2815.0},
        {"date": date(2026, 5, 20), "description": "Gas", "amount": -40.0, "balance": 2775.0},
    ]
    
    forecasts = ml_pipeline.forecast_spending(txs, days_to_forecast=10)
    assert len(forecasts) > 0
    # Must have both historical and forecast points
    assert any(f["is_forecast"] is True for f in forecasts)
    assert any(f["is_forecast"] is False for f in forecasts)
