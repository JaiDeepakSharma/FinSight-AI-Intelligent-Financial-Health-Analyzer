import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Tuple

# Seed data for initial model training
SEED_DATA = [
    # Housing & Rent
    ("rent payment", "Housing & Rent"),
    ("monthly mortgage", "Housing & Rent"),
    ("apartments leasing", "Housing & Rent"),
    ("landlord association", "Housing & Rent"),
    # Groceries
    ("whole foods market", "Groceries"),
    ("trader joe's groceries", "Groceries"),
    ("safeway store", "Groceries"),
    ("kroger supermarket", "Groceries"),
    ("walmart grocery", "Groceries"),
    ("costco wholesale", "Groceries"),
    ("h-mart grocery", "Groceries"),
    # Food & Dining
    ("starbucks coffee", "Food & Dining"),
    ("mcdonald's restaurant", "Food & Dining"),
    ("uber eats delivery", "Food & Dining"),
    ("doordash food order", "Food & Dining"),
    ("domino's pizza", "Food & Dining"),
    ("dunkin donuts", "Food & Dining"),
    ("chipotle mexican grill", "Food & Dining"),
    ("subway sandwiches", "Food & Dining"),
    ("local diner cafe", "Food & Dining"),
    # Utilities
    ("comcast internet", "Utilities"),
    ("verizon wireless bill", "Utilities"),
    ("at&t mobile utility", "Utilities"),
    ("city electric power", "Utilities"),
    ("pg&e utility bill", "Utilities"),
    ("waste management trash", "Utilities"),
    ("municipal water district", "Utilities"),
    # Transportation
    ("uber trip ride", "Transportation"),
    ("lyft ride share", "Transportation"),
    ("chevron gas station", "Transportation"),
    ("shell oil fuel", "Transportation"),
    ("exxon mobil gas", "Transportation"),
    ("metro transit ticket", "Transportation"),
    ("subway metro card", "Transportation"),
    # Entertainment
    ("netflix subscription", "Entertainment"),
    ("spotify music premium", "Entertainment"),
    ("hulu tv streaming", "Entertainment"),
    ("disney plus subscription", "Entertainment"),
    ("steam games", "Entertainment"),
    ("playstation network", "Entertainment"),
    ("amc movie theater", "Entertainment"),
    # Shopping
    ("amazon.com online purchase", "Shopping"),
    ("ebay marketplace", "Shopping"),
    ("zara clothing shop", "Shopping"),
    ("h&m retail fashion", "Shopping"),
    ("target department store", "Shopping"),
    ("apple store hardware", "Shopping"),
    ("best buy electronics", "Shopping"),
    # Salary & Income
    ("direct deposit salary", "Salary & Income"),
    ("payroll direct deposit", "Salary & Income"),
    ("employer paycheck payroll", "Salary & Income"),
    ("wire transfer incoming", "Salary & Income"),
    ("venmo cash out deposit", "Salary & Income"),
    # Investment
    ("fidelity investments transfer", "Investment"),
    ("robinhood brokerage deposit", "Investment"),
    ("vanguard mutual funds", "Investment"),
    ("charles schwab account", "Investment"),
    # Insurance & Medical
    ("geico auto insurance", "Insurance & Medical"),
    ("state farm home insurance", "Insurance & Medical"),
    ("cvs pharmacy medicine", "Insurance & Medical"),
    ("walgreens health prescription", "Insurance & Medical"),
    ("aetna medical insurance", "Insurance & Medical"),
    ("local dental clinic", "Insurance & Medical"),
]

# Static rules engine keywords for rapid matching
STATIC_RULES = {
    "starbucks": "Food & Dining",
    "mcdonald": "Food & Dining",
    "burger": "Food & Dining",
    "pizza": "Food & Dining",
    "diner": "Food & Dining",
    "subway": "Food & Dining",
    "doordash": "Food & Dining",
    "ubereats": "Food & Dining",
    "wholefoods": "Groceries",
    "safeway": "Groceries",
    "kroger": "Groceries",
    "trader joe": "Groceries",
    "supermarket": "Groceries",
    "grocery": "Groceries",
    "netflix": "Entertainment",
    "spotify": "Entertainment",
    "hulu": "Entertainment",
    "disney": "Entertainment",
    "steam": "Entertainment",
    "nintendo": "Entertainment",
    "playstation": "Entertainment",
    "amazon": "Shopping",
    "ebay": "Shopping",
    "target": "Shopping",
    "walmart": "Shopping",
    "zara": "Shopping",
    "h&m": "Shopping",
    "nordstrom": "Shopping",
    "gas": "Transportation",
    "chevron": "Transportation",
    "shell": "Transportation",
    "exxon": "Transportation",
    "uber": "Transportation",
    "lyft": "Transportation",
    "transit": "Transportation",
    "subway ride": "Transportation",
    "mortgage": "Housing & Rent",
    "rent": "Housing & Rent",
    "apartment": "Housing & Rent",
    "electric": "Utilities",
    "power": "Utilities",
    "water bill": "Utilities",
    "internet": "Utilities",
    "comcast": "Utilities",
    "verizon": "Utilities",
    "at&t": "Utilities",
    "t-mobile": "Utilities",
    "salary": "Salary & Income",
    "payroll": "Salary & Income",
    "paycheck": "Salary & Income",
    "deposit": "Salary & Income",
    "fidelity": "Investment",
    "vanguard": "Investment",
    "robinhood": "Investment",
    "schwab": "Investment",
    "insurance": "Insurance & Medical",
    "pharmacy": "Insurance & Medical",
    "cvs": "Insurance & Medical",
    "walgreens": "Insurance & Medical",
    "clinic": "Insurance & Medical",
    "hospital": "Insurance & Medical",
}

