import logging
import os
import uuid
import numpy as np
from typing import List, Dict, Any, Tuple
from app.config import settings

# Configure logger
logger = logging.getLogger("finsight.rag")
logging.basicConfig(level=logging.INFO)

# --- RESILIENT CHROMADB IMPORT ---
CHROMADB_AVAILABLE = False
chroma_client = None

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    # Persistent SQLite-based ChromaDB storage
    chroma_client = chromadb.PersistentClient(path="./finsight_chroma")
    CHROMADB_AVAILABLE = True
    logger.info("ChromaDB initialized successfully.")
except Exception as e:
    logger.warning(f"Failed to load ChromaDB ({e}). Falling back to Scikit-learn + NumPy vector store.")
    CHROMADB_AVAILABLE = False


# --- RESILIENT GEMINI IMPORT & CLIENT SETUP ---
GEMINI_AVAILABLE = False
genai_client = None

if settings.GEMINI_API_KEY:
    try:
        from google import genai
        # Initialize Google GenAI client
        genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
        logger.info("Google GenAI client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Google GenAI SDK ({e}). Check your GEMINI_API_KEY.")
        GEMINI_AVAILABLE = False
else:
    logger.warning("GEMINI_API_KEY not found in settings. AI Chat Advisor will run in offline demo mode.")


# --- FALLBACK IN-MEMORY VECTOR STORE ---
# To make this application resilient, if ChromaDB fails, we store chunks in memory 
# and use Scikit-learn TF-IDF Vectorizer + Cosine Similarity to find relevant texts.
class FallbackVectorStore:
    def __init__(self):
        self.db: Dict[int, List[Dict[str, Any]]] = {}  # Map user_id -> List of chunks: {"id": str, "text": str, "metadata": dict}
        
    def clear_user_docs(self, user_id: int):
        self.db[user_id] = []
        
    def add_documents(self, user_id: int, texts: List[str], metadatas: List[Dict[str, Any]]):
        if user_id not in self.db:
            self.db[user_id] = []
        for text, meta in zip(texts, metadatas):
            self.db[user_id].append({
                "id": str(uuid.uuid4()),
                "text": text,
                "metadata": meta
            })
            
    def similarity_search(self, user_id: int, query: str, k: int = 5) -> List[Dict[str, Any]]:
        user_chunks = self.db.get(user_id, [])
        if not user_chunks:
            return []
            
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        texts = [chunk["text"] for chunk in user_chunks]
        
        try:
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
            tfidf_matrix = vectorizer.fit_transform(texts)
            query_vec = vectorizer.transform([query])
            
            similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
            top_indices = np.argsort(similarities)[::-1][:k]
            
            results = []
            for idx in top_indices:
                # Only return results that have some overlap / similarity
                if similarities[idx] >= 0.0:
                    results.append(user_chunks[idx])
            return results
        except Exception as e:
            logger.error(f"Error in fallback similarity search: {e}")
            # simple keyword match fallback
            query_words = set(query.lower().split())
            scores = []
            for chunk in user_chunks:
                text_words = set(chunk["text"].lower().split())
                overlap = len(query_words.intersection(text_words))
                scores.append(overlap)
            
            top_indices = np.argsort(scores)[::-1][:k]
            return [user_chunks[idx] for idx in top_indices if scores[idx] > 0]

fallback_vector_store = FallbackVectorStore()


