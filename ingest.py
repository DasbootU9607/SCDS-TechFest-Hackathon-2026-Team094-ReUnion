import os
import shutil
import logging
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from models import SessionLocal, Job, init_db, Base, engine
from data_source import DataSourceManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from config import config

def get_embeddings_model():
    """
    Returns the best available embedding model.
    Prioritizes OpenAI if key exists (more stable for demo), falls back to Ollama.
    """
    if config.API_KEY:
        logger.info("🧠 Using OpenAI Embeddings (API Key detected)")
        return OpenAIEmbeddings(model=config.EMBEDDING_MODEL_NAME, openai_api_key=config.API_KEY, openai_api_base=config.LLM_API_BASE)
    else:
        logger.info("🦙 Using Ollama Embeddings (nomic-embed-text)")
        return OllamaEmbeddings(model="nomic-embed-text")

def sync_all_data():
    """
    Full Sync: Official CSVs + Official PDF -> SQLite + ChromaDB
    """
    logger.info("🚀 Starting Data Ingestion Pipeline...")
    
    # 1. Reset Database (Ensure Schema Updates)
    if os.path.exists("career_aide.db"):
        os.remove("career_aide.db")
        logger.info("🗑️ Removed old SQLite database to apply new schema.")
    
    init_db()
    session = SessionLocal()
    manager = DataSourceManager()
    
    # 2. Clear old Vector DB
    if os.path.exists("./chroma_db_jobs"):
        shutil.rmtree("./chroma_db_jobs")
        logger.info("🗑️ Cleared old vector database.")

    all_jobs_buffer = []

    # 3. Load Official CSVs
    csv_files = [
        "efinancialcareers.csv", "glassdoor.csv", "indeed.csv", 
        "jobstreet.csv", "mycareersfuture.csv", "prosple.csv"
    ]
    
    for filename in csv_files:
        path = Path(f"./official_csv_data/{filename}")
        if path.exists():
            logger.info(f"📂 Loading: {filename}")
            jobs = manager.load_jobs_from_csv(filename)
            all_jobs_buffer.extend(jobs)
        else:
            logger.warning(f"⚠️ File not found: {filename}")

    # 4. Load Official PDF
    pdf_path = "./official_csv_data/Techfest Problem Statement.pdf"
    if os.path.exists(pdf_path):
        logger.info("📄 Parsing Official PDF Table...")
        pdf_jobs = manager.extract_from_official_pdf(pdf_path)
        all_jobs_buffer.extend(pdf_jobs)

    logger.info(f"∑ Total jobs collected: {len(all_jobs_buffer)}")

    # 5. Ingest into SQL and Chroma
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    docs_to_index = []

    for item in all_jobs_buffer:
        try:
            # SQL Record
            job_record = Job(
                external_id=item['id'],
                title=item['title'],
                company=item['company'],
                location=item['location'],
                salary_min=item['salary_min'],
                salary_max=item.get('salary_max', 0),
                description=item['description'],
                skills_required=item['skills'],
                application_status="New" # Default status
            )
            session.merge(job_record)

            # Vector Doc
            content = f"""Source: {item['source']}
Role: {item['title']} at {item['company']}
Details: {item['description']}
Skills: {', '.join(item['skills'])}"""
            
            chunks = text_splitter.split_text(content)
            for chunk in chunks:
                docs_to_index.append(Document(
                    page_content=chunk,
                    metadata={
                        "job_id": item['id'],
                        "source": item['source'],
                        "is_fresh": item['is_fresh_friendly']
                    }
                ))

        except Exception as e:
            continue

    session.commit()
    session.close()

    if docs_to_index:
        try:
            embeddings = get_embeddings_model()
            Chroma.from_documents(
                documents=docs_to_index,
                embedding=embeddings,
                persist_directory="./chroma_db_jobs"
            )
            logger.info(f"✅ Indexed {len(docs_to_index)} document chunks to ChromaDB.")
        except Exception as e:
            logger.error(f"❌ Vector embedding failed: {e}. Check if Ollama is running or API key is valid.")
    
    logger.info("🎉 Ingestion Complete!")

if __name__ == "__main__":
    sync_all_data()
