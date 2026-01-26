import logging
from sqlalchemy import and_
from models import SessionLocal, Job

try:
    from langchain_chroma import Chroma
    from langchain_ollama import OllamaEmbeddings
    from langchain_core.documents import Document
except ImportError:
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import OllamaEmbeddings


logger = logging.getLogger(__name__)

import os
from langchain_openai import OpenAIEmbeddings
from config import config

class JobSearchEngine:
    def __init__(self):
        try:
            if config.API_KEY:
                self.embeddings = OpenAIEmbeddings(
                    model=config.EMBEDDING_MODEL_NAME, 
                    openai_api_key=config.API_KEY,
                    openai_api_base=config.LLM_API_BASE
                )
            else:
                self.embeddings = OllamaEmbeddings(
                    model="nomic-embed-text",
                    base_url="http://localhost:11434"
                )
            
            self.vector_db = Chroma(
                persist_directory="./chroma_db_jobs",
                embedding_function=self.embeddings
            )
            logger.info("Vector DB initialized successfully")
        except Exception as e:
            logger.warning(f"Vector DB initialization failed: {e}")
            self.vector_db = None

    def search(self, min_salary: float = 0, location: str = None, query: str = "", limit: int = 5):
        """
        Hybrid Search: SQL Hard Filter + Vector Semantic Search
        """
        session = SessionLocal()
        try:
            # Step 1: SQL Pre-filtering for Hard Constraints
            filters = [Job.salary_min >= min_salary]
            if location:
                filters.append(Job.location.ilike(f"%{location}%"))
            
            sql_results = session.query(Job).filter(and_(*filters)).all()
            
            if not sql_results:
                return []
            
            valid_ids = [j.external_id for j in sql_results]

            # Step 2: Semantic Search
            if not self.vector_db or not query:
                return self._convert_jobs_to_documents(sql_results[:limit])

            # Use Chroma's where clause for efficient filtering (if vector store supports ID filtering)
            # Note: Depends on metadata structure during ingestion
            results = self.vector_db.similarity_search(
                query, 
                k=limit * 3 # Expand sampling to account for filtering loss
            )

            # Step 3: Cross-validation and Metadata Enrichment
            # Only return jobs present in SQL results
            filtered_docs = []
            for doc in results:
                jid = doc.metadata.get("job_id")
                if jid in valid_ids:
                    # Enrich missing metadata to ensure Agent gets full info
                    job_obj = next((j for j in sql_results if j.external_id == jid), None)
                    if job_obj:
                        doc.metadata.update({
                            'salary_max': job_obj.salary_max,
                            'skills': job_obj.skills_required,
                            'is_entry': 'No exp required' in (job_obj.description or "")
                        })
                    filtered_docs.append(doc)
                
                if len(filtered_docs) >= limit:
                    break
            
            return filtered_docs if filtered_docs else self._convert_jobs_to_documents(sql_results[:limit])

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
        finally:
            session.close()

    def _convert_jobs_to_documents(self, jobs):
        """Convert database models to standard LangChain Document format"""
        documents = []
        for job in jobs:
            # Enhance content description to help LLM better understand the job
            content = (
                f"Company: {job.company}\n"
                f"Title: {job.title}\n"
                f"Location: {job.location}\n"
                f"Salary Range: ${job.salary_min} - ${job.salary_max}\n"
                f"Required Skills: {', '.join(job.skills_required) if job.skills_required else 'Not specified'}\n"
                f"Description: {job.description[:500]}..." # Limit length to prevent Token overflow
            )
            
            doc = Document(
                page_content=content,
                metadata={
                    'job_id': job.external_id,
                    'title': job.title,
                    'company': job.company,
                    'salary_min': job.salary_min,
                    'is_fresh_friendly': True if (job.salary_min and job.salary_min < 5000) else False 
                }
            )
            documents.append(doc)
        return documents
