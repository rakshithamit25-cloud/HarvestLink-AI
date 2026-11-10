import json
import pytest
from unittest.mock import patch, MagicMock
import httpx

from app.core.config import settings
from app.agents.llm_client import LLMClient
from app.models import ProduceListing, BuyerRequirement, MatchResult, AgentLog, User
from app.agents.demand_discovery import run_demand_discovery
from app.agents.matching_agent import run_matching_agent
from app.agents.negotiation_agent import run_negotiation_agent
from app.agents.state import HarvestLinkState


# ---------------------------------------------------------------------------
# LLMClient Unit Tests
# ---------------------------------------------------------------------------

def test_llm_client_unconfigured():
    client = LLMClient(api_key="", model="")
    assert not client.is_configured()
    assert client.chat_completion_json([{"role": "user", "content": "hi"}]) is None

    client_no_key = LLMClient(api_key=None, model="test-model")
    with patch.object(settings, "LLM_API_KEY", ""):
        client_no_key.api_key = ""
        assert not client_no_key.is_configured()
        assert client_no_key.chat_completion_json([{"role": "user", "content": "hi"}]) is None


def test_llm_client_success():
    client = LLMClient(api_key="mock-key", model="mock-model", base_url="https://api.test.com/v1")
    assert client.is_configured()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({"summary": "High demand in Salem", "demand_level": "high"})
                }
            }
        ]
    }

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        result = client.chat_completion_json([{"role": "user", "content": "test"}])
        assert result == {"summary": "High demand in Salem", "demand_level": "high"}
        assert mock_post.call_count == 1
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.test.com/v1/chat/completions"
        assert kwargs["headers"]["Authorization"] == "Bearer mock-key"
        assert kwargs["json"]["model"] == "mock-model"
        assert kwargs["json"]["response_format"] == {"type": "json_object"}


def test_llm_client_retry_on_timeout_succeeds():
    client = LLMClient(api_key="mock-key", model="mock-model", max_retries=1)

    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.json.return_value = {
        "choices": [{"message": {"content": json.dumps({"status": "ok"})}}]
    }

    with patch("httpx.Client.post", side_effect=[httpx.TimeoutException("timeout"), mock_success]) as mock_post:
        result = client.chat_completion_json([{"role": "user", "content": "test"}])
        assert result == {"status": "ok"}
        assert mock_post.call_count == 2


def test_llm_client_exhausts_retries_returns_none():
    client = LLMClient(api_key="mock-key", model="mock-model", max_retries=1)

    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("timeout")) as mock_post:
        result = client.chat_completion_json([{"role": "user", "content": "test"}])
        assert result is None
        assert mock_post.call_count == 2


def test_llm_client_invalid_json_returns_none():
    client = LLMClient(api_key="mock-key", model="mock-model")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "This is raw text, not valid JSON."}}]
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        result = client.chat_completion_json([{"role": "user", "content": "test"}])
        assert result is None


def test_llm_client_http_error_status_returns_none():
    client = LLMClient(api_key="mock-key", model="mock-model", max_retries=1)

    mock_resp = MagicMock()
    mock_resp.status_code = 500

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        result = client.chat_completion_json([{"role": "user", "content": "test"}])
        assert result is None
        assert mock_post.call_count == 2


# ---------------------------------------------------------------------------
# Demand Discovery Agent Tests
# ---------------------------------------------------------------------------

@pytest.fixture
def agent_test_data(db_session):
    farmer = db_session.query(User).filter(User.role == "farmer").first()
    buyers = db_session.query(User).filter(User.role == "buyer").all()

    listing = ProduceListing(
        farmer_id=farmer.id,
        crop_name="Tomato",
        quantity=500.0,
        available_quantity=500.0,
        unit="kg",
        expected_price=1.00,
        minimum_price=0.90,
        location="Salem",
        harvest_date="2026-11-08",
        freshness_status="fresh",
        listing_status="active"
    )
    db_session.add(listing)

    req = BuyerRequirement(
        buyer_id=buyers[0].id,
        buyer_name="Restaurant A",
        crop_name="Tomato",
        required_quantity=200.0,
        maximum_price=1.20,
        location="Salem",
        required_date="2026-11-10",
        status="open"
    )
    db_session.add(req)
    db_session.commit()
    db_session.refresh(listing)
    db_session.refresh(req)

    initial_state: HarvestLinkState = {
        "listing_id": listing.id,
        "farmer_id": farmer.id,
        "crop_name": "Tomato",
        "quantity": 500.0,
        "expected_price": 1.00,
        "minimum_price": 0.90,
        "location": "Salem",
        "freshness_status": "fresh",
        "available_quantity": 500.0,
        "candidates": [],
        "proposals": [],
        "agent_logs": []
    }
    return listing, req, initial_state


