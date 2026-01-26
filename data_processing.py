"""
数据预处理管道
"""
import pandas as pd
import numpy as np
from pathlib import Path
import hashlib
import re

class DataPreprocessor:
    def __init__(self, input_dir="./official_csv_data", output_dir="./processed_data"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def preprocess_all(self):
        """预处理所有CSV文件"""
        processed_files = []
        
        for csv_file in self.input_dir.glob("*.csv"):
            print(f"处理文件: {csv_file.name}")
            
            try:
                # 读取CSV
                df = pd.read_csv(csv_file)
                
                # 应用预处理步骤
                df = self.clean_column_names(df)
                df = self.fill_missing_values(df)
                df = self.standardize_data(df)
                df = self.enrich_data(df)
                df = self.generate_ids(df, csv_file.name)
                
                # 保存处理后的文件
                output_file = self.output_dir / f"processed_{csv_file.name}"
                df.to_csv(output_file, index=False, encoding='utf-8')
                
                processed_files.append({
                    "original": csv_file.name,
                    "processed": output_file.name,
                    "rows": len(df),
                    "columns": list(df.columns)
                })
                
                print(f"  ✅ 已处理: {len(df)} 行, {len(df.columns)} 列")
                
            except Exception as e:
                print(f"  ❌ 处理失败: {e}")
        
        # 合并所有处理后的文件
        if processed_files:
            self.merge_files()
        
        return processed_files
    
    def clean_column_names(self, df):
        """清理列名"""
        df.columns = [self.normalize_column_name(col) for col in df.columns]
        return df
    
    def normalize_column_name(self, col_name):
        """标准化列名"""
        if not isinstance(col_name, str):
            col_name = str(col_name)
        
        # 转换为小写，替换空格和下划线
        col_name = col_name.lower().strip()
        col_name = re.sub(r'[^\w]', '_', col_name)
        col_name = re.sub(r'_+', '_', col_name)
        
        # 常见列名映射
        column_mapping = {
            'job_title': 'title',
            'position_title': 'title',
            'company_name': 'company',
            'employer': 'company',
            'work_location': 'location',
            'city': 'location',
            'job_description': 'description',
            'responsibilities': 'description',
            'required_skills': 'skills',
            'technical_skills': 'skills',
            'min_salary': 'salary_min',
            'max_salary': 'salary_max'
        }
        
        return column_mapping.get(col_name, col_name)
    
    def fill_missing_values(self, df):
        """填充缺失值"""
        # 根据列名填充不同的默认值
        for col in df.columns:
            if df[col].isna().any():
                if 'salary' in col:
                    df[col] = df[col].fillna(0)
                elif 'location' in col:
                    df[col] = df[col].fillna('Not specified')
                elif 'skills' in col:
                    df[col] = df[col].fillna('Not specified')
                elif 'description' in col:
                    df[col] = df[col].fillna('No description provided')
                else:
                    df[col] = df[col].fillna('')
        
        return df
    
    def standardize_data(self, df):
        """标准化数据"""
        # 标准化薪资
        for col in ['salary_min', 'salary_max']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 标准化地点
        if 'location' in df.columns:
            df['location'] = df['location'].apply(self.standardize_location)
        
        return df
    
    def standardize_location(self, location):
        """标准化地点"""
        if not isinstance(location, str):
            return 'Not specified'
        
        location = location.strip().title()
        
        # 新加坡地点标准化
        singapore_keywords = ['singapore', 'sg', 's\'pore']
        if any(keyword in location.lower() for keyword in singapore_keywords):
            return 'Singapore'
        
        # 常见缩写扩展
        location_mapping = {
            'Sg': 'Singapore',
            'Spore': 'Singapore',
            'SGP': 'Singapore',
            'Central': 'Singapore Central',
            'CBD': 'Singapore CBD',
            'Remote': 'Remote (Anywhere)',
            'WFH': 'Remote'
        }
        
        return location_mapping.get(location, location)
    
    def enrich_data(self, df):
        """丰富数据"""
        # 添加技能计数
        if 'skills' in df.columns:
            df['skill_count'] = df['skills'].apply(
                lambda x: len(str(x).split(',')) if pd.notna(x) else 0
            )
        
        # 添加薪资范围
        if all(col in df.columns for col in ['salary_min', 'salary_max']):
            df['salary_range'] = df.apply(
                lambda row: f"{row['salary_min']:.0f}-{row['salary_max']:.0f}", 
                axis=1
            )
        
        # 添加数据源标记
        df['data_source'] = 'Official CSV'
        
        return df
    
    def generate_ids(self, df, source_file):
        """生成唯一ID"""
        if 'id' not in df.columns or df['id'].isna().all():
            # 基于标题和公司生成ID
            df['id'] = df.apply(
                lambda row: self._generate_job_id(
                    row.get('title', ''),
                    row.get('company', ''),
                    source_file
                ), axis=1
            )
        
        return df
    
    def _generate_job_id(self, title, company, source_file):
        """生成职位ID"""
        base_str = f"{title}_{company}_{source_file}".encode('utf-8')
        hash_obj = hashlib.md5(base_str)
        return f"JOB-{hash_obj.hexdigest()[:8].upper()}"
    
    def merge_files(self):
        """合并所有处理后的文件"""
        all_dfs = []
        
        for processed_file in self.output_dir.glob("processed_*.csv"):
            df = pd.read_csv(processed_file)
            all_dfs.append(df)
        
        if all_dfs:
            merged_df = pd.concat(all_dfs, ignore_index=True)
            merged_file = self.output_dir / "all_jobs_merged.csv"
            merged_df.to_csv(merged_file, index=False, encoding='utf-8')
            
            print(f"\n✅ 合并完成!")
            print(f"总职位数: {len(merged_df)}")
            print(f"合并文件: {merged_file}")
            
            # 统计信息
            stats = {
                "total_jobs": len(merged_df),
                "unique_companies": merged_df['company'].nunique(),
                "unique_locations": merged_df['location'].nunique(),
                "avg_salary_min": merged_df['salary_min'].mean(),
                "avg_salary_max": merged_df['salary_max'].mean()
            }
            
            print("\n📊 统计信息:")
            for key, value in stats.items():
                print(f"  {key}: {value:.2f}" if isinstance(value, float) else f"  {key}: {value}")

if __name__ == "__main__":
    print("🔧 数据预处理管道")
    print("="*50)
    
    preprocessor = DataPreprocessor()
    results = preprocessor.preprocess_all()
    
    print(f"\n✅ 预处理完成! 处理了 {len(results)} 个文件")
    print(f"处理后的文件保存在: ./processed_data/")