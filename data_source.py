import pandas as pd
import pdfplumber
import os
import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class DataSourceManager:
    def __init__(self, csv_directory: str = "./official_csv_data"):
        self.csv_directory = csv_directory

    def _clean_salary_string(self, salary_str: str) -> float:
        """从各种格式提取最高薪资用于排序"""
        if pd.isna(salary_str) or str(salary_str).lower() in ['not specified', 'nan', '']:
            return 0.0
        s = str(salary_str).lower().replace(',', '')
        numbers = re.findall(r'(\d+\.?\d*)', s)
        if not numbers:
            return 0.0
        # 取最大值作为参考
        val = max([float(n) for n in numbers])
        if 'k' in s: val *= 1000
        # 如果是年薪(通常>20k)，转月薪
        if val > 20000: val /= 12
        return round(val, 2)

    def _get_value(self, row, possible_columns):
        """尝试从多个可能的列名中获取值"""
        for col in possible_columns:
            # 忽略大小写匹配
            keys = [k for k in row.keys() if k.lower() == col.lower()]
            if keys:
                val = row[keys[0]]
                return str(val) if pd.notna(val) else "Not Specified"
        return "Not Specified"

    def load_jobs_from_csv(self, csv_file: str) -> List[Dict]:
        """读取官方 CSV 文件"""
        jobs = []
        file_path = os.path.join(self.csv_directory, csv_file)
        
        try:
            # 处理编码问题
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='ISO-8859-1')

            logger.info(f"Processing {csv_file} with columns: {list(df.columns)}")

            for idx, row in df.iterrows():
                # 智能列名匹配
                title = self._get_value(row, ['title', 'job title', 'role', 'position'])
                company = self._get_value(row, ['company', 'company name', 'employer'])
                desc = self._get_value(row, ['description', 'job description', 'summary'])
                salary = self._get_value(row, ['salary', 'salary range', 'min_salary'])
                skills = self._get_value(row, ['skills', 'tech stack', 'requirements'])

                # 识别应届生友好度
                is_fresh = any(k in (desc + title).lower() for k in ['fresh', 'graduate', 'entry', 'junior', 'no experience'])

                jobs.append({
                    "id": f"{csv_file.split('.')[0]}-{idx}",
                    "title": title,
                    "company": company,
                    "location": self._get_value(row, ['location', 'city', 'area']),
                    "salary_min": self._clean_salary_string(salary),
                    "salary_max": self._clean_salary_string(salary) * 1.2, # 估算
                    "description": desc[:2000], # 截断过长文本
                    "skills": [s.strip() for s in skills.split(',')] if ',' in skills else [skills],
                    "is_fresh_friendly": is_fresh,
                    "source": f"CSV: {csv_file}"
                })
            return jobs
        except Exception as e:
            logger.error(f"Failed to load {csv_file}: {e}")
            return []

    def extract_from_official_pdf(self, pdf_path: str) -> List[Dict]:
        """
        高难度动作：解析 Techfest Problem Statement.pdf 第8页的表格
        """
        extracted_jobs = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # PDF page index starts at 0, page 8 is index 7
                if len(pdf.pages) < 8: return []
                
                page = pdf.pages[7] 
                table = page.extract_table()
                
                if not table: return []

                # 从 PDF 表格中提取 (跳过表头)
                # 根据 PDF 内容 [cite: 50]，第一列通常混合了 title 和 company
                for row in table[1:]:
                    if not row or len(row) < 2: continue
                    
                    # 尝试解析第一列 (Company/Title)
                    col1 = row[0].split('\n')
                    title = col1[0] if len(col1) > 0 else "Unknown Role"
                    company = col1[1] if len(col1) > 1 else "Unknown Company"
                    
                    # 尝试解析薪资
                    salary_raw = row[5] if len(row) > 5 else "Not Specified"

                    extracted_jobs.append({
                        "id": f"PDF-{len(extracted_jobs)}",
                        "title": title,
                        "company": company,
                        "location": "Singapore",
                        "salary_min": self._clean_salary_string(salary_raw),
                        "salary_max": 0,
                        "description": f"Extracted from Official Problem Statement. Salary: {salary_raw}. Original row data available.",
                        "skills": ["General Tech"],
                        "is_fresh_friendly": "fresh" in str(row).lower(),
                        "source": "Official PDF (Page 8)"
                    })
            
            logger.info(f"Successfully extracted {len(extracted_jobs)} jobs from PDF table")
            return extracted_jobs
        except Exception as e:
            logger.error(f"PDF Extraction Error: {e}")
            return []