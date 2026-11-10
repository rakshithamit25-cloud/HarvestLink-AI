import time
import logging
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.agents.state import HarvestLinkState
from app.models import AgentLog, MatchResult, BuyerRequirement
from app.agents.llm_client import LLMClient

logger = logging.getLogger(__name__)

class NegotiationSuggestion(BaseModel):
    suggested_price: float
    rationale: str

def run_negotiation_agent(state: HarvestLinkState, db: Session) -> HarvestLinkState:
    start_time = time.time()
    task = f"Formulate suggested prices within limits for {len(state.get('proposals', []))} proposals"
    
    llm_client = LLMClient()
    llm_calls_succeeded = 0
    fallback_reasons: list[str] = []
    results = []

    for prop in state.get("proposals", []):
        if prop["status"] == "no_overlap" or prop["allocated_quantity"] <= 0:
            continue

        req = db.query(BuyerRequirement).filter(BuyerRequirement.id == prop["buyer_requirement_id"]).first()
        if not req:
            continue

        # Negotiation pricing boundaries strictly set by backend
        farmer_ask = state["expected_price"]
        farmer_min = state["minimum_price"]
        buyer_max = req.maximum_price

        # Deterministic rule-based calculation
        if buyer_max >= farmer_ask:
            rule_suggested = round((farmer_ask + buyer_max) / 2.0, 2)
            rule_terms_note = f"Suggested ${rule_suggested:.2f}/kg (farmer asked ${farmer_ask:.2f}, buyer max ${buyer_max:.2f}). Both parties gain surplus."
        elif buyer_max >= farmer_min:
            rule_suggested = round((farmer_min + buyer_max) / 2.0, 2)
            rule_terms_note = f"Suggested ${rule_suggested:.2f}/kg (acceptable above farmer minimum ${farmer_min:.2f}, within buyer limit ${buyer_max:.2f})."
        else:
            rule_suggested = 0.0
            rule_terms_note = f"No price overlap: Farmer minimum ${farmer_min:.2f} > Buyer max ${buyer_max:.2f}."

        suggested = rule_suggested
        terms_note = rule_terms_note

        # If LLM is configured and overlap exists, query LLM for price suggestion within bounds
        if llm_client.is_configured() and buyer_max >= farmer_min:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an agricultural price negotiation assistant. "
                        "Suggest a price within the farmer's minimum and the buyer's maximum. "
                        "Return a JSON object with keys 'suggested_price' (float) and 'rationale' (string)."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Crop: {state['crop_name']}, Farmer Asking Price: ${farmer_ask:.2f}, "
                        f"Farmer Minimum Floor: ${farmer_min:.2f}, Buyer Maximum Ceiling: ${buyer_max:.2f}."
                    )
                }
            ]
            llm_resp = llm_client.chat_completion_json(messages)
            if llm_resp:
                try:
                    parsed = NegotiationSuggestion(**llm_resp)
                    # Backend strictly enforces bounds: LLM price cannot violate farmer_min or buyer_max
                    if farmer_min <= parsed.suggested_price <= buyer_max:
                        suggested = round(parsed.suggested_price, 2)
                        terms_note = f"AI Suggested ${suggested:.2f}/kg (bounded between ${farmer_min:.2f}-${buyer_max:.2f}): {parsed.rationale}"
                        llm_calls_succeeded += 1
                    else:
                        logger.warning(
                            f"Negotiation Agent price out of bounds: suggested {parsed.suggested_price} "
                            f"outside limits [{farmer_min}, {buyer_max}] (price out of bounds)"
                        )
                        fallback_reasons.append("fallback: price out of bounds")
                except Exception as e:
                    logger.warning(f"Negotiation Agent validation failed: {type(e).__name__} (invalid schema)")
                    fallback_reasons.append("fallback: invalid schema")

        prop["ai_suggested_price"] = suggested
        prop["match_reason"] += f" | Negotiation: {terms_note}"

        # Update in DB
        db_match = db.query(MatchResult).filter(
            MatchResult.listing_id == state["listing_id"],
            MatchResult.buyer_requirement_id == req.id
        ).first()
        if db_match:
            db_match.ai_suggested_price = suggested
            db_match.match_reason = prop["match_reason"]
            db.commit()

        results.append({
            "buyer_id": req.buyer_id,
            "buyer_name": prop["buyer_name"],
            "allocated_quantity": prop["allocated_quantity"],
            "suggested_price": suggested,
            "terms_note": terms_note
        })

    mode = "LLM" if (llm_client.is_configured() and llm_calls_succeeded > 0) else "rule-based fallback"
    duration_ms = int((time.time() - start_time) * 1000)
    input_sum = f"Proposals: {len(state.get('proposals', []))}, Farmer Min: ${state['minimum_price']}"
    output_sum = f"Negotiated suggested terms for {len(results)} deals within mutually acceptable boundaries."
    if mode == "rule-based fallback" and fallback_reasons:
        reasons_str = ", ".join(dict.fromkeys(fallback_reasons))
        output_sum = f"{output_sum} ({reasons_str})"

    agent_log = AgentLog(
        agent_name="Negotiation Agent",
        task=task,
        mode=mode,
        input_summary=input_sum,
        output_summary=output_sum,
        decision_status="COMPLETED",
        execution_time_ms=duration_ms
    )
    db.add(agent_log)
    db.commit()

    state["negotiation_results"] = results
    state["agent_logs"].append({
        "agent": "Negotiation Agent",
        "task": task,
        "mode": mode,
        "summary": output_sum,
        "duration_ms": duration_ms
    })
    return state
