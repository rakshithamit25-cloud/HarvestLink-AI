from typing import TypedDict, List, Dict, Any, Optional

class BuyerCandidate(TypedDict):
    requirement_id: int
    buyer_id: int
    buyer_name: str
    crop_name: str
    required_quantity: float
    maximum_price: float
    location: str
    distance_km: float
    has_price_overlap: bool
    discovery_notes: str

class MatchProposal(TypedDict):
    buyer_requirement_id: int
    buyer_name: str
    allocated_quantity: float
    farmer_asking_price: float
    ai_suggested_price: float
    match_reason: str
    status: str

class HarvestLinkState(TypedDict):
    listing_id: int
    farmer_id: int
    crop_name: str
    quantity: float
    available_quantity: float
    expected_price: float
    minimum_price: float
    location: str
    freshness_status: str
    harvest_date: str
    mode: str  # 'llm' or 'rule-based'
    
    # Pipeline stages
    candidates: List[BuyerCandidate]
    proposals: List[MatchProposal]
    negotiation_results: List[Dict[str, Any]]
    commerce_results: List[Dict[str, Any]]
    
    # Audit & Status
    agent_logs: List[Dict[str, Any]]
    error: Optional[str]