class FinancialRAGService:
    @staticmethod
    def get_embeddings(texts: List[str]) -> List[List[float]]:
        """Fetch embeddings for a list of texts using text-embedding-004."""
        if not GEMINI_AVAILABLE or not genai_client:
            return [[0.0] * 768 for _ in texts] # mock zero vector
            
        try:
            embeddings = []
            for text in texts:
                response = genai_client.models.embed_content(
                    model="text-embedding-004",
                    contents=text
                )
                embeddings.append(response.embeddings[0].values)
            return embeddings
        except Exception as e:
            logger.error(f"Error fetching Gemini embeddings: {e}")
            return [[0.0] * 768 for _ in texts]

    @staticmethod
    def build_chunks(user_id: int, transactions: List[Dict[str, Any]], analytics_data: Dict[str, Any]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Converts raw transactions and spending aggregates into structured chunks for RAG."""
        chunks = []
        metadatas = []
        
        # 1. Individual Transaction Chunks (capped to last 150 for storage sizes)
        # Sort transactions by date descending
        sorted_txs = sorted(transactions, key=lambda x: x['date'], reverse=True)
        for tx in sorted_txs[:150]:
            amount_str = f"${abs(tx['amount']):.2f} Credit" if tx['amount'] >= 0 else f"${abs(tx['amount']):.2f} Debit"
            balance_str = f" resulting in a ledger balance of ${tx['balance']:.2f}" if tx.get('balance') else ""
            
            chunk = (
                f"On {tx['date'].strftime('%Y-%m-%d')}, a transaction of {amount_str} was processed "
                f"at '{tx['description']}'. The system categorized this transaction under '{tx['category']}'{balance_str}."
            )
            chunks.append(chunk)
            metadatas.append({
                "user_id": user_id,
                "type": "transaction",
                "date": tx['date'].strftime('%Y-%m-%d'),
                "id": tx.get('id', 0)
            })
            
        # 2. Monthly Spend Analytics Summaries
        for trend in analytics_data.get("monthly_trends", []):
            month = trend.get("month")
            spending = trend.get("spending", 0.0)
            income = trend.get("income", 0.0)
            net = income - spending
            
            chunk = (
                f"In the month of {month}, total income was ${income:,.2f} and total spending was ${spending:,.2f}, "
                f"resulting in net savings of ${net:,.2f}."
            )
            chunks.append(chunk)
            metadatas.append({
                "user_id": user_id,
                "type": "monthly_summary",
                "month": month
            })
            
        # 3. Category Distribution Summaries
        cats_breakdown = ", ".join([
            f"{c['category']}: ${c['amount']:,.2f} ({c['percentage']:.1f}%)"
            for c in analytics_data.get("spend_by_category", [])
        ])
        if cats_breakdown:
            chunk = f"The historical spending breakdown across all transactions by category is: {cats_breakdown}."
            chunks.append(chunk)
            metadatas.append({
                "user_id": user_id,
                "type": "category_breakdown"
            })
            
        # 4. Flagged Anomalies Chunks
        anomalies = [tx for tx in transactions if tx.get("is_anomaly")]
        if anomalies:
            list_str = "; ".join([
                f"On {a['date'].strftime('%Y-%m-%d')}, a transaction at '{a['description']}' for ${abs(a['amount']):.2f} was flagged. Reason: {a.get('anomaly_reason')}"
                for a in anomalies
            ])
            chunk = f"The system has identified the following anomalies in your financial history: {list_str}."
            chunks.append(chunk)
            metadatas.append({
                "user_id": user_id,
                "type": "anomalies"
            })
        else:
            chunk = "No financial anomalies or duplicate charges were detected in your financial history."
            chunks.append(chunk)
            metadatas.append({
                "user_id": user_id,
                "type": "anomalies"
            })
            
        # 5. Future Forecasting Chunks
        forecasts = [f for f in analytics_data.get("forecast", []) if f.get("is_forecast")]
        if forecasts:
            final_pred = forecasts[-1].get("amount", 0.0)
            chunk = (
                f"AI Financial forecasting models project cumulative spending to reach "
                f"${final_pred:,.2f} at the end of the next 30 days."
            )
            chunks.append(chunk)
            metadatas.append({
                "user_id": user_id,
                "type": "forecasting"
            })
            
        return chunks, metadatas

    @classmethod
    def index_financial_data(cls, user_id: int, transactions: List[Dict[str, Any]], analytics_data: Dict[str, Any]):
        """Generates embedding chunks and indexes them into ChromaDB or the local fallback store."""
        chunks, metadatas = cls.build_chunks(user_id, transactions, analytics_data)
        if not chunks:
            return
            
        # Write to Fallback store (always updated for safety)
        fallback_vector_store.clear_user_docs(user_id)
        fallback_vector_store.add_documents(user_id, chunks, metadatas)
        
        # Write to ChromaDB if available
        if CHROMADB_AVAILABLE and chroma_client:
            try:
                # Access or create collection
                collection_name = f"user_{user_id}_financials"
                
                # Delete existing collection to refresh
                try:
                    chroma_client.delete_collection(collection_name)
                except Exception:
                    pass
                
                collection = chroma_client.create_collection(name=collection_name)
                
                # Generate embeddings using Gemini API
                embeddings = cls.get_embeddings(chunks)
                
                # Insert documents into Chroma
                ids = [str(uuid.uuid4()) for _ in chunks]
                collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=chunks,
                    metadatas=metadatas
                )
                logger.info(f"Successfully indexed {len(chunks)} chunks into ChromaDB for user {user_id}.")
            except Exception as e:
                logger.error(f"Error writing to ChromaDB ({e}). Relying solely on TF-IDF fallback store.")

    @classmethod
    def retrieve_context(cls, user_id: int, query: str, k: int = 5) -> List[str]:
        """Retrieves the most contextually relevant chunks matching the query."""
        # Check if ChromaDB is active and has the user collection
        if CHROMADB_AVAILABLE and chroma_client:
            try:
                collection_name = f"user_{user_id}_financials"
                collection = chroma_client.get_collection(name=collection_name)
                
                # Get embeddings for query
                query_embeddings = cls.get_embeddings([query])
                
                results = collection.query(
                    query_embeddings=query_embeddings,
                    n_results=k
                )
                if results and 'documents' in results and results['documents']:
                    flat_docs = [doc for sublist in results['documents'] for doc in sublist]
                    if flat_docs:
                        return flat_docs
            except Exception as e:
                logger.error(f"Failed to query ChromaDB collection ({e}). Falling back to TF-IDF vector search.")

        # Fallback to Scikit-learn search
        results = fallback_vector_store.similarity_search(user_id, query, k)
        return [item["text"] for item in results]

    @classmethod
    def answer_query(cls, user_id: int, query: str) -> str:
        """Answers financial queries using RAG context and Gemini 2.5 Flash."""
        # 1. API Key Check
        if not GEMINI_AVAILABLE or not genai_client:
            # Informative error message with local fallback summary
            context_chunks = cls.retrieve_context(user_id, query, k=3)
            context_summary = "\n- ".join(context_chunks) if context_chunks else "No transaction data available."
            
            return (
                "⚠️ **Gemini API Key Missing:**\n"
                "To enable smart conversational answers, please add your Google Gemini API key to the "
                "`GEMINI_API_KEY` parameter in `backend/.env`.\n\n"
                "**Local Analysis (Offline Mode):**\n"
                "I retrieved the following relevant records from your statement files:\n\n"
                f"- {context_summary}\n\n"
                "*Tip: Once the Gemini API key is configured, I will be able to synthesize these details "
                "into fully-grounded explanations, answer budgeting questions, and compute custom charts!*"
            )

        # 2. Retrieve context
        context_docs = cls.retrieve_context(user_id, query, k=8)
        context_str = "\n".join([f"- {doc}" for doc in context_docs])
        
        # 3. Formulate Prompt
        prompt = (
            "You are FinSight AI, a highly skilled and professional AI Financial Advisor. "
            "Your goal is to answer the user's question regarding their personal financial transaction history. "
            "You MUST use only the provided context blocks extracted from their uploaded bank statements "
            "to answer their question. Be precise, refer to exact dates, amounts, and descriptions. "
            "If the information is not present in the context, state that you do not have that transaction data.\n\n"
            "Here is the context representing the user's financial statement details:\n"
            "---------------------\n"
            f"{context_str}\n"
            "---------------------\n\n"
            f"User's Question: {query}\n\n"
            "Answer the question in a clear, concise format using clean Markdown. Focus on actionable insights."
        )
        
        try:
            # Call Gemini 2.5 Flash using the new client syntax
            response = genai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Error querying Gemini model: {e}")
            return f"Error: Failed to process query using Gemini LLM ({e}). Please check your API key and connection."
