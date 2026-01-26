from langgraph.graph import StateGraph, END
import os

# 1. 定义更丰富的状态
class AgentState(dict):
    pass

workflow = StateGraph(AgentState)

# 2. 定义功能节点
# 模拟：数据预处理层
workflow.add_node("data_standardization", lambda x: x) 
# 模拟：混合检索层（SQL + Vector）
workflow.add_node("hybrid_retrieval", lambda x: x)
# 模拟：Agent 思考层（分析差距）
workflow.add_node("skill_gap_analysis", lambda x: x)
# 模拟：路线图生成层
workflow.add_node("roadmap_generation", lambda x: x)

# 3. 设置逻辑连线
workflow.set_entry_point("data_standardization")
workflow.add_edge("data_standardization", "hybrid_retrieval")
workflow.add_edge("hybrid_retrieval", "skill_gap_analysis")

# 4. 【核心升级】添加条件分支（逻辑判断）
# 如果分析发现技能完全不匹配，跳回搜索层优化关键词；否则进入生成层
workflow.add_conditional_edges(
    "skill_gap_analysis",
    lambda x: "optimize_search" if x.get("low_relevance", False) else "generate",
    {
        "optimize_search": "hybrid_retrieval", # 循环：重新搜索
        "generate": "roadmap_generation"       # 继续：生成路线图
    }
)

workflow.add_edge("roadmap_generation", END)

# 5. 编译并保存图片
app = workflow.compile()

try:
    img_data = app.get_graph().draw_mermaid_png()
    with open("reunion_advanced_arch.png", "wb") as f:
        f.write(img_data)
    print("✅ 升级版架构图已生成：reunion_advanced_arch.png")
except Exception as e:
    print(f"绘图失败: {e}")