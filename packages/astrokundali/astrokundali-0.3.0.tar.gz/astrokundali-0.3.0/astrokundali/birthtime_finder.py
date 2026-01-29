# birthtime_finder.py

import swisseph as swe
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Union

from astrokundali.astro_data import AstroData, AYANAMSA

# Rāśi names 1–12
RASHI_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]


def _ascendant_sign(jd_ut: float, lat: float, lon: float) -> int:
    """
    Compute sidereal Ascendant sign number (1–12) for a given
    Julian Day UT, latitude, and longitude.
    Assumes sidereal mode already set via swe.set_sid_mode().
    """
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
    _, ascmc = swe.houses_ex(jd_ut, lat, lon, b'B', flags)
    asc_lon = ascmc[0]
    return int(asc_lon // 30) + 1


def find_birthtime_ranges(
    first_arg: Union[str, AstroData],
    latitude: float = None,
    longitude: float = None,
    utc_offset_hours: int = 0,
    utc_offset_minutes: int = 0,
    step_minutes: int = 60,
    ayanamsa: str = 'lahiri',
    desc_path: str = "rashi_descriptions.json"
) -> Dict[str, Any]:
    """
    Generate Ascendant‑sign time ranges for a calendar date at given lat/lon,
    using the specified sidereal ayanamsa (default 'lahiri').

    first_arg:
      - if AstroData: uses its julian_day, .lat/.lon and stored UTC offset.
      - if str: treated as local date "YYYY-MM-DD", requires latitude/longitude.

    Returns a dict:
      {
        "date":       "YYYY-MM-DD",
        "latitude":   float,
        "longitude":  float,
        "utc_offset": "+05:30",
        "ayanamsa":   "lahiri",
        "ranges": [
          {
            "start":       "HH:MM",
            "end":         "HH:MM",
            "sign_number": int,
            "sign_name":   str,
            "description": str
          },
          ...
        ]
      }
    """
    # ─── Normalize inputs ─────────────────────────────────────────────────────
    if isinstance(first_arg, AstroData):
        data = first_arg

        # read stored offsets from AstroData
        offset_h = getattr(data, "utc_offset_hours", None)
        offset_m = getattr(data, "utc_offset_minutes", None)
        if offset_h is None or offset_m is None:
            raise ValueError(
                "AstroData instance lacks utc_offset_hours/utc_offset_minutes attributes."
            )

        # reverse‑convert Julian day (UT) back to UTC calendar date/time
        utc_year, utc_month, utc_day, utc_hour_frac = swe.revjul(data.julian_day, swe.GREG_CAL)
        utc_hour   = int(utc_hour_frac)
        utc_minute = int((utc_hour_frac - utc_hour) * 60)

        # apply stored offset to get LOCAL date
        local_dt = (
            datetime(utc_year, utc_month, utc_day, utc_hour, utc_minute)
            + timedelta(hours=offset_h, minutes=offset_m)
        )
        date_str  = f"{local_dt.year:04d}-{local_dt.month:02d}-{local_dt.day:02d}"
        latitude  = data.lat
        longitude = data.lon

        # override function inputs
        utc_offset_hours   = offset_h
        utc_offset_minutes = offset_m

    else:
        date_str = first_arg
        if latitude is None or longitude is None:
            raise ValueError(
                "Must provide latitude and longitude when not using AstroData"
            )

    # ─── Set the sidereal ayanamsa ─────────────────────────────────────────────
    mode = AYANAMSA.get(ayanamsa.lower())
    if mode is None:
        raise ValueError(f"Unknown ayanamsa '{ayanamsa}'. Available: {list(AYANAMSA)}")
    swe.set_sid_mode(mode, 0, 0)

    # ─── Load Rāśi descriptions ────────────────────────────────────────────────
    pkg_dir   = Path(__file__).parent
    data_file = Path(desc_path)
    if not data_file.is_file():
        data_file = pkg_dir / "data" / desc_path
    if not data_file.is_file():
        raise FileNotFoundError(f"Cannot find descriptions file at {data_file}")
    with open(data_file, encoding="utf-8") as f:
        descs = json.load(f)

    # ─── Prepare the local‑day iteration ───────────────────────────────────────
    base_date = datetime.fromisoformat(date_str)
    day_start = datetime(base_date.year, base_date.month, base_date.day, 0, 0)
    step      = timedelta(minutes=step_minutes)

    def julian_day_ut(dt_local: datetime) -> float:
        dt_ut = dt_local - timedelta(
            hours=utc_offset_hours,
            minutes=utc_offset_minutes
        )
        return swe.julday(
            dt_ut.year, dt_ut.month, dt_ut.day,
            dt_ut.hour + dt_ut.minute/60 + dt_ut.second/3600
        )

    # ─── Sample Ascendant sign at each timestep ────────────────────────────────
    times: List[datetime] = []
    signs: List[int]      = []
    total_steps = int(24*60 // step_minutes) + 1
    for i in range(total_steps):
        t  = day_start + i * step
        jd = julian_day_ut(t)
        sign = _ascendant_sign(jd, latitude, longitude)
        times.append(t)
        signs.append(sign)

    # ─── Group contiguous intervals of the same sign ───────────────────────────
    results = []
    current_sign = signs[0]
    range_start  = times[0]

    for t, s in zip(times[1:], signs[1:]):
        if s != current_sign:
            results.append({
                "start":       range_start.strftime("%H:%M"),
                "end":         t.strftime("%H:%M"),
                "sign_number": current_sign,
                "sign_name":   RASHI_NAMES[current_sign-1],
                "description": descs[RASHI_NAMES[current_sign-1]]
            })
            current_sign = s
            range_start  = t

    # Final interval until midnight
    results.append({
        "start":       range_start.strftime("%H:%M"),
        "end":         (day_start + timedelta(days=1)).strftime("%H:%M"),
        "sign_number": current_sign,
        "sign_name":   RASHI_NAMES[current_sign-1],
        "description": descs[RASHI_NAMES[current_sign-1]]
    })

    return {
        "date":        date_str,
        "latitude":    latitude,
        "longitude":   longitude,
        "utc_offset":  f"{utc_offset_hours:+03d}:{utc_offset_minutes:02d}",
        "ayanamsa":    ayanamsa.lower(),
        "ranges":      results
    }


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Ascendant‑Range Finder")
    p.add_argument("--date",     type=str, help="YYYY-MM-DD (omit if passing AstroData)")
    p.add_argument("--lat",      type=float, required=False)
    p.add_argument("--lon",      type=float, required=False)
    p.add_argument("--utc-h",    type=int,   default=0)
    p.add_argument("--utc-m",    type=int,   default=0)
    p.add_argument("--step",     type=int,   default=60,  help="Minutes resolution")
    p.add_argument("--ayanamsa", type=str,   default="lahiri", help="Sidereal ayanamsa")
    p.add_argument("--desc",     type=str,   default="rashi_descriptions.json")

    args = p.parse_args()

    if args.date is None:
        p.error("Please supply --date when not using an AstroData object")

    output = find_birthtime_ranges(
        args.date,
        latitude           = args.lat,
        longitude          = args.lon,
        utc_offset_hours   = args.utc_h,
        utc_offset_minutes = args.utc_m,
        step_minutes       = args.step,
        ayanamsa           = args.ayanamsa,
        desc_path          = args.desc
    )
    print(json.dumps(output, ensure_ascii=False, indent=2))
