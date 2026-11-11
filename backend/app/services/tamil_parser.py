import re
from typing import Dict, Any, List, Optional

TAMIL_CROP_MAP = {
    # Vegetables
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
    "chillies": "Chilli",
    "chili": "Chilli",
    "முட்டைக்கோஸ்": "Cabbage",
    "cabbage": "Cabbage",
    "காலிஃபிளவர்": "Cauliflower",
    "காலிபிளவர்": "Cauliflower",
    "cauliflower": "Cauliflower",
    "பீன்ஸ்": "Beans",
    "beans": "Beans",
    "bean": "Beans",
    "முருங்கைக்காய்": "Drumstick",
    "முருங்கை": "Drumstick",
    "murungakkai": "Drumstick",
    "drumstick": "Drumstick",
    "பாகற்காய்": "Bitter Gourd",
    "பாகற்கா": "Bitter Gourd",
    "pavakkai": "Bitter Gourd",
    "bitter gourd": "Bitter Gourd",
    "bittergourd": "Bitter Gourd",
    "பூசணிக்காய்": "Pumpkin",
    "பூசணி": "Pumpkin",
    "poosanikkai": "Pumpkin",
    "pumpkin": "Pumpkin",
    "வெள்ளரிக்காய்": "Cucumber",
    "வெள்ளரி": "Cucumber",
    "vellarikkai": "Cucumber",
    "cucumber": "Cucumber",
    "முள்ளங்கி": "Radish",
    "radish": "Radish",
    "பீட்ரூட்": "Beetroot",
    "beetroot": "Beetroot",

    # Fruits
    "தேங்காய்": "Coconut",
    "thengai": "Coconut",
    "coconut": "Coconut",
    "coconuts": "Coconut",
    "வாழைப்பழம்": "Banana",
    "வாழை": "Banana",
    "vazhaipazham": "Banana",
    "banana": "Banana",
    "bananas": "Banana",
    "மாம்பழம்": "Mango",
    "மாங்காய்": "Mango",
    "mango": "Mango",
    "mangoes": "Mango",
    "பப்பாளி": "Papaya",
    "pappali": "Papaya",
    "papaya": "Papaya",
    "கொய்யா": "Guava",
    "கொய்யாப்பழம்": "Guava",
    "koyya": "Guava",
    "guava": "Guava",
    "மாதுளை": "Pomegranate",
    "மாதுளம்பழம்": "Pomegranate",
    "madhulai": "Pomegranate",
    "pomegranate": "Pomegranate",
    "தர்பூசணி": "Watermelon",
    "watermelon": "Watermelon",

    # Pulses and Grains
    "அரிசி": "Rice",
    "நெல்": "Rice",
    "arisi": "Rice",
    "paddy": "Rice",
    "rice": "Rice",
    "மக்காச்சோளம்": "Maize",
    "மக்கா சோளம்": "Maize",
    "சோளம்": "Maize",
    "maize": "Maize",
    "corn": "Maize",
    "வேர்க்கடலை": "Groundnut",
    "நிலக்கடலை": "Groundnut",
    "கடலை": "Groundnut",
    "groundnut": "Groundnut",
    "peanut": "Groundnut",
    "peanuts": "Groundnut",
    "உளுந்து": "Black Gram",
    "ulundhu": "Black Gram",
    "black gram": "Black Gram",
    "blackgram": "Black Gram",
    "urad dal": "Black Gram",
    "பாசிப்பருப்பு": "Green Gram",
    "பாசிப்பயறு": "Green Gram",
    "பயறு": "Green Gram",
    "green gram": "Green Gram",
    "greengram": "Green Gram",
    "moong dal": "Green Gram",

    # Spices
    "மஞ்சள்": "Turmeric",
    "manjal": "Turmeric",
    "turmeric": "Turmeric",
    "இஞ்சி": "Ginger",
    "inji": "Ginger",
    "ginger": "Ginger",
    "பூண்டு": "Garlic",
    "poondu": "Garlic",
    "garlic": "Garlic",
    "கொத்தமல்லி": "Coriander",
    "மல்லி": "Coriander",
    "kothamalli": "Coriander",
    "coriander": "Coriander",

    # Others / Commercial
    "கரும்பு": "Sugarcane",
    "karumbu": "Sugarcane",
    "sugarcane": "Sugarcane"
}

TAMIL_DIGITS = {
    '௦': '0', '௧': '1', '௨': '2', '௩': '3', '௪': '4',
    '௫': '5', '௬': '6', '௭': '7', '௮': '8', '௯': '9'
}

