import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Any

# Auth & User
class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    preferred_language: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Listings
class ProduceListingCreate(BaseModel):
    crop_name: str
    quantity: float
    expected_price: float
    minimum_price: float
    location: str
    harvest_date: str
    freshness_status: Optional[str] = "fresh"

class ProduceListingResponse(BaseModel):
    id: int
    farmer_id: int
    crop_name: str
    quantity: float
    available_quantity: float
    unit: str
    expected_price: float
    minimum_price: float
    location: str
    harvest_date: str
    freshness_status: str
    listing_status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Buyer Requirement
class BuyerRequirementCreate(BaseModel):
    crop_name: str
    required_quantity: float
    maximum_price: float
    location: str
    required_date: str

class BuyerRequirementResponse(BaseModel):
    id: int
    buyer_id: int
    buyer_name: Optional[str] = None
    crop_name: str
    required_quantity: float
    maximum_price: float
    location: str
    required_date: str
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Matches
class MatchResultResponse(BaseModel):
    id: int
    listing_id: int
    buyer_requirement_id: int
    buyer_name: Optional[str] = None
    crop_name: Optional[str] = None
    allocated_quantity: float
    farmer_asking_price: float
    ai_suggested_price: float
    agreed_price: Optional[float] = None
    match_reason: str
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class MatchApprovalRequest(BaseModel):
    consent_method: Optional[str] = None  # 'verbal' or 'written' (required if operator)
    farmer_name: Optional[str] = None     # required if operator
    operator_note: Optional[str] = None

# Orders
class OrderResponse(BaseModel):
    id: int
    listing_id: int
    match_id: Optional[int] = None
    farmer_id: int
    buyer_id: int
    buyer_name: Optional[str] = None
    crop_name: Optional[str] = None
    quantity: float
    agreed_price: float
    total_amount: float
    payment_status: str
    order_status: str
    delivery_verified_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class DeliveryConfirmRequest(BaseModel):
    notes: Optional[str] = "Produce inspected and accepted"
    consent_method: Optional[str] = None
    farmer_name: Optional[str] = None

# Payments
class PayPalCreateOrderResponse(BaseModel):
    order_id: int
    paypal_order_id: str
    status: str
    approval_url: str
    is_mock: bool
    mock_mode_notice: Optional[str] = None

class PayPalCaptureRequest(BaseModel):
    paypal_order_id: str

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    paypal_order_id: Optional[str] = None
    paypal_capture_id: Optional[str] = None
    amount: float
    currency: str
    status: str
    is_mock: bool
    verified_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# NLP & Tamil Voice / Text Parsing
class TamilParseRequest(BaseModel):
    text: str

class TamilParseResponse(BaseModel):
    crop_name: Optional[str] = None
    quantity: Optional[float] = None
    unit: str = "kg"
    expected_price: Optional[float] = None
    location: Optional[str] = None
    missing_fields: List[str] = []
    original_text: str
    is_manual_fallback: bool = False

# Agent Logs
class AgentLogResponse(BaseModel):
    id: int
    agent_name: str
    task: str
    mode: str
    input_summary: str
    output_summary: str
    decision_status: str
    execution_time_ms: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Audit Log
class AuditLogResponse(BaseModel):
    id: int
    action: str
    actor_id: int
    actor_role: str
    consent_method: Optional[str] = None
    farmer_name: Optional[str] = None
    details: Optional[str] = None
    timestamp: datetime.datetime

    class Config:
        from_attributes = True

# Impact Metrics
class ImpactMetricsResponse(BaseModel):
    listed_quantity: float
    matched_quantity: float
    confirmed_quantity: float
    delivered_quantity: float
    remaining_unsold_quantity: float
    waste_prevented_verified_kg: float
    is_simulated_demo: bool = True
    active_farmers_count: int
    active_buyers_count: int
    total_value_usd: float
