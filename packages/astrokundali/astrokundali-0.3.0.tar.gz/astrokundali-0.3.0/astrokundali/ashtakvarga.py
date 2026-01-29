# ashtakvarga.py

import math
from typing import Dict, List, Any
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from .astro_data import AstroData
from .plotter import (
    _build_houses, _region,
    SIGN_SHIFT, PLANET_SHIFT,
    HOUSE_VERTICES, CENTERS
)

# ─── Rāśi Names ───────────────────────────────────────────────────────────────
RASHI_NAMES = [
    "Mesha", "Vrishabha", "Mithuna", "Karka",
    "Simha", "Kanya",     "Tula",   "Vrischika",
    "Dhanu", "Makara",    "Kumbha", "Meena"
]

# ─── ashtakvarga.py (fixes highlighted) ───────────────────────────────────────

# … your imports …

# 1) Use these 8 factors for Bhinna
FACTORS = [
    'ascendant','sun','moon','mercury','venus',
    'mars','jupiter','saturn'
]

# 2) Parāśara aspects unchanged
ASPECTS = {
    'sun': [7], 'moon': [7], 'mercury': [7], 'venus': [7],
    'mars': [4,7,8], 'jupiter': [5,7,9], 'saturn': [3,7,10]
}

def compute_full_bhinna_ashtakvarga(data: AstroData) -> Dict[str, Dict[int,int]]:
    raw = data.get_rashi_data()
    bav = {}
    for X in FACTORS:
        x_sign = raw[X]['sign_num']
        counts = {h:0 for h in range(1,13)}

        # **NO** self‑point here

        for Y in FACTORS:
            if Y == X:
                continue
            y_sign = raw[Y]['sign_num']

            # occupancy
            d = (y_sign - x_sign) % 12 or 12
            counts[d] += 1

            # aspects
            for a in ASPECTS.get(Y, []):
                counts[a] += 1

        bav[X] = counts
    return bav

def compute_binary_bhinna(data: AstroData) -> Dict[str,Dict[int,int]]:
    """
    Clamp each X→house to 0 or 1 (if raw_count>0).
    """
    raw_bav = compute_full_bhinna_ashtakvarga(data)
    bin_bav = {}
    for X, chart in raw_bav.items():
        bin_bav[X] = {h: (1 if pts>0 else 0) for h,pts in chart.items()}
    return bin_bav

def compute_sarva_ashtakvarga(data: AstroData) -> Dict[int,int]:
    """
    SUM the **raw** BAV charts for Sun–Saturn (no ascendant),
    to get the 337 total and 22–39 per‑rāśi.
    """
    # NB: Sarva uses only the 7 grahas, ascendant **not** included
    sarva = {h:0 for h in range(1,13)}
    raw = data.get_rashi_data()

    for X in ['sun','moon','mercury','venus','mars','jupiter','saturn']:
        x_sign = raw[X]['sign_num']
        counts = {h:0 for h in range(1,13)}

        # **include** self‑point if you want, but Prokerala does **not** for Sarva
        # counts[1] += 1   # remove for their style

        for Y in ['sun','moon','mercury','venus','mars','jupiter','saturn']:
            if Y == X: continue
            y_sign = raw[Y]['sign_num']
            d = (y_sign - x_sign) % 12 or 12
            counts[d] += 1
            for a in ASPECTS.get(Y, []):
                counts[a] += 1

        # now add X’s raw_counts into the Sarva total
        for h,pts in counts.items():
            sarva[h] += pts

    return sarva

# ─── JSON EXPORTS ────────────────────────────────────────────────────────────

def get_bhinna_ashtakvarga_json(data: AstroData, factor: str) -> dict:
    if factor not in FACTORS:
        raise ValueError(f"Choose from {FACTORS}")
    bin_bav = compute_binary_bhinna(data)[factor]
    # row total = sum of 1’s = 48 for Sun
    total = sum(bin_bav.values())
    table = [
        {"rashi_number": i,
         "rashi_name":   RASHI_NAMES[i-1],
         "bindus":       bin_bav[i]}
        for i in range(1,13)
    ]
    return {"factor": factor, "total": total, "table": table}

def get_sarva_ashtakvarga_json(data: AstroData) -> dict:
    sarva = compute_sarva_ashtakvarga(data)
    total = sum(sarva.values())    # 337
    table = [
        {"rashi_number": i,
         "rashi_name":   RASHI_NAMES[i-1],
         "score":        sarva[i]}
        for i in range(1,13)
    ]
    return {"total": total, "table": table}


# # ashtakvarga.py

# import math
# from typing import Dict, List
# import matplotlib.pyplot as plt
# from matplotlib.patches import Polygon

# from .astro_data import AstroData
# from .plotter import (
#     _build_houses,         # your existing house‐system builder
#     _region,               # region‐bucketing helper
#     SIGN_SHIFT, PLANET_SHIFT,
#     HOUSE_VERTICES, CENTERS
# )

# # 1. Which “factors” (bodies) to include in Ashtākavarga
# FACTORS = [
#     'ascendant','sun','moon','mercury','venus',
#     'mars','jupiter','saturn' #,'north_node','south_node'
# ]

# # 2. Parāśara aspect‐houses per factor
# ASPECTS: Dict[str,List[int]] = {
#     'sun':     [7],
#     'moon':    [7],
#     'mercury': [7],
#     'venus':   [7],
#     'mars':    [4,7,8],
#     'jupiter': [5,7,9],
#     'saturn':  [3,7,10],
#     'north_node':[5,7,9],
#     'south_node':[5,7,9]
# }

