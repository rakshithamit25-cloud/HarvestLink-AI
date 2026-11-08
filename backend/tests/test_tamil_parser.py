from app.services.tamil_parser import parse_tamil_or_english_text
from app.api.listings import parse_voice_or_manual_text
from app.schemas import TamilParseRequest

def test_tamil_voice_input_parsing():
    # 1. Test classic Tamil phrase: "என்னிடம் 500 கிலோ தக்காளி விற்பனைக்கு உள்ளது"
    phrase = "என்னிடம் 500 கிலோ தக்காளி விற்பனைக்கு உள்ளது"
    result = parse_tamil_or_english_text(phrase)
    
    assert result["crop_name"] == "Tomato"
    assert result["quantity"] == 500.0
    assert result["unit"] == "kg"
    
    # Missing fields must be detected accurately so the UI prompts the farmer
    assert "expected_price" in result["missing_fields"]
    assert "location" in result["missing_fields"]
    assert "crop_name" not in result["missing_fields"]
    assert "quantity" not in result["missing_fields"]

    # 2. Test full Tamil text with price and location
    full_phrase = "சேலத்தில் 200 கிலோ வெங்காயம் 1 டாலர்"
    result_full = parse_tamil_or_english_text(full_phrase)
    assert result_full["crop_name"] == "Onion"
    assert result_full["quantity"] == 200.0
    assert result_full["expected_price"] == 1.0
    assert result_full["location"] == "Salem"
    assert len(result_full["missing_fields"]) == 0

    # 3. Test API endpoint POST /api/listings/parse-text
    resp = parse_voice_or_manual_text(TamilParseRequest(text=phrase))
    assert resp["crop_name"] == "Tomato"
    assert resp["quantity"] == 500.0
    assert len(resp["missing_fields"]) > 0

    # 4. Test manual fallback when empty or unrecognized
    empty_resp = parse_voice_or_manual_text(TamilParseRequest(text=""))
    assert empty_resp["crop_name"] is None
    assert empty_resp["is_manual_fallback"] is True
    assert len(empty_resp["missing_fields"]) == 4
