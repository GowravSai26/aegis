import json
import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from agents.state import AegisState
from tools.auth_history import get_auth_status
from tools.cardholder_comms import get_correspondence
from tools.delivery_proof import get_delivery_proof
from tools.device_fingerprint import get_device_data
from tools.order_lookup import get_order

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)

SYSTEM = """You are the Evidence Collector Agent for AEGIS.
Given collected evidence and required evidence list, return ONLY a JSON object:
- evidence_strength: float 0.0-1.0 (how strong is the merchant's evidence)
- missing_evidence: list of evidence items that are absent or weak
- summary: one sentence assessment

Return only valid JSON. No explanation, no markdown."""


def _collect(transaction_id: str, required: list[str]) -> dict:
    collected = {}
    order = get_order(transaction_id)
    if not order:
        return collected

    collected["order_details"] = order

    if any(e in required for e in ["delivery_confirmation", "tracking_number", "carrier_proof"]):
        collected["delivery_proof"] = get_delivery_proof(order["order_id"])

    if any(e in required for e in ["device_fingerprint", "ip_address"]):
        collected["device_data"] = get_device_data(transaction_id)

    if any(e in required for e in ["3ds_auth_status"]):
        collected["auth_status"] = get_auth_status(transaction_id)

    if any(e in required for e in ["cardholder_correspondence"]):
        collected["correspondence"] = get_correspondence(order["customer_email"])

    return collected


def run_evidence_collector_agent(state: AegisState) -> AegisState:
    required = state.get("required_evidence") or []
    collected = _collect(state["transaction_id"], required)

    prompt = f"""
Required evidence for reason code {state["reason_code"]}: {required}

Collected evidence:
{json.dumps(collected, indent=2, default=str)}

Assess how well the collected evidence covers the required evidence.
"""
    response = llm.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=prompt)])

    try:
        raw = response.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {
            "evidence_strength": 0.5,
            "missing_evidence": [],
            "summary": "Parse error",
        }

    trace = state.get("agent_trace", [])
    trace.append(
        f"EvidenceCollector: strength={parsed.get('evidence_strength')} | missing={parsed.get('missing_evidence')}"
    )

    return {
        **state,
        "evidence_collected": collected,
        "evidence_strength": parsed.get("evidence_strength", 0.5),
        "missing_evidence": parsed.get("missing_evidence", []),
        "agent_trace": trace,
    }
