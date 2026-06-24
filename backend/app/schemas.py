from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import List, Optional

# --- Auth Schemas ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None


# --- Statement Schemas ---
class StatementResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


# --- Transaction Schemas ---
class TransactionResponse(BaseModel):
    id: int
    statement_id: Optional[int] = None
    date: date
    description: str
    category: str
    amount: float
    balance: Optional[float] = None
    is_anomaly: bool
    anomaly_reason: Optional[str] = None

    class Config:
        from_attributes = True

class TransactionCategoryUpdate(BaseModel):
    category: str


# --- Analytics Schemas ---
class SpendByCategory(BaseModel):
    category: str
    amount: float
    percentage: float

class MonthlyTrend(BaseModel):
    month: str  # YYYY-MM
    income: float
    spending: float

class ForecastData(BaseModel):
    date: str  # YYYY-MM-DD
    amount: float
    is_forecast: bool

class AnalyticsDashboard(BaseModel):
    total_income: float
    total_spending: float
    net_savings: float
    anomalies_count: int
    spend_by_category: List[SpendByCategory]
    monthly_trends: List[MonthlyTrend]
    forecast: List[ForecastData]


# --- Chat Schemas ---
class ChatQuery(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str
    references: List[TransactionResponse]
