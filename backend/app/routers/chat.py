from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models import User, Transaction
from app.schemas import ChatQuery, ChatResponse, TransactionResponse
from app.routers.auth import get_current_user
from app.services.rag_service import FinancialRAGService

router = APIRouter(prefix="/api/chat", tags=["AI Chat Advisor"])

@router.post("/query", response_model=ChatResponse)
def query_financial_advisor(
    query: ChatQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    user_msg = query.message
    
    # 1. Run RAG service to get LLM response
    try:
        answer = FinancialRAGService.answer_query(user_id, user_msg)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing AI query: {str(e)}"
        )
        
    # 2. Extract database transactions as structured UI reference cards
    # Filter transaction database using words from the query that are likely search terms
    stopwords = {"show", "much", "spend", "what", "where", "when", "find", "large", "small", "food", "rent", "rate", "over", "under", "total", "category", "here", "were", "went", "many", "than", "they", "them", "then", "their", "that", "this", "there"}
    words = [
        w.strip("?,.!;\"'") 
        for w in user_msg.lower().split() 
        if len(w) > 3 and w.strip("?,.!;\"'") not in stopwords
    ]
    
    references = []
    if words:
        filters = []
        for word in words[:4]:  # limit to top 4 search terms to prevent SQL complexity
            filters.append(Transaction.description.ilike(f"%{word}%"))
            filters.append(Transaction.category.ilike(f"%{word}%"))
            
        # Run query
        ref_models = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .filter(or_(*filters))
            .order_by(Transaction.date.desc())
            .limit(5)
            .all()
        )
        references = ref_models
        
    # If no word matches or query was generic, pull recent transactions or largest transactions
    if not references:
        # If user asked for large/highest, fetch largest debits
        if any(w in user_msg.lower() for w in ["large", "high", "expensive", "big"]):
            references = (
                db.query(Transaction)
                .filter(Transaction.user_id == user_id, Transaction.amount < 0)
                .order_by(Transaction.amount.asc())  # Negative numbers, so asc gets largest debits
                .limit(5)
                .all()
            )
        else:
            # Fallback to 5 most recent transactions
            references = (
                db.query(Transaction)
                .filter(Transaction.user_id == user_id)
                .order_by(Transaction.date.desc())
                .limit(5)
                .all()
            )
            
    return {
        "answer": answer,
        "references": references
    }