class FinancialMLPipeline:
    def __init__(self):
        # Initialize text classification pipeline
        self.clf = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), lowercase=True)),
            ('lr', LogisticRegression(C=1.0, max_iter=200))
        ])
        self.train_classifier(SEED_DATA)

    def train_classifier(self, training_data: List[Tuple[str, str]]):
        """Fits the text classification pipeline on description -> category data."""
        descriptions, categories = zip(*training_data)
        self.clf.fit(descriptions, categories)

    def predict_category(self, description: str) -> str:
        """Predicts the category of a transaction description."""
        desc_clean = str(description).lower().strip()
        
        # 1. Check static rules first
        for keyword, cat in STATIC_RULES.items():
            if keyword in desc_clean:
                return cat
                
        # 2. Fall back to Scikit-learn Classifier
        try:
            pred = self.clf.predict([desc_clean])
            return pred[0]
        except Exception:
            return "Uncategorized"

    def retrain_with_user_data(self, user_overrides: List[Tuple[str, str]]):
        """Retrains the classifier using both seed data and user corrected transactions."""
        combined_data = SEED_DATA.copy()
        # Clean user overrides
        for desc, cat in user_overrides:
            combined_data.append((desc.lower().strip(), cat))
        
        self.train_classifier(combined_data)

    def detect_anomalies(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Flags anomalies in the transaction list.
        Uses Isolation Forest on amount and timing features for larger lists,
        complemented by Z-score metrics and duplicate checks for all sizes.
        """
        if not transactions:
            return []
            
        df = pd.DataFrame(transactions)
        
        # Standardize amount column
        df['abs_amount'] = df['amount'].abs()
        df['is_anomaly'] = False
        df['anomaly_reason'] = ""
        
        # 1. Rule-based: Duplicate checks (Potential Double Charges)
        # Transactions with the exact same amount and description within 2 days of each other
        df = df.sort_values(by=['date'])
        for idx in range(1, len(df)):
            prev_row = df.iloc[idx - 1]
            curr_row = df.iloc[idx]
            
            # Outflows only for double charges
            if curr_row['amount'] < 0 and curr_row['amount'] == prev_row['amount']:
                if curr_row['description'] == prev_row['description']:
                    days_diff = (curr_row['date'] - prev_row['date']).days
                    if days_diff <= 2:
                        df.at[df.index[idx], 'is_anomaly'] = True
                        df.at[df.index[idx], 'anomaly_reason'] = f"Potential double charge. Matches transaction on {prev_row['date']}."

        # Filter outflows (debits) for amount-based anomaly detection
        debits_mask = df['amount'] < 0
        debits_df = df[debits_mask].copy()
        
        if len(debits_df) >= 10:
            # 2. Isolation Forest Outlier Detection
            # Features: absolute amount, day of month, day of week
            debits_df['day_of_month'] = debits_df['date'].apply(lambda x: x.day)
            debits_df['day_of_week'] = debits_df['date'].apply(lambda x: x.weekday())
            
            X = debits_df[['abs_amount', 'day_of_month', 'day_of_week']]
            
            # Fit Isolation Forest (contamination is the estimated proportion of outliers)
            iso = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
            preds = iso.fit_predict(X)
            
            # Isolation Forest returns -1 for outliers
            for i, p in enumerate(preds):
                if p == -1:
                    row_idx = debits_df.index[i]
                    # Only overwrite anomaly if not already set by duplicates
                    if not df.at[row_idx, 'is_anomaly']:
                        amt = debits_df.iloc[i]['abs_amount']
                        df.at[row_idx, 'is_anomaly'] = True
                        df.at[row_idx, 'anomaly_reason'] = f"Statistical spending outlier. Amount of ${amt:.2f} is atypical for this user profile."
                        
        else:
            # 3. Z-score Fallback (when transaction volume is small)
            # Flag anything that is 2.5 standard deviations higher than the mean debit amount
            if len(debits_df) > 2:
                mean_debit = debits_df['abs_amount'].mean()
                std_debit = debits_df['abs_amount'].std()
                
                if std_debit > 0:
                    for idx, row in debits_df.iterrows():
                        z_score = (row['abs_amount'] - mean_debit) / std_debit
                        if z_score > 2.5 and row['abs_amount'] > 500: # Ensure we don't flag tiny items
                            if not df.at[idx, 'is_anomaly']:
                                df.at[idx, 'is_anomaly'] = True
                                df.at[idx, 'anomaly_reason'] = f"Transaction amount of ${row['abs_amount']:.2f} is exceptionally high compared to average debit (${mean_debit:.2f})."

        # Format output back into transaction dicts
        updated_transactions = []
        for _, row in df.iterrows():
            tx = row.to_dict()
            # Convert timestamp dates back to python datetime.date
            if isinstance(tx['date'], pd.Timestamp):
                tx['date'] = tx['date'].date()
            updated_transactions.append(tx)
            
        return updated_transactions

    def forecast_spending(self, transactions: List[Dict[str, Any]], days_to_forecast: int = 30) -> List[Dict[str, Any]]:
        """
        Forecasts daily cumulative spending for the next 30 days.
        Uses time-based Ridge Regression to model spending trend.
        """
        if not transactions:
            return []
            
        df = pd.DataFrame(transactions)
        # We only forecast spending (debits)
        df_spend = df[df['amount'] < 0].copy()
        if df_spend.empty:
            return []
            
        df_spend['date'] = pd.to_datetime(df_spend['date'])
        df_spend['abs_amount'] = df_spend['amount'].abs()
        
        # Group spendings by date
        daily_spend = df_spend.groupby('date')['abs_amount'].sum().reset_index()
        daily_spend = daily_spend.sort_values(by='date')
        
        # Complete the date range grid to include days with $0 spend
        start_date = daily_spend['date'].min()
        end_date = daily_spend['date'].max()
        all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        daily_spend = daily_spend.set_index('date').reindex(all_dates, fill_value=0.0).reset_index()
        daily_spend.columns = ['date', 'amount']
        
        # Calculate rolling cumulative spending per month
        # This shows how the user accumulates spend throughout the month
        daily_spend['day_of_month'] = daily_spend['date'].dt.day
        daily_spend['month'] = daily_spend['date'].dt.month
        daily_spend['year'] = daily_spend['date'].dt.year
        
        # Calculate daily cumulative sum within each month
        daily_spend['cumulative_spend'] = daily_spend.groupby(['year', 'month'])['amount'].cumsum()
        
        # For training, let's learn how spending accumulates based on day of month, day of week, and overall day index
        daily_spend['day_index'] = np.arange(len(daily_spend))
        daily_spend['day_of_week'] = daily_spend['date'].dt.weekday
        
        # We will train a model to predict cumulative monthly spending
        X_train = daily_spend[['day_of_month', 'day_of_week', 'day_index']]
        y_train = daily_spend['cumulative_spend']
        
        # Fit Ridge regression
        model = Ridge(alpha=1.0)
        model.fit(X_train, y_train)
        
        # Determine the last month in the historical data
        last_date = daily_spend['date'].max()
        
        # Build forecasting dates
        forecast_dates = pd.date_range(start=last_date + timedelta(days=1), periods=days_to_forecast, freq='D')
        
        forecast_rows = []
        for i, dt in enumerate(forecast_dates):
            day_idx = len(daily_spend) + i
            day_of_month = dt.day
            day_of_week = dt.weekday()
            
            # Predict the cumulative spending
            pred_cum = model.predict([[day_of_month, day_of_week, day_idx]])[0]
            
            # Bound cumulative spend to be positive and non-decreasing relative to month boundary
            # If day_of_month is 1, reset baseline.
            if day_of_month == 1:
                pred_cum = max(0.0, pred_cum)
            else:
                # Make sure it's at least as high as previous predicted day or 0
                prev_val = forecast_rows[-1]['amount'] if forecast_rows else daily_spend['cumulative_spend'].iloc[-1]
                if prev_val > 0 and dt.day != 1:
                    pred_cum = max(prev_val, pred_cum)
                else:
                    pred_cum = max(0.0, pred_cum)
            
            forecast_rows.append({
                "date": dt.strftime("%Y-%m-%d"),
                "amount": round(pred_cum, 2),
                "is_forecast": True
            })
            
        # Format historical data for output
        historical_rows = []
        # Filter down to the last 90 days to avoid cluttering charts
        hist_filtered = daily_spend.tail(90)
        for _, row in hist_filtered.iterrows():
            historical_rows.append({
                "date": row['date'].strftime("%Y-%m-%d"),
                "amount": round(row['cumulative_spend'], 2),
                "is_forecast": False
            })
            
        return historical_rows + forecast_rows

# Singleton instance of pipeline
ml_pipeline = FinancialMLPipeline()
