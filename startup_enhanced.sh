#!/bin/bash

echo "🚀 启动 Career AIDE 系统 (增强版)"
echo "="*50

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p official_csv_data
mkdir -p company_data
mkdir -p csv_analysis
mkdir -p csv_templates

echo "📊 检查数据文件..."
if [ -d "./official_csv_data" ] && [ "$(ls -A ./official_csv_data/*.csv 2>/dev/null)" ]; then
    echo "✅ 发现CSV数据文件"
    echo "分析CSV文件结构..."
    python process_csv_data.py
else
    echo "⚠️  未发现CSV数据文件"
    echo "请将官方CSV文件放入 ./official_csv_data/ 目录"
    echo "或系统将使用示例数据"
    read -p "是否继续? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 继续原有启动流程...
# ... [原有脚本内容]