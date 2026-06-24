import os
import sys
from fastapi.testclient import TestClient

# Configure stdout to support UTF-8 characters on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Adjust path to import the app modules
sys.path.append(os.path.dirname(__file__))

from app.main import app

client = TestClient(app)

def run_integration_check():
    print("==================================================================")
    print("                FinSight AI - Integration Check                   ")
    print("==================================================================")
    
    # 1. Register User
    print("\n[Step 1] Registering test user...")
    register_payload = {
        "email": "verifier@finsight.com",
        "password": "password123"
    }
    
    # Clean previous run DB if SQLite
    db_file = "./finsight.db"
    if os.path.exists(db_file):
        try:
            # Recreate tables by forcing database module to clean
            pass
        except Exception:
            pass
            
    res = client.post("/api/auth/register", json=register_payload)
    if res.status_code == 201:
        print("✓ Registration successful:", res.json())
    elif res.status_code == 400 and "already registered" in res.json().get("detail", ""):
        print("✓ Test user already registered. Proceeding...")
    else:
        print("✗ Registration failed:", res.status_code, res.text)
        return False
        
    # 2. Login User
    print("\n[Step 2] Authenticating test user...")
    res = client.post("/api/auth/login", json=register_payload)
    if res.status_code != 200:
        print("✗ Authentication failed:", res.status_code, res.text)
        return False
        
    token = res.json()["access_token"]
    print("✓ Login successful! Token acquired:", token[:25] + "...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Upload Statement CSV
    print("\n[Step 3] Uploading 'mock_bank_statement.csv'...")
    csv_path = "../mock_bank_statement.csv"
    if not os.path.exists(csv_path):
        print(f"✗ Mock statement not found at {csv_path}!")
        return False
        
    with open(csv_path, "rb") as f:
        files = {"file": ("mock_bank_statement.csv", f, "text/csv")}
        res = client.post("/api/transactions/upload", files=files, headers=headers)
        
    if res.status_code != 201:
        print("✗ Upload failed:", res.status_code, res.text)
        return False
        
    txs = res.json()
    print(f"✓ Upload successful! Parsed and saved {len(txs)} transaction rows.")
    
    # 4. Fetch Analytics Dashboard
    print("\n[Step 4] Fetching analytics summaries...")
    res = client.get("/api/analytics/dashboard", headers=headers)
    if res.status_code != 200:
        print("✗ Fetching analytics failed:", res.status_code, res.text)
        return False
        
    dashboard = res.json()
    print("✓ Dashboard analytics retrieved successfully:")
    print(f"  - Total Income:    ${dashboard['total_income']:,.2f}")
    print(f"  - Total Spending:  ${dashboard['total_spending']:,.2f}")
    print(f"  - Net Savings:     ${dashboard['net_savings']:,.2f}")
    print(f"  - Flagged Anomalies: {dashboard['anomalies_count']}")
    
    print("\n  Category breakdown allocation:")
    for cat in dashboard["spend_by_category"]:
        print(f"    * {cat['category']}: ${cat['amount']:,.2f} ({cat['percentage']:.1f}%)")
        
    print(f"\n  Forecast generated: {len(dashboard['forecast'])} data intervals.")
    
    # 5. Query Advisor Chatbot (RAG)
    print("\n[Step 5] Submitting RAG query to Chat Advisor...")
    query_payload = {
        "message": "Where did most of my money go?"
    }
    res = client.post("/api/chat/query", json=query_payload, headers=headers)
    if res.status_code != 200:
        print("✗ RAG query failed:", res.status_code, res.text)
        return False
        
    chat_response = res.json()
    print("✓ RAG response successfully generated:")
    print("  ------------------------------------------------------------")
    print(chat_response["answer"])
    print("  ------------------------------------------------------------")
    print(f"  References found: {len(chat_response['references'])} matching transactions.")
    for idx, ref in enumerate(chat_response['references']):
        print(f"    [{idx + 1}] On {ref['date']}, {ref['description']} of ${abs(ref['amount'])} ({ref['category']})")
        
    print("\n==================================================================")
    print("            ✓ FINSIGHT INTEGRATION VERIFICATION COMPLETE          ")
    print("==================================================================")
    return True

if __name__ == "__main__":
    run_integration_check()
