from unittest.mock import MagicMock, patch

from agents.state import AegisState
from agents.writer_agent import run_writer_agent


def make_state(**kwargs):
    base = AegisState(
        chargeback_id="CB-TEST",
        merchant_id="MERCH-001",
        transaction_id="TXN-001",
        amount=450.0,
        reason_code="13.1",
        reason_description="Item not received",
        dispute_deadline="2024-04-01",
        dispute_category="not_received",
        urgency="MEDIUM",
        required_evidence=[],
        evidence_collected={"order_lookup": {"found": True}},
        evidence_strength=0.8,
        missing_evidence=[],
        verdict="FIGHT",
        winability_score=0.8,
        strategy_reasoning="Strong evidence",
        recommended_arguments=["Delivery confirmed"],
        dispute_response_draft="",
        revision_count=0,
        review_passed=False,
        review_feedback="",
        document_path="",
        escalation_reason=None,
        agent_trace=[],
        error=None,
    )
    base.update(kwargs)
    return base


@patch("agents.writer_agent.ChatGroq")
def test_writer_produces_draft(mock_groq):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "This is a formal dispute response for CB-TEST."
    mock_groq.return_value = mock_llm

    state = make_state()
    result = run_writer_agent(state)

    assert len(result["dispute_response_draft"]) > 0
    assert any("WriterAgent" in t for t in result["agent_trace"])
