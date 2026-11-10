import time
import logging
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.agents.state import HarvestLinkState, BuyerCandidate
from app.models import BuyerRequirement, AgentLog
from app.core.geo import calculate_approx_distance_km
from app.agents.llm_client import LLMClient

logger = logging.getLogger(__name__)

class DemandDiscoveryExplanation(BaseModel):
    summary: str
    demand_level: str

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
    
    # LLM Enhancement for Demand Summary
    mode = "rule-based fallback"
    llm_client = LLMClient()
    overlap_count = sum(1 for c in candidates if c["has_price_overlap"])
    base_summary = f"Found {len(candidates)} buyers ({overlap_count} with budget overlap)."
    output_sum = base_summary

    if llm_client.is_configured():
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an agricultural demand discovery assistant. "
                    "Analyze the discovery results and return a JSON object with keys: "
                    "'summary' (string: brief 1-sentence market assessment) and "
                    "'demand_level' (string: 'high', 'moderate', or 'low')."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Crop: {state['crop_name']}, Quantity: {state['quantity']} kg, "
                    f"Location: {state['location']}, Total Buyers Found: {len(candidates)}, "
                    f"Buyers with Budget Overlap: {overlap_count}."
                )
            }
        ]
        llm_resp = llm_client.chat_completion_json(messages)
        if llm_resp:
            try:
                validated = DemandDiscoveryExplanation(**llm_resp)
                mode = "LLM"
                output_sum = f"{base_summary} AI Demand: {validated.demand_level.upper()} - {validated.summary}"
            except Exception as e:
                logger.warning(f"Demand Discovery validation failed: {type(e).__name__} (invalid schema)")
                mode = "rule-based fallback"
                output_sum = f"{base_summary} (fallback: invalid schema)"

    duration_ms = int((time.time() - start_time) * 1000)
    input_sum = f"Crop: {state['crop_name']}, Qty: {state['quantity']} kg, Asking: ${state['expected_price']}, Min: ${state['minimum_price']}"
    
    # Persist log to DB
    agent_log = AgentLog(
        agent_name="Demand Discovery Agent",
        task=task,
        mode=mode,
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
        "mode": mode,
        "summary": output_sum,
        "duration_ms": duration_ms
    })
    return state
