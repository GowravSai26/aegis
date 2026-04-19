import json
import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from agents.state import AegisState
from tools.reason_code_rules import get_reason_code, get_required_evidence

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)

SYSTEM = """You are the Intake Agent for AEGIS, an autonomous chargeback defense system.
Given a chargeback notification, you must return ONLY a JSON object with these fields:
- dispute_category: one of [fraud, not_received, not_as_described, duplicate, cancelled, authorization, other]
- urgency: one of [HIGH, MEDIUM, LOW] based on amount and deadline proximity
- summary: one sentence describing the dispute

Return only valid JSON. No explanation, no markdown."""


def run_intake_agent(state: AegisState) -> AegisState:
    prompt = f"""
Chargeback ID: {state["chargeback_id"]}
Reason Code: {state["reason_code"]}
Reason Description: {state["reason_description"]}
Amount: ${state["amount"]}
Deadline: {state["dispute_deadline"]}
"""
    response = llm.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=prompt)])

    try:
        raw = response.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {
            "dispute_category": "other",
            "urgency": "HIGH",
            "summary": "Parse error",
        }

    required = get_required_evidence(state["reason_code"])
    code_info = get_reason_code(state["reason_code"])

    trace = state.get("agent_trace", [])
    trace.append(f"IntakeAgent: classified as {parsed.get('dispute_category')} | urgency={parsed.get('urgency')}")

    return {
        **state,
        "dispute_category": parsed.get("dispute_category"),
        "urgency": parsed.get("urgency"),
        "required_evidence": required,
        "reason_description": code_info["name"] if code_info else state["reason_description"],
        "agent_trace": trace,
    }
