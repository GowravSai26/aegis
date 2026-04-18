from unittest.mock import MagicMock, patch

from agents.evidence_collector_agent import run_evidence_collector_agent
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
        dispute_category="not_received",
        urgency="MEDIUM",
        required_evidence=["order_lookup", "delivery_proof"],
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


@patch("agents.evidence_collector_agent.ChatGroq")
def test_evidence_collector_returns_strength(mock_groq):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = (
        '{"evidence_collected": {"order_lookup": {"found": true},'
        ' "delivery_proof": {"found": true}}, "evidence_strength": 0.8, "missing_evidence": []}'
    )
    mock_groq.return_value = mock_llm

    state = make_state()
    result = run_evidence_collector_agent(state)

    assert result["evidence_strength"] >= 0.0
    assert isinstance(result["evidence_collected"], dict)
    assert any("EvidenceCollector" in t for t in result["agent_trace"])
