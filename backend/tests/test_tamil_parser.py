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


def test_tamil_parser_fused_forms():
    # Fused forms: ஐநூறு=500, இருநூறு=200, முந்நூறு=300, நானூறு=400
    res_500 = parse_tamil_or_english_text("என்னிடம் ஐநூறு கிலோ தக்காளி உள்ளது")
    assert res_500["quantity"] == 500.0
    assert res_500["crop_name"] == "Tomato"
    assert res_500["status"] == "parsed"

    res_200 = parse_tamil_or_english_text("இருநூறு கிலோ வெங்காயம்")
    assert res_200["quantity"] == 200.0
    assert res_200["crop_name"] == "Onion"
    assert res_200["status"] == "parsed"

    res_300 = parse_tamil_or_english_text("முந்நூறு கிலோ தக்காளி")
    assert res_300["quantity"] == 300.0
    assert res_300["crop_name"] == "Tomato"
    assert res_300["status"] == "parsed"

    res_400 = parse_tamil_or_english_text("நானூறு கிலோ உருளைக்கிழங்கு")
    assert res_400["quantity"] == 400.0
    assert res_400["crop_name"] == "Potato"
    assert res_400["status"] == "parsed"


def test_tamil_parser_multi_word_numbers():
    # Multi-word numbers: நான்கு நூறு=400, இருநூற்று ஐம்பது=250
    res_400 = parse_tamil_or_english_text("நான்கு நூறு கிலோ தக்காளி")
    assert res_400["quantity"] == 400.0
    assert res_400["crop_name"] == "Tomato"
    assert res_400["status"] == "parsed"

    res_250 = parse_tamil_or_english_text("இருநூற்று ஐம்பது கிலோ வெங்காயம்")
    assert res_250["quantity"] == 250.0
    assert res_250["crop_name"] == "Onion"
    assert res_250["status"] == "parsed"


def test_tamil_parser_ambiguous_input():
    # Ambiguous input must return status "needs_confirmation" with candidate values and never a guessed quantity
    res_tamil_or = parse_tamil_or_english_text("500 அல்லது 600 கிலோ தக்காளி")
    assert res_tamil_or["status"] == "needs_confirmation"
    assert res_tamil_or["quantity"] is None
    assert res_tamil_or["candidates"] == [500.0, 600.0]
    assert "quantity" in res_tamil_or["missing_fields"]

    res_words_or = parse_tamil_or_english_text("ஐநூறு அல்லது அறுநூறு கிலோ தக்காளி")
    assert res_words_or["status"] == "needs_confirmation"
    assert res_words_or["quantity"] is None
    assert res_words_or["candidates"] == [500.0, 600.0]
    assert "quantity" in res_words_or["missing_fields"]

    res_en_or = parse_tamil_or_english_text("500 or 600 kg tomatoes")
    assert res_en_or["status"] == "needs_confirmation"
    assert res_en_or["quantity"] is None
    assert res_en_or["candidates"] == [500.0, 600.0]
    assert "quantity" in res_en_or["missing_fields"]


def test_tamil_parser_tamil_digits():
    # Tamil numeral glyphs: ௫௦௦ = 500
    res = parse_tamil_or_english_text("சேலத்தில் ௫௦௦ கிலோ தக்காளி $1")
    assert res["crop_name"] == "Tomato"
    assert res["quantity"] == 500.0
    assert res["expected_price"] == 1.0
    assert res["location"] == "Salem"
    assert res["status"] == "parsed"


def test_tamil_parser_english_digits():
    # Standard English / Arabic digits: 500
    res = parse_tamil_or_english_text("சேலத்தில் 500 கிலோ தக்காளி $1")
    assert res["crop_name"] == "Tomato"
    assert res["quantity"] == 500.0
    assert res["expected_price"] == 1.0
    assert res["location"] == "Salem"
    assert res["status"] == "parsed"


def test_tamil_parser_missing_quantity():
    # Missing quantity must leave quantity None and list it in missing_fields
    res = parse_tamil_or_english_text("என்னிடம் தக்காளி உள்ளது சேலம்")
    assert res["crop_name"] == "Tomato"
    assert res["quantity"] is None
    assert "quantity" in res["missing_fields"]
    assert res["location"] == "Salem"
    assert res["status"] == "parsed"


def test_tamil_parser_english_sentence():
    # Full English sentence parsing
    res = parse_tamil_or_english_text("I have 500 kg of fresh tomatoes in Salem for 1 dollar")
    assert res["crop_name"] == "Tomato"
    assert res["quantity"] == 500.0
    assert res["expected_price"] == 1.0
    assert res["location"] == "Salem"
    assert len(res["missing_fields"]) == 0
    assert res["status"] == "parsed"

