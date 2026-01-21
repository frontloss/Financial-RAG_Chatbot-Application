from langgraph.graph import StateGraph, END
from src.agents.nodes import AgentNodes
from src.agents.state import AgentState

def build_graph(llm, tools):
    nodes = AgentNodes(llm, tools)
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("planner", nodes.planner_node)
    workflow.add_node("researcher", nodes.research_node)
    workflow.add_node("synthesizer", nodes.synthesizer_node)

    # Define Edges
    workflow.set_conditional_entry_point(
        route_query_ai,
    {
        "planner": "planner",
        "researcher": "researcher"
    }
    )
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "synthesizer")
    workflow.add_edge("synthesizer", END)

    return workflow.compile()