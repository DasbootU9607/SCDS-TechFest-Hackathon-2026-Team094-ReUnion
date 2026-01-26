from langgraph.graph import StateGraph, END
from IPython.display import Image, display

# 1. 定义状态（你的数据流）
class AgentState(dict):
    pass

# 2. 初始化图
workflow = StateGraph(AgentState)

# 3. 添加节点 (这里对应你 agents.py 里的功能)
workflow.add_node("search_engine", lambda x: x) # 对应 JobSearchEngine
workflow.add_node("gap_analyzer", lambda x: x)  # 对应 perform_gap_analysis
workflow.add_node("roadmap_generator", lambda x: x)

# 4. 建立连线
workflow.set_entry_point("search_engine")
workflow.add_edge("search_engine", "gap_analyzer")
workflow.add_edge("gap_analyzer", "roadmap_generator")
workflow.add_edge("roadmap_generator", END)

# 5. 编译
app = workflow.compile()

# 6. 【核心】生成并保存图片
try:
    # 使用 Mermaid 渲染成 PNG
    img_data = app.get_graph().draw_mermaid_png()
    with open("reunion_architecture.png", "wb") as f:
        f.write(img_data)
    print("✅ 框架图已保存为 reunion_architecture.png")
except Exception as e:
    print(f"绘图失败，请确保安装了 pygraphviz 或使用 mermaid 接口: {e}")