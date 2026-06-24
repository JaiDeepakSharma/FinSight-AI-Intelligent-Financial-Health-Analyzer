# FinSight AI — Intelligent Financial Health Analyzer

FinSight AI is a portfolio-grade, production-ready financial intelligence platform. It processes raw bank statements (PDF/CSV), automatically sanitizes and categorizes transaction lines using custom Scikit-learn text classifiers, flags anomalous activities (such as duplicate charges or spending spikes) using Isolation Forests, projects cumulative spending trends with Ridge Regression time-series forecasting, and implements an interactive Retrieval-Augmented Generation (RAG) Financial Advisor chatbot using ChromaDB and Google Gemini 2.5.

---

## Key Features

1. **Automated Spending Categorization**: A hybrid pipeline combining high-precision regex matching and a Scikit-learn `TF-IDF + Logistic Regression` text classifier. Retrains dynamically in the background when users override transaction categories in the UI.
2. **Anomalies Detection**: Multi-layered anomaly engine combining an `Isolation Forest` (outflow, day of week, day of month) with deterministic double-charge checks and standard-deviation Z-scores for smaller transaction histories.
3. **Budget Time-Series Forecasting**: Time-based `Ridge Regression` modeling cumulative monthly spending aggregates and projecting expenditure levels for the upcoming 30 days.
4. **RAG Conversational Chatbot**: Integrates ChromaDB (with local TF-IDF vector similarity search fallback) and the official `google-genai` SDK (`gemini-2.5-flash` and `text-embedding-004`) to generate contextually grounded financial advisory answers.
5. **Interactive Dashboard**: Reactive user dashboard built with React, Tailwind CSS, and Recharts displaying cash flow, allocations, forecasting limits, anomalies, and chat transcripts.
6. **Robust SQLite/PostgreSQL Database**: Built on SQLAlchemy to support SQLite for zero-configuration local development and PostgreSQL for production deployments.

---

## Project Structure

```
FinSight AI — Intelligent Financial Health Analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint
│   │   ├── config.py            # Environment & config
│   │   ├── database.py          # SQLAlchemy engine
│   │   ├── models.py            # Relational tables
│   │   ├── schemas.py           # Pydantic models
│   │   ├── routers/             # API Router endpoints
│   │   ├── services/            # Parsers, ML models, RAG configs
│   │   └── utils/               # JWT & bcrypt security
│   ├── tests/                   # Pytest automation suite
│   ├── .env.example
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/          # Auth, Chart details, Chat pane, Upload drops
│   │   ├── context/             # Auth JWT provider
│   │   ├── App.jsx              # Workspace router & state Sync
│   │   ├── index.css            # Tailwind directives
│   │   └── main.jsx             # React DOM binder
│   ├── package.json
│   ├── tailwind.config.js
│   ├── vite.config.js           # Proxies /api to 127.0.0.1:8000
│   └── Dockerfile
├── mock_bank_statement.csv      # Sample 3-month statement for quick uploads
├── docker-compose.yml
└── README.md
```

---

## Local Setup & Installation

### Prerequisite: API Key
Create a `.env` file inside the `backend/` directory (you can copy `backend/.env.example`).
To use the AI Chat Advisor, get a **free Gemini API Key** from Google AI Studio and place it in the `.env` file:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```
*Note: If no API key is specified, the application will still launch and perform all local parsing, ML classification, chart aggregates, and anomalies detections. The chatbot will gracefully operate in an offline warning demo mode, showing you local context matching.*

---

### Step 1: Run the Backend (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```
   The API docs will be active at `http://127.0.0.1:8000/docs`.

---

### Step 2: Run the Frontend (Vite + React)

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Launch the development server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

## Running with Docker

You can spin up both services containerized in one command:
```bash
docker-compose up --build
```
This mounts the backend on `http://localhost:8000` and the compiled React Nginx server on `http://localhost:5173`.

---

## Testing the Application

### 1. Automated Tests
To run the Pytest verification checks on the backend parser heuristics, security signatures, and ML boundaries:
```bash
cd backend
pytest
```

### 2. Manual Walkthrough
1. Open the application in the browser: `http://localhost:5173`
2. Register a new account (e.g. `user@example.com`, password `password123`) and log in.
3. Click on the **Upload zone** and select the [mock_bank_statement.csv](file:///c:/Users/HP/OneDrive/Desktop/FinSight%20AI%20%E2%80%94%20Intelligent%20Financial%20Health%20Analyzer/mock_bank_statement.csv) located in the project root.
4. **Observe the metrics**:
   * Total income vs. total spending display.
   * Two anomalies flagged: a double Starbucks coffee charge and a massive Apple Store purchase.
   * Category allocation pie chart showing allocations (Rent accounts for the majority, followed by Groceries, etc.).
   * The Area Chart shows your monthly income vs. spending.
   * The Forecast line shows historical spending transitioning into predicted cumulative June spending.
5. **Interact with the AI Advisor Chatbot**:
   * Try clicking on the suggested chips or type: *"Why did I overspend in May?"* or *"Where did most of my money go?"*
   * The RAG engine will fetch relevant transaction groups and answer using Gemini.
   * Citations will show up as interactive transaction cards.
6. **Override Categories**:
   * Try changing a transaction's category in the grid (e.g., reclassifying a Starbucks charge from `Food & Dining` to `Shopping`).
   * The backend will fine-tune the classifier, refresh the RAG chunking indexes, and update your dashboard in real-time.