def test_demand_discovery_agent_llm_success(db_session, agent_test_data):
    listing, req, state = agent_test_data

    llm_mock_data = {
        "summary": "Strong demand in Salem area.",
        "demand_level": "high"
    }

    with patch.object(LLMClient, "is_configured", return_value=True), \
         patch.object(LLMClient, "chat_completion_json", return_value=llm_mock_data):
        out_state = run_demand_discovery(state, db_session)

        assert len(out_state["candidates"]) == 1
        log = out_state["agent_logs"][-1]
        assert log["mode"] == "LLM"
        assert "AI Demand: HIGH" in log["summary"]

        # Check DB log
        db_log = db_session.query(AgentLog).filter(AgentLog.agent_name == "Demand Discovery Agent").order_by(AgentLog.id.desc()).first()
        assert db_log.mode == "LLM"
        assert "AI Demand: HIGH" in db_log.output_summary


def test_demand_discovery_agent_fallback_on_unconfigured(db_session, agent_test_data):
    listing, req, state = agent_test_data

    with patch.object(LLMClient, "is_configured", return_value=False):
        out_state = run_demand_discovery(state, db_session)

        log = out_state["agent_logs"][-1]
        assert log["mode"] == "rule-based fallback"
        assert "Found 1 buyers" in log["summary"]

        db_log = db_session.query(AgentLog).filter(AgentLog.agent_name == "Demand Discovery Agent").order_by(AgentLog.id.desc()).first()
        assert db_log.mode == "rule-based fallback"


def test_demand_discovery_agent_fallback_on_invalid_schema(db_session, agent_test_data):
    listing, req, state = agent_test_data

    # Missing 'demand_level' key required by DemandDiscoveryExplanation
    with patch.object(LLMClient, "is_configured", return_value=True), \
         patch.object(LLMClient, "chat_completion_json", return_value={"summary": "Some summary without level"}):
        out_state = run_demand_discovery(state, db_session)

        log = out_state["agent_logs"][-1]
        assert log["mode"] == "rule-based fallback"

        db_log = db_session.query(AgentLog).filter(AgentLog.agent_name == "Demand Discovery Agent").order_by(AgentLog.id.desc()).first()
        assert db_log.mode == "rule-based fallback"


# ---------------------------------------------------------------------------
# Matching Agent Tests
# ---------------------------------------------------------------------------

def test_matching_agent_llm_success(db_session, agent_test_data):
    listing, req, state = agent_test_data
    # First populate candidates
    state["candidates"] = [{
        "requirement_id": req.id,
        "buyer_id": req.buyer_id,
        "buyer_name": req.buyer_name,
        "crop_name": req.crop_name,
        "required_quantity": req.required_quantity,
        "maximum_price": req.maximum_price,
        "location": req.location,
        "distance_km": 0.0,
        "has_price_overlap": True,
        "discovery_notes": "Test"
    }]

    with patch.object(LLMClient, "is_configured", return_value=True), \
         patch.object(LLMClient, "chat_completion_json", return_value={"rationale": "Prioritized local buyer."}):
        out_state = run_matching_agent(state, db_session)

        assert len(out_state["proposals"]) == 1
        assert out_state["proposals"][0]["allocated_quantity"] == 200.0
        assert out_state["available_quantity"] == 300.0

        log = out_state["agent_logs"][-1]
        assert log["mode"] == "LLM"
        assert "AI Note: Prioritized local buyer." in log["summary"]

        db_log = db_session.query(AgentLog).filter(AgentLog.agent_name == "Matching Agent").order_by(AgentLog.id.desc()).first()
        assert db_log.mode == "LLM"


def test_matching_agent_fallback_on_llm_timeout(db_session, agent_test_data):
    listing, req, state = agent_test_data
    state["candidates"] = [{
        "requirement_id": req.id,
        "buyer_id": req.buyer_id,
        "buyer_name": req.buyer_name,
        "crop_name": req.crop_name,
        "required_quantity": req.required_quantity,
        "maximum_price": req.maximum_price,
        "location": req.location,
        "distance_km": 0.0,
        "has_price_overlap": True,
        "discovery_notes": "Test"
    }]

    with patch.object(LLMClient, "is_configured", return_value=True), \
         patch.object(LLMClient, "chat_completion_json", return_value=None):
        out_state = run_matching_agent(state, db_session)

        log = out_state["agent_logs"][-1]
        assert log["mode"] == "rule-based fallback"

        db_log = db_session.query(AgentLog).filter(AgentLog.agent_name == "Matching Agent").order_by(AgentLog.id.desc()).first()
        assert db_log.mode == "rule-based fallback"


# ---------------------------------------------------------------------------
# Negotiation Agent Tests
# ---------------------------------------------------------------------------

