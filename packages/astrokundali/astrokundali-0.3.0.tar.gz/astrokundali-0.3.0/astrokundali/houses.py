import math
import swisseph as swe

def equal_houses(asc: float) -> list[float]:
    """Equal 30° houses from the Ascendant."""
    return [(asc + 30*i) % 360 for i in range(12)]

def whole_sign_houses(asc: float) -> list[float]:
    """Whole‐Sign houses: each zodiac sign = one house."""
    start = math.floor(asc/30)*30
    return [(start + 30*i) % 360 for i in range(12)]

def porphyry_houses(asc: float, mc: float) -> list[float]:
    """Porphyry: tri-sect each cardinal quadrant."""
    desc = (asc + 180) % 360
    ic   = (mc   + 180) % 360
    quad = [asc, mc, desc, ic]
    cusps = []
    for i in range(4):
        a, b = quad[i], quad[(i+1)%4]
        diff = (b - a) % 360
        cusps.extend([a, (a+diff/3)%360, (a+2*diff/3)%360])
    return cusps

def swiss_houses(JD, lat, lon, code: bytes) -> list[float]:
    """Swiss Ephemeris house cusps via swe.houses()."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    cusps, _ = swe.houses(JD, lat, lon, code)
    return [cusps[i] for i in range(1,13)]

def placidus_houses(JD, lat, lon):
    return swiss_houses(JD, lat, lon, b'P')

def koch_houses(JD, lat, lon):
    return swiss_houses(JD, lat, lon, b'K')

def campanus_houses(JD, lat, lon):
    return swiss_houses(JD, lat, lon, b'C')

def regiomontanus_houses(JD, lat, lon):
    return swiss_houses(JD, lat, lon, b'R')

HOUSE_SYSTEMS = {
    "equal":         (equal_houses,      False),
    "whole_sign":    (whole_sign_houses, False),
    "porphyry":      (porphyry_houses,   True),
    "placidus":      (placidus_houses,   True),
    "koch":          (koch_houses,       True),
    "campanus":      (campanus_houses,   True),
    "regiomontanus": (regiomontanus_houses, True),
}

def get_house_cusps(
    system: str,
    asc: float,
    JD: float=None,
    lat: float=None,
    lon: float=None,
    mc: float=None
) -> list[float]:
    """
    Dispatch house‐cusp calculation.
    If `needs_mc` is True, `mc` (or JD,lat,lon) must be provided.
    """
    fn, needs_mc = HOUSE_SYSTEMS[system]
    if needs_mc:
        # Porphyry needs (asc,mc); Swiss needs (JD,lat,lon)
        if system == "porphyry":
            if mc is None:
                raise ValueError("Porphyry requires MC")
            return fn(asc, mc)
        else:
            if JD is None or lat is None or lon is None:
                raise ValueError(f"{system} requires JD, lat, lon")
            return fn(JD, lat, lon)
    else:
        return fn(asc)
