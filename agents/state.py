from typing import TypedDict, Optional, List
from enum import Enum


class DisputeVerdict(str, Enum):
    FIGHT = "FIGHT"
    ACCEPT = "ACCEPT"
    ESCALATE = "ESCALATE"


class AegisState(TypedDict):
    # Input
    chargeback_id: str
    merchant_id: str
    transaction_id: str
    amount: float
    reason_code: str
    reason_description: str
    dispute_deadline: str

    # Intake Agent output
    dispute_category: Optional[str]
    urgency: Optional[str]           # HIGH / MEDIUM / LOW
    required_evidence: Optional[List[str]]

    # Evidence Collector output
    evidence_collected: Optional[dict]
    evidence_strength: Optional[float]   # 0.0 - 1.0
    missing_evidence: Optional[List[str]]

    # Strategy Agent output
    verdict: Optional[DisputeVerdict]
    winability_score: Optional[float]
    strategy_reasoning: Optional[str]
    recommended_arguments: Optional[List[str]]

    # Writer Agent output
    dispute_response_draft: Optional[str]
    document_path: Optional[str]
    revision_count: int

    # Reviewer Agent output
    review_passed: Optional[bool]
    review_feedback: Optional[str]

    # System
    escalation_reason: Optional[str]
    agent_trace: List[str]
    error: Optional[str]
