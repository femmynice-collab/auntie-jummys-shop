import os
from decimal import Decimal
import pgeocode

def _parse_fee_tiers(s: str):
    tiers = []
    for part in (s or "").split(","):
        part = part.strip()
        if not part: continue
        miles, fee = part.split(":")
        tiers.append((float(miles), Decimal(str(fee))))
    tiers.sort(key=lambda x: x[0])
    return tiers

def distance_miles(zip1: str, zip2: str) -> float:
    nomi = pgeocode.Nominatim('US')
    a = nomi.query_postal_code(zip1)
    b = nomi.query_postal_code(zip2)
    if a is None or b is None or a.latitude != a.latitude or b.latitude != b.latitude:
        return 9999.0
    # Haversine
    from math import radians, sin, cos, sqrt, atan2
    R = 3958.8  # miles
    lat1, lon1 = radians(a.latitude), radians(a.longitude)
    lat2, lon2 = radians(b.latitude), radians(b.longitude)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 2 * R * atan2(sqrt(h), sqrt(1-h))

def compute_tiered_fee(store_zip: str, dest_zip: str, tiers_str: str) -> Decimal:
    try:
        d = distance_miles(store_zip, dest_zip)
        tiers = _parse_fee_tiers(tiers_str)
        for miles, fee in tiers:
            if d <= miles:
                return fee.quantize(Decimal('0.01'))
        return Decimal('0.00')
    except Exception:
        return Decimal('0.00')