TAMIL_COMPOUND_PREFIXES = {
    # Hundreds compound (e.g. இருநூற்று ஐம்பது = 250)
    "தொள்ளாயிரத்து": 900,
    "எண்ணூற்று": 800,
    "எழுநூற்று": 700,
    "அறுநூற்று": 600,
    "ஐந்நூற்று": 500,
    "ஐநூற்று": 500,
    "நானூற்று": 400,
    "முந்நூற்று": 300,
    "இருநூற்று": 200,
    "நூற்று": 100,
    "நூற்றி": 100,
    "ஆயிரத்து": 1000,
    # Tens compound (e.g. இருபத்து ஐந்து = 25)
    "தொண்ணூற்று": 90,
    "எண்பத்து": 80,
    "எழுபத்து": 70,
    "அறுபத்து": 60,
    "ஐம்பத்து": 50,
    "நாற்பத்து": 40,
    "முப்பத்து": 30,
    "இருபத்து": 20,
}

TAMIL_STANDALONE_WORDS = {
    # Thousands
    "ஆயிரம்": 1000,
    # Hundreds
    "தொள்ளாயிரம்": 900,
    "எண்ணூறு": 800,
    "எழுநூறு": 700,
    "அறுநூறு": 600,
    "ஐந்நூறு": 500,
    "ஐநூறு": 500,
    "நானூறு": 400,
    "முந்நூறு": 300,
    "இருநூறு": 200,
    "நூறு": 100,
    # Tens
    "தொண்ணூறு": 90,
    "எண்பது": 80,
    "எழுபது": 70,
    "அறுபது": 60,
    "ஐம்பது": 50,
    "நாற்பது": 40,
    "முப்பது": 30,
    "இருபது": 20,
    "பத்து": 10,
    # Teens
    "பத்தொன்பது": 19,
    "பதினெட்டு": 18,
    "பதினேழு": 17,
    "பதினாறு": 16,
    "பதினைந்து": 15,
    "பதினான்கு": 14,
    "பதின்மூன்று": 13,
    "பதிமூன்று": 13,
    "பன்னிரண்டு": 12,
    "பதினொன்று": 11,
    # Units
    "ஒன்பது": 9,
    "எட்டு": 8,
    "ஏழு": 7,
    "ஆறு": 6,
    "ஐந்து": 5,
    "நான்கு": 4,
    "மூன்று": 3,
    "இரண்டு": 2,
    "ஒன்று": 1,
}

TAMIL_MULTIPLIERS = {
    "ஒன்று": 1, "ஒரு": 1,
    "இரண்டு": 2, "இரு": 2,
    "மூன்று": 3, "மு": 3,
    "நான்கு": 4,
    "ஐந்து": 5,
    "ஆறு": 6,
    "ஏழு": 7,
    "எட்டு": 8,
    "ஒன்பது": 9,
}

TAMIL_SCALES = {
    "ஆயிரம்": 1000,
    "நூறு": 100,
}

def extract_tamil_word_numbers(text: str) -> List[float]:
    """
    Extracts numerical values written in Tamil words, supporting:
    - Fused forms (e.g. ஐநூறு=500, இருநூறு=200, முந்நூறு=300, நானூறு=400)
    - Multi-word numbers (e.g. நான்கு நூறு=400, இருநூற்று ஐம்பது=250)
    - Compound hundreds + tens/units
    """
    found_values = []
    tokens = text.split()
    i = 0
    while i < len(tokens):
        token = tokens[i].strip(",.?!;:()")
        
        # 3 tokens: e.g. "நான்கு நூற்று ஐம்பது" -> 450
        if i + 2 < len(tokens):
            t1 = tokens[i].strip(",.?!;:()")
            t2 = tokens[i+1].strip(",.?!;:()")
            t3 = tokens[i+2].strip(",.?!;:()")
            if t1 in TAMIL_MULTIPLIERS and t2 in ["நூற்று", "நூற்றி"]:
                mult = TAMIL_MULTIPLIERS[t1]
                if t3 in TAMIL_STANDALONE_WORDS:
                    found_values.append(float(mult * 100 + TAMIL_STANDALONE_WORDS[t3]))
                    i += 3
                    continue

        # 2 tokens:
        if i + 1 < len(tokens):
            t1 = tokens[i].strip(",.?!;:()")
            t2 = tokens[i+1].strip(",.?!;:()")
            # Multiplier + Scale (e.g. 'நான்கு நூறு' -> 400)
            if t1 in TAMIL_MULTIPLIERS and t2 in TAMIL_SCALES:
                found_values.append(float(TAMIL_MULTIPLIERS[t1] * TAMIL_SCALES[t2]))
                i += 2
                continue
            # Compound prefix + standalone (e.g. 'இருநூற்று ஐம்பது' -> 250)
            if t1 in TAMIL_COMPOUND_PREFIXES and t2 in TAMIL_STANDALONE_WORDS:
                found_values.append(float(TAMIL_COMPOUND_PREFIXES[t1] + TAMIL_STANDALONE_WORDS[t2]))
                i += 2
                continue

        # 1 token compound (e.g. if written together)
        matched_compound = False
        for prefix, p_val in TAMIL_COMPOUND_PREFIXES.items():
            if token.startswith(prefix) and len(token) > len(prefix):
                suffix = token[len(prefix):]
                if suffix in TAMIL_STANDALONE_WORDS:
                    found_values.append(float(p_val + TAMIL_STANDALONE_WORDS[suffix]))
                    matched_compound = True
                    break
        if matched_compound:
            i += 1
            continue

        # 1 token standalone (e.g. 'ஐநூறு' -> 500)
        if token in TAMIL_STANDALONE_WORDS:
            found_values.append(float(TAMIL_STANDALONE_WORDS[token]))
            i += 1
            continue

        i += 1

    return found_values

