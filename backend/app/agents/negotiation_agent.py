import time
from sqlalchemy.orm import Session
from app.agents.state import HarvestLinkState
from app.models import AgentLog, MatchResult, BuyerRequirement

def run_negotiation_agent(state: HarvestLinkState, db: Session) -> HarvestLinkState:
    start_time = time.time()
    task = f"Formulate suggested prices within limits for {len(state.get('proposals', []))} proposals"
    
    results = []
    for prop in state.get("proposals", []):
        if prop["status"] == "no_overlap" or prop["allocated_quantity"] <= 0:
            continue

        req = db.query(BuyerRequirement).filter(BuyerRequirement.id == prop["buyer_requirement_id"]).first()
        if not req:
            continue

        # Negotiation pricing logic
        farmer_ask = state["expected_price"]
        farmer_min = state["minimum_price"]
        buyer_max = req.maximum_price

        # Check if buyer max >= asking price
        if buyer_max >= farmer_ask:
            # Middle-ground between farmer asking and buyer max
            suggested = round((farmer_ask + buyer_max) / 2.0, 2)
            terms_note = f"Suggested ${suggested:.2f}/kg (farmer asked ${farmer_ask:.2f}, buyer max ${buyer_max:.2f}). Both parties gain surplus."
        elif buyer_max >= farmer_min:
            # Between farmer minimum and buyer max
            suggested = round((farmer_min + buyer_max) / 2.0, 2)
            terms_note = f"Suggested ${suggested:.2f}/kg (acceptable above farmer minimum ${farmer_min:.2f}, within buyer limit ${buyer_max:.2f})."
        else:
            suggested = 0.0
            terms_note = f"No price overlap: Farmer minimum ${farmer_min:.2f} > Buyer max ${buyer_max:.2f}."

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

    duration_ms = int((time.time() - start_time) * 1000)
    input_sum = f"Proposals: {len(state.get('proposals', []))}, Farmer Min: ${state['minimum_price']}"
    output_sum = f"Negotiated suggested terms for {len(results)} deals within mutually acceptable boundaries."

    agent_log = AgentLog(
        agent_name="Negotiation Agent",
        task=task,
        mode=state.get("mode", "rule-based"),
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
        "mode": state.get("mode", "rule-based"),
        "summary": output_sum,
        "duration_ms": duration_ms
    })
    return state
