import math
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import swisseph as swe

from .astro_chart import House
from .astro_data import AstroData
from .houses import equal_houses, get_house_cusps
from .dispositions import DEBILITATIONS
from typing import List, Dict, Any
from .dispositions import DRISHTI, _anticlockwise_house, SIGN_LORDS, get_dispositions
# from .dispositions import _anticlockwise_house, get_dispositions, SIGN_LORDS

# ─── House‐drawing definitions ───────────────────────────────────────────

HOUSE_VERTICES = [
    [(100,225),(200,300),(300,225),(200,150)],
    [(100,225),(  0,300),(200,300)],
    [(  0,150),(  0,300),(100,225)],
    [(  0,150),(100,225),(200,150),(100, 75)],
    [(  0,  0),(  0,150),(100, 75)],
    [(  0,  0),(100, 75),(200,  0)],
    [(100, 75),(200,150),(300, 75),(200,  0)],
    [(200,  0),(300, 75),(400,  0)],
    [(300, 75),(400,150),(400,  0)],
    [(300, 75),(200,150),(300,225),(400,150)],
    [(300,225),(400,300),(400,150)],
    [(300,225),(200,300),(400,300)]
]

CENTERS = [
    (190,75),(100,30),(30,75),(90,150),
    (30,225),(90,278),(190,225),(290,278),
    (360,225),(290,150),(360,75),(290,30)
]

PLANET_ABBR = {
    'sun':'Su','moon':'Mo','mercury':'Me','venus':'Ve',
    'mars':'Ma','jupiter':'Ju','saturn':'Sa','uranus':'Ur',
    'neptune':'Ne','pluto':'Pl','north_node':'Ra','south_node':'Ke'
}

def _build_houses(raw: dict, house_system: str, astrodata: AstroData) -> List[House]:
    """
    Build 12 House objects (House.sign_num tells the zodiac sign)
    and put each planet into the correct house‐index.  We also
    mark retrograde + debilitation flags here.
    """
    asc_lon = raw['ascendant']['lon']
    sign0   = raw['ascendant']['sign_num']

    # 1) Compute cusp longitudes
    if house_system == 'equal':
        cusps = equal_houses(asc_lon)
    else:
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
        _, ascmc = swe.houses_ex(
            astrodata.julian_day,
            astrodata.lat,
            astrodata.lon,
            b'B', flags
        )
        mc = ascmc[1]
        cusps = get_house_cusps(
            house_system, asc_lon,
            JD = astrodata.julian_day,
            lat = astrodata.lat,
            lon = astrodata.lon,
            mc = mc
        )

    # 2) Create an empty House at each of the 12 positions
    houses: List[House] = []
    s = sign0
    for _ in range(12):
        h = House(s)
        houses.append(h)
        s = 1 if s == 12 else s + 1
    houses[0].is_asc = True

    # 3) Assign each planet (and mark retrograde + debilitated)
    for name, info in raw.items():
        if name == 'ascendant':
            continue
        lon    = info['lon']
        retro  = info.get('retro', False)
        sign_n = info.get('sign_num')
        deb    = (name in DEBILITATIONS and DEBILITATIONS[name] == sign_n)

        for i in range(12):
            start = cusps[i]
            end   = cusps[(i+1) % 12]
            if end > start:
                in_house = (start <= lon < end)
            else:
                # wraps around 360° → 0°
                in_house = (lon >= start or lon < end)

            if in_house:
                houses[i].planets[name] = {
                    'lon':         lon,
                    'retro':       retro,
                    'debilitated': deb
                }
                break

    return houses

# ─── SIGN / PLANET SHIFT for label placement ────────────────────────────────

SIGN_SHIFT = {
    'top':       ( 0, +5),
    'bottom':    ( 0, -5),
    'left':      (+5,  0),
    'right':     (-5,  0),
    'center':    ( 0,  0),
    'top-left':  (+3, +3),
    'top-right': (-3, +3),
    'bot-left':  (+3, -3),
    'bot-right': (-3, -3),
}
PLANET_SHIFT = { region: (-dx, -dy) for region,(dx,dy) in SIGN_SHIFT.items() }

def _region(cx: float, cy: float, width=400, height=300) -> str:
    """
    Bucket a point (cx,cy) into one of:
      'top', 'bottom', 'left','right','center',
      'top-left','top-right','bot-left','bot-right'.
    Used to decide how to shift sign‐numbers inward
    and planet–labels outward.
    """
    x3 = width  / 3
    y3 = height / 3

    vert = 'center'
    if cy < y3:
        vert = 'top'
    elif cy > 2*y3:
        vert = 'bottom'

    horiz = 'center'
    if cx < x3:
        horiz = 'left'
    elif cx > 2*x3:
        horiz = 'right'

    if vert in ('top','bottom') and horiz in ('left','right'):
        if vert == 'top':
            return f"top-{horiz}"
        else:
            return f"bot-{horiz}"
    return vert if vert != 'center' else horiz

