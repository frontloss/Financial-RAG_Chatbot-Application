from langgraph.graph import StateGraph, END
from src.agents.nodes import AgentNodes
from src.agents.state import AgentState

def build_graph(llm, tools):
    nodes = AgentNodes(llm, tools)
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("answerer", nodes.answer_node)
    workflow.add_node("reviewer", nodes.reviewer_node)
    #workflow.add_node("synthesizer", nodes.synthesizer_node)

    # Define Edges
    workflow.set_entry_point("answerer")
    #workflow.add_edge("planner", "researcher")
    workflow.add_edge("answerer", "reviewer")
    workflow.add_edge("reviewer", END)

    return workflow.compile()