import time
from sqlalchemy.orm import Session
from app.agents.state import HarvestLinkState, MatchProposal
from app.models import AgentLog, MatchResult, ProduceListing
from app.services.inventory_service import InventoryService, InsufficientStockException

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
            # Atomic reservation in DB
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

    duration_ms = int((time.time() - start_time) * 1000)
    input_sum = f"Stock: {state['quantity']} kg, Candidates: {len(state.get('candidates', []))}"
    output_sum = f"Allocated {allocated_total:.0f} kg across {len([p for p in proposals if p['allocated_quantity'] > 0])} buyers. Remaining: {avail:.0f} kg."

    agent_log = AgentLog(
        agent_name="Matching Agent",
        task=task,
        mode=state.get("mode", "rule-based"),
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
        "mode": state.get("mode", "rule-based"),
        "summary": output_sum,
        "duration_ms": duration_ms
    })
    return state