# def compute_full_bhinna_ashtakvarga(data: AstroData) -> Dict[str, Dict[int,int]]:
#     """
#     Full Bhinna‑Ashtākavarga per Parāśara:
#       • self‐point in House 1
#       • occupancy bindu for each other factor Y
#       • aspect‐bindus per ASPECTS[Y]
#     Returns: { factor: {house_number: bindu_count} }
#     """
#     raw = data.get_rashi_data()
#     bav: Dict[str, Dict[int,int]] = {}
#     for X in FACTORS:
#         x_sign = raw[X]['sign_num']
#         counts = {i:0 for i in range(1,13)}

#         # (a) Self‐point
#         counts[1] += 1

#         # (b) From each other factor Y
#         for Y in FACTORS:
#             if Y == X:
#                 continue
#             y_sign = raw[Y]['sign_num']

#             # (b1) Occupancy: 1 bindu in house = distance(X→Y)
#             d = (y_sign - x_sign) % 12 or 12
#             counts[d] += 1

#             # (b2) Aspects: each aspect‐house from Y adds 1 bindu
#             for a in ASPECTS.get(Y, []):
#                 counts[a] += 1

#         bav[X] = counts
#     return bav

# def compute_sarva_ashtakvarga(data: AstroData) -> Dict[int,int]:
#     """
#     Sum all Bhinna‑Ashtākavarga charts to get Sarva‑Ashtākavarga.
#     Returns: { house_number: total_bindus }
#     """
#     bav = compute_full_bhinna_ashtakvarga(data)
#     sarva = {i:0 for i in range(1,13)}
#     for counts in bav.values():
#         for h, v in counts.items():
#             sarva[h] += v
#     return sarva

# # -------------------------------------------------------------------
# # Plotting routines
# # -------------------------------------------------------------------

# def _plot_ashtakvarga(
#     houses: List,
#     title: str,
#     description: str
# ):
#     """
#     Shared plot helper: draws the 12 diamond houses,
#     prints sign numbers in blue, bindu‐counts in green.
#     """
#     fig, ax = plt.subplots(figsize=(6,6))
#     fig.suptitle(title, fontsize=16, y=0.88, weight='bold')
#     fig.subplots_adjust(top=0.85, bottom=0.07, left=0.03, right=0.97)

#     ax.set_xlim(0,400); ax.set_ylim(0,300)
#     ax.set_aspect('equal'); ax.axis('off'); ax.invert_yaxis()

#     # draw house outlines
#     for verts in HOUSE_VERTICES:
#         ax.add_patch(Polygon(verts, closed=True, fill=False, edgecolor='black'))

#     # annotate each house
#     for i, h in enumerate(houses):
#         xs, ys = zip(*HOUSE_VERTICES[i])
#         cx, cy = sum(xs)/len(xs), sum(ys)/len(ys)

#         region   = _region(cx, cy)
#         sdx, sdy = SIGN_SHIFT.get(region,(0,0))
#         pdx, pdy = PLANET_SHIFT.get(region,(0,0))

#         # sign number
#         ax.text(cx+sdx, cy+sdy, str(h.sign_num),
#                 ha='center', va='center',
#                 fontsize=10, weight='bold', color='blue')

#         # bindu count
#         bindu = getattr(h, 'bindus', 0)
#         ax.text(cx+pdx, cy+20+pdy, str(bindu),
#                 ha='center', va='center',
#                 fontsize=12, weight='bold', color='green')

#     fig.text(0.5, 0.06, description, ha='center', fontsize=12)
#     plt.show()

# def plot_bhinna_ashtakvarga(
#     data: AstroData,
#     factor: str,
#     house_system: str = 'whole_sign'
# ):
#     """
#     Plot Bhinna‑Ashtākavarga for one factor (e.g. 'moon', 'mars', etc.).
#     """
#     bav = compute_full_bhinna_ashtakvarga(data)
#     if factor not in bav:
#         raise ValueError(f"Unknown factor '{factor}'. Choose from {FACTORS}")
#     scores = bav[factor]

#     # build houses (to get sign ordering)
#     raw    = data.get_rashi_data()
#     houses = _build_houses(raw, house_system, data)
#     # attach bindus
#     for idx, h in enumerate(houses, start=1):
#         h.bindus = scores[idx]

#     _plot_ashtakvarga(
#         houses,
#         title=f"Bhinna‑Ashtākavarga ({factor.capitalize()})",
#         description="Self‐point + occupancy + aspects per Parāśara"
#     )
#     return houses

# def plot_sarva_ashtakvarga(
#     data: AstroData,
#     house_system: str = 'whole_sign'
# ):
#     """
#     Plot Sarva‑Ashtākavarga (sum of all BAV charts).
#     """
#     sarva  = compute_sarva_ashtakvarga(data)
#     raw    = data.get_rashi_data()
#     houses = _build_houses(raw, house_system, data)
#     for idx, h in enumerate(houses, start=1):
#         h.bindus = sarva[idx]

#     _plot_ashtakvarga(
#         houses,
#         title="Sarva‑Ashtākavarga (Total Bindus)",
#         description="Summed across Asc, Sun, Moon, Mars, Mer., Jup., Ven., Sat."
#     )
#     return houses
