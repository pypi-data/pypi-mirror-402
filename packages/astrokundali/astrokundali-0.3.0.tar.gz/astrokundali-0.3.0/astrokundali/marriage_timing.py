"""
astrokundali/marriage_timing.py

Marriage Timing Prediction Module
- Analyzes 7th house, its lord, Venus, Jupiter positions
- Identifies favorable dasha-antardasha periods for marriage
- Returns probable marriage year ranges with confidence scores
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from .astro_data import AstroData
from .astro_chart import AstroChart
from .dispositions import get_dispositions, SIGN_LORDS, RASHI_NAMES
from .dasha import (
    get_dasha_periods, 
    get_antardasha_periods, 
    calculate_dasha_balance,
    get_birth_datetime,
    DashaPeriod,
    DASHA_SEQUENCE
)


# Marriage-related house significances
MARRIAGE_HOUSES = {
    7: 'Primary house of marriage and partnerships',
    2: 'Family life and domestic happiness',
    5: 'Romance, love affairs, and emotional connections',
    11: 'Fulfillment of desires and gains through relationships',
    1: 'Self, personality, and initiative in relationships',
    4: 'Home, comfort, and emotional security'
}

# Planets and their marriage significance
MARRIAGE_KARAKAS = {
    'venus': {
        'role': 'Primary Karaka',
        'significance': 'Universal significator of marriage, love, romance for all genders',
        'weight': 3
    },
    'jupiter': {
        'role': 'Husband Karaka',
        'significance': 'Significator of husband for women, wisdom and blessings in marriage',
        'weight': 2
    },
    'moon': {
        'role': 'Emotional Karaka',
        'significance': 'Emotional compatibility and mental peace in marriage',
        'weight': 1
    }
}

# Drishti (aspects) for marriage timing
FULL_ASPECTS = {
    'sun': [7],
    'moon': [7],
    'mercury': [7],
    'venus': [7],
    'mars': [4, 7, 8],
    'jupiter': [5, 7, 9],
    'saturn': [3, 7, 10],
    'rahu': [5, 7, 9],
    'ketu': [5, 7, 9]
}


@dataclass
class MarriageWindow:
    """Represents a favorable period for marriage"""
    start_year: int
    end_year: int
    mahadasha: str
    antardasha: str
    score: float
    factors: List[str]
    confidence: str  # 'High', 'Medium', 'Low'


def _get_house_from_ascendant(planet_sign: int, ascendant_sign: int) -> int:
    """Calculate house number from planet's sign relative to ascendant"""
    house = (planet_sign - ascendant_sign) % 12 + 1
    return house


