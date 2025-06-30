from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

# 1) 定义最简单状态
class Msg(TypedDict):
    content: str

# 2) 两个节点：echo1 -> echo2
def echo1(state: Msg) -> Msg:
    return {"content": f"[Node1] {state['content']}"}

def echo2(state: Msg) -> Msg:
    return {"content": f"[Node2] {state['content']}"}

# 3) 构建图
graph = StateGraph(Msg)
graph.add_node("n1", echo1)
graph.add_node("n2", echo2)
graph.add_edge("n1", "n2")  # 顺序
graph.add_edge(START, "n1")
graph.add_edge("n2", END)
compiled_graph = graph.compile()

if __name__ == "__main__":
    out = compiled_graph.invoke({"content": "Hello LangGraph!"})
    print(out)
    
    # 注意：保存状态功能可能在新版本中有所不同
    # graph.save_state("snapshot.json")
