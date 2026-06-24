import io
import re
import pandas as pd
import pypdf
from datetime import datetime, date
from typing import List, Dict, Any, Tuple

# Supported date formats to try
DATE_FORMATS = [
    "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y", "%d/%m/%y",
    "%Y/%m/%d", "%d-%b-%Y", "%d-%b-%y", "%b %d, %Y", "%d %b %Y"
]

def clean_amount(val: Any) -> float:
    """Helper to convert string/numeric amounts to standard float."""
    if pd.isna(val) or val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    
    # Remove currency symbols, commas, and whitespace
    clean_str = re.sub(r'[^\d\.\-\+]', '', str(val).strip())
    if not clean_str:
        return 0.0
    try:
        return float(clean_str)
    except ValueError:
        return 0.0

def parse_date(date_str: str) -> date:
    """Helper to parse a date string into a datetime.date object."""
    date_str = date_str.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    # Fallback to current date if parsing fails
    try:
        return pd.to_datetime(date_str).date()
    except Exception:
        return date.today()

class BankStatementParser:
    @staticmethod
    def parse_csv(file_bytes: bytes) -> List[Dict[str, Any]]:
        """Parses a bank statement CSV and returns a list of transaction dicts."""
        # Read CSV file using pandas
        df = pd.read_csv(io.BytesIO(file_bytes))
        
        # Lowercase column names for uniform matching
        orig_cols = list(df.columns)
        cols = [str(c).lower().strip() for c in orig_cols]
        
        # Heuristic mapping for standard columns
        date_col = None
        desc_col = None
        amount_col = None
        debit_col = None
        credit_col = None
        balance_col = None
        
        for idx, col in enumerate(cols):
            if any(k in col for k in ["date", "trans_date", "transaction_date"]):
                date_col = orig_cols[idx]
            elif any(k in col for k in ["desc", "description", "detail", "payee", "memo"]):
                desc_col = orig_cols[idx]
            elif any(k in col for k in ["debit", "withdrawal", "charge", "spent"]):
                debit_col = orig_cols[idx]
            elif any(k in col for k in ["credit", "deposit", "payment", "received"]):
                credit_col = orig_cols[idx]
            elif any(k in col for k in ["amount", "value", "sum"]):
                amount_col = orig_cols[idx]
            elif any(k in col for k in ["balance", "bal", "ledger"]):
                balance_col = orig_cols[idx]
        
        # Basic validation: We need a Date and a Description at minimum
        if not date_col:
            # Fallback to first column as Date
            date_col = orig_cols[0]
        if not desc_col:
            # Fallback to second column as Description if available
            desc_col = orig_cols[1] if len(orig_cols) > 1 else orig_cols[0]
            
        transactions = []
        for _, row in df.iterrows():
            row_date_val = row.get(date_col)
            row_desc_val = row.get(desc_col)
            
            if pd.isna(row_date_val) or pd.isna(row_desc_val):
                continue
                
            tx_date = parse_date(str(row_date_val))
            tx_desc = str(row_desc_val).strip()
            
            # Resolve amount:
            # 1. If we have debit and credit columns
            # 2. Else if we have amount column
            tx_amount = 0.0
            if debit_col and credit_col:
                deb = clean_amount(row.get(debit_col))
                cred = clean_amount(row.get(credit_col))
                # debits are negative, credits are positive
                if deb != 0:
                    # if debit is already written as negative, preserve it. Else negate it.
                    tx_amount = deb if deb < 0 else -deb
                elif cred != 0:
                    tx_amount = cred
            elif amount_col:
                tx_amount = clean_amount(row.get(amount_col))
            else:
                # Fallback search if no clear columns were mapped
                # Look for columns that contain numerical entries
                for col in orig_cols:
                    if col in [date_col, desc_col]:
                        continue
                    val = row.get(col)
                    if isinstance(val, (int, float)) and not pd.isna(val):
                        tx_amount = float(val)
                        break
            
            tx_balance = None
            if balance_col:
                tx_balance = clean_amount(row.get(balance_col))
                
            transactions.append({
                "date": tx_date,
                "description": tx_desc,
                "amount": tx_amount,
                "balance": tx_balance
            })
            
        return transactions

    @staticmethod
    def parse_pdf(file_bytes: bytes) -> List[Dict[str, Any]]:
        """Extracts transactions from a bank statement PDF using text extraction and regex matching."""
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text_content = []
        
        # Read text from all pages
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content.append(page_text)
                
        full_text = "\n".join(text_content)
        lines = full_text.split("\n")
        
        transactions = []
        
        # Regex patterns to detect transactions
        # E.g., Matches: "04/12/2026 Starbucks -12.50" or "12-Apr-2026 Gas Station 45.00 1205.21"
        # Match standard date format + description + amount + optional balance
        pattern = re.compile(
            # Date (e.g. 12/04/2026, 2026-04-12, 12-Apr-2026)
            r'^(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}|\d{2}-\d{2}-\d{4}|\d{2}\s[a-zA-Z]{3}\s\d{2,4})\s+' 
            # Description (letters, spaces, typical characters up to amount)
            r'([a-zA-Z0-9\s\*\#\.\,\-\/]+?)\s+'
            # Amount: Optional minus/plus, optional dollar sign, numbers, optional comma, dot, cents
            r'([\-\+]?\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})|[\-\+]?\$?\d+\.\d{2})'
            # Optional Balance: optional dollar sign, numbers, optional comma, dot, cents
            r'(?:\s+([\-\+]?\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})|[\-\+]?\$?\d+\.\d{2}))?$'
        )

        for line in lines:
            line = line.strip()
            match = pattern.match(line)
            if match:
                date_str, desc, amount_str, balance_str = match.groups()
                
                tx_date = parse_date(date_str)
                tx_desc = desc.strip()
                tx_amount = clean_amount(amount_str)
                tx_balance = clean_amount(balance_str) if balance_str else None
                
                # Check for standard transaction characteristics
                if tx_desc and tx_amount != 0:
                    transactions.append({
                        "date": tx_date,
                        "description": tx_desc,
                        "amount": tx_amount,
                        "balance": tx_balance
                    })
        
        # Fallback PDF parsing if regex fails to match structured lines
        # Sometimes PDF tables are extracted with columns split across pages or text misaligned
        if len(transactions) == 0:
            # Let's do a weaker line parsing: look for lines that contain a date and a monetary value
            date_regex = re.compile(r'(\d{2}/\d{2}/\d{2,4}|\d{4}-\d{2}-\d{2}|\d{2}-[A-Za-z]{3}-\d{2,4})')
            amount_regex = re.compile(r'(\-?\$?\d+\.\d{2})')
            
            for line in lines:
                line = line.strip()
                d_match = date_regex.search(line)
                a_matches = amount_regex.findall(line)
                
                if d_match and a_matches:
                    # The date is the matched substring
                    date_str = d_match.group(0)
                    tx_date = parse_date(date_str)
                    
                    # Assume the last amount is the balance (if multiple matches) or the amount
                    # Let's say: if there is 1 amount, it's transaction amount. If 2, first is transaction, second is balance.
                    if len(a_matches) >= 2:
                        tx_amount = clean_amount(a_matches[0])
                        tx_balance = clean_amount(a_matches[1])
                    else:
                        tx_amount = clean_amount(a_matches[0])
                        tx_balance = None
                        
                    # The description is the line with date and amounts removed
                    desc = line.replace(date_str, "").strip()
                    for amt in a_matches:
                        desc = desc.replace(amt, "").strip()
                    
                    # Clean up remaining whitespace and common table separators
                    desc = re.sub(r'\s+', ' ', desc).strip()
                    
                    if desc and tx_amount != 0:
                        transactions.append({
                            "date": tx_date,
                            "description": desc,
                            "amount": tx_amount,
                            "balance": tx_balance
                        })
                        
        return transactions
