from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
from app.agents.state import HarvestLinkState
from app.agents.demand_discovery import run_demand_discovery
from app.agents.matching_agent import run_matching_agent
from app.agents.negotiation_agent import run_negotiation_agent
from app.agents.commerce_agent import run_commerce_agent

def create_harvestlink_graph(db: Session):
    workflow = StateGraph(HarvestLinkState)

    # Wrap nodes with db session
    def demand_discovery_node(state: HarvestLinkState) -> HarvestLinkState:
        return run_demand_discovery(state, db)

    def matching_node(state: HarvestLinkState) -> HarvestLinkState:
        return run_matching_agent(state, db)

    def negotiation_node(state: HarvestLinkState) -> HarvestLinkState:
        return run_negotiation_agent(state, db)

    workflow.add_node("demand_discovery", demand_discovery_node)
    workflow.add_node("matching", matching_node)
    workflow.add_node("negotiation", negotiation_node)

    workflow.set_entry_point("demand_discovery")
    workflow.add_edge("demand_discovery", "matching")
    workflow.add_edge("matching", "negotiation")
    workflow.add_edge("negotiation", END)

    return workflow.compile()

def execute_matching_pipeline(db: Session, listing, mode: str = "rule-based") -> HarvestLinkState:
    graph = create_harvestlink_graph(db)
    
    initial_state: HarvestLinkState = {
        "listing_id": listing.id,
        "farmer_id": listing.farmer_id,
        "crop_name": listing.crop_name,
        "quantity": listing.quantity,
        "available_quantity": listing.available_quantity,
        "expected_price": listing.expected_price,
        "minimum_price": listing.minimum_price,
        "location": listing.location,
        "freshness_status": listing.freshness_status,
        "harvest_date": listing.harvest_date,
        "mode": mode,
        "candidates": [],
        "proposals": [],
        "negotiation_results": [],
        "commerce_results": [],
        "agent_logs": [],
        "error": None
    }
    
    final_state = graph.invoke(initial_state)
    return final_state
