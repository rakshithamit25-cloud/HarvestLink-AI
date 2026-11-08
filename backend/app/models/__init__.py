import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.session import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # 'farmer', 'buyer', 'operator'
    phone = Column(String(20), nullable=True)
    preferred_language = Column(String(10), default="ta")  # 'ta' or 'en'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    listings = relationship("ProduceListing", back_populates="farmer")
    requirements = relationship("BuyerRequirement", back_populates="buyer")


class ProduceListing(Base):
    __tablename__ = "produce_listings"
    
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crop_name = Column(String(100), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    available_quantity = Column(Float, nullable=False)
    unit = Column(String(20), default="kg")
    expected_price = Column(Float, nullable=False)   # farmer_asking_price
    minimum_price = Column(Float, nullable=False)    # threshold for negotiation overlap
    location = Column(String(100), nullable=False)
    harvest_date = Column(String(50), nullable=False)
    freshness_status = Column(String(50), default="fresh")  # 'fresh', 'moderate', 'critical_surplus'
    listing_status = Column(String(50), default="active")    # 'active', 'partially_matched', 'fully_matched', 'completed', 'cancelled'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    farmer = relationship("User", back_populates="listings")
    matches = relationship("MatchResult", back_populates="listing")
    orders = relationship("Order", back_populates="listing")


class BuyerRequirement(Base):
    __tablename__ = "buyer_requirements"
    
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    buyer_name = Column(String(100), nullable=True)
    crop_name = Column(String(100), nullable=False, index=True)
    required_quantity = Column(Float, nullable=False)
    maximum_price = Column(Float, nullable=False)
    location = Column(String(100), nullable=False)
    required_date = Column(String(50), nullable=False)
    status = Column(String(50), default="open")  # 'open', 'partially_fulfilled', 'fulfilled', 'cancelled'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    buyer = relationship("User", back_populates="requirements")
    matches = relationship("MatchResult", back_populates="buyer_requirement")


class MatchResult(Base):
    __tablename__ = "match_results"
    
    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("produce_listings.id"), nullable=False)
    buyer_requirement_id = Column(Integer, ForeignKey("buyer_requirements.id"), nullable=False)
    allocated_quantity = Column(Float, nullable=False)
    
    # Clearly separated pricing fields
    farmer_asking_price = Column(Float, nullable=False)
    ai_suggested_price = Column(Float, nullable=False)  # "AI suggestion, not agreed"
    agreed_price = Column(Float, nullable=True)         # Set only when confirmed by both
    
    match_reason = Column(Text, nullable=False)
    
    # State machine: proposed -> farmer_approved -> buyer_approved -> confirmed (or rejected/no_overlap)
    status = Column(String(50), default="proposed")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    listing = relationship("ProduceListing", back_populates="matches")
    buyer_requirement = relationship("BuyerRequirement", back_populates="matches")
    orders = relationship("Order", back_populates="match")


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("produce_listings.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("match_results.id"), nullable=True)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    quantity = Column(Float, nullable=False)
    agreed_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    
    # Payment status: strictly updated by backend verification
    payment_status = Column(String(50), default="pending")  # 'pending', 'created', 'approved', 'completed', 'failed'
    
    # Order lifecycle
    order_status = Column(String(50), default="created")     # 'created', 'processing', 'delivered', 'cancelled'
    delivery_verified_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    listing = relationship("ProduceListing", back_populates="orders")
    match = relationship("MatchResult", back_populates="orders")
    payment = relationship("Payment", uselist=False, back_populates="order")


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True, nullable=False)  # 1 payment record per order
    paypal_order_id = Column(String(100), nullable=True, index=True)
    paypal_capture_id = Column(String(100), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    
    # Payment state locked transition: created -> approved -> completed
    status = Column(String(50), default="created")
    idempotency_key = Column(String(100), unique=True, nullable=False, index=True)
    is_mock = Column(Boolean, default=False)
    raw_response_json = Column(Text, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    order = relationship("Order", back_populates="payment")


class AgentLog(Base):
    __tablename__ = "agent_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(100), nullable=False)
    task = Column(String(255), nullable=False)
    mode = Column(String(50), default="rule-based")  # 'llm' or 'rule-based'
    input_summary = Column(Text, nullable=False)
    output_summary = Column(Text, nullable=False)
    decision_status = Column(String(50), nullable=False)
    execution_time_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False)
    actor_id = Column(Integer, nullable=False)
    actor_role = Column(String(50), nullable=False)
    
    # Required for FPO operator consent tracking
    consent_method = Column(String(50), nullable=True)  # 'verbal' | 'written'
    farmer_name = Column(String(100), nullable=True)
    
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