def analyze_7th_house(astrodata: AstroData, house_system: str = 'whole_sign') -> Dict[str, Any]:
    """
    Comprehensive analysis of the 7th house for marriage potential.
    
    Returns:
        Dict with 7th house details, lord, occupants, aspects
    """
    raw = astrodata.get_rashi_data()
    dispositions = get_dispositions(astrodata, house_system)
    
    # Get ascendant sign
    asc_sign = raw['ascendant']['sign_num']
    
    # Calculate 7th house sign
    seventh_house_sign = ((asc_sign - 1 + 6) % 12) + 1
    seventh_house_lord = SIGN_LORDS[seventh_house_sign]
    
    # Get 7th lord's position
    seventh_lord_data = dispositions.get(seventh_house_lord, {})
    seventh_lord_house = seventh_lord_data.get('house_number', None)
    seventh_lord_sign = seventh_lord_data.get('sign_number', None)
    
    # Find planets in 7th house
    planets_in_7th = []
    for planet, data in dispositions.items():
        if planet in ['ascendant']:
            continue
        if data.get('house_number') == 7:
            planets_in_7th.append({
                'planet': planet,
                'sign': data.get('sign_number'),
                'nakshatra': data.get('nakshatra'),
                'retrograde': data.get('retrograde', False)
            })
    
    # Find planets aspecting 7th house
    aspecting_7th = []
    for planet, data in dispositions.items():
        if planet in ['ascendant']:
            continue
        planet_house = data.get('house_number')
        if planet_house and planet in FULL_ASPECTS:
            for aspect in FULL_ASPECTS[planet]:
                target_house = ((planet_house - 1 + aspect - 1) % 12) + 1
                if target_house == 7:
                    aspecting_7th.append({
                        'planet': planet,
                        'from_house': planet_house,
                        'aspect_type': f"{aspect}th aspect"
                    })
    
    # Check Venus position
    venus_data = dispositions.get('venus', {})
    venus_house = venus_data.get('house_number')
    venus_sign = venus_data.get('sign_number')
    venus_nakshatra = venus_data.get('nakshatra')
    
    # Check Jupiter position (important for female charts)
    jupiter_data = dispositions.get('jupiter', {})
    jupiter_house = jupiter_data.get('house_number')
    jupiter_sign = jupiter_data.get('sign_number')
    
    # Calculate 7th house strength score
    strength_score = 0
    strength_factors = []
    
    # Benefic planets in 7th house
    benefics = ['jupiter', 'venus', 'mercury', 'moon']
    malefics = ['saturn', 'mars', 'rahu', 'ketu', 'sun']
    
    for p in planets_in_7th:
        if p['planet'] in benefics:
            strength_score += 2
            strength_factors.append(f"Benefic {p['planet'].title()} in 7th house")
        elif p['planet'] in malefics:
            strength_score -= 1
            strength_factors.append(f"Malefic {p['planet'].title()} in 7th house (challenging)")
    
    # 7th lord in good houses (1, 2, 4, 5, 7, 9, 10, 11)
    favorable_houses = [1, 2, 4, 5, 7, 9, 10, 11]
    if seventh_lord_house in favorable_houses:
        strength_score += 2
        strength_factors.append(f"7th lord in favorable {seventh_lord_house}th house")
    elif seventh_lord_house in [6, 8, 12]:
        strength_score -= 1
        strength_factors.append(f"7th lord in dusthana {seventh_lord_house}th house")
    
    # Venus in good position
    if venus_house in [1, 2, 4, 5, 7, 9, 10, 11]:
        strength_score += 1
        strength_factors.append(f"Venus in favorable {venus_house}th house")
    
    # Jupiter aspecting 7th or 7th lord
    for asp in aspecting_7th:
        if asp['planet'] == 'jupiter':
            strength_score += 2
            strength_factors.append("Jupiter aspects 7th house (auspicious)")
    
    return {
        'seventh_house_sign': seventh_house_sign,
        'seventh_house_sign_name': RASHI_NAMES[seventh_house_sign - 1],
        'seventh_house_lord': seventh_house_lord,
        'seventh_lord_house': seventh_lord_house,
        'seventh_lord_sign': seventh_lord_sign,
        'planets_in_7th': planets_in_7th,
        'planets_aspecting_7th': aspecting_7th,
        'venus_position': {
            'house': venus_house,
            'sign': venus_sign,
            'sign_name': RASHI_NAMES[venus_sign - 1] if venus_sign else None,
            'nakshatra': venus_nakshatra
        },
        'jupiter_position': {
            'house': jupiter_house,
            'sign': jupiter_sign,
            'sign_name': RASHI_NAMES[jupiter_sign - 1] if jupiter_sign else None
        },
        'strength_score': strength_score,
        'strength_factors': strength_factors
    }


