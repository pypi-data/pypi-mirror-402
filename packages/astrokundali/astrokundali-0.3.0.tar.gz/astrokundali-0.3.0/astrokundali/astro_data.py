import swisseph as swe
from .date_converter import DateConverter

# Available ayanamsa modes
AYANAMSA = {
    "fagan_bradley": 0,
    "lahiri":        1,
    "deluce":        2,
    "raman":         3,
    "krishnamurti":  5,
    "sassanian":    16,
    "aldebaran":    14,
    "galcenter":    17
}

# Planet codes for swe.calc_ut
PLANETS = {
    "sun":        swe.SUN,
    "moon":       swe.MOON,
    "mercury":    swe.MERCURY,
    "venus":      swe.VENUS,
    "mars":       swe.MARS,
    "jupiter":    swe.JUPITER,
    "saturn":     swe.SATURN,
    "uranus":     swe.URANUS,
    "neptune":    swe.NEPTUNE,
    "pluto":      swe.PLUTO,
    "north_node": swe.MEAN_NODE
}

class AstroData:
    """
    Compute sidereal longitudes for Ascendant and planets via pyswisseph.
    """
    def __init__(
        self,
        year, month, day, hour, minute, second,
        utc_offset_hours, utc_offset_minutes,
        latitude, longitude,
        ayanamsa="lahiri"
    ):
        # pack into simple object
        DateInfo = type("D",(),dict(
            year=year, month=month, day=day,
            hour=hour, minute=minute, second=second,
            utc_offset_hours=utc_offset_hours,
            utc_offset_minutes=utc_offset_minutes
        ))
        self.julian_day = DateConverter(DateInfo).to_julian_day()
        self.lat = latitude
        self.lon = longitude
        self._sid_mode = AYANAMSA[ayanamsa.lower()]

        # Remember the UTC offset so others can read it later
        self.utc_offset_hours   = utc_offset_hours
        self.utc_offset_minutes = utc_offset_minutes

    def get_rashi_data(self) -> dict:
        """
        Returns a dict of:
          { 'ascendant':{sign_num,lon,retro}, 'sun':{...}, ... }
        """
        swe.set_sid_mode(self._sid_mode, 0, 0)
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL

        # Ascendant from Swiss Ephemeris
        cusps, ascmc = swe.houses_ex(
            self.julian_day, self.lat, self.lon, b'B', flags
        )
        asc = ascmc[0]
        out = {
            "ascendant": {
                "sign_num": int(asc/30) + 1,
                "lon":       asc,
                "retro":    False
            }
        }

        # planets
        for name, code in PLANETS.items():
            pos, ret = swe.calc_ut(self.julian_day, code, flags)
            out[name] = {
                "sign_num": int(pos[0]/30) + 1,
                "lon":       pos[0],
                "retro":    ret < 0
            }

        # south node (Ketu)
        rn = out["north_node"]["lon"]
        kn = swe.degnorm(rn + 180)
        out["south_node"] = {
            "sign_num": int(kn/30) + 1,
            "lon":       kn,
            "retro":    False
        }

        swe.close()
        return out
