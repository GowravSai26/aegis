import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from agents.state import AegisState

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.2,
)

SYSTEM = """You are the Writer Agent for AEGIS, an autonomous chargeback defense system.
Write a professional, legally formatted chargeback dispute response document.

Use EXACTLY this structure:

CHARGEBACK DISPUTE RESPONSE
============================
Case Reference: {chargeback_id}
Merchant: {merchant_name}
Transaction Date: {order_date}
Dispute Amount: ${amount}
Reason Code: {reason_code} — {reason_description}
Response Deadline: {deadline}

EXECUTIVE SUMMARY
-----------------
[2-3 sentences: what happened, why merchant should win]

EVIDENCE SUMMARY
----------------
1. [Evidence item — what it proves]
2. [Evidence item — what it proves]
3. [Evidence item — what it proves]

DETAILED ARGUMENT
-----------------
[Full professional argument referencing Visa reason code rules,
citing each piece of evidence, explaining why the dispute is invalid]

EVIDENCE ATTACHMENTS
--------------------
[List each evidence item with checkmark]

MERCHANT REQUEST
----------------
We respectfully request that this chargeback be reversed in full
and the disputed amount of ${amount} be returned to the merchant.

Submitted by AEGIS Autonomous Dispute System
{timestamp}

Write the full document now. No preamble, start directly with CHARGEBACK DISPUTE RESPONSE."""


def run_writer_agent(state: AegisState) -> AegisState:
    from datetime import datetime

    order = state.get("evidence_collected", {}).get("order_details", {})
    feedback_section = ""
    if state.get("review_feedback"):
        feedback_section = f"\n\nPREVIOUS REVIEW FEEDBACK TO ADDRESS:\n{state['review_feedback']}"

    prompt = f"""
Write a dispute response for this chargeback:

Case Reference: {state["chargeback_id"]}
Merchant: {order.get("merchant_name", "Unknown Merchant")}
Transaction Date: {order.get("order_date", "N/A")}
Dispute Amount: ${state["amount"]}
Reason Code: {state["reason_code"]} — {state["reason_description"]}
Response Deadline: {state["dispute_deadline"]}
Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}

Strategy verdict: {state.get("verdict")}
Winability score: {state.get("winability_score")}
Recommended arguments: {state.get("recommended_arguments")}

Evidence collected:
- Order details: {order}
- Delivery proof: {state.get("evidence_collected", {}).get("delivery_proof")}
- Device data: {state.get("evidence_collected", {}).get("device_data")}
- Auth status: {state.get("evidence_collected", {}).get("auth_status")}
- Correspondence: {state.get("evidence_collected", {}).get("correspondence")}
{feedback_section}
"""
    response = llm.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=prompt)])

    trace = state.get("agent_trace", [])
    revision = state.get("revision_count", 0)
    trace.append(f"WriterAgent: drafted response (revision {revision})")

    return {
        **state,
        "dispute_response_draft": response.content,
        "revision_count": revision,
        "agent_trace": trace,
    }
