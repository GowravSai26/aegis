from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from agents.orchestrator import aegis_graph
from agents.state import AegisState
from api.schemas import DisputeRequest, DisputeResponse
from tools.document_generator import generate_docx

router = APIRouter()


def _build_state(req: DisputeRequest) -> AegisState:
    return AegisState(
        chargeback_id=req.chargeback_id,
        merchant_id=req.merchant_id,
        transaction_id=req.transaction_id,
        amount=req.amount,
        reason_code=req.reason_code,
        reason_description=req.reason_description,
        dispute_deadline=req.dispute_deadline,
        dispute_category=None,
        urgency=None,
        required_evidence=None,
        evidence_collected=None,
        evidence_strength=None,
        missing_evidence=None,
        verdict=None,
        winability_score=None,
        strategy_reasoning=None,
        recommended_arguments=None,
        dispute_response_draft=None,
        document_path=None,
        revision_count=0,
        review_passed=None,
        review_feedback=None,
        escalation_reason=None,
        agent_trace=[],
        error=None,
    )


@router.post("/dispute", response_model=DisputeResponse)
async def run_dispute(req: DisputeRequest):
    try:
        state = _build_state(req)
        result = aegis_graph.invoke(state)

        doc_path = None
        if result.get("dispute_response_draft"):
            doc_path = generate_docx(result)
            result["document_path"] = doc_path

        return DisputeResponse(
            chargeback_id=result["chargeback_id"],
            verdict=str(result.get("verdict", "ESCALATE")).replace("DisputeVerdict.", ""),
            winability_score=result.get("winability_score"),
            strategy_reasoning=result.get("strategy_reasoning"),
            recommended_arguments=result.get("recommended_arguments"),
            review_passed=result.get("review_passed"),
            dispute_category=result.get("dispute_category"),
            urgency=result.get("urgency"),
            agent_trace=result.get("agent_trace", []),
            document_path=doc_path,
            escalation_reason=result.get("escalation_reason"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dispute/{chargeback_id}/download")
async def download_document(chargeback_id: str):
    path = Path(f"generated_docs/{chargeback_id}.docx")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(
        path=str(path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{chargeback_id}_dispute_response.docx",
    )
