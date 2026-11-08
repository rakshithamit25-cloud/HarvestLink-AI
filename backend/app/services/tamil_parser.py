import re
from typing import Dict, Any, List

TAMIL_CROP_MAP = {
    "தக்காளி": "Tomato",
    "thakkali": "Tomato",
    "tomato": "Tomato",
    "tomatoes": "Tomato",
    "வெங்காயம்": "Onion",
    "vengayam": "Onion",
    "onion": "Onion",
    "onions": "Onion",
    "கத்தரிக்காய்": "Brinjal",
    "kathirikkai": "Brinjal",
    "brinjal": "Brinjal",
    "eggplant": "Brinjal",
    "உருளைக்கிழங்கு": "Potato",
    "urulaikilangu": "Potato",
    "potato": "Potato",
    "potatoes": "Potato",
    "கேரட்": "Carrot",
    "carrot": "Carrot",
    "carrots": "Carrot",
    "வெண்டைக்காய்": "Okra",
    "vendaikkai": "Okra",
    "okra": "Okra",
    "ladiesfinger": "Okra",
    "மிளகாய்": "Chilli",
    "milagai": "Chilli",
    "chilli": "Chilli",
    "முட்டைக்கோஸ்": "Cabbage",
    "cabbage": "Cabbage"
}

TAMIL_NUMBER_WORDS = {
    "ஒன்று": 1, "ஒரு": 1,
    "இரண்டு": 2, "இரு": 2,
    "மூன்று": 3, "மு": 3,
    "நான்கு": 4,
    "ஐந்து": 5,
    "ஆறு": 6,
    "ஏழு": 7,
    "எட்டு": 8,
    "ஒன்பது": 9,
    "பத்து": 10,
    "இருபது": 20,
    "முப்பது": 30,
    "நாற்பது": 40,
    "ஐம்பது": 50,
    "நூறு": 100,
    "இருநூறு": 200,
    "முந்நூறு": 300,
    "நானூறு": 400,
    "ஐநூறு": 500,
    "அறுநூறு": 600,
    "எழுநூறு": 700,
    "எண்ணூறு": 800,
    "தொள்ளாயிரம்": 900,
    "ஆயிரம்": 1000
}

TAMIL_DIGITS = {
    '௦': '0', '௧': '1', '௨': '2', '௩': '3', '௪': '4',
    '௫': '5', '௬': '6', '௭': '7', '௮': '8', '௯': '9'
}

def parse_tamil_or_english_text(raw_text: str) -> Dict[str, Any]:
    """
    Parses voice-transcribed or typed Tamil / English text to extract
    crop name, quantity, expected price, and location. Identifies missing fields.
    """
    if not raw_text or not raw_text.strip():
        return {
            "crop_name": None,
            "quantity": None,
            "unit": "kg",
            "expected_price": None,
            "location": None,
            "missing_fields": ["crop_name", "quantity", "expected_price", "location"],
            "original_text": raw_text or "",
            "is_manual_fallback": True
        }
        
    text = raw_text.strip()
    
    # Replace Tamil numeral glyphs with standard digits
    for t_char, d_char in TAMIL_DIGITS.items():
        text = text.replace(t_char, d_char)
        
    lower_text = text.lower()
    
    # 1. Extract Crop
    detected_crop = None
    for keyword, standard_name in TAMIL_CROP_MAP.items():
        if keyword in lower_text or keyword in text:
            detected_crop = standard_name
            break

    # 2. Extract Quantity
    detected_qty = None
    
    # Check numeric patterns e.g. "500 kg", "500 கிலோ", "500"
    num_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:கிலோ|கிகி|kg|kilogram|kilograms|quintal)?', text, re.IGNORECASE)
    if num_match:
        try:
            detected_qty = float(num_match.group(1))
        except ValueError:
            pass

    # Check Tamil written number words if no digit found
    if detected_qty is None:
        for word, val in TAMIL_NUMBER_WORDS.items():
            if word in text:
                detected_qty = float(val)
                break

    # 3. Extract Price if present (e.g. "$1", "1 டாலர்", "80 ரூபாய்", "1 dollar")
    detected_price = None
    price_match = re.search(r'(?:\$|ரூபாய்|rs|usd|\$|டாலர்)\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    if not price_match:
        price_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:\$|ரூபாய்|rs|usd|டாலர்|dollars?|dollar)', text, re.IGNORECASE)
    if price_match:
        try:
            detected_price = float(price_match.group(1))
        except ValueError:
            pass

    # 4. Extract Location if mentioned (e.g. "Salem", "சேலம்", "சேலத்தில்", "Erode", "ஈரோடு")
    detected_location = None
    loc_keywords = {
        "சேல": "Salem", "salem": "Salem",
        "ஈரோ": "Erode", "erode": "Erode",
        "நாமக்": "Namakkal", "namakkal": "Namakkal",
        "தர்மபுரி": "Dharmapuri", "dharmapuri": "Dharmapuri",
        "கோயம்ப": "Coimbatore", "கோவை": "Coimbatore", "coimbatore": "Coimbatore",
        "திருச்சி": "Trichy", "trichy": "Trichy", "மதுரை": "Madurai", "madurai": "Madurai",
        "சென்னை": "Chennai", "chennai": "Chennai"
    }
    for loc_key, loc_val in loc_keywords.items():
        if loc_key in lower_text or loc_key in text:
            detected_location = loc_val
            break

    missing = []
    if not detected_crop:
        missing.append("crop_name")
    if detected_qty is None or detected_qty <= 0:
        missing.append("quantity")
    if detected_price is None or detected_price <= 0:
        missing.append("expected_price")
    if not detected_location:
        missing.append("location")

    return {
        "crop_name": detected_crop,
        "quantity": detected_qty,
        "unit": "kg",
        "expected_price": detected_price,
        "location": detected_location,
        "missing_fields": missing,
        "original_text": raw_text,
        "is_manual_fallback": False
    }