def _plot_chart(
    houses: List[House],
    title: str,
    description: str,
    show_retro: bool = False
):
    """
    Draw the 12‐house North‐Indian diamond chart. We:
      • place each diamond at its HOUSE_VERTICES,
      • write the sign number (shifted inward),
      • write each planet’s “Name & deg°” (shifted outward),
      • annotate a superscript “Re” if retrograde,
      • annotate a subscript “De” if debilitated,
      • clamp all labels inside the 5–395 × 5–295 range,
      • and keep Matplotlib’s default Y‐axis (0 at bottom, 300 at top).
    """
    fig, ax = plt.subplots(figsize=(6,6))

    # 1) Title near the top, slightly larger
    fig.suptitle(title, fontsize=18, y=0.88, weight='bold')
    fig.subplots_adjust(top=0.85, bottom=0.07, left=0.03, right=0.97)

    # 2) Use default orientation: 0 ≤ y ≤ 300 (0 at bottom)
    ax.set_xlim(0,400)
    ax.set_ylim(0,300)            # ← keep upward = larger y
    ax.set_aspect('equal')
    ax.axis('off')

    # 3) Draw all twelve house outlines
    for verts in HOUSE_VERTICES:
        ax.add_patch(Polygon(verts, closed=True, fill=False, edgecolor='black', linewidth=1))

    # 4) Annotate each house
    for i, h in enumerate(houses):
        xs, ys = zip(*HOUSE_VERTICES[i])
        cx, cy = sum(xs)/len(xs), sum(ys)/len(ys)

        region   = _region(cx, cy)
        sdx, sdy = SIGN_SHIFT.get(region, (0,0))
        pdx, pdy = PLANET_SHIFT.get(region, (0,0))

        # 4a) Draw the sign number (in blue, shifted inward)
        ax.text(
            cx + sdx, cy + sdy,
            str(h.sign_num),
            ha='center', va='center',
            fontsize=10, weight='bold', color='blue'
        )

        # 4b) Draw each planet in that house (shifted outward)
        for j, (pl, dat) in enumerate(h.planets.items()):
            angle = 2 * math.pi * j / max(len(h.planets),1)
            x0 = cx + pdx + 20 * math.cos(angle)
            y0 = cy + pdy + 20 * math.sin(angle)

            # clamp inside [5,395] × [5,295]
            x = min(max(x0, 5), 395)
            y = min(max(y0, 5), 295)

            deg = int(dat['lon'] % 30)
            label = f"{PLANET_ABBR.get(pl,pl[:2])} {deg}°"
            if show_retro and dat.get('retro', False):
                label = f"{label}$^{{Re}}$"
            if show_retro and dat.get('debilitated', False):
                label = f"{label}$_{{De}}$"

            ax.text(
                x, y, label,
                ha='center', va='center',
                fontsize=8, weight='bold', color='orange'
            )

    # 5) Bottom description, moved up slightly so it doesn’t collide
    fig.text(0.5, 0.06, description, ha='center', fontsize=12)
    plt.show()

