import os
from langgraph.graph import StateGraph, END

# 1. 定义状态机（模拟你的数据流）
class GraphState(dict):
    def __init__(self):
        super().__init__()
        self["user_query"] = ""
        self["job_results"] = []
        self["gap_analysis"] = ""
        self["roadmap"] = ""

# 2. 初始化图
workflow = StateGraph(GraphState)

# 3. 定义节点名称（对应你项目的功能模块）
# 这里的 lambda 只是占位符，为了导出结构图
workflow.add_node("data_ingestion", lambda x: x)    # ingest.py: SQL + VectorDB
workflow.add_node("hybrid_search", lambda x: x)     # job_search.py: SQL Filter + Chroma
workflow.add_node("gap_analyzer", lambda x: x)      # agents.py: 技能差距分析
workflow.add_node("roadmap_generator", lambda x: x) # agents.py: 课程与路径规划

# 4. 构建连线逻辑
workflow.set_entry_point("data_ingestion")
workflow.add_edge("data_ingestion", "hybrid_search")
workflow.add_edge("hybrid_search", "gap_analyzer")
workflow.add_edge("gap_analyzer", "roadmap_generator")
workflow.add_edge("roadmap_generator", END)

workflow.add_conditional_edges(
    "gap_analyzer",
    lambda x: "continue" if x.get("is_complete") else "refine",
    {
        "continue": "roadmap_generator",
        "refine": "hybrid_search"
    }
)

# 5. 编译图
app = workflow.compile()

# 6. 导出图片
try:
    print("正在生成架构图...")
    # 使用 mermaid 渲染
    graph_png = app.get_graph().draw_mermaid_png()
    with open("reunion_architecture.png", "wb") as f:
        f.write(graph_png)
    print("✅ 成功！请在项目文件夹中查看 'reunion_architecture.png'")
except Exception as e:
    print(f"❌ 绘图失败: {e}")
    print("提示：如果报错，请确保运行了 pip install grandalf")