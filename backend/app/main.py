from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, upload, analytics, chat

# Initialize database tables on application start
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FinSight AI — Intelligent Financial Health Analyzer",
    description="Backend API powered by FastAPI, Scikit-learn, and Gemini RAG.",
    version="1.0.0"
)

# Set up CORS middleware for React frontend connection
# Allows localhost dev ports (5173, 3000) or any other origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(analytics.router)
app.include_router(chat.router)

import os

# Resolve dist directory
dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dist"))

# Serve frontend SPA if dist folder exists
if os.path.exists(dist_dir):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

    @app.get("/favicon.svg")
    def serve_favicon():
        return FileResponse(os.path.join(dist_dir, "favicon.svg"))

    @app.get("/icons.svg")
    def serve_icons():
        return FileResponse(os.path.join(dist_dir, "icons.svg"))

    @app.get("/api/health")
    def health_check():
        return {"status": "healthy"}

    @app.get("/{catchall:path}")
    def serve_spa(catchall: str):
        if catchall.startswith("api/") or catchall.startswith("docs") or catchall.startswith("redoc") or catchall.startswith("openapi.json"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="API endpoint not found")
        return FileResponse(os.path.join(dist_dir, "index.html"))
else:
    @app.get("/")
    def read_root():
        return {
            "status": "online",
            "message": "FinSight AI API is running (development mode). Build the frontend to serve the app here.",
            "docs_url": "/docs"
        }

    @app.get("/api/health")
    def health_check():
        return {"status": "healthy"}
