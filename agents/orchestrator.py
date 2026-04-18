from langgraph.graph import StateGraph, END
from agents.state import AegisState, DisputeVerdict
from agents.intake_agent import run_intake_agent
from agents.evidence_collector_agent import run_evidence_collector_agent
from agents.strategy_agent import run_strategy_agent
from agents.writer_agent import run_writer_agent
from agents.reviewer_agent import run_reviewer_agent


def escalate_node(state: AegisState) -> AegisState:
    trace = state.get("agent_trace", [])
    trace.append("Orchestrator: ESCALATED TO HUMAN")
    return {
        **state,
        "verdict": DisputeVerdict.ESCALATE,
        "escalation_reason": state.get("escalation_reason") or "Max revisions reached or low confidence",
        "agent_trace": trace,
    }


def route_after_strategy(state: AegisState) -> str:
    if state.get("verdict") == DisputeVerdict.ACCEPT:
        return "end"
    if state.get("verdict") == DisputeVerdict.ESCALATE:
        return "escalate"
    return "writer"  # FIGHT → write the response


def route_after_review(state: AegisState) -> str:
    if state.get("review_passed"):
        return "end"
    if state.get("revision_count", 0) >= 2:
        return "escalate"
    # increment revision count and send back
    state["revision_count"] = state.get("revision_count", 0) + 1
    return "writer"


def build_graph() -> StateGraph:
    graph = StateGraph(AegisState)

    graph.add_node("intake_agent", run_intake_agent)
    graph.add_node("evidence_collector_agent", run_evidence_collector_agent)
    graph.add_node("strategy_agent", run_strategy_agent)
    graph.add_node("writer_agent", run_writer_agent)
    graph.add_node("reviewer_agent", run_reviewer_agent)
    graph.add_node("escalate_node", escalate_node)

    graph.set_entry_point("intake_agent")
    graph.add_edge("intake_agent", "evidence_collector_agent")
    graph.add_edge("evidence_collector_agent", "strategy_agent")

    graph.add_conditional_edges(
        "strategy_agent",
        route_after_strategy,
        {"end": END, "escalate": "escalate_node", "writer": "writer_agent"},
    )

    graph.add_edge("writer_agent", "reviewer_agent")

    graph.add_conditional_edges(
        "reviewer_agent",
        route_after_review,
        {"end": END, "escalate": "escalate_node", "writer": "writer_agent"},
    )

    graph.add_edge("escalate_node", END)

    return graph.compile()


aegis_graph = build_graph()
