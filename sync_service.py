"""
数据同步服务 - 简化版本
"""
from data_source import DataSourceManager
from models import SessionLocal, Job, init_db
from langchain.docstore.document import Document as LangchainDocument
import logging
# 在顶部添加CSV支持
import pandas as pd
from pathlib import Path

# 在 DataSyncService 类的 sync_jobs 方法中添加CSV检查
def sync_jobs(self):
    """同步职位数据"""
    logger.info("=" * 50)
    logger.info("Starting job data synchronization...")
    logger.info("=" * 50)
    
    # 检查数据源
    csv_dir = Path("./official_csv_data")
    if csv_dir.exists():
        csv_files = list(csv_dir.glob("*.csv"))
        logger.info(f"Found {len(csv_files)} CSV files in official_csv_data directory")
    else:
        logger.warning("No official_csv_data directory found, using sample data")
    
    # 1. 获取职位数据
    try:
        jobs_data = self.data_manager.fetch_mcf_jobs()
        logger.info(f"✓ Fetched {len(jobs_data)} jobs from data source")
    except Exception as e:
        logger.error(f"✗ Failed to fetch jobs: {e}")
        return
    
    # 继续原有逻辑...
try:
    from langchain_chroma import Chroma
    from langchain_ollama import OllamaEmbeddings
except ImportError:
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import OllamaEmbeddings

logger = logging.getLogger(__name__)

class DataSyncService:
    """简化版数据同步服务，只同步职位数据"""
    
    def __init__(self):
        self.data_manager = DataSourceManager()
        self.db = SessionLocal()
        
        # 初始化向量数据库
        try:
            self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
            self.vector_db = Chroma(
                persist_directory="./chroma_db_jobs",
                embedding_function=self.embeddings
            )
        except Exception as e:
            logger.error(f"Vector DB init error: {e}")
            self.vector_db = None
    
    def sync_jobs(self):
        """同步职位数据"""
        logger.info("=" * 50)
        logger.info("Starting job data synchronization...")
        logger.info("=" * 50)
        
        # 1. 获取职位数据
        try:
            jobs_data = self.data_manager.fetch_mcf_jobs()
            logger.info(f"✓ Fetched {len(jobs_data)} jobs from data source")
        except Exception as e:
            logger.error(f"✗ Failed to fetch jobs: {e}")
            return
        
        # 2. 存入PostgreSQL
        sql_count = self._save_jobs_to_sql(jobs_data)
        logger.info(f"✓ Saved {sql_count} jobs to PostgreSQL")
        
        # 3. 存入向量数据库
        if self.vector_db:
            vector_count = self._save_jobs_to_vector_db(jobs_data)
            logger.info(f"✓ Indexed {vector_count} jobs in ChromaDB")
        
        logger.info("✅ Job synchronization completed!")
        return {"sql_count": sql_count, "vector_count": vector_count if self.vector_db else 0}
    
    def _save_jobs_to_sql(self, jobs_data: list) -> int:
        """保存到PostgreSQL数据库"""
        saved = 0
        errors = 0
        
        for job_data in jobs_data:
            try:
                # 检查是否已存在
                existing = self.db.query(Job).filter(
                    Job.external_id == job_data['id']
                ).first()
                
                if existing:
                    # 更新现有记录
                    existing.title = job_data['title']
                    existing.company = job_data['company']
                    existing.location = job_data['location']
                    existing.salary_min = job_data['salary_min']
                    existing.salary_max = job_data['salary_max']
                    existing.description = job_data['description']
                    existing.skills_required = job_data['skills']
                else:
                    # 创建新记录
                    job = Job(
                        external_id=job_data['id'],
                        title=job_data['title'],
                        company=job_data['company'],
                        location=job_data['location'],
                        salary_min=job_data['salary_min'],
                        salary_max=job_data['salary_max'],
                        description=job_data['description'],
                        skills_required=job_data['skills']
                    )
                    self.db.add(job)
                
                saved += 1
                
            except Exception as e:
                errors += 1
                logger.error(f"Error saving job {job_data.get('id')}: {e}")
        
        try:
            self.db.commit()
        except Exception as e:
            logger.error(f"Commit error: {e}")
            self.db.rollback()
            saved = 0
        
        if errors > 0:
            logger.warning(f"Encountered {errors} errors during SQL save")
        
        return saved
    
    def _save_jobs_to_vector_db(self, jobs_data: list) -> int:
        """保存到向量数据库"""
        if not self.vector_db:
            return 0
            
        documents = []
        
        for job_data in jobs_data:
            try:
                # 创建向量文档
                content = f"""
                职位: {job_data['title']}
                公司: {job_data['company']}
                地点: {job_data['location']}
                薪资: ${job_data['salary_min']} - ${job_data['salary_max']}
                描述: {job_data['description']}
                所需技能: {', '.join(job_data['skills'])}
                """
                
                doc = LangchainDocument(
                    page_content=content.strip(),
                    metadata={
                        'job_id': job_data['id'],
                        'title': job_data['title'],
                        'company': job_data['company'],
                        'location': job_data['location'],
                        'salary_min': job_data['salary_min']
                    }
                )
                documents.append(doc)
                
            except Exception as e:
                logger.error(f"Error creating vector doc: {e}")
        
        if documents:
            try:
                # 清除旧的向量数据（可选）
                # self.vector_db.delete_collection()
                
                # 添加新文档
                self.vector_db.add_documents(documents)
                logger.info(f"Added {len(documents)} documents to vector DB")
                return len(documents)
            except Exception as e:
                logger.error(f"Error adding to vector DB: {e}")
                return 0
        
        return 0
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'db'):
            self.db.close()

# 命令行接口
if __name__ == "__main__":
    import sys
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 初始化数据库
    init_db()
    
    # 执行同步
    sync_service = DataSyncService()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        print("Force syncing all jobs...")
    else:
        print("Syncing jobs...")
    
    result = sync_service.sync_jobs()
    
    if result:
        print(f"\n同步结果:")
        print(f"  - 保存到SQL: {result['sql_count']} 个职位")
        print(f"  - 索引到向量库: {result.get('vector_count', 0)} 个职位")
    else:
        print("同步失败，请检查日志")