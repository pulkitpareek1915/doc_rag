from langgraph.graph import END, START, StateGraph

from docguard.agent.nodes import (
    generate,
    grade,
    refuse,
    retrieve,
    rewrite,
    security,
)
from docguard.agent.state import AgentState
from docguard.config import settings


def _route_after_grade(state: AgentState) -> str:
    relevant = state.get("relevant_docs", [])

    if len(relevant) >= settings.min_relevant_docs:
        return "security"

    if state.get("rewrite_count", 0) < settings.max_rewrites:
        return "rewrite"

    if relevant:
        return "security"

    return "refuse"


def _route_after_security(state: AgentState) -> str:
    clean = [
        document
        for document in state.get("relevant_docs", [])
        if document.get("security") == "clean"
    ]

    return "generate" if clean else "refuse"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("retrieve", retrieve.retrieve_node)
    graph.add_node("grade", grade.grade_node)
    graph.add_node("security", security.security_node)
    graph.add_node("rewrite", rewrite.rewrite_node)
    graph.add_node("generate", generate.generate_node)
    graph.add_node("refuse", refuse.refuse_node)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "grade")

    graph.add_conditional_edges(
        "grade",
        _route_after_grade,
        {
            "security": "security",
            "rewrite": "rewrite",
            "refuse": "refuse",
        },
    )

    graph.add_edge("rewrite", "retrieve")

    graph.add_conditional_edges(
        "security",
        _route_after_security,
        {
            "generate": "generate",
            "refuse": "refuse",
        },
    )

    graph.add_edge("generate", END)
    graph.add_edge("refuse", END)

    return graph.compile()


graph = build_graph()