def calculate_corrected_varga(longitude: float, division: int, chart_type: str) -> tuple:
    """Calculate correct Varga position using traditional Vedic methods"""
    sign = int(longitude // 30) + 1
    degree = longitude % 30
    
    if chart_type == 'D2':  # Hora Chart
        if sign % 2 == 1:  # Odd signs
            new_sign = 5 if degree < 15 else 4  # Leo : Cancer
        else:  # Even signs  
            new_sign = 4 if degree < 15 else 5  # Cancer : Leo
        new_lon = (new_sign - 1) * 30 + degree
        
    elif chart_type == 'D3':  # Drekkana Chart
        drekkana = int(degree // 10)
        if drekkana == 0:
            new_sign = sign
        elif drekkana == 1:
            new_sign = ((sign + 3) % 12) + 1
        else:
            new_sign = ((sign + 7) % 12) + 1
        new_lon = (new_sign - 1) * 30 + (degree % 10) * 3
        
    elif chart_type == 'D10':  # Dashamamsa Chart
        dashamamsa = int(degree // 3)
        if sign % 2 == 1:  # Odd signs
            new_sign = ((sign - 1 + dashamamsa) % 12) + 1
        else:  # Even signs
            new_sign = ((sign + 7 + dashamamsa) % 12) + 1
        new_lon = (new_sign - 1) * 30 + (degree % 3) * 10
        
    elif chart_type == 'D12':  # Dwadashamsa Chart
        dwadashamsa = int(degree // 2.5)
        new_sign = ((sign - 1 + dwadashamsa) % 12) + 1
        new_lon = (new_sign - 1) * 30 + (degree % 2.5) * 12
        
    elif chart_type == 'D24':  # Chaturvimshamsa Chart
        chaturvimshamsa = int(degree // 1.25)
        if sign % 2 == 1:  # Odd signs start from Leo
            new_sign = ((4 + chaturvimshamsa) % 12) + 1
        else:  # Even signs start from Cancer
            new_sign = ((3 + chaturvimshamsa) % 12) + 1
        new_lon = (new_sign - 1) * 30 + (degree % 1.25) * 24
        
    elif chart_type == 'D27':  # Saptavimshamsa Chart
        saptavimshamsa = int(degree // (30/27))
        fire_signs = [1, 5, 9]
        earth_signs = [2, 6, 10]
        air_signs = [3, 7, 11]
        water_signs = [4, 8, 12]
        
        if sign in fire_signs:
            start = 1  # Aries
        elif sign in earth_signs:
            start = 4  # Cancer
        elif sign in air_signs:
            start = 7  # Libra
        else:  # water_signs
            start = 10  # Capricorn
            
        new_sign = ((start - 1 + saptavimshamsa) % 12) + 1
        new_lon = (new_sign - 1) * 30 + (degree % (30/27)) * 27
        
    elif chart_type == 'D30':  # Trimshamsa Chart
        if degree < 5:
            new_sign = 11  # Mars - Aquarius
        elif degree < 10:
            new_sign = 6   # Mercury - Virgo
        elif degree < 18:
            new_sign = 9   # Jupiter - Sagittarius
        elif degree < 25:
            new_sign = 7   # Venus - Libra
        else:
            new_sign = 10  # Saturn - Capricorn
        new_lon = (new_sign - 1) * 30 + degree  # Keep original degree
        
    elif chart_type == 'D40':  # Khavedamsa Chart
        khavedamsa = int(degree // 0.75)
        if sign % 2 == 1:  # Odd signs start from Aries
            new_sign = ((0 + khavedamsa) % 12) + 1
        else:  # Even signs start from Libra
            new_sign = ((6 + khavedamsa) % 12) + 1
        new_lon = (new_sign - 1) * 30 + (degree % 0.75) * 40
        
    elif chart_type == 'D45':  # Akshavedamsa Chart
        akshavedamsa = int(degree // (30/45))
        movable_signs = [1, 4, 7, 10]
        fixed_signs = [2, 5, 8, 11]
        dual_signs = [3, 6, 9, 12]
        
        if sign in movable_signs:
            start = 1  # Aries
        elif sign in fixed_signs:
            start = 5  # Leo
        else:  # dual_signs
            start = 9  # Sagittarius
            
        new_sign = ((start - 1 + akshavedamsa) % 12) + 1
        new_lon = (new_sign - 1) * 30 + (degree % (30/45)) * 45
        
    elif chart_type == 'D60':  # Shashtiamsa Chart
        shashtiamsa = int(degree // 0.5)
        new_sign = ((sign - 1 + shashtiamsa) % 12) + 1
        new_lon = (new_sign - 1) * 30 + (degree % 0.5) * 60
        
    else:
        # Default - keep original for working charts
        new_sign = int((longitude * division) % 360 / 30) + 1
        new_lon = (longitude * division) % 360
        
    return new_sign, new_lon

def apply_house_offset(raw_data: dict, house_offset: int) -> dict:
    """Apply house offset by adjusting ascendant"""
    if house_offset == 0:
        return raw_data
    
    adjusted_raw = raw_data.copy()
    asc_info = raw_data['ascendant']
    
    # Calculate new ascendant sign with offset
    original_sign = asc_info['sign_num']
    new_sign = ((original_sign - 1 + house_offset) % 12) + 1
    
    # Keep same longitude but update sign_num
    adjusted_raw['ascendant'] = {
        'lon': asc_info['lon'],
        'sign_num': new_sign,
        'retro': False
    }
    
    return adjusted_raw


def format_houses(houses: List[House]) -> List[Dict[str, Any]]:
    """
    Convert list[House] into a serializable, human-readable list of dicts.
    """
    def lon_to_dms(lon: float) -> str:
        """
        Convert a decimal longitude into D:MM:SS format within its 30° sign.
        """
        # Extract degrees within the 30° sign
        total = lon % 30
        d = int(total)
        m_full = (total - d) * 60
        m = int(m_full)
        s = int((m_full - m) * 60)
        return f"{d:02d}:{m:02d}:{s:02d}"

    formatted = []
    for idx, h in enumerate(houses, start=1):
        house_entry: Dict[str, Any] = {
            "house_number": idx,
            "rashi": h.sign_num,
            "is_ascendant": getattr(h, "is_asc", False),
            "planets": {}
        }
        for pl, dat in h.planets.items():
            raw_lon = dat["lon"]
            house_entry["planets"][pl] = {
                "degree_raw": round(raw_lon, 6),
                "degree_dms": lon_to_dms(raw_lon),
                "retrograde": bool(dat.get("retro", False)),
                "debilitated": bool(dat.get("debilitated", False))
            }
        formatted.append(house_entry)
    return formatted


def plot_lagna_chart(
    first_arg,
    house_system: str = 'whole_sign',
    show_retro: bool = False
) -> list[House]:
    """
    Plot D1 chart. Accepts AstroData or precomputed houses.
    """
    if isinstance(first_arg, list) and all(isinstance(h, House) for h in first_arg):
        houses = first_arg
    else:
        astrodata = first_arg
        raw       = astrodata.get_rashi_data()
        houses    = _build_houses(raw, house_system, astrodata)
    _plot_chart(houses, 'Lagna Chart', 'Main Kundali (D1)', show_retro=show_retro)
    return houses


def plot_moon_chart(
    astrodata: AstroData,
    house_system: str = 'whole_sign',
    show_retro: bool = False
) -> list[House]:
    """
    Plot Moon Chart: rotate so Moon is ascendant.
    """
    raw = astrodata.get_rashi_data()
    moon = raw['moon']
    raw_moon = raw.copy()
    raw_moon['ascendant'] = {'lon': moon['lon'], 'sign_num': moon['sign_num'], 'retro': False}
    houses = _build_houses(raw_moon, house_system, astrodata)
    _plot_chart(houses, 'Moon Chart (Chandra Lagna)', 'Mental & emotional insights', show_retro=show_retro)
    return houses


def plot_navamsa_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
    """Plot D9 (Navamsa): Marriage & Partnerships."""
    raw = astrodata.get_rashi_data()
    raw9 = {k: {'sign_num': int((v['lon']*9)%360/30)+1, 'lon': (v['lon']*9)%360, 'retro': v.get('retro',False)} for k,v in raw.items()}
    houses = _build_houses(raw9, house_system, astrodata)
    _plot_chart(houses, 'Navamsa Chart (D9)', 'Marriage & Partnerships', show_retro=show_retro)
    return houses

def plot_hora_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
    """Plot D2 (Hora): Corrected with +2 offset."""
    raw = astrodata.get_rashi_data()
    
    # Apply traditional D2 calculation
    corrected_raw = {}
    for k, v in raw.items():
        if k == 'ascendant':
            corrected_raw[k] = v
        else:
            new_sign, new_lon = calculate_corrected_varga(v['lon'], 2, 'D2')
            corrected_raw[k] = {
                'sign_num': new_sign,
                'lon': new_lon,
                'retro': v.get('retro', False)
            }
    
    # Apply +2 house offset
    corrected_raw = apply_house_offset(corrected_raw, 2)
    houses = _build_houses(corrected_raw, house_system, astrodata)
    _plot_chart(houses, 'Hora Chart (D2)', 'Prosperity & Wealth', show_retro=show_retro)
    return houses

def plot_drekkana_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
    """Plot D3 (Drekkana): Corrected with +6 offset."""
    raw = astrodata.get_rashi_data()
    
    corrected_raw = {}
    for k, v in raw.items():
        if k == 'ascendant':
            corrected_raw[k] = v
        else:
            new_sign, new_lon = calculate_corrected_varga(v['lon'], 3, 'D3')
            corrected_raw[k] = {
                'sign_num': new_sign,
                'lon': new_lon,
                'retro': v.get('retro', False)
            }
    
    # Apply +6 house offset
    corrected_raw = apply_house_offset(corrected_raw, 6)
    houses = _build_houses(corrected_raw, house_system, astrodata)
    _plot_chart(houses, 'Drekkana Chart (D3)', 'Siblings & well-being', show_retro=show_retro)
    return houses


# def plot_hora_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
#     """Plot D2 (Hora): Prosperity & Wealth."""
#     raw = astrodata.get_rashi_data()
#     raw2 = {k: {'sign_num': int((v['lon']*2)%360/30)+1, 'lon': (v['lon']*2)%360, 'retro': v.get('retro',False)} for k,v in raw.items()}
#     houses = _build_houses(raw2, house_system, astrodata)
#     _plot_chart(houses, 'Hora Chart (D2)', 'Prosperity & Wealth', show_retro=show_retro)
#     return houses


# def plot_drekkana_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
#     """Plot D3 (Drekkana): Siblings & Courage."""
#     raw = astrodata.get_rashi_data()
#     raw3 = {k: {'sign_num': int((v['lon']*3)%360/30)+1, 'lon': (v['lon']*3)%360, 'retro': v.get('retro',False)} for k,v in raw.items()}
#     houses = _build_houses(raw3, house_system, astrodata)
#     _plot_chart(houses, 'Drekkana Chart (D3)', 'Siblings & well-being', show_retro=show_retro)
#     return houses


def plot_chaturthamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
    """Plot D4 (Chaturthamsha): Luck & Residence."""
    raw = astrodata.get_rashi_data()
    raw4 = {k: {'sign_num': int((v['lon']*4)%360/30)+1, 'lon': (v['lon']*4)%360, 'retro': v.get('retro',False)} for k,v in raw.items()}
    houses = _build_houses(raw4, house_system, astrodata)
    _plot_chart(houses, 'Chaturthamsha Chart (D4)', 'Luck & Residence', show_retro=show_retro)
    return houses


def plot_saptamamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
    """Plot D7 (Saptamamsha): Children & Progeny."""
    raw = astrodata.get_rashi_data()
    raw7 = {k: {'sign_num': int((v['lon']*7)%360/30)+1, 'lon': (v['lon']*7)%360, 'retro': v.get('retro',False)} for k,v in raw.items()}
    houses = _build_houses(raw7, house_system, astrodata)
    _plot_chart(houses, 'Saptamamsha Chart (D7)', 'Children & Grandchildren', show_retro=show_retro)
    return houses

def plot_navamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
    """Plot D9 (Navamsha): Marriage & Partnerships."""
    raw = astrodata.get_rashi_data()
    raw9 = {k: {'sign_num': int((v['lon']*9)%360/30)+1, 'lon': (v['lon']*9)%360, 'retro': v.get('retro',False)} for k,v in raw.items()}
    houses = _build_houses(raw9, house_system, astrodata)
    _plot_chart(houses, 'Navamsha Chart (D9)', 'Marriage & Partnerships', show_retro=show_retro)
    return houses

def plot_dashamamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
    """Plot D10 (Dashamamsha): Corrected."""
    raw = astrodata.get_rashi_data()
    
    corrected_raw = {}
    for k, v in raw.items():
        if k == 'ascendant':
            corrected_raw[k] = v
        else:
            new_sign, new_lon = calculate_corrected_varga(v['lon'], 10, 'D10')
            corrected_raw[k] = {
                'sign_num': new_sign,
                'lon': new_lon,
                'retro': v.get('retro', False)
            }
    
    houses = _build_houses(corrected_raw, house_system, astrodata)
    _plot_chart(houses, 'Dashamamsha Chart (D10)', 'Profession & Social Status', show_retro=show_retro)
    return houses

def plot_dwadashamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
    """Plot D12 (Dwadashamsha): Corrected."""
    raw = astrodata.get_rashi_data()
    
    corrected_raw = {}
    for k, v in raw.items():
        if k == 'ascendant':
            corrected_raw[k] = v
        else:
            new_sign, new_lon = calculate_corrected_varga(v['lon'], 12, 'D12')
            corrected_raw[k] = {
                'sign_num': new_sign,
                'lon': new_lon,
                'retro': v.get('retro', False)
            }
    
    houses = _build_houses(corrected_raw, house_system, astrodata)
    _plot_chart(houses, 'Dwadashamsha Chart (D12)', 'Parents & Ancestry', show_retro=show_retro)
    return houses

# def plot_dashamamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
#     """Plot D10 (Dashamamsha): Profession & Success."""
#     raw = astrodata.get_rashi_data()
#     raw10 = {k: {'sign_num': int((v['lon']*10)%360/30)+1, 'lon': (v['lon']*10)%360, 'retro': v.get('retro',False)} for k,v in raw.items()}
#     houses = _build_houses(raw10, house_system, astrodata)
#     _plot_chart(houses, 'Dashamamsha Chart (D10)', 'Profession & Social Status', show_retro=show_retro)
#     return houses


# def plot_dwadashamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
#     """Plot D12 (Dwadashamsha): Parents & Heritage."""
#     raw = astrodata.get_rashi_data()
#     raw12 = {k: {'sign_num': int((v['lon']*12)%360/30)+1, 'lon': (v['lon']*12)%360, 'retro': v.get('retro',False)} for k,v in raw.items()}
#     houses = _build_houses(raw12, house_system, astrodata)
#     _plot_chart(houses, 'Dwadashamsha Chart (D12)', 'Parents & Ancestry', show_retro=show_retro)
#     return houses


def plot_shodashamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
    """Plot D16 (Shodashamsha): Vehicles & Comforts."""
    raw = astrodata.get_rashi_data()
    raw16 = {k: {'sign_num': int((v['lon']*16)%360/30)+1, 'lon': (v['lon']*16)%360, 'retro': v.get('retro',False)} for k,v in raw.items()}
    houses = _build_houses(raw16, house_system, astrodata)
    _plot_chart(houses, 'Shodashamsha Chart (D16)', 'Vehicles & Daily Comforts', show_retro=show_retro)
    return houses


def plot_vimshamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
    """Plot D20 (Vimshamsha): Spiritual Undertakings."""
    raw = astrodata.get_rashi_data()
    raw20 = {k: {'sign_num': int((v['lon']*20)%360/30)+1, 'lon': (v['lon']*20)%360, 'retro': v.get('retro',False)} for k,v in raw.items()}
    houses = _build_houses(raw20, house_system, astrodata)
    _plot_chart(houses, 'Vimshamsha Chart (D20)', 'Spiritual Pursuits', show_retro=show_retro)
    return houses

def plot_chatuvimshamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
    """Plot D24 (Chatuvimshamsha): Corrected."""
    raw = astrodata.get_rashi_data()
    
    corrected_raw = {}
    for k, v in raw.items():
        if k == 'ascendant':
            corrected_raw[k] = v
        else:
            new_sign, new_lon = calculate_corrected_varga(v['lon'], 24, 'D24')
            corrected_raw[k] = {
                'sign_num': new_sign,
                'lon': new_lon,
                'retro': v.get('retro', False)
            }
    
    houses = _build_houses(corrected_raw, house_system, astrodata)
    _plot_chart(houses, 'Chatuvimshamsha Chart (D24)', 'Education & Intellect', show_retro=show_retro)
    return houses

def plot_saptvimshamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
    """Plot D27 (Saptvimshamsha): Corrected with +1 offset."""
    raw = astrodata.get_rashi_data()
    
    corrected_raw = {}
    for k, v in raw.items():
        if k == 'ascendant':
            corrected_raw[k] = v
        else:
            new_sign, new_lon = calculate_corrected_varga(v['lon'], 27, 'D27')
            corrected_raw[k] = {
                'sign_num': new_sign,
                'lon': new_lon,
                'retro': v.get('retro', False)
            }
    
    # Apply +1 house offset
    corrected_raw = apply_house_offset(corrected_raw, 1)
    houses = _build_houses(corrected_raw, house_system, astrodata)
    _plot_chart(houses, 'Saptvimshamsha Chart (D27)', 'Innate Strengths & Challenges', show_retro=show_retro)
    return houses

def plot_trishamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
    """Plot D30 (Trishamsha): Corrected."""
    raw = astrodata.get_rashi_data()
    
    corrected_raw = {}
    for k, v in raw.items():
        if k == 'ascendant':
            corrected_raw[k] = v
        else:
            new_sign, new_lon = calculate_corrected_varga(v['lon'], 30, 'D30')
            corrected_raw[k] = {
                'sign_num': new_sign,
                'lon': new_lon,
                'retro': v.get('retro', False)
            }
    
    houses = _build_houses(corrected_raw, house_system, astrodata)
    _plot_chart(houses, 'Trishamsha Chart (D30)', 'Miseries & Disasters', show_retro=show_retro)
    return houses

def plot_khavedamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
    """Plot D40 (Khavedamsha): Corrected with +1 offset."""
    raw = astrodata.get_rashi_data()
    
    corrected_raw = {}
    for k, v in raw.items():
        if k == 'ascendant':
            corrected_raw[k] = v
        else:
            new_sign, new_lon = calculate_corrected_varga(v['lon'], 40, 'D40')
            corrected_raw[k] = {
                'sign_num': new_sign,
                'lon': new_lon,
                'retro': v.get('retro', False)
            }
    
    # Apply +1 house offset
    corrected_raw = apply_house_offset(corrected_raw, 1)
    houses = _build_houses(corrected_raw, house_system, astrodata)
    _plot_chart(houses, 'Khavedamsha Chart (D40)', 'Major Life Events', show_retro=show_retro)
    return houses

def plot_akshavedamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
    """Plot D45 (Akshavedamsha): Corrected."""
    raw = astrodata.get_rashi_data()
    
    corrected_raw = {}
    for k, v in raw.items():
        if k == 'ascendant':
            corrected_raw[k] = v
        else:
            new_sign, new_lon = calculate_corrected_varga(v['lon'], 45, 'D45')
            corrected_raw[k] = {
                'sign_num': new_sign,
                'lon': new_lon,
                'retro': v.get('retro', False)
            }
    
    houses = _build_houses(corrected_raw, house_system, astrodata)
    _plot_chart(houses, 'Akshavedamsha Chart (D45)', 'General Conduct & Life Themes', show_retro=show_retro)
    return houses

def plot_shashtiamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
    """Plot D60 (Shashtiamsha): Corrected."""
    raw = astrodata.get_rashi_data()
    
    corrected_raw = {}
    for k, v in raw.items():
        if k == 'ascendant':
            corrected_raw[k] = v
        else:
            new_sign, new_lon = calculate_corrected_varga(v['lon'], 60, 'D60')
            corrected_raw[k] = {
                'sign_num': new_sign,
                'lon': new_lon,
                'retro': v.get('retro', False)
            }
    
    houses = _build_houses(corrected_raw, house_system, astrodata)
    _plot_chart(houses, 'Shashtiamsha Chart (D60)', 'Past-life Karma & Destiny', show_retro=show_retro)
    return houses


# Exaltation / Debilitation mapping
EX_DE_RASHI = {
    'sun':     (1,  7),    # Exalted in Aries (1), Debilitated in Libra (7)
    'moon':    (2,  8),    # Exalted in Taurus (2), Debilitated in Scorpio (8)
    'mars':    (10, 4),    # Exalted in Capricorn (10), Debilitated in Cancer (4)
    'mercury': (6, 12),    # Exalted in Virgo (6), Debilitated in Pisces (12)
    'jupiter': (4, 10),    # Exalted in Cancer (4), Debilitated in Capricorn (10)
    'venus':   (12, 6),    # Exalted in Pisces (12), Debilitated in Virgo (6)
    'saturn':  (7,  1)     # Exalted in Libra (7), Debilitated in Aries (1)
}

EXCEPTIONS = {'rahu', 'ketu', 'uranus', 'neptune', 'pluto'}

def plot_comprehensive_chart(
    astrodata: AstroData,
    house_system: str = 'whole_sign',
    plot_signs: bool = False
):
    """
    Comprehensive Kundali chart:
      • Planets in houses: degrees, ↑/↓ arrows, retrograde markers, color-coded strength
      • Drishti aspects: planets aspecting houses shown with _Drishti subscript
      • Sign lords: ^Rashi tags with combined ^Rashi_Drishti when applicable
      • Exaltation ↑ and Debilitation ↓ arrows for all planets
      • Color intensity based on degrees (10-25° = dark, else = light)
    """
    raw    = astrodata.get_rashi_data()
    disp   = get_dispositions(astrodata, house_system)
    houses = _build_houses(raw, house_system, astrodata)

    # Build comprehensive drishti mapping
    drishti_map = {i+1: [] for i in range(12)}
    for src_idx, src in enumerate(houses):
        src_house = src_idx + 1
        for planet, pdata in src.planets.items():
            if planet in DRISHTI:
                for step in DRISHTI[planet]:
                    tgt = _anticlockwise_house(src_house, step)
                    drishti_map[tgt].append(planet)

    fig, ax = plt.subplots(figsize=(7,7))
    fig.suptitle("Comprehensive Kundali", fontsize=20, y=0.92, weight='bold')
    fig.subplots_adjust(top=0.88, bottom=0.05, left=0.02, right=0.98)
    ax.set_xlim(0,400); ax.set_ylim(0,300); ax.set_aspect('equal'); ax.axis('off')

    # Draw house outlines
    for verts in HOUSE_VERTICES:
        ax.add_patch(Polygon(verts, closed=True, fill=False, edgecolor='black', linewidth=1))

    # Sign-lord corner tags with Drishti integration
    for hi, h in enumerate(houses):
        xs, ys = zip(*HOUSE_VERTICES[hi])
        cx, cy = sum(xs)/len(xs), sum(ys)/len(ys)
        region = _region(cx, cy)
        sdx, sdy = SIGN_SHIFT[region]
        
        if plot_signs:
            ax.text(cx+sdx, cy+sdy, str(h.sign_num),
                    ha='center', va='center', fontsize=16, weight='bold', color='blue')
        
        lord = SIGN_LORDS[h.sign_num]
        abbr = PLANET_ABBR[lord]
        
        # Check if sign lord also has drishti on this house
        has_drishti = lord in drishti_map[hi+1]
        
        if has_drishti:
            lord_label = f"{abbr}$^{{Rashi}}_{{Drishti}}$"
        else:
            lord_label = f"{abbr}$^{{Rashi}}$"
            
        ax.text(cx+sdx+6, cy+sdy+4, lord_label,
                ha='left', va='bottom', fontsize=8, color='darkgreen')

    # Planets in houses + Drishti aspects
    for hi, h in enumerate(houses):
        xs, ys = zip(*HOUSE_VERTICES[hi])
        cx, cy = sum(xs)/len(xs), sum(ys)/len(ys)
        region = _region(cx, cy)
        pdx, pdy = PLANET_SHIFT[region]
        
        all_display_items = []  # Fresh list for this house

        # 1. Planets actually placed in this house
        for pname, pdata in h.planets.items():
            deg = pdata['lon'] % 30
            deg_int = int(deg)
            abbr = PLANET_ABBR[pname]

            # Get current sign for Ex/De arrows
            current_sign = disp[pname]['sign_number']
            
            # Determine exaltation/debilitation arrow
            arrow = ''
            if pname not in EXCEPTIONS and pname in EX_DE_RASHI:
                exalt_sign, debil_sign = EX_DE_RASHI[pname]
                if current_sign == exalt_sign:
                    arrow = '↑'  # Exalted
                elif current_sign == debil_sign:
                    arrow = '↓'  # Debilitated

            # Build label with degree and arrow
            label = f"{abbr} {deg_int}°{arrow}"

            # Add retrograde marker
            if pdata.get('retro', False):
                label += "$^{Re}$"

            # Color based on degree strength
            color = '#800000' if 10 <= deg <= 25 else '#C04040'

            all_display_items.append((label, color))

        # 2. Planets aspecting this house (Drishti)
        sign_lord = SIGN_LORDS[h.sign_num]
        for planet in drishti_map[hi+1]:
            # Exclude planets already in house and sign lord (already shown)
            if planet not in h.planets and planet != sign_lord:
                abbr = PLANET_ABBR[planet]
                
                # Get aspecting planet's sign for Ex/De markers
                current_sign = disp[planet]['sign_number']
                
                # Add Ex/De markers to Drishti planets too
                ex_de_marker = ''
                if planet not in EXCEPTIONS and planet in EX_DE_RASHI:
                    exalt_sign, debil_sign = EX_DE_RASHI[planet]
                    if current_sign == exalt_sign:
                        ex_de_marker = '$^{Ex}$'
                    elif current_sign == debil_sign:
                        ex_de_marker = '$_{De}$'
                
                drishti_label = f"{abbr}$_{{Drishti}}${ex_de_marker}"
                
                # Drishti planets use standard color
                all_display_items.append((drishti_label, '#8B4513'))  # Brown color for aspects

        # 3. Position all items around house center
        for idx, (lbl, color) in enumerate(all_display_items):
            if len(all_display_items) == 1:
                angle, radius = 0, 0
            else:
                angle = 2 * math.pi * idx / len(all_display_items)
                radius = 18
            
            x0 = cx + pdx + radius * math.cos(angle)
            y0 = cy + pdy + radius * math.sin(angle)
            x = min(max(x0, 5), 395)
            y = min(max(y0, 5), 295)
            
            ax.text(x, y, lbl, ha='center', va='center', 
                   fontsize=7, weight='bold', color=color)

    # Enhanced footer legend
    fig.text(0.5, 0.03,
             "↑=Exalted • ↓=Debilitated • Re=Retrograde • _Drishti=Aspect • Dark=Strong • Light=Weak",
             ha='center', fontsize=9)

    plt.show()
    return houses

# def plot_chatuvimshamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
#     """Plot D24 (Chatuvimshamsha): Education & Learning."""
#     raw = astrodata.get_rashi_data()
#     raw24 = {k: {'sign_num': int((v['lon']*24)%360/30)+1, 'lon': (v['lon']*24)%360, 'retro': v.get('retro',False)} for k,v in raw.items()}
#     houses = _build_houses(raw24, house_system, astrodata)
#     _plot_chart(houses, 'Chatuvimshamsha Chart (D24)', 'Education & Intellect', show_retro=show_retro)
#     return houses


# def plot_saptvimshamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
#     """Plot D27 (Saptvimshamsha): Strengths & Weaknesses."""
#     raw = astrodata.get_rashi_data()
#     raw27 = {k: {'sign_num': int((v['lon']*27)%360/30)+1, 'lon': (v['lon']*27)%360, 'retro': v.get('retro',False)} for k,v in raw.items()}
#     houses = _build_houses(raw27, house_system, astrodata)
#     _plot_chart(houses, 'Saptvimshamsha Chart (D27)', 'Innate Strengths & Challenges', show_retro=show_retro)
#     return houses


# def plot_trishamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
#     """Plot D30 (Trishamsha): Miseries & Troubles."""
#     raw = astrodata.get_rashi_data()
#     raw30 = {k: {'sign_num': int((v['lon']*30)%360/30)+1, 'lon': (v['lon']*30)%360, 'retro': v.get('retro',False)} for k,v in raw.items()}
#     houses = _build_houses(raw30, house_system, astrodata)
#     _plot_chart(houses, 'Trishamsha Chart (D30)', 'Miseries & Disasters', show_retro=show_retro)
#     return houses


# def plot_khavedamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
#     """Plot D40 (Khavedamsha): Auspicious/Inauspicious Events."""
#     raw = astrodata.get_rashi_data()
#     raw40 = {k: {'sign_num': int((v['lon']*40)%360/30)+1, 'lon': (v['lon']*40)%360, 'retro': v.get('retro',False)} for k,v in raw.items()}
#     houses = _build_houses(raw40, house_system, astrodata)
#     _plot_chart(houses, 'Khavedamsha Chart (D40)', 'Major Life Events', show_retro=show_retro)
#     return houses


# def plot_akshavedamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
#     """Plot D45 (Akshavedamsha): Overall Character."""
#     raw = astrodata.get_rashi_data()
#     raw45 = {k: {'sign_num': int((v['lon']*45)%360/30)+1, 'lon': (v['lon']*45)%360, 'retro': v.get('retro',False)} for k,v in raw.items()}
#     houses = _build_houses(raw45, house_system, astrodata)
#     _plot_chart(houses, 'Akshavedamsha Chart (D45)', 'General Conduct & Life Themes', show_retro=show_retro)
#     return houses


# def plot_shashtiamsha_chart(astrodata: AstroData, house_system: str = 'whole_sign', show_retro: bool = False) -> list[House]:
#     """Plot D60 (Shashtiamsha): Karma & Destiny."""
#     raw = astrodata.get_rashi_data()
#     raw60 = {k: {'sign_num': int((v['lon']*60)%360/30)+1, 'lon': (v['lon']*60)%360, 'retro': v.get('retro',False)} for k,v in raw.items()}
#     houses = _build_houses(raw60, house_system, astrodata)
#     _plot_chart(houses, 'Shashtiamsha Chart (D60)', 'Past-life Karma & Destiny', show_retro=show_retro)
#     return houses


# def plot_comprehensive_chart(
#     astrodata: AstroData,
#     house_system: str = 'whole_sign',
#     plot_signs: bool = False
# ):
#     """
#     Mega‑chart showing:
#       • D1 Lagna‐chart with retrograde superscript Re.
#       • ↑/↓ for upper/lower half of each sign.
#       • Sign‑lord corner tags "X^Rashi" in green.
#       • All planets get $_{Drishti}$ on every house they aspect.
#       • If planet is both sign lord and has drishti, show both ^Rashi and _Drishti.
#       • Optional plot_signs: big blue sign‑numbers.
#     """
    
#     # Full drishti map - defines which houses each planet aspects
#     DRISHTI = {
#         'sun': [7],
#         'moon': [7],
#         'mercury': [7],
#         'venus': [7],
#         'mars': [4,7,8],
#         'jupiter': [5,7,9],
#         'saturn': [3,7,10],
#         'north_node': [7],  # Rahu
#         'south_node': [7],  # Ketu (Note: traditionally Ketu doesn't aspect, but keeping for consistency)
#     }
    
#     # 1) Get raw data, dispositions, and houses
#     raw = astrodata.get_rashi_data()
#     disp = get_dispositions(astrodata, house_system)
#     houses = _build_houses(raw, house_system, astrodata)
    
#     # 2) Set up figure with same formatting as original
#     fig, ax = plt.subplots(figsize=(7,7))
#     fig.suptitle("Comprehensive Kundali", fontsize=20, y=0.92, weight='bold')
#     fig.subplots_adjust(top=0.88, bottom=0.05, left=0.02, right=0.98)
    
#     ax.set_xlim(0,400)
#     ax.set_ylim(0,300)
#     ax.set_aspect('equal')
#     ax.axis('off')
    
#     # 3) Draw house outlines
#     for verts in HOUSE_VERTICES:
#         ax.add_patch(Polygon(verts, closed=True, fill=False, edgecolor='black', linewidth=1))
    
#     # 4) Create comprehensive drishti mapping
#     # This maps house_number -> [list of planets that aspect this house]
#     drishti_map = {}
    
#     for hi, h in enumerate(houses):
#         house_num = hi + 1
#         drishti_map[house_num] = []
        
#         # Check all planets in all houses to see if they aspect this house
#         for other_hi, other_h in enumerate(houses):
#             other_house_num = other_hi + 1
#             for planet_name, planet_data in other_h.planets.items():
#                 if planet_name in DRISHTI:
#                     aspects = DRISHTI[planet_name]
#                     for step in aspects:
#                         aspected_house = _anticlockwise_house(other_house_num, step)
#                         if aspected_house == house_num:
#                             drishti_map[house_num].append(planet_name)
    
#     # 5) Draw sign-numbers & sign-lords (with improved Rashi+Drishti logic)
#     for hi, h in enumerate(houses):
#         xs, ys = zip(*HOUSE_VERTICES[hi])
#         cx, cy = sum(xs)/len(xs), sum(ys)/len(ys)
#         region = _region(cx, cy)
#         sdx, sdy = SIGN_SHIFT[region]
        
#         # Optional big blue sign-number (unchanged from original)
#         if plot_signs:
#             ax.text(cx+sdx, cy+sdy,
#                     str(h.sign_num),
#                     ha='center', va='center',
#                     fontsize=16, weight='bold', color='blue')
        
#         # Sign-lord with potential combined Rashi+Drishti
#         lord = SIGN_LORDS[h.sign_num]
#         l_abbr = PLANET_ABBR[lord]
#         house_num = hi + 1
        
#         # Check if this sign lord also has drishti on this house
#         has_drishti = lord in drishti_map.get(house_num, [])
        
#         if has_drishti:
#             # Show both Rashi and Drishti for sign lord
#             lord_label = f"{l_abbr}$^{{Rashi}}_{{Drishti}}$"
#         else:
#             # Show only Rashi for sign lord
#             lord_label = f"{l_abbr}$^{{Rashi}}$"
            
#         ax.text(cx + sdx + 6, cy + sdy + 4,
#                 lord_label,
#                 ha='left', va='bottom',
#                 fontsize=8, color='darkgreen')
    
#     # 6) Draw planets in houses + drishti planets
#     for hi, h in enumerate(houses):
#         xs, ys = zip(*HOUSE_VERTICES[hi])
#         cx, cy = sum(xs)/len(xs), sum(ys)/len(ys)
#         region = _region(cx, cy)
#         pdx, pdy = PLANET_SHIFT[region]
#         house_num = hi + 1
        
#         # Collect all items to display in this house
#         all_display_items = []
        
#         # 1. Add planets actually in this house (with degrees, arrows, Re, De)
#         for planet_name, planet_data in h.planets.items():
#             deg = int(planet_data['lon'] % 30)
#             abbr = PLANET_ABBR[planet_name]
#             half = '↑' if (planet_data['lon'] % 30) >= 15 else '↓'
            
#             label = f"{abbr} {deg}°{half}"
#             if planet_data.get('retro'):
#                 label += "$^{Re}$"
#             if planet_data.get('debilitated'):
#                 label += "$_{De}$"
            
#             all_display_items.append(label)
        
#         # 2. Add planets that aspect this house (with Drishti subscript)
#         # But exclude: planets already in house, sign lord (already handled above)
#         sign_lord = SIGN_LORDS[h.sign_num]
#         for planet_name in drishti_map.get(house_num, []):
#             if planet_name not in h.planets and planet_name != sign_lord:
#                 abbr = PLANET_ABBR[planet_name]
#                 label = f"{abbr}$_{{Drishti}}$"
#                 all_display_items.append(label)
        
#         # 3. Position all items around the house center
#         for idx, label in enumerate(all_display_items):
#             if len(all_display_items) == 1:
#                 # Single item positioned at center with slight offset
#                 angle = 0
#                 radius = 0
#             else:
#                 # Multiple items distributed around circle
#                 angle = 2 * math.pi * idx / len(all_display_items)
#                 radius = 18
            
#             x0 = cx + pdx + radius * math.cos(angle)
#             y0 = cy + pdy + radius * math.sin(angle)
            
#             # Clamp to chart boundaries (unchanged from original)
#             x = min(max(x0, 5), 395)
#             y = min(max(y0, 5), 295)
            
#             # Draw with same formatting as original
#             ax.text(x, y, label,
#                     ha='center', va='center',
#                     fontsize=7, weight='bold', color='maroon')
    
#     # 7) Footer legend (updated to mention Drishti)
#     fig.text(0.5, 0.03,
#              "↑/↓=upper/lower half • Green=sign-lord • Drishti=subscript • Re=retro • De=debilitated",
#              ha='center', fontsize=10)
    
#     plt.show()
#     return houses

# plot_lagna_chart, plot_moon_chart, plot_hora_chart,
# plot_drekkana_chart, plot_chaturthamsha_chart, plot_saptamamsha_chart, plot_dashamamsha_chart,
# plot_dwadashamsha_chart, plot_shodashamsha_chart, plot_vimshamsha_chart, plot_shashtiamsha_chart,
# plot_chatuvimshamsha_chart, plot_saptvimshamsha_chart, plot_trishamsha_chart, plot_khavedamsha_chart,
# plot_akshavedamsha_chart, plot_shashtiamsha_chart
