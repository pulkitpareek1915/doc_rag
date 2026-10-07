from docguard.agent.state import AgentState


def refuse_node(state: AgentState) -> dict:
    return {
        "answer": (
            "I couldn't find enough verified, safe context "
            "to answer that question."
        ),
        "citations": [],
        "refusal_reason": (
            state.get("refusal_reason")
            or "insufficient_or_unsafe_context"
        ),
    }
