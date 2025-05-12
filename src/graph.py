from langgraph.graph import StateGraph, START
from src.nodes import reasoning_node, human_approval_node, graph_tools_node
from src.schema import AgentState


def build_graph():
    """
    Build the state graph for the agent.
    """
    # Define the nodes of the workflow
    workflow = StateGraph(AgentState)
    workflow.add_node("Reasoning", reasoning_node)
    workflow.add_node("HumanApproval", human_approval_node)
    workflow.add_node("GraphTools", graph_tools_node)
    workflow.add_node("END", lambda state: state)

    workflow.set_entry_point("Reasoning")
    workflow.set_finish_point("END")

    workflow.add_edge(START, "Reasoning")
    workflow.add_conditional_edges(
        "Reasoning",
        lambda state: state.next,
        {
            "HumanApproval": "HumanApproval",
            "END": "END",
        }
    )
    workflow.add_edge("HumanApproval", "GraphTools")
    workflow.add_edge("GraphTools", "END")

    return workflow.compile()