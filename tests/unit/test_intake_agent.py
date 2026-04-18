from unittest.mock import MagicMock, patch

from agents.intake_agent import run_intake_agent
from agents.state import AegisState


def make_state(**kwargs):
    base = AegisState(
        chargeback_id="CB-TEST",
        merchant_id="MERCH-001",
        transaction_id="TXN-001",
        amount=450.0,
        reason_code="13.1",
        reason_description="Item not received",
        dispute_deadline="2024-04-01",
        dispute_category=None,
        urgency=None,
        required_evidence=[],
        evidence_collected={},
        evidence_strength=0.0,
        missing_evidence=[],
        verdict=None,
        winability_score=0.0,
        strategy_reasoning="",
        recommended_arguments=[],
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


@patch("agents.intake_agent.ChatGroq")
def test_intake_agent_sets_category(mock_groq):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = (
        '{"dispute_category": "not_received", "urgency": "HIGH",'
        ' "required_evidence": ["delivery_proof", "order_lookup"]}'
    )
    mock_groq.return_value = mock_llm

    state = make_state()
    result = run_intake_agent(state)

    assert result["dispute_category"] == "not_received"
    assert result["urgency"] == "HIGH"
    assert "delivery_proof" in result["required_evidence"]
    assert any("IntakeAgent" in t for t in result["agent_trace"])
