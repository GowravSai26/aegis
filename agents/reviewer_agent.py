from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import AegisState
from dotenv import load_dotenv
import json, os

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)

SYSTEM = """You are the Reviewer Agent for AEGIS, an autonomous chargeback defense system.
Review the dispute response document and check for quality.

Return ONLY a JSON object:
- review_passed: true or false
- feedback: if failed, specific instructions for the writer to fix. If passed, empty string.
- checks: object with these boolean fields:
  - has_executive_summary
  - has_evidence_summary
  - has_detailed_argument
  - has_merchant_request
  - cites_reason_code
  - professional_tone

Pass criteria: all checks true AND argument is legally sound.

Return only valid JSON. No markdown. No backticks."""

def _parse(content: str) -> dict:
    clean = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(clean)

def run_reviewer_agent(state: AegisState) -> AegisState:
    prompt = f"""
Review this dispute response document:

{state.get('dispute_response_draft', '')}

---
Required evidence for reason code {state['reason_code']}: {state.get('required_evidence')}
Recommended arguments: {state.get('recommended_arguments')}
Revision number: {state.get('revision_count', 0)}
"""
    response = llm.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=prompt)])

    try:
        parsed = _parse(response.content)
    except json.JSONDecodeError:
        parsed = {"review_passed": False, "feedback": "Could not parse review — please revise for clarity."}

    passed = parsed.get("review_passed", False)
    trace = state.get("agent_trace", [])
    trace.append(f"ReviewerAgent: passed={passed} | feedback='{parsed.get('feedback', '')[:80]}'")

    return {
        **state,
        "review_passed": passed,
        "review_feedback": parsed.get("feedback", ""),
        "agent_trace": trace,
    }
