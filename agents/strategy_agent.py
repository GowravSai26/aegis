from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import AegisState, DisputeVerdict
from tools.reason_code_rules import get_winability_factors
from dotenv import load_dotenv
import json, os

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)

SYSTEM = """You are the Strategy Agent for AEGIS, an autonomous chargeback defense system.
Analyze the evidence and decide whether the merchant should fight or accept the chargeback.

Return ONLY a JSON object with these exact fields:
- verdict: one of [FIGHT, ACCEPT, ESCALATE]
- winability_score: float 0.0-1.0
- strategy_reasoning: 2-3 sentences explaining the decision
- recommended_arguments: list of 2-4 specific arguments to use in the dispute response

Rules:
- winability_score >= 0.6 → FIGHT
- winability_score < 0.4 → ACCEPT
- 0.4 <= winability_score < 0.6 → ESCALATE
- Amount > 10000 → always ESCALATE
- Rare reason codes (10.5) → ESCALATE

Return only valid JSON. No markdown. No backticks. No explanation."""

def _parse(content: str) -> dict:
    clean = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(clean)

def run_strategy_agent(state: AegisState) -> AegisState:
    winability_factors = get_winability_factors(state["reason_code"])

    prompt = f"""
Chargeback: {state['chargeback_id']}
Reason Code: {state['reason_code']} — {state['reason_description']}
Amount: ${state['amount']}
Evidence Strength: {state['evidence_strength']}
Missing Evidence: {state['missing_evidence']}
Winability Factors for this reason code: {winability_factors}

Evidence collected:
{json.dumps(state.get('evidence_collected', {}), indent=2, default=str)}

Make your FIGHT / ACCEPT / ESCALATE decision.
"""
    response = llm.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=prompt)])

    try:
        parsed = _parse(response.content)
    except json.JSONDecodeError:
        parsed = {
            "verdict": "ESCALATE",
            "winability_score": 0.5,
            "strategy_reasoning": "Parse error — escalating to human.",
            "recommended_arguments": [],
        }

    verdict = DisputeVerdict(parsed.get("verdict", "ESCALATE"))
    trace = state.get("agent_trace", [])
    trace.append(
        f"StrategyAgent: verdict={verdict} | "
        f"winability={parsed.get('winability_score')}"
    )

    return {
        **state,
        "verdict": verdict,
        "winability_score": parsed.get("winability_score"),
        "strategy_reasoning": parsed.get("strategy_reasoning"),
        "recommended_arguments": parsed.get("recommended_arguments", []),
        "agent_trace": trace,
    }
