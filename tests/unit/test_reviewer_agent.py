from unittest.mock import MagicMock, patch

from agents.reviewer_agent import reviewer_agent
from agents.state import AegisState


def make_state(**kwargs):
    return AegisState(
        chargeback_id="CB-TEST",
        merchant_id="MERCH-001",
        transaction_id="TXN-001",
        amount=450.0,
        reason_code="13.1",
        reason_description="Item not received",
        dispute_category="not_received",
        urgency="MEDIUM",
        required_evidence=[],
        evidence_collected={},
        evidence_strength=0.8,
        missing_evidence=[],
        verdict="FIGHT",
        winability_score=0.8,
        strategy_reasoning="Strong evidence",
        recommended_arguments=["Delivery confirmed"],
        draft_response="This is a formal dispute response.",
        revision_count=0,
        review_passed=False,
        review_feedback="",
        document_path="",
        escalation_reason=None,
        agent_trace=[],
        **kwargs,
    )


@patch("agents.reviewer_agent.ChatGroq")
def test_reviewer_passes(mock_groq):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = '{"review_passed": true, "feedback": ""}'
    mock_groq.return_value = mock_llm

    state = make_state()
    result = reviewer_agent(state)

    assert isinstance(result["review_passed"], bool)
    assert any("ReviewerAgent" in t for t in result["agent_trace"])


@patch("agents.reviewer_agent.ChatGroq")
def test_reviewer_fails_and_gives_feedback(mock_groq):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = '{"review_passed": false, "feedback": "Missing delivery details"}'
    mock_groq.return_value = mock_llm

    state = make_state(draft_response="Too short.")
    result = reviewer_agent(state)

    assert isinstance(result["review_passed"], bool)
