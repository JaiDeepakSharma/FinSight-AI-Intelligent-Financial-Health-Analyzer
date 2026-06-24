from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
from typing import Dict, Any
from app.database import get_db
from app.models import User, Transaction
from app.schemas import AnalyticsDashboard
from app.routers.auth import get_current_user
from app.services.ml_pipeline import ml_pipeline

router = APIRouter(prefix="/api/analytics", tags=["Financial Analytics"])

@router.get("/dashboard", response_model=AnalyticsDashboard)
def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch user transactions
    txs = db.query(Transaction).filter(Transaction.user_id == current_user.id).all()
    
    if not txs:
        return {
            "total_income": 0.0,
            "total_spending": 0.0,
            "net_savings": 0.0,
            "anomalies_count": 0,
            "spend_by_category": [],
            "monthly_trends": [],
            "forecast": []
        }
        
    txs_dict = []
    for t in txs:
        txs_dict.append({
            "id": t.id,
            "date": t.date,
            "description": t.description,
            "amount": t.amount,
            "category": t.category,
            "balance": t.balance,
            "is_anomaly": t.is_anomaly,
            "anomaly_reason": t.anomaly_reason
        })
        
    df = pd.DataFrame(txs_dict)
    
    # Identify spending (debits) and income (credits)
    spending_mask = df['amount'] < 0
    income_mask = df['amount'] > 0
    
    total_spending = df[spending_mask]['amount'].abs().sum() if not df[spending_mask].empty else 0.0
    total_income = df[income_mask]['amount'].sum() if not df[income_mask].empty else 0.0
    
    net_savings = total_income - total_spending
    anomalies_count = int(df['is_anomaly'].sum())
    
    # Calculate spending breakdown by category
    spend_by_cat = []
    if total_spending > 0:
        cat_df = df[spending_mask].copy()
        cat_df['amount'] = cat_df['amount'].abs()
        cat_df = cat_df.groupby('category')['amount'].sum().reset_index()
        for _, row in cat_df.iterrows():
            spend_by_cat.append({
                "category": row['category'],
                "amount": round(float(row['amount']), 2),
                "percentage": round(float((row['amount'] / total_spending) * 100), 2)
            })
        spend_by_cat = sorted(spend_by_cat, key=lambda x: x['amount'], reverse=True)
        
    # Calculate monthly income and spending trends
    monthly_trends = []
    df['month'] = df['date'].apply(lambda x: x.strftime('%Y-%m'))
    grouped = df.groupby('month')
    
    for month, group in grouped:
        month_str = month[0] if isinstance(month, (list, tuple)) else month
        m_spend = group[group['amount'] < 0]['amount'].abs().sum()
        m_inc = group[group['amount'] > 0]['amount'].sum()
        monthly_trends.append({
            "month": month_str,
            "income": round(float(m_inc), 2),
            "spending": round(float(m_spend), 2)
        })
    monthly_trends = sorted(monthly_trends, key=lambda x: x['month'])
    
    # Generate spending forecast for the next 30 days
    try:
        forecast = ml_pipeline.forecast_spending(txs_dict)
    except Exception as e:
        forecast = []
        
    return {
        "total_income": round(total_income, 2),
        "total_spending": round(total_spending, 2),
        "net_savings": round(net_savings, 2),
        "anomalies_count": anomalies_count,
        "spend_by_category": spend_by_cat,
        "monthly_trends": monthly_trends,
        "forecast": forecast
    }
