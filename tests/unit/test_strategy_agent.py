from unittest.mock import patch, MagicMock
from agents.strategy_agent import strategy_agent
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
        required_evidence=["order_lookup"],
        evidence_collected={"order_lookup": {"found": True}},
        evidence_strength=0.8,
        missing_evidence=[],
        verdict=None,
        winability_score=0.0,
        strategy_reasoning="",
        recommended_arguments=[],
        draft_response="",
        revision_count=0,
        review_passed=False,
        review_feedback="",
        document_path="",
        escalation_reason=None,
        agent_trace=[],
        **kwargs
    )

@patch("agents.strategy_agent.ChatGroq")
def test_strategy_returns_fight(mock_groq):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = '{"verdict": "FIGHT", "winability_score": 0.8, "strategy_reasoning": "Strong evidence", "recommended_arguments": ["arg1"], "escalation_reason": null}'
    mock_groq.return_value = mock_llm

    state = make_state()
    result = strategy_agent(state)

    assert result["verdict"] is not None
    assert 0.0 <= result["winability_score"] <= 1.0
    assert any("StrategyAgent" in t for t in result["agent_trace"])

@patch("agents.strategy_agent.ChatGroq")
def test_strategy_returns_accept(mock_groq):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = '{"verdict": "ACCEPT", "winability_score": 0.2, "strategy_reasoning": "Weak evidence", "recommended_arguments": [], "escalation_reason": null}'
    mock_groq.return_value = mock_llm

    state = make_state(evidence_strength=0.1)
    result = strategy_agent(state)

    assert result["verdict"] is not None