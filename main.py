#!/usr/bin/env python3
"""
Career AIDE Main Program (Backend Core) - Final Enhanced Version
Integrates startup checks, multi-source data sync interface, and FastAPI routes.
"""
import sys
import logging
import uvicorn
import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import Core Modules
from models import init_db, SessionLocal, UserProfile, Job
from agents import CareerAIDEAgents
from ingest import sync_all_data  # Ensure your ingest.py is updated to the multi-source sync version
from config import config

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('career_aide.log')
    ]
)
logger = logging.getLogger(__name__)

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Career AIDE API",
    description="Backend for Techfest Hackathon - AI Career Assistant (Integrated Data Sources)",
    version="2.3.0" 
)

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Agent Instance
career_agent = None

# --- Data Model Definitions ---
class RoadmapRequest(BaseModel):
    user_id: str
    query: str
    location: Optional[str] = "Singapore"
    salary_min: Optional[int] = 3000

class ChatRequest(BaseModel):
    user_id: str
    message: str
    context: Optional[str] = None

# --- Startup Events ---
@app.on_event("startup")
async def startup_event():
    """Initialization logic executed on service startup"""
    global career_agent
    logger.info("🚀 Starting Career AIDE Backend...")
    
    # 1. Check Environment Variables (Strict Check)
    if not config.API_KEY:
        logger.error("API KEY missing!")
        print("\n❌ CRITICAL: DEEPSEEK_API_KEY OR OPENAI_API_KEY IS MISSING IN .ENV\n")
        # Ensure agent can handle empty key if not forcing exit during demo

    # 2. Initialize Database
    init_db()
    
    # 3. Auto-detect Data State (Demo Mode)
    db = SessionLocal()
    job_count = db.query(Job).count()
    db.close()
    
    if job_count == 0:
        logger.warning("Database is empty. Triggering auto-ingest for official CSV/PDF data...")
        try:
            sync_all_data() # Execute multi-source sync
            logger.info("Auto-ingest completed successfully.")
        except Exception as e:
            logger.error(f"Auto-ingest failed: {e}")

    # 4. Initialize AI Agent
    try:
        career_agent = CareerAIDEAgents()
        logger.info("🤖 AI Agent (DeepSeek) initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to init Agent: {e}")

@app.get("/")
async def root():
    return {"status": "online", "message": "Career AIDE Backend is ready for Techfest!"}

# --- Core API Routes ---

@app.post("/api/sync")
async def manual_sync():
    """
    Manual Trigger Interface: Allows Streamlit Frontend to re-scan CSV folders and PDF.
    """
    logger.info("Manual sync triggered from Admin UI.")
    try:
        sync_all_data()
        return {"status": "success", "message": "Official CSVs and PDF data re-indexed."}
    except Exception as e:
        logger.error(f"Manual sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/roadmap")
async def generate_roadmap(request: RoadmapRequest):
    """Core interface for generating career roadmaps"""
    if not career_agent:
        raise HTTPException(status_code=503, detail="AI Agent not initialized")
    
    logger.info(f"Generating roadmap for user: {request.user_id}, query: {request.query}")
    try:
        filters = {"salary": request.salary_min, "location": request.location}
        result = career_agent.get_career_roadmap(request.user_id, request.query, filters)
        return result
    except Exception as e:
        logger.error(f"Error in roadmap generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Intelligent Q&A Interface"""
    if not career_agent:
        raise HTTPException(status_code=503, detail="AI Agent not initialized")
    
    response = career_agent.chat_response(request.user_id, request.message, request.context)
    return {"response": response}

@app.get("/api/jobs/stats")
async def get_job_stats():
    """Improved Statistics Interface: Reflects data source diversity (Hackathon Highlight)"""
    session = SessionLocal()
    try:
        total_jobs = session.query(Job).count()
        # Count entry-level positions
        entry_level = session.query(Job).filter(Job.description.ilike("%fresh%")).count()
        return {
            "total_jobs_indexed": total_jobs,
            "entry_level_opportunities": entry_level,
            "data_sources": [
                "Government CSV Datasets (6 sources)", 
                "Techfest Official PDF (Table Extraction)", 
                "Live MCF API"
            ],
            "status": "Centralized Knowledge Base Ready"
        }
    finally:
        session.close()

# --- Main Entry Point ---
if __name__ == "__main__":
    print_banner = """
    ╔════════════════════════════════════════════════╗
    ║      🚀 Career AIDE Backend (FastAPI)          ║
    ║      Integrated with Official Data Sources     ║
    ║      Powered by DeepSeek & RAG Engine          ║
    ╚════════════════════════════════════════════════╝
    """
    print(print_banner)
    uvicorn.run(app, host="0.0.0.0", port=8000)
