from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta


class DisputeRequest(BaseModel):
    chargeback_id: str
    merchant_id: str
    transaction_id: str
    amount: float
    reason_code: str
    reason_description: str = ""
    dispute_deadline: str = Field(
        default_factory=lambda: (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    )


class DisputeResponse(BaseModel):
    chargeback_id: str
    verdict: str
    winability_score: Optional[float]
    strategy_reasoning: Optional[str]
    recommended_arguments: Optional[List[str]]
    review_passed: Optional[bool]
    dispute_category: Optional[str]
    urgency: Optional[str]
    agent_trace: List[str]
    document_path: Optional[str]
    escalation_reason: Optional[str]