def get_marriage_significators(astrodata: AstroData, house_system: str = 'whole_sign') -> Dict[str, Any]:
    """
    Identify all planets that can trigger marriage in their dasha/antardasha.
    
    Marriage can occur during periods of:
    1. 7th house lord
    2. Planets in 7th house
    3. Venus (universal marriage karaka)
    4. Jupiter (husband karaka for women)
    5. Lords of 2nd, 5th, 11th houses (supporting houses)
    6. Planets aspecting 7th house
    """
    raw = astrodata.get_rashi_data()
    dispositions = get_dispositions(astrodata, house_system)
    asc_sign = raw['ascendant']['sign_num']
    
    significators = {}
    
    # 1. 7th house lord (highest significance)
    seventh_sign = ((asc_sign - 1 + 6) % 12) + 1
    seventh_lord = SIGN_LORDS[seventh_sign]
    significators[seventh_lord] = {
        'weight': 5,
        'reason': '7th house lord (primary marriage significator)'
    }
    
    # 2. Planets in 7th house
    for planet, data in dispositions.items():
        if planet in ['ascendant']:
            continue
        if data.get('house_number') == 7:
            if planet not in significators:
                significators[planet] = {'weight': 0, 'reason': ''}
            significators[planet]['weight'] += 4
            if significators[planet]['reason']:
                significators[planet]['reason'] += '; '
            significators[planet]['reason'] += 'Placed in 7th house'
    
    # 3. Venus (always a significator)
    if 'venus' not in significators:
        significators['venus'] = {'weight': 0, 'reason': ''}
    significators['venus']['weight'] += 4
    if significators['venus']['reason']:
        significators['venus']['reason'] += '; '
    significators['venus']['reason'] += 'Natural marriage karaka'
    
    # 4. Jupiter
    if 'jupiter' not in significators:
        significators['jupiter'] = {'weight': 0, 'reason': ''}
    significators['jupiter']['weight'] += 2
    if significators['jupiter']['reason']:
        significators['jupiter']['reason'] += '; '
    significators['jupiter']['reason'] += 'Husband karaka and auspicious planet'
    
    # 5. Lords of supporting houses (2, 5, 11)
    second_sign = ((asc_sign - 1 + 1) % 12) + 1
    fifth_sign = ((asc_sign - 1 + 4) % 12) + 1
    eleventh_sign = ((asc_sign - 1 + 10) % 12) + 1
    
    supporting_lords = {
        SIGN_LORDS[second_sign]: ('2nd house lord', 'Family happiness'),
        SIGN_LORDS[fifth_sign]: ('5th house lord', 'Romance and love'),
        SIGN_LORDS[eleventh_sign]: ('11th house lord', 'Fulfillment of desires')
    }
    
    for lord, (house_desc, significance) in supporting_lords.items():
        if lord not in significators:
            significators[lord] = {'weight': 0, 'reason': ''}
        significators[lord]['weight'] += 2
        if significators[lord]['reason']:
            significators[lord]['reason'] += '; '
        significators[lord]['reason'] += f'{house_desc} ({significance})'
    
    # 6. Planets aspecting 7th house
    for planet, data in dispositions.items():
        if planet in ['ascendant']:
            continue
        planet_house = data.get('house_number')
        if planet_house and planet in FULL_ASPECTS:
            for aspect in FULL_ASPECTS[planet]:
                target_house = ((planet_house - 1 + aspect - 1) % 12) + 1
                if target_house == 7:
                    if planet not in significators:
                        significators[planet] = {'weight': 0, 'reason': ''}
                    significators[planet]['weight'] += 1
                    if significators[planet]['reason']:
                        significators[planet]['reason'] += '; '
                    significators[planet]['reason'] += 'Aspects 7th house'
    
    return significators


