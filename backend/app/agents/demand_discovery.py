import time
from sqlalchemy.orm import Session
from app.agents.state import HarvestLinkState, BuyerCandidate
from app.models import BuyerRequirement, AgentLog
from app.core.geo import calculate_approx_distance_km

def run_demand_discovery(state: HarvestLinkState, db: Session) -> HarvestLinkState:
    start_time = time.time()
    task = f"Discover buyer demand for {state['quantity']} kg {state['crop_name']} in {state['location']}"
    
    requirements = db.query(BuyerRequirement).filter(
        BuyerRequirement.crop_name.ilike(state["crop_name"]),
        BuyerRequirement.status == "open"
    ).all()

    candidates: list[BuyerCandidate] = []
    for req in requirements:
        dist_km = calculate_approx_distance_km(state["location"], req.location)
        has_overlap = req.maximum_price >= state["minimum_price"]
        
        notes = (
            f"Buyer {req.buyer_name or f'#{req.buyer_id}'} requires {req.required_quantity} kg at max ${req.maximum_price:.2f}/kg. "
            f"Located in {req.location} (~{dist_km} km away). "
            f"{'Budget covers asking/minimum threshold.' if has_overlap else 'No price overlap with farmer minimum threshold.'}"
        )
        
        candidates.append({
            "requirement_id": req.id,
            "buyer_id": req.buyer_id,
            "buyer_name": req.buyer_name or f"Buyer #{req.buyer_id}",
            "crop_name": req.crop_name,
            "required_quantity": req.required_quantity,
            "maximum_price": req.maximum_price,
            "location": req.location,
            "distance_km": dist_km,
            "has_price_overlap": has_overlap,
            "discovery_notes": notes
        })

    # Sort candidates by overlap first, then distance
    candidates.sort(key=lambda c: (not c["has_price_overlap"], c["distance_km"]))
    
    duration_ms = int((time.time() - start_time) * 1000)
    input_sum = f"Crop: {state['crop_name']}, Qty: {state['quantity']} kg, Asking: ${state['expected_price']}, Min: ${state['minimum_price']}"
    output_sum = f"Found {len(candidates)} buyers ({sum(1 for c in candidates if c['has_price_overlap'])} with budget overlap)."
    
    # Persist log to DB
    agent_log = AgentLog(
        agent_name="Demand Discovery Agent",
        task=task,
        mode=state.get("mode", "rule-based"),
        input_summary=input_sum,
        output_summary=output_sum,
        decision_status="COMPLETED",
        execution_time_ms=duration_ms
    )
    db.add(agent_log)
    db.commit()

    state["candidates"] = candidates
    state["agent_logs"].append({
        "agent": "Demand Discovery Agent",
        "task": task,
        "mode": state.get("mode", "rule-based"),
        "summary": output_sum,
        "duration_ms": duration_ms
    })
    return state
