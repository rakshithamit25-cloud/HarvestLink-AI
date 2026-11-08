import math
from typing import Dict, Tuple

# Approximate coordinates for key Tamil Nadu districts and agricultural hubs
# Note: Distances computed using Haversine formula and marked clearly as approximate road distances.
TN_DISTRICT_COORDINATES: Dict[str, Tuple[float, float]] = {
    "salem": (11.6643, 78.1460),
    "salem city": (11.6643, 78.1460),
    "erode": (11.3410, 77.7172),
    "namakkal": (11.2189, 78.1674),
    "dharmapuri": (12.1211, 78.1582),
    "coimbatore": (11.0168, 76.9558),
    "trichy": (10.7905, 78.7047),
    "tiruchirappalli": (10.7905, 78.7047),
    "madurai": (9.9252, 78.1198),
    "chennai": (13.0827, 80.2707),
    "thanjavur": (10.7870, 79.1378),
    "vellore": (12.9165, 79.1325),
    "dindigul": (10.3673, 77.9803),
    "krishnagiri": (12.5186, 78.2138),
    "tiruppur": (11.1085, 77.3411)
}

def normalize_location(name: str) -> str:
    if not name:
        return "salem"
    cleaned = name.strip().lower()
    for key in TN_DISTRICT_COORDINATES:
        if key in cleaned:
            return key
    return "salem"

def calculate_approx_distance_km(loc1: str, loc2: str) -> float:
    """
    Computes approximate road distance in kilometers between two locations.
    Uses Haversine geodesic distance * 1.25 road winding factor.
    """
    norm1 = normalize_location(loc1)
    norm2 = normalize_location(loc2)
    
    if norm1 == norm2:
        return 12.0  # approximate intra-district local delivery km
        
    lat1, lon1 = TN_DISTRICT_COORDINATES.get(norm1, (11.6643, 78.1460))
    lat2, lon2 = TN_DISTRICT_COORDINATES.get(norm2, (11.6643, 78.1460))
    
    # Haversine formula
    r = 6371.0 # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    direct_km = r * c
    
    # Road tortuosity multiplier (approx 1.25x direct geodesic distance)
    approx_road_km = round(direct_km * 1.25, 1)
    return max(approx_road_km, 8.0)
