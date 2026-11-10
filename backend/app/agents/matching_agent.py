import time
import logging
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.agents.state import HarvestLinkState, MatchProposal
from app.models import AgentLog, MatchResult, ProduceListing
from app.services.inventory_service import InventoryService, InsufficientStockException
from app.agents.llm_client import LLMClient

logger = logging.getLogger(__name__)

class MatchingExplanation(BaseModel):
    rationale: str

def run_matching_agent(state: HarvestLinkState, db: Session) -> HarvestLinkState:
    start_time = time.time()
    task = f"Allocate {state['quantity']} kg {state['crop_name']} across discovered buyers"
    
    listing = db.query(ProduceListing).filter(ProduceListing.id == state["listing_id"]).first()
    avail = listing.available_quantity if listing else state.get("available_quantity", state["quantity"])
    
    proposals: list[MatchProposal] = []
    allocated_total = 0.0

    for candidate in state.get("candidates", []):
        if not candidate["has_price_overlap"]:
            # Record no overlap
            proposals.append({
                "buyer_requirement_id": candidate["requirement_id"],
                "buyer_name": candidate["buyer_name"],
                "allocated_quantity": 0.0,
                "farmer_asking_price": state["expected_price"],
                "ai_suggested_price": 0.0,
                "match_reason": f"No price overlap: Farmer minimum ${state['minimum_price']:.2f} exceeds buyer max ${candidate['maximum_price']:.2f}",
                "status": "no_overlap"
            })
            continue

        if avail <= 0.001:
            break

        to_alloc = min(avail, candidate["required_quantity"])
        if to_alloc <= 0:
            continue

        # Propose initial price within limits
        if candidate["maximum_price"] >= state["expected_price"]:
            initial_price = round((state["expected_price"] + candidate["maximum_price"]) / 2.0, 2)
        else:
            initial_price = round(candidate["maximum_price"], 2)

        reason = (
            f"Needs {candidate['crop_name']}, {to_alloc:.0f} kg allocated. "
            f"Located in {candidate['location']} (~{candidate['distance_km']} km away). "
            f"Freshness status: {state['freshness_status']}."
        )

        try:
            # Atomic reservation in DB - backend strictly decides and reserves
            InventoryService.reserve_stock(db, state["listing_id"], to_alloc)
            avail -= to_alloc
            allocated_total += to_alloc

            # Create or update MatchResult record in DB
            match_rec = MatchResult(
                listing_id=state["listing_id"],
                buyer_requirement_id=candidate["requirement_id"],
                allocated_quantity=to_alloc,
                farmer_asking_price=state["expected_price"],
                ai_suggested_price=initial_price,
                agreed_price=None,
                match_reason=reason,
                status="proposed"
            )
            db.add(match_rec)
            db.commit()
            db.refresh(match_rec)

            proposals.append({
                "buyer_requirement_id": candidate["requirement_id"],
                "buyer_name": candidate["buyer_name"],
                "allocated_quantity": to_alloc,
                "farmer_asking_price": state["expected_price"],
                "ai_suggested_price": initial_price,
                "match_reason": reason,
                "status": "proposed"
            })
        except InsufficientStockException:
            break

    state["available_quantity"] = avail
    state["proposals"] = proposals

    # LLM Enhancement for Allocation Rationale
    mode = "rule-based fallback"
    llm_client = LLMClient()
    active_matches_count = len([p for p in proposals if p["allocated_quantity"] > 0])
    base_summary = f"Allocated {allocated_total:.0f} kg across {active_matches_count} buyers. Remaining: {avail:.0f} kg."
    output_sum = base_summary

    if llm_client.is_configured():
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an agricultural inventory allocation assistant. "
                    "Provide a brief rationale for the stock allocation across buyers based on proximity and price in JSON. "
                    "Return a JSON object with key 'rationale' (string)."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Crop: {state['crop_name']}, Total stock: {state['quantity']} kg, "
                    f"Allocated: {allocated_total:.0f} kg across {active_matches_count} buyers, "
                    f"Remaining: {avail:.0f} kg."
                )
            }
        ]
        llm_resp = llm_client.chat_completion_json(messages)
        if llm_resp:
            try:
                validated = MatchingExplanation(**llm_resp)
                mode = "LLM"
                output_sum = f"{base_summary} AI Note: {validated.rationale}"
            except Exception as e:
                logger.warning(f"Matching Agent validation failed: {type(e).__name__} (invalid schema)")
                mode = "rule-based fallback"
                output_sum = f"{base_summary} (fallback: invalid schema)"

    duration_ms = int((time.time() - start_time) * 1000)
    input_sum = f"Stock: {state['quantity']} kg, Candidates: {len(state.get('candidates', []))}"

    agent_log = AgentLog(
        agent_name="Matching Agent",
        task=task,
        mode=mode,
        input_summary=input_sum,
        output_summary=output_sum,
        decision_status="COMPLETED",
        execution_time_ms=duration_ms
    )
    db.add(agent_log)
    db.commit()

    state["agent_logs"].append({
        "agent": "Matching Agent",
        "task": task,
        "mode": mode,
        "summary": output_sum,
        "duration_ms": duration_ms
    })
    return state
