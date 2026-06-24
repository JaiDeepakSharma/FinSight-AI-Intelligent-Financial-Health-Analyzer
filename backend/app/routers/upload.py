from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
from app.database import get_db
from app.models import User, Statement, Transaction
from app.schemas import TransactionResponse, StatementResponse, TransactionCategoryUpdate
from app.routers.auth import get_current_user
from app.services.parser import BankStatementParser
from app.services.ml_pipeline import ml_pipeline
from app.services.rag_service import FinancialRAGService

router = APIRouter(prefix="/api/transactions", tags=["Transactions & Uploads"])

def refresh_user_rag_index(user_id: int, db: Session):
    """Compiles the latest user analytics data and updates the RAG indexes in ChromaDB."""
    # 1. Fetch all transactions
    txs = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    if not txs:
        FinancialRAGService.index_financial_data(user_id, [], {})
        return
        
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
    spending_mask = df['amount'] < 0
    total_spending = df[spending_mask]['amount'].abs().sum() if not df[spending_mask].empty else 0.0
    total_income = df[df['amount'] > 0]['amount'].sum() if not df[df['amount'] > 0].empty else 0.0
    
    # Category spending breakdown
    spend_by_cat = []
    if total_spending > 0:
        cat_df = df[spending_mask].copy()
        cat_df['amount'] = cat_df['amount'].abs()
        cat_df = cat_df.groupby('category')['amount'].sum().reset_index()
        for _, row in cat_df.iterrows():
            spend_by_cat.append({
                "category": row['category'],
                "amount": float(row['amount']),
                "percentage": float((row['amount'] / total_spending) * 100)
            })
            
    # Monthly trend calculation
    monthly_trends = []
    df['month'] = df['date'].apply(lambda x: x.strftime('%Y-%m'))
    grouped = df.groupby('month')
    for month, group in grouped:
        month_str = month[0] if isinstance(month, (list, tuple)) else month
        m_spend = group[group['amount'] < 0]['amount'].abs().sum()
        m_inc = group[group['amount'] > 0]['amount'].sum()
        monthly_trends.append({
            "month": month_str,
            "income": float(m_inc),
            "spending": float(m_spend)
        })
    monthly_trends = sorted(monthly_trends, key=lambda x: x['month'])
    
    # Forecast next 30 days
    forecast = ml_pipeline.forecast_spending(txs_dict)
    
    analytics_data = {
        "spend_by_category": spend_by_cat,
        "monthly_trends": monthly_trends,
        "forecast": forecast
    }
    
    # Update Vector database index
    FinancialRAGService.index_financial_data(user_id, txs_dict, analytics_data)

@router.post("/upload", response_model=List[TransactionResponse], status_code=status.HTTP_201_CREATED)
async def upload_statement(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Determine file extension
    filename = file.filename
    file_ext = filename.split(".")[-1].lower()
    
    if file_ext not in ["csv", "pdf"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Please upload a CSV or PDF statement."
        )
        
    contents = await file.read()
    
    # Parse transaction records
    try:
        if file_ext == "csv":
            parsed_txs = BankStatementParser.parse_csv(contents)
        else:
            parsed_txs = BankStatementParser.parse_pdf(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing statement file: {str(e)}"
        )
        
    if not parsed_txs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transaction rows could be extracted from this statement. Please check the file formatting."
        )
        
    # Save statement entry
    new_statement = Statement(
        user_id=current_user.id,
        filename=filename,
        file_type=file_ext
    )
    db.add(new_statement)
    db.commit()
    db.refresh(new_statement)
    
    # Process transactions with ML
    # 1. Apply category classification
    for tx in parsed_txs:
        tx['category'] = ml_pipeline.predict_category(tx['description'])
        
    # 2. Run Isolation Forest / statistical anomaly detection
    processed_txs = ml_pipeline.detect_anomalies(parsed_txs)
    
    # 3. Create database Transaction models
    tx_models = []
    for tx in processed_txs:
        tx_models.append(Transaction(
            user_id=current_user.id,
            statement_id=new_statement.id,
            date=tx['date'],
            description=tx['description'],
            category=tx['category'],
            amount=tx['amount'],
            balance=tx.get('balance'),
            is_anomaly=tx.get('is_anomaly', False),
            anomaly_reason=tx.get('anomaly_reason')
        ))
        
    db.add_all(tx_models)
    db.commit()
    
    # Trigger RAG refresh
    refresh_user_rag_index(current_user.id, db)
    
    # Return saved models
    return db.query(Transaction).filter(Transaction.statement_id == new_statement.id).all()

@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Transaction).filter(Transaction.user_id == current_user.id).order_by(Transaction.date.desc()).all()

@router.get("/statements", response_model=List[StatementResponse])
def get_statements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Statement).filter(Statement.user_id == current_user.id).order_by(Statement.uploaded_at.desc()).all()

@router.delete("/statements/{statement_id}", status_code=status.HTTP_200_OK)
def delete_statement(
    statement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    statement = db.query(Statement).filter(Statement.id == statement_id, Statement.user_id == current_user.id).first()
    if not statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statement not found"
        )
        
    db.delete(statement)
    db.commit()
    
    # Refresh RAG Index since transactions have changed
    refresh_user_rag_index(current_user.id, db)
    
    return {"message": "Statement and associated transactions deleted successfully"}

@router.delete("/clear", status_code=status.HTTP_200_OK)
def clear_all_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Deleting statements deletes transactions via cascade
    db.query(Statement).filter(Statement.user_id == current_user.id).delete()
    db.query(Transaction).filter(Transaction.user_id == current_user.id).delete()
    db.commit()
    
    # Clear vector store
    refresh_user_rag_index(current_user.id, db)
    
    return {"message": "All transaction data reset successfully"}

@router.put("/{transaction_id}/category", response_model=TransactionResponse)
def update_transaction_category(
    transaction_id: int,
    cat_update: TransactionCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tx = db.query(Transaction).filter(Transaction.id == transaction_id, Transaction.user_id == current_user.id).first()
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
        
    tx.category = cat_update.category
    db.commit()
    db.refresh(tx)
    
    # Retrain ML model based on user override
    # Fetch all overrides (where user corrected it manually)
    # Since we don't have an explicit 'corrected' flag, we can collect user's unique transactions or use this single override
    # Let's collect all transactions in db as additional training points
    all_user_txs = db.query(Transaction).filter(Transaction.user_id == current_user.id).all()
    user_training_points = [(t.description, t.category) for t in all_user_txs]
    
    # Retrain pipeline
    ml_pipeline.retrain_with_user_data(user_training_points)
    
    # Refresh vector DB
    refresh_user_rag_index(current_user.id, db)
    
    return tx