def score_dasha_for_marriage(mahadasha: str, antardasha: str,
                            significators: Dict[str, Any],
                            seventh_analysis: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Score a dasha-antardasha combination for marriage potential.
    
    Returns:
        Tuple of (score, list of contributing factors)
    """
    score = 0.0
    factors = []
    
    # Check Mahadasha
    if mahadasha in significators:
        sig = significators[mahadasha]
        score += sig['weight'] * 0.6  # Mahadasha contributes 60%
        factors.append(f"Mahadasha of {mahadasha.title()}: {sig['reason']}")
    
    # Check Antardasha
    if antardasha in significators:
        sig = significators[antardasha]
        score += sig['weight'] * 0.4  # Antardasha contributes 40%
        factors.append(f"Antardasha of {antardasha.title()}: {sig['reason']}")
    
    # Bonus for Venus or Jupiter in either position
    if mahadasha == 'venus' or antardasha == 'venus':
        score += 1.5
        factors.append("Venus period (very favorable for marriage)")
    
    if mahadasha == 'jupiter' or antardasha == 'jupiter':
        score += 1.0
        factors.append("Jupiter period (auspicious blessings)")
    
    # Bonus for 7th lord in either position
    seventh_lord = seventh_analysis.get('seventh_house_lord')
    if mahadasha == seventh_lord or antardasha == seventh_lord:
        score += 2.0
        factors.append(f"Period of 7th lord ({seventh_lord.title()})")
    
    # Penalty for malefic-only combinations
    malefics = ['saturn', 'mars', 'rahu', 'ketu']
    if mahadasha in malefics and antardasha in malefics:
        if mahadasha not in significators or antardasha not in significators:
            score -= 1.0
            factors.append("Double malefic period (may cause delays)")
    
    return score, factors


def predict_marriage_timing(astrodata: AstroData, 
                           house_system: str = 'whole_sign',
                           min_age: int = 18,
                           max_age: int = 45) -> Dict[str, Any]:
    """
    Predict favorable periods for marriage based on Vedic astrology principles.
    
    Args:
        astrodata: Birth data
        house_system: House system to use (default 'whole_sign')
        min_age: Minimum marriage age to consider (default 18)
        max_age: Maximum age to analyze up to (default 45)
        
    Returns:
        Dict containing:
        - seventh_house_analysis: Detailed 7th house analysis
        - significators: Marriage-indicating planets and their weights
        - favorable_periods: List of favorable dasha-antardasha windows
        - summary: Text summary of findings
    """
    # Get 7th house analysis
    seventh_analysis = analyze_7th_house(astrodata, house_system)
    
    # Get marriage significators
    significators = get_marriage_significators(astrodata, house_system)
    
    # Get birth datetime and calculate age range
    birth_dt = get_birth_datetime(astrodata)
    min_date = birth_dt.replace(year=birth_dt.year + min_age)
    max_date = birth_dt.replace(year=birth_dt.year + max_age)
    
    # Get dasha periods
    mahadashas = get_dasha_periods(astrodata, years_ahead=max_age + 5)
    
    # Score each dasha-antardasha combination
    all_periods = []
    
    for md in mahadashas:
        # Skip if entirely outside our age range
        if md.end_date < min_date or md.start_date > max_date:
            continue
        
        antardashas = get_antardasha_periods(md)
        
        for ad in antardashas:
            # Skip if outside age range
            if ad.end_date < min_date or ad.start_date > max_date:
                continue
            
            # Clip to our age range
            effective_start = max(ad.start_date, min_date)
            effective_end = min(ad.end_date, max_date)
            
            # Score this period
            score, factors = score_dasha_for_marriage(
                md.planet, ad.planet, significators, seventh_analysis
            )
            
            if score > 0:  # Only include positive-scoring periods
                all_periods.append({
                    'start_date': effective_start,
                    'end_date': effective_end,
                    'start_year': effective_start.year,
                    'end_year': effective_end.year,
                    'mahadasha': md.planet,
                    'antardasha': ad.planet,
                    'score': round(score, 2),
                    'factors': factors
                })
    
    # Sort by score (descending)
    all_periods.sort(key=lambda x: (-x['score'], x['start_year']))
    
    # Assign confidence levels
    if all_periods:
        max_score = all_periods[0]['score']
        for period in all_periods:
            ratio = period['score'] / max_score if max_score > 0 else 0
            if ratio >= 0.8:
                period['confidence'] = 'High'
            elif ratio >= 0.5:
                period['confidence'] = 'Medium'
            else:
                period['confidence'] = 'Low'
    
    # Take top periods (up to 10)
    favorable_periods = all_periods[:10]
    
    # Generate summary
    summary_lines = []
    summary_lines.append("=== Marriage Timing Analysis ===\n")
    
    # 7th house summary
    summary_lines.append(f"7th House Sign: {seventh_analysis['seventh_house_sign_name']}")
    summary_lines.append(f"7th House Lord: {seventh_analysis['seventh_house_lord'].title()} "
                        f"(in house {seventh_analysis['seventh_lord_house']})")
    
    if seventh_analysis['planets_in_7th']:
        planets_str = ', '.join([p['planet'].title() for p in seventh_analysis['planets_in_7th']])
        summary_lines.append(f"Planets in 7th House: {planets_str}")
    else:
        summary_lines.append("Planets in 7th House: None")
    
    summary_lines.append(f"Venus Position: House {seventh_analysis['venus_position']['house']} "
                        f"in {seventh_analysis['venus_position']['sign_name']}")
    
    summary_lines.append(f"\n7th House Strength Score: {seventh_analysis['strength_score']}")
    for factor in seventh_analysis['strength_factors']:
        summary_lines.append(f"  • {factor}")
    
    # Top favorable periods
    summary_lines.append("\n=== Most Favorable Periods ===\n")
    
    if favorable_periods:
        for i, period in enumerate(favorable_periods[:5], 1):
            summary_lines.append(
                f"{i}. {period['start_year']}-{period['end_year']}: "
                f"{period['mahadasha'].title()}-{period['antardasha'].title()} "
                f"(Score: {period['score']}, Confidence: {period['confidence']})"
            )
    else:
        summary_lines.append("No highly favorable periods found in the specified age range.")
    
    return {
        'seventh_house_analysis': seventh_analysis,
        'significators': significators,
        'favorable_periods': favorable_periods,
        'all_scored_periods': all_periods,
        'summary': '\n'.join(summary_lines),
        'birth_date': birth_dt.strftime('%Y-%m-%d'),
        'analysis_range': f"Age {min_age} to {max_age}"
    }


def get_marriage_yogas(astrodata: AstroData, house_system: str = 'whole_sign') -> List[Dict[str, Any]]:
    """
    Detect specific marriage-related yogas in the chart.
    
    Returns:
        List of detected marriage yogas with descriptions
    """
    raw = astrodata.get_rashi_data()
    dispositions = get_dispositions(astrodata, house_system)
    asc_sign = raw['ascendant']['sign_num']
    
    yogas = []
    
    # Calculate house signs
    seventh_sign = ((asc_sign - 1 + 6) % 12) + 1
    seventh_lord = SIGN_LORDS[seventh_sign]
    
    # Get house positions
    venus_house = dispositions.get('venus', {}).get('house_number')
    jupiter_house = dispositions.get('jupiter', {}).get('house_number')
    seventh_lord_house = dispositions.get(seventh_lord, {}).get('house_number')
    
    # 1. Venus in 7th house
    if venus_house == 7:
        yogas.append({
            'name': 'Venus in 7th House',
            'type': 'Favorable',
            'description': 'Venus (natural marriage karaka) in 7th house indicates beautiful spouse and happy marriage.',
            'effect': 'Early and harmonious marriage likely'
        })
    
    # 2. Jupiter aspecting 7th house or in 7th
    if jupiter_house == 7:
        yogas.append({
            'name': 'Jupiter in 7th House',
            'type': 'Favorable',
            'description': 'Jupiter in 7th house brings spiritual and wise spouse, blessed married life.',
            'effect': 'Stable and prosperous marriage'
        })
    
    # Check Jupiter's 5th and 9th aspects on 7th house
    if jupiter_house:
        fifth_from_jupiter = ((jupiter_house - 1 + 4) % 12) + 1
        ninth_from_jupiter = ((jupiter_house - 1 + 8) % 12) + 1
        if fifth_from_jupiter == 7 or ninth_from_jupiter == 7:
            yogas.append({
                'name': 'Jupiter Aspect on 7th House',
                'type': 'Favorable',
                'description': 'Jupiter\'s benefic aspect on 7th house protects marriage.',
                'effect': 'Divine blessings in married life'
            })
    
    # 3. 7th lord in 1st house (mutual reception)
    if seventh_lord_house == 1:
        yogas.append({
            'name': '7th Lord in Lagna',
            'type': 'Favorable',
            'description': '7th lord in 1st house indicates strong focus on partnership.',
            'effect': 'Marriage plays central role in life'
        })
    
    # 4. 7th lord in 7th house (own house)
    if seventh_lord_house == 7:
        yogas.append({
            'name': '7th Lord in Own House',
            'type': 'Very Favorable',
            'description': '7th lord in its own sign strengthens marriage prospects.',
            'effect': 'Strong and stable marriage indicated'
        })
    
    # 5. 7th lord in dusthana (6, 8, 12) - challenging
    if seventh_lord_house in [6, 8, 12]:
        yogas.append({
            'name': '7th Lord in Dusthana',
            'type': 'Challenging',
            'description': f'7th lord in {seventh_lord_house}th house may cause delays or challenges.',
            'effect': 'Marriage may face obstacles, patience required'
        })
    
    # 6. Saturn aspects 7th house
    saturn_house = dispositions.get('saturn', {}).get('house_number')
    if saturn_house:
        seventh_from_saturn = ((saturn_house - 1 + 6) % 12) + 1  # Saturn's 7th aspect
        third_from_saturn = ((saturn_house - 1 + 2) % 12) + 1   # Saturn's 3rd aspect
        tenth_from_saturn = ((saturn_house - 1 + 9) % 12) + 1   # Saturn's 10th aspect
        
        if 7 in [seventh_from_saturn, third_from_saturn, tenth_from_saturn]:
            yogas.append({
                'name': 'Saturn Aspect on 7th House',
                'type': 'Delaying',
                'description': 'Saturn\'s aspect on 7th house typically delays marriage.',
                'effect': 'Marriage after 28-30 years likely, stable after initial challenges'
            })
    
    # 7. Rahu/Ketu axis on 1-7
    rahu_house = dispositions.get('rahu', {}).get('house_number')
    ketu_house = dispositions.get('ketu', {}).get('house_number')
    
    if rahu_house == 7 or ketu_house == 7:
        yogas.append({
            'name': 'Rahu/Ketu on 7th House',
            'type': 'Karmic',
            'description': 'Nodal axis on marriage house indicates karmic lessons in relationships.',
            'effect': 'Unconventional marriage path, learning through relationships'
        })
    
    return yogas