def parse_tamil_or_english_text(raw_text: str) -> Dict[str, Any]:
    """
    Parses voice-transcribed or typed Tamil / English text to extract
    crop name, quantity, expected price, and location. Identifies missing fields.
    Supports fused forms (ஐநூறு=500, இருநூறு=200, முந்நூறு=300, நானூறு=400)
    and multi-word numbers (நான்கு நூறு=400, இருநூற்று ஐம்பது=250).
    Ambiguous input returns status 'needs_confirmation' with candidate values
    and never a guessed quantity.
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
            "is_manual_fallback": True,
            "status": "parsed",
            "candidates": None
        }

    text = raw_text.strip()
    
    # Replace Tamil numeral glyphs with standard Arabic digits
    for t_char, d_char in TAMIL_DIGITS.items():
        text = text.replace(t_char, d_char)

    lower_text = text.lower()

    # 1. Extract Crop (match longer, more specific keywords first)
    detected_crop = None
    for keyword in sorted(TAMIL_CROP_MAP.keys(), key=len, reverse=True):
        if keyword in lower_text or keyword in text:
            detected_crop = TAMIL_CROP_MAP[keyword]
            break

    # 2. Extract Price if present (e.g. "$1", "1 டாலர்", "80 ரூபாய்", "1 dollar")
    # Identify price span so we don't treat price digits as quantity
    detected_price = None
    price_spans = []
    
    for pat in [
        r'(?:\$|ரூபாய்|rs\.?|usd|டாலர்)\s*(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)\s*(?:\$|ரூபாய்|rs\.?|usd|டாலர்|dollars?|dollar|inr)'
    ]:
        for match in re.finditer(pat, text, re.IGNORECASE):
            try:
                val = float(match.group(1))
                if detected_price is None:
                    detected_price = val
                price_spans.append(match.span())
            except ValueError:
                pass

    # Helper: check if a span overlaps with price spans
    def overlaps_price(start: int, end: int) -> bool:
        for p_start, p_end in price_spans:
            if not (end <= p_start or start >= p_end):
                return True
        return False

    # 3. Extract Quantity candidates
    quantity_candidates: List[float] = []

    # A) Find all digit numbers not belonging to price
    unit_pat = r'(\d+(?:\.\d+)?)\s*(?:கிலோ|கிகி|kg|kilogram|kilograms|quintal|quintals|டன்|ton|tons)?'
    for match in re.finditer(unit_pat, text, re.IGNORECASE):
        start, end = match.span()
        if not overlaps_price(start, end):
            try:
                num = float(match.group(1))
                if num > 0:
                    quantity_candidates.append(num)
            except ValueError:
                pass

    # B) Extract Tamil word numbers
    tamil_words_candidates = extract_tamil_word_numbers(text)
    for w_val in tamil_words_candidates:
        if w_val > 0:
            quantity_candidates.append(w_val)

    # De-duplicate while preserving order
    unique_candidates: List[float] = []
    for c in quantity_candidates:
        if c not in unique_candidates:
            unique_candidates.append(c)

    # Ambiguity check:
    # If multiple candidates found, mark as 'needs_confirmation' and never guess!
    status = "parsed"
    detected_qty: Optional[float] = None
    reported_candidates: Optional[List[float]] = None

    if len(unique_candidates) > 1:
        status = "needs_confirmation"
        detected_qty = None
        reported_candidates = unique_candidates
    elif len(unique_candidates) == 1:
        detected_qty = unique_candidates[0]
        status = "parsed"
        reported_candidates = None
    else:
        detected_qty = None
        status = "parsed"
        reported_candidates = None

    # 4. Extract Location if mentioned
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
        "is_manual_fallback": False,
        "status": status,
        "candidates": reported_candidates
    }
