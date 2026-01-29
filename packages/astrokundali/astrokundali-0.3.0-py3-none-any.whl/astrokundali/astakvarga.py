# ashtakvarga.py

import math
from typing import Dict, List
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from .astro_data import AstroData
from .plotter import (
    _build_houses, _region,
    SIGN_SHIFT, PLANET_SHIFT,
    HOUSE_VERTICES
)

# master ordered list of all possible factors
ALL_FACTORS = [
    'ascendant','sun','moon','mercury','venus',
    'mars','jupiter','saturn','north_node','south_node',
    'uranus','neptune','pluto'
]

# Parāśara aspect‑houses
ASPECTS: Dict[str,List[int]] = {
    'sun':     [7],    'moon':    [7],
    'mercury': [7],    'venus':   [7],
    'mars':    [4,7,8],'jupiter':[5,7,9],
    'saturn':  [3,7,10],
    'north_node':[5,7,9],'south_node':[5,7,9]
}

DEFAULT_N = 8   # asc + 7 classical planets

# ─────────────────────────────────────────────────────────────────────────────

def compute_bhinna_ashtakvarga(
    data: AstroData,
    n_factors:        int  = DEFAULT_N,
    include_occupancy: bool = True,
    include_aspects:   bool = True
) -> Dict[str, Dict[int,int]]:
    """
    Bhinna‑Ashtakavarga for the first `n_factors` bodies in ALL_FACTORS.
    Each X gets:
      - occupancy bindu from each other Y (if include_occupancy)
      - aspect bindus per ASPECTS[Y] (if include_aspects)
    """
    if not (1 <= n_factors <= len(ALL_FACTORS)):
        raise ValueError(f"n_factors must be 1–{len(ALL_FACTORS)}")
    factors = ALL_FACTORS[:n_factors]
    raw     = data.get_rashi_data()
    bav: Dict[str,Dict[int,int]] = {}

    for X in factors:
        x_sign = raw[X]['sign_num']
        counts = {h:0 for h in range(1,13)}
        for Y in factors:
            if Y == X:
                continue
            y_sign = raw[Y]['sign_num']
            if include_occupancy:
                d = (y_sign - x_sign) % 12 or 12
                counts[d] += 1
            if include_aspects and Y in ASPECTS:
                for a in ASPECTS[Y]:
                    counts[a] += 1
        bav[X] = counts

    return bav

# ─────────────────────────────────────────────────────────────────────────────

def compute_full_ashtakvarga(
    data: AstroData,
    n_factors:        int  = DEFAULT_N,
    include_self:      bool = True,
    include_occupancy: bool = True,
    include_aspects:   bool = True
) -> Dict[str, Dict[int,int]]:
    """
    Full Parāśara BAV = optional self‑point + Bhinna‑AV.
    """
    bav = compute_bhinna_ashtakvarga(
        data, n_factors,
        include_occupancy=include_occupancy,
        include_aspects=  include_aspects
    )
    if include_self:
        for counts in bav.values():
            counts[1] += 1
    return bav

# ─────────────────────────────────────────────────────────────────────────────

def compute_sarva_ashtakvarga(
    data: AstroData,
    n_factors:        int  = DEFAULT_N,
    include_self:      bool = True,
    include_occupancy: bool = True,
    include_aspects:   bool = True
) -> Dict[int,int]:
    """
    Sarva‑Ashtākavarga = sum of full AV for each X in first n_factors.
    """
    bav   = compute_full_ashtakvarga(
        data, n_factors,
        include_self, include_occupancy, include_aspects
    )
    sarva = {h:0 for h in range(1,13)}
    for counts in bav.values():
        for h,v in counts.items():
            sarva[h] += v
    return sarva

# ─────────────────────────────────────────────────────────────────────────────
# Plot helpers (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

def _plot_ashtakvarga(
    houses: List,
    title: str,
    description: str
):
    fig, ax = plt.subplots(figsize=(6,6))
    fig.suptitle(title, fontsize=16, y=0.88, weight='bold')
    fig.subplots_adjust(top=0.85, bottom=0.07, left=0.03, right=0.97)

    ax.set_xlim(0,400); ax.set_ylim(0,300)
    ax.set_aspect('equal'); ax.axis('off'); ax.invert_yaxis()

    for verts in HOUSE_VERTICES:
        ax.add_patch(Polygon(verts, closed=True, fill=False, edgecolor='black'))

    for i, h in enumerate(houses):
        xs, ys = zip(*HOUSE_VERTICES[i])
        cx, cy = sum(xs)/len(xs), sum(ys)/len(ys)

        region   = _region(cx, cy)
        sdx, sdy = SIGN_SHIFT.get(region,(0,0))
        pdx, pdy = PLANET_SHIFT.get(region,(0,0))

        # sign number
        ax.text(cx+sdx, cy+sdy, str(h.sign_num),
                ha='center', va='center',
                fontsize=10, weight='bold', color='blue')

        # bindu count
        bindu = getattr(h, 'bindus', 0)
        ax.text(cx+pdx, cy+20+pdy, str(bindu),
                ha='center', va='center',
                fontsize=12, weight='bold', color='green')

    fig.text(0.5, 0.06, description, ha='center', fontsize=12)
    plt.show()

# ─────────────────────────────────────────────────────────────────────────────

def plot_bhinna_ashtakvarga(
    data: AstroData,
    factor: str,
    include_occupancy: bool = True,
    include_aspects:   bool = True,
    house_system:      str  = 'whole_sign'
):
    """
    Plot Bhinna‑AV for a single `factor` (must be one of the first 8 in ALL_FACTORS).
    """
    if factor not in ALL_FACTORS[:DEFAULT_N]:
        raise ValueError(
            f"'{factor}' not in default factors {ALL_FACTORS[:DEFAULT_N]}"
        )
    bav     = compute_bhinna_ashtakvarga(
        data, DEFAULT_N,
        include_occupancy, include_aspects
    )
    raw     = data.get_rashi_data()
    houses  = _build_houses(raw, house_system, data)
    for idx, h in enumerate(houses, start=1):
        h.bindus = bav[factor][idx]

    _plot_ashtakvarga(
        houses,
        title=f"Bhinna‑Ashtākavarga ({factor.capitalize()})",
        description=f"occupancy={include_occupancy}, aspects={include_aspects}"
    )
    return houses

def plot_sarva_ashtakvarga(
    data: AstroData,
    n_factors:        int  = DEFAULT_N,
    include_self:      bool = True,
    include_occupancy: bool = True,
    include_aspects:   bool = True,
    house_system:      str  = 'whole_sign'
):
    """
    Plot Sarva‑AV for the first `n_factors` bodies.
    """
    sarva   = compute_sarva_ashtakvarga(
        data, n_factors,
        include_self, include_occupancy, include_aspects
    )
    raw     = data.get_rashi_data()
    houses  = _build_houses(raw, house_system, data)
    for idx, h in enumerate(houses, start=1):
        h.bindus = sarva[idx]

    _plot_ashtakvarga(
        houses,
        title="Sarva‑Ashtākavarga",
        description=(
            f"factors=first {n_factors}, self={include_self}, "
            f"occupancy={include_occupancy}, aspects={include_aspects}"
        )
    )
    return houses
