import time
from sqlalchemy.orm import Session
from app.agents.state import HarvestLinkState
from app.models import AgentLog, MatchResult, Order
from app.services.order_service import OrderService
from app.services.paypal_service import PayPalService

def run_commerce_agent(state: HarvestLinkState, db: Session) -> HarvestLinkState:
    start_time = time.time()
    task = f"Coordinate PayPal Sandbox checkout preparation for confirmed matches on listing {state['listing_id']}"
    
    confirmed_matches = db.query(MatchResult).filter(
        MatchResult.listing_id == state["listing_id"],
        MatchResult.status == "confirmed"
    ).all()

    commerce_results = []
    for match in confirmed_matches:
        order = OrderService.create_order_from_confirmed_match(db, match.id)
        payment, approval_url = PayPalService.create_order(db, order)
        
        commerce_results.append({
            "order_id": order.id,
            "paypal_order_id": payment.paypal_order_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status,
            "approval_url": approval_url,
            "is_mock": payment.is_mock
        })

    duration_ms = int((time.time() - start_time) * 1000)
    input_sum = f"Confirmed matches: {len(confirmed_matches)}"
    output_sum = f"Prepared {len(commerce_results)} PayPal checkout orders with unique idempotency keys."

    agent_log = AgentLog(
        agent_name="PayPal Commerce Agent",
        task=task,
        mode=state.get("mode", "rule-based"),
        input_summary=input_sum,
        output_summary=output_sum,
        decision_status="COMPLETED",
        execution_time_ms=duration_ms
    )
    db.add(agent_log)
    db.commit()

    state["commerce_results"] = commerce_results
    state["agent_logs"].append({
        "agent": "PayPal Commerce Agent",
        "task": task,
        "mode": state.get("mode", "rule-based"),
        "summary": output_sum,
        "duration_ms": duration_ms
    })
    return state