def test_negotiation_agent_llm_success_and_within_bounds(db_session, agent_test_data):
    listing, req, state = agent_test_data

    # Setup match in DB first
    match_rec = MatchResult(
        listing_id=listing.id,
        buyer_requirement_id=req.id,
        allocated_quantity=200.0,
        farmer_asking_price=1.00,
        ai_suggested_price=1.10,
        agreed_price=None,
        match_reason="Initial allocation",
        status="proposed"
    )
    db_session.add(match_rec)
    db_session.commit()

    state["proposals"] = [{
        "buyer_requirement_id": req.id,
        "buyer_name": req.buyer_name,
        "allocated_quantity": 200.0,
        "farmer_asking_price": 1.00,
        "ai_suggested_price": 1.10,
        "match_reason": "Initial allocation",
        "status": "proposed"
    }]

    # Farmer min is 0.90, buyer max is 1.20. LLM suggests 1.12.
    llm_suggestion = {
        "suggested_price": 1.12,
        "rationale": "Fair split of surplus between farmer and buyer."
    }

    with patch.object(LLMClient, "is_configured", return_value=True), \
         patch.object(LLMClient, "chat_completion_json", return_value=llm_suggestion):
        out_state = run_negotiation_agent(state, db_session)

        assert out_state["proposals"][0]["ai_suggested_price"] == 1.12
        log = out_state["agent_logs"][-1]
        assert log["mode"] == "LLM"

        db_log = db_session.query(AgentLog).filter(AgentLog.agent_name == "Negotiation Agent").order_by(AgentLog.id.desc()).first()
        assert db_log.mode == "LLM"

        db_session.refresh(match_rec)
        assert match_rec.ai_suggested_price == 1.12


def test_negotiation_agent_rejects_out_of_bounds_llm_price(db_session, agent_test_data):
    listing, req, state = agent_test_data

    match_rec = MatchResult(
        listing_id=listing.id,
        buyer_requirement_id=req.id,
        allocated_quantity=200.0,
        farmer_asking_price=1.00,
        ai_suggested_price=1.10,
        agreed_price=None,
        match_reason="Initial allocation",
        status="proposed"
    )
    db_session.add(match_rec)
    db_session.commit()

    state["proposals"] = [{
        "buyer_requirement_id": req.id,
        "buyer_name": req.buyer_name,
        "allocated_quantity": 200.0,
        "farmer_asking_price": 1.00,
        "ai_suggested_price": 1.10,
        "match_reason": "Initial allocation",
        "status": "proposed"
    }]

    # Buyer max is 1.20. LLM suggests 1.50 (violating buyer max ceiling!).
    llm_suggestion = {
        "suggested_price": 1.50,
        "rationale": "High price suggested by LLM."
    }

    with patch.object(LLMClient, "is_configured", return_value=True), \
         patch.object(LLMClient, "chat_completion_json", return_value=llm_suggestion):
        out_state = run_negotiation_agent(state, db_session)

        # Rule-based calculation: (expected_price 1.00 + buyer_max 1.20) / 2 = 1.10
        assert out_state["proposals"][0]["ai_suggested_price"] == 1.10
        log = out_state["agent_logs"][-1]
        # Because the LLM price was rejected, llm_calls_succeeded is 0 -> fallback
        assert log["mode"] == "rule-based fallback"

        db_log = db_session.query(AgentLog).filter(AgentLog.agent_name == "Negotiation Agent").order_by(AgentLog.id.desc()).first()
        assert db_log.mode == "rule-based fallback"


def test_negotiation_agent_fallback_on_unconfigured(db_session, agent_test_data):
    listing, req, state = agent_test_data

    match_rec = MatchResult(
        listing_id=listing.id,
        buyer_requirement_id=req.id,
        allocated_quantity=200.0,
        farmer_asking_price=1.00,
        ai_suggested_price=1.10,
        agreed_price=None,
        match_reason="Initial allocation",
        status="proposed"
    )
    db_session.add(match_rec)
    db_session.commit()

    state["proposals"] = [{
        "buyer_requirement_id": req.id,
        "buyer_name": req.buyer_name,
        "allocated_quantity": 200.0,
        "farmer_asking_price": 1.00,
        "ai_suggested_price": 1.10,
        "match_reason": "Initial allocation",
        "status": "proposed"
    }]

    with patch.object(LLMClient, "is_configured", return_value=False):
        out_state = run_negotiation_agent(state, db_session)

        # Rule-based price
        assert out_state["proposals"][0]["ai_suggested_price"] == 1.10
        log = out_state["agent_logs"][-1]
        assert log["mode"] == "rule-based fallback"

        db_log = db_session.query(AgentLog).filter(AgentLog.agent_name == "Negotiation Agent").order_by(AgentLog.id.desc()).first()
        assert db_log.mode == "rule-based fallback"
