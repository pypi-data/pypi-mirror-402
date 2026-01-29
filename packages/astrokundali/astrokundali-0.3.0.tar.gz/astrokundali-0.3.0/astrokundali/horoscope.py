"""
astrokundali/horoscope.py

Enhanced Secular Horoscope Report Generator
- Fixed ascendant element extraction
- Improved conjunction interpretations
- Comprehensive secular guidance
"""

import json
from pathlib import Path
from itertools import combinations
from typing import List, Dict, Any, Tuple

from .astro_data import AstroData
from .dispositions import get_dispositions, DRISHTI, _anticlockwise_house
from .yogas_detector import detect_yogas

# ─── Load Interpretation Data ──────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / 'data'

def _load_json(path: Path) -> dict:
    """Load JSON and strip any remaining religious content."""
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        print(f"Warning: {path} not found. Using default data.")
        return {}
    
    def strip(obj):
        if isinstance(obj, str):
            if any(word in obj.lower() for word in ['remedy:', 'chant', 'mantra', 'puja', 'donate']):
                return ''
            return obj
        if isinstance(obj, list):
            return [strip(i) for i in obj if strip(i)]
        if isinstance(obj, dict):
            return {k: strip(v) for k, v in obj.items()}
        return obj
    return strip(data)

ASC_INT      = _load_json(DATA_DIR / 'ascendant_interpretations.json')
CONJ_INT     = _load_json(DATA_DIR / 'conj_interpretations.json')
GEN_INT      = _load_json(DATA_DIR / 'general_interpretations.json')
YOGAS        = _load_json(DATA_DIR / 'yogas.json')
ARUDHA_DATA  = _load_json(DATA_DIR / 'arudha_lagna.json')
ELEMENTS     = _load_json(DATA_DIR / 'elements.json')
RASHI_DESCR  = _load_json(DATA_DIR / 'rashi_descriptions.json')
ASPECTS_INT  = _load_json(DATA_DIR / 'aspects_interpretations.json')

# ─── Enhanced Helper Functions ──────────────────────────────────────────────

def _get_conjunction_key(planets: List[str], house: int) -> str:
    """Generate standardized conjunction key for lookup."""
    sorted_planets = sorted(planets)
    return "_".join(sorted_planets + [str(house)])

def _analyze_house_conjunctions(planets: List[str]) -> List[Tuple[str, ...]]:
    """Get all meaningful planet combinations (2-3 planets)."""
    combos = []
    # Two-planet combinations
    if len(planets) >= 2:
        for combo in combinations(planets, 2):
            combos.append(combo)
    # Three-planet combinations
    if len(planets) >= 3:
        for combo in combinations(planets, 3):
            combos.append(combo)
    return combos

def _get_conjunction_interpretation(planets: Tuple[str, ...], house: int) -> Dict[str, Any]:
    """Get interpretation for planet combination in specific house."""
    key = _get_conjunction_key(list(planets), house)
    
    # Direct lookup in conjunction interpretations
    if key in CONJ_INT:
        return {
            'key': key,
            'planets': planets,
            'house': house,
            'text': CONJ_INT[key]['text'],
            'canceled': False,
            'source': 'direct'
        }
    
    # Try to build from individual planet interpretations
    planet_effects = []
    for planet in planets:
        planet_key = f"{planet}_{house}"
        if planet_key in CONJ_INT:
            planet_effects.extend(CONJ_INT[planet_key].get('text', []))
    
    if planet_effects:
        return {
            'key': key,
            'planets': planets,
            'house': house,
            'text': planet_effects,
            'canceled': False,
            'source': 'combined'
        }
    
    # Enhanced generic fallback with specific house interpretations
    planet_names = ", ".join([p.replace('_', ' ').title() for p in planets])
    house_meanings = {
        1: "personality and self-expression",
        2: "wealth, family, and values",
        3: "communication, siblings, and courage",
        4: "home, mother, and emotional security",
        5: "creativity, children, and romance",
        6: "health, service, and daily work",
        7: "partnerships, marriage, and business",
        8: "transformation, mysteries, and shared resources",
        9: "wisdom, higher learning, and spirituality",
        10: "career, reputation, and public status",
        11: "gains, friendships, and aspirations",
        12: "spirituality, losses, and foreign connections"
    }
    
    house_meaning = house_meanings.get(house, f"the {house}th house")
    
    # Create more specific interpretations based on planet combinations
    interpretations = []
    
    if 'sun' in planets and 'mercury' in planets:
        interpretations.append(f"Sun-Mercury conjunction in {house_meaning} enhances intellectual confidence and authoritative communication.")
        interpretations.append("Develop leadership through clear communication and avoid becoming overly argumentative.")
    
    if 'sun' in planets and 'venus' in planets:
        interpretations.append(f"Sun-Venus conjunction in {house_meaning} brings charm and artistic expression to your personality.")
        interpretations.append("Balance ego with diplomacy and use your natural charisma to help others.")
    
    if 'mercury' in planets and 'venus' in planets:
        interpretations.append(f"Mercury-Venus conjunction in {house_meaning} creates eloquent, harmonious communication.")
        interpretations.append("Develop artistic or diplomatic skills and practice persuasive yet ethical communication.")
    
    if 'mars' in planets and house == 1:
        interpretations.append("Mars influence creates dynamic energy and assertiveness in your personality.")
        interpretations.append("Channel this energy through regular exercise and constructive goal-setting.")
    
    if 'jupiter' in planets:
        interpretations.append(f"Jupiter's presence in {house_meaning} brings wisdom and expansion to these life areas.")
        interpretations.append("Use this positive influence to guide others and engage in meaningful learning.")
    
    if 'saturn' in planets:
        interpretations.append(f"Saturn's influence in {house_meaning} requires patience and disciplined effort.")
        interpretations.append("Develop consistent habits and maintain long-term perspective in these areas.")
    
    if 'rahu' in planets or 'north_node' in planets:
        interpretations.append(f"Rahu influence in {house_meaning} indicates areas of spiritual growth and learning.")
        interpretations.append("Focus on developing new skills and overcoming past limitations in these areas.")
    
    if 'ketu' in planets or 'south_node' in planets:
        interpretations.append(f"Ketu influence in {house_meaning} suggests natural talents that need conscious direction.")
        interpretations.append("Balance intuitive abilities with practical application and avoid over-attachment.")
    
    # If no specific interpretations, provide general guidance
    if not interpretations:
        interpretations = [
            f"{planet_names} conjunction in {house_meaning} creates combined planetary energies.",
            "Focus on integrating these influences through conscious effort and balanced development.",
            "Practice mindfulness and seek guidance to make the most of these planetary combinations."
        ]
    
    return {
        'key': key,
        'planets': planets,
        'house': house,
        'text': interpretations,
        'canceled': False,
        'source': 'enhanced_generic'
    }

def json_sanitize(obj):
    """Clean and sanitize JSON output."""
    try:
        from ftfy import fix_text
        if isinstance(obj, str):
            return fix_text(obj)
    except ImportError:
        pass
    
    if isinstance(obj, str):
        return obj
    if isinstance(obj, list):
        return [json_sanitize(i) for i in obj]
    if isinstance(obj, dict):
        return {k: json_sanitize(v) for k, v in obj.items()}
    return obj

def get_ascendant_element(disp: Dict[str, Any]) -> Dict[str, Any]:
    """Get ascendant element information with proper mapping."""
    asc_sign = disp["ascendant"]["sign_name"]
    
    # Get element data from the sign-specific mapping
    element_data = ELEMENTS.get(asc_sign, {})
    
    if isinstance(element_data, dict):
        element = element_data.get("element", "")
        interpretation = element_data.get("interpretation", [])
    else:
        # Fallback for old format
        element = ""
        interpretation = []
    
    return {
        "asc_sign": asc_sign,
        "element": element,
        "interpretation": interpretation
    }

def refine_node_names(report):
    """
    Refine all string content in the report for consistency and formatting
    """
    def process_string(text):
        if not isinstance(text, str):
            return text
            
        # Your string refinements here
        # text = text.replace('_', ' ')  # Replace underscores with spaces
        text = text.replace('North Node', 'Rahu')  # Replace North Node with Rahu
        text = text.replace('South Node', 'Ketu')  # Replace South Node with Ketu
        text = text.replace('north Node', 'rahu')  # Replace North Node with Rahu
        text = text.replace('south Node', 'ketu')  # Replace South Node with Ketu
        text = text.replace('North_node', 'Rahu')  # Replace North Node with Rahu
        text = text.replace('South_node', 'Ketu')  # Replace South Node with Ketu
        text = text.replace('north_node', 'rahu')  # Replace North Node with Rahu
        text = text.replace('south_node', 'ketu')  # Replace South Node with Ketu
        # text = text.title()  # Convert to proper case if needed
        # Add any other string processing rules
        
        return text
    
    def recursive_process(obj):
        if isinstance(obj, str):
            return process_string(obj)
        elif isinstance(obj, list):
            return [recursive_process(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: recursive_process(value) for key, value in obj.items()}
        else:
            return obj
    
    return recursive_process(report)

def refine_strings(report, case_sensitive=True, custom_replacements=None):
    """
    Flexible string processing with user options
    """
    if custom_replacements is None:
        custom_replacements = {
            'south_node': 'ketu',
            'north_node': 'rahu',
            'north Node': 'rahu',
            'south Node': 'ketu',
            'North Node': 'Rahu',
            'South Node': 'Ketu',
            '_': ' '
        }

    def process_string(text):
        if not isinstance(text, str):
            return text
            
        processed = text
        
        # Apply custom replacements
        for old, new in custom_replacements.items():
            if case_sensitive:
                processed = processed.replace(old, new)
            else:
                processed = processed.replace(old.lower(), new)
                processed = processed.replace(old.upper(), new)
                processed = processed.replace(old.title(), new)
        
        return processed
    
    def recursive_process(obj):
        if isinstance(obj, str):
            return process_string(obj)
        elif isinstance(obj, list):
            return [recursive_process(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: recursive_process(value) for key, value in obj.items()}
        else:
            return obj
    
    return recursive_process(report)


# ─── Main Report Function ─────────────────────────────────────────────────────

def generate_report(astrodata: AstroData, house_system: str = 'whole_sign') -> Dict[str, Any]:
    """Generate comprehensive horoscope report with enhanced analysis."""
    
    disp = get_dispositions(astrodata, house_system)
    asc = disp['ascendant']
    
    # Build houses dictionary
    houses = {i: [] for i in range(1, 13)}
    for p, d in disp.items():
        if p == 'ascendant':
            continue
        hn = d.get('house_number')
        if hn:
            houses[hn].append(p)
    
    # Enhanced conjunction analysis
    conj_out = {}
    conjunction_summary = []
    
    for hn, pls in houses.items():
        if len(pls) >= 2:  # Only analyze houses with 2+ planets
            # Get all meaningful combinations
            combos = _analyze_house_conjunctions(pls)
            
            for combo in combos:
                interpretation = _get_conjunction_interpretation(combo, hn)
                conj_out[interpretation['key']] = interpretation
                
                # Add to summary
                planet_names = ", ".join([p.replace('_', ' ').title() for p in combo])
                house_name = f"{hn}th house"
                conjunction_summary.append(f"{planet_names} conjunction in {house_name}")
    
    # Ascendant analysis
    friends = [p for p, d in disp.items() if p != 'ascendant' and 'Friendly Sign' in d.get('status', [])]
    neutrals = [p for p, d in disp.items() if p != 'ascendant' and 'Neutral Sign' in d.get('status', [])]
    enemies = [p for p, d in disp.items() if p != 'ascendant' and 'Enemy Sign' in d.get('status', [])]
    
    asc_section = {
        "sign_name": asc['sign_name'],
        "lord": asc['sign_lord'],
        "friends": friends,
        "neutrals": neutrals,
        "enemies": enemies,
        "sign_text": ASC_INT.get('sign', {}).get(str(asc['sign_number']), []),
        "lord_text": ASC_INT.get('lord', {}).get(asc['sign_lord'], []),
        "friends_text": sum((ASC_INT.get('friends', {}).get(p, []) for p in friends), []),
        "neutrals_text": sum((ASC_INT.get('neutrals', {}).get(p, []) for p in neutrals), []),
        "enemies_text": sum((ASC_INT.get('enemies', {}).get(p, []) for p in enemies), []),
    }
    
    # Interpretation building
    interp: List[str] = []
    
    # Add author's secular perspective
    interp.append(
        "Author's Secular Perspective: This analysis is based on traditional astrological principles "
        "but emphasizes practical behavioral insights and personal development. The author believes "
        "that conscious effort and evidence-based practices create real change, not religious rituals."
    )
    
    # Ascendant interpretation
    f_str = ", ".join(friends) or "none"
    n_str = ", ".join(neutrals) or "none"
    e_str = ", ".join(enemies) or "none"
    
    interp.append(
        f"Ascendant ({asc_section['sign_name']}): Lord is {asc_section['lord']}. "
        f"Friendly planets: {f_str}. Neutral planets: {n_str}. Challenging planets: {e_str}."
    )
    
    # Add ascendant texts
    interp.extend(asc_section['sign_text'])
    interp.extend(asc_section['lord_text'])
    interp.extend(asc_section['friends_text'])
    interp.extend(asc_section['neutrals_text'])
    interp.extend(asc_section['enemies_text'])
    
    # Enhanced conjunction analysis
    if conjunction_summary:
        interp.append("Planetary Conjunction Analysis:")
        # Group similar conjunctions to reduce repetition
        unique_conjunctions = []
        for summary in conjunction_summary:
            if not any(summary in existing for existing in unique_conjunctions):
                unique_conjunctions.append(summary)
        
        for summary in unique_conjunctions[:8]:  # Limit to top 8 to avoid overwhelming
            interp.append(f"• {summary}")
            
        # Add detailed conjunction interpretations
        for key, conj_data in list(conj_out.items())[:3]:  # Limit to top 3 detailed interpretations
            if conj_data['source'] != 'generic':
                interp.extend(conj_data['text'])
    
    # Yogas analysis
    yoga_keys = detect_yogas(astrodata, disp, houses)
    yoga_section: List[str] = []
    
    if yoga_keys:
        names = [YOGAS.get(k, {}).get('name', k) for k in yoga_keys]
        yoga_section.append(f"Beneficial Yogas Detected: {', '.join(names)}.")
        yoga_section.append("These planetary combinations suggest positive potential that can be developed through conscious effort and disciplined practice.")
        
        # Add specific yoga interpretations
        for key in yoga_keys[:3]:  # Limit to top 3
            yoga_info = YOGAS.get(key, {})
            yoga_description = yoga_info.get('description', [])
            if yoga_description:
                yoga_section.extend(yoga_description[:2])  # Limit to 2 lines per yoga
    else:
        yoga_section.append("No major yogas detected in this chart.")
        yoga_section.append("Focus on developing your natural talents through consistent effort and personal growth practices.")
    
    # Arudha Lagna analysis
    lord = asc['sign_lord']
    lord_house = disp[lord]['house_number'] or 1
    ar = (lord_house - 1 + lord_house - 1) % 12 + 1
    if ar == 1:
        ar = 10
    if ar == 7:
        ar = 4
    
    arudha_section = {
        'house': ar,
        'planets': houses.get(ar, []),
        'interpretation': ARUDHA_DATA.get('houses', {}).get(str(ar), [
            "This represents your public image and how others perceive you.",
            "Focus on aligning your public persona with your authentic self."
        ])
    }
    
    # Enhanced element analysis
    element_section = get_ascendant_element(disp)
    
    if element_section['element']:
        interp.append(f"Your Ascendant element is {element_section['element']}, which influences your basic approach to life.")
        
        if element_section['interpretation']:
            interp.extend(element_section['interpretation'])
    else:
        interp.append("Element analysis: Focus on developing balance through diverse activities and experiences.")
    
    # Practical guidance based on chart analysis
    practical_tips = []
    
    if friends:
        practical_tips.append(f"Strengthen relationships with {', '.join(friends)} influences through corresponding activities.")
    
    if conjunction_summary:
        practical_tips.append("The multiple planetary conjunctions in your chart suggest focused energy that benefits from structured channeling.")
    
    if len(houses[9]) >= 2:  # Multiple planets in 9th house
        practical_tips.append("Strong 9th house emphasis suggests teaching, learning, or sharing wisdom as beneficial activities.")
    
    if practical_tips:
        interp.append("Practical Guidance:")
        interp.extend([f"• {tip}" for tip in practical_tips])
    
    # Final guidance
    interp.append(
        "Remember: These planetary patterns indicate tendencies and potentials, not fixed destinies. "
        "Your conscious choices, daily habits, emotional intelligence, and commitment to serving others "
        "are the primary factors that shape your actual life experience."
    )
    
    # Enhanced practical guidance
    enhanced_guidance = {
        'daily_practices': [
            "Practice mindfulness meditation for 10-15 minutes daily",
            "Engage in regular physical exercise suited to your energy level",
            "Develop communication skills through active listening",
            "Set clear, achievable goals and track your progress",
            "Practice gratitude and positive thinking"
        ],
        'relationship_advice': [
            "Practice empathy and try to understand others' perspectives",
            "Communicate openly and honestly while respecting boundaries",
            "Show appreciation for others' positive qualities",
            "Work on forgiveness and letting go of grudges",
            "Focus on mutual growth and supportive partnerships"
        ],
        'career_guidance': [
            "Develop your unique talents through consistent practice",
            "Build meaningful professional relationships and networks",
            "Maintain integrity and ethical standards in all dealings",
            "Seek opportunities to serve others and contribute to society",
            "Balance ambition with patience and long-term thinking"
        ],
        'health_and_wellness': [
            "Maintain a balanced diet and regular sleep schedule",
            "Practice stress management through exercise or meditation",
            "Seek preventive healthcare and regular check-ups",
            "Engage in activities that bring you joy and relaxation",
            "Build a support network of friends and family"
        ]
    }
    
    # Compile comprehensive report
    report = {
        'ascendant': asc_section,
        'houses': houses,
        'conjunctions': conj_out,
        'conjunction_summary': conjunction_summary,
        'yogas_found': yoga_keys,
        'yogas': yoga_section,
        'arudha_lagna': arudha_section,
        'interpretation': json_sanitize(interp),
        'ascendant_element': element_section,
        'practical_guidance': enhanced_guidance,
        'chart_summary': {
            'total_planets': len([p for p, d in disp.items() if p != 'ascendant']),
            'houses_occupied': len([h for h, planets in houses.items() if planets]),
            'major_conjunctions': len([k for k, v in conj_out.items() if len(v['planets']) >= 2]),
            'yogas_count': len(yoga_keys),
            'element': element_section['element'],
            'ascendant_lord': asc['sign_lord']
        }
    }
    
    return refine_node_names(report)


# """
# astrokundali/horoscope.py

# Enhanced Secular Horoscope Report Generator with Comprehensive Conjunction Analysis
# """

# import json
# from pathlib import Path
# from itertools import combinations
# from typing import List, Dict, Any, Tuple

# from .astro_data import AstroData
# from .dispositions import get_dispositions, DRISHTI, _anticlockwise_house
# from .yogas_detector import detect_yogas

# # ─── Load Interpretation Data ──────────────────────────────────────────────────

# DATA_DIR = Path(__file__).parent / 'data'

# def _load_json(path: Path) -> dict:
#     """Load JSON and strip any remaining religious content."""
#     data = json.loads(path.read_text(encoding='utf-8'))
#     def strip(obj):
#         if isinstance(obj, str):
#             if any(word in obj.lower() for word in ['remedy:', 'chant', 'mantra', 'puja', 'donate']):
#                 return ''
#             return obj
#         if isinstance(obj, list):
#             return [strip(i) for i in obj if strip(i)]
#         if isinstance(obj, dict):
#             return {k: strip(v) for k, v in obj.items()}
#         return obj
#     return strip(data)

# ASC_INT      = _load_json(DATA_DIR / 'ascendant_interpretations.json')
# CONJ_INT     = _load_json(DATA_DIR / 'conj_interpretations.json')
# GEN_INT      = _load_json(DATA_DIR / 'general_interpretations.json')
# YOGAS        = _load_json(DATA_DIR / 'yogas.json')
# ARUDHA_DATA  = _load_json(DATA_DIR / 'arudha_lagna.json')
# ELEMENTS     = _load_json(DATA_DIR / 'elements.json')
# RASHI_DESCR  = _load_json(DATA_DIR / 'rashi_descriptions.json')
# ASPECTS_INT  = _load_json(DATA_DIR / 'aspects_interpretations.json')

# # ─── Enhanced Conjunction Analysis ──────────────────────────────────────────────

# def _get_conjunction_key(planets: List[str], house: int) -> str:
#     """Generate standardized conjunction key for lookup."""
#     sorted_planets = sorted(planets)
#     return "_".join(sorted_planets + [str(house)])

# def _analyze_house_conjunctions(planets: List[str]) -> List[Tuple[str, ...]]:
#     """Get all meaningful planet combinations (2-3 planets)."""
#     combos = []
#     # Two-planet combinations
#     for combo in combinations(planets, 2):
#         combos.append(combo)
#     # Three-planet combinations
#     if len(planets) >= 3:
#         for combo in combinations(planets, 3):
#             combos.append(combo)
#     return combos

# def _get_conjunction_interpretation(planets: Tuple[str, ...], house: int) -> Dict[str, Any]:
#     """Get interpretation for planet combination in specific house."""
#     key = _get_conjunction_key(list(planets), house)
    
#     # Direct lookup
#     if key in CONJ_INT:
#         return {
#             'key': key,
#             'planets': planets,
#             'house': house,
#             'text': CONJ_INT[key]['text'],
#             'canceled': False,
#             'source': 'direct'
#         }
    
#     # Fallback to generic interpretations
#     planet_effects = []
#     for planet in planets:
#         planet_key = f"{planet}_{house}"
#         if planet_key in CONJ_INT:
#             planet_effects.extend(CONJ_INT[planet_key].get('text', []))
    
#     if planet_effects:
#         return {
#             'key': key,
#             'planets': planets,
#             'house': house,
#             'text': planet_effects,
#             'canceled': False,
#             'source': 'combined'
#         }
    
#     # Generic fallback
#     planet_names = ", ".join(planets).title()
#     house_names = {
#         1: "1st house of self and personality",
#         2: "2nd house of wealth and family",
#         3: "3rd house of communication and siblings",
#         4: "4th house of home and mother",
#         5: "5th house of creativity and children",
#         6: "6th house of health and service",
#         7: "7th house of partnerships and marriage",
#         8: "8th house of transformation and shared resources",
#         9: "9th house of wisdom and higher learning",
#         10: "10th house of career and reputation",
#         11: "11th house of gains and friendships",
#         12: "12th house of spirituality and losses"
#     }
    
#     return {
#         'key': key,
#         'planets': planets,
#         'house': house,
#         'text': [f"{planet_names} conjunction in {house_names.get(house, f'{house}th house')} creates combined energies requiring balance and conscious direction."],
#         'canceled': False,
#         'source': 'generic'
#     }

# def json_sanitize(obj):
#     """Clean and sanitize JSON output."""
#     from ftfy import fix_text
#     if isinstance(obj, str):
#         return fix_text(obj)
#     if isinstance(obj, list):
#         return [json_sanitize(i) for i in obj]
#     if isinstance(obj, dict):
#         return {k: json_sanitize(v) for k, v in obj.items()}
#     return obj

# def get_ascendant_element(disp: Dict[str, Any]) -> Dict[str, Any]:
#     """Get ascendant element information with proper nested structure handling."""
#     asc_sign = disp["ascendant"]["sign_name"]
#     sign_data = ELEMENTS.get(asc_sign, {})
#     element = sign_data.get("element", "Unknown")
#     interpretation = sign_data.get("interpretation", [])
    
#     return {
#         "asc_sign": asc_sign, 
#         "element": element, 
#         "interpretation": interpretation
#     }


# # ─── Main Report Function ─────────────────────────────────────────────────────

# def generate_report(astrodata: AstroData, house_system: str = 'whole_sign') -> Dict[str, Any]:
#     """Generate comprehensive horoscope report with enhanced conjunction analysis."""
    
#     disp = get_dispositions(astrodata, house_system)
#     asc = disp['ascendant']
    
#     # Build houses dictionary
#     houses = {i: [] for i in range(1, 13)}
#     for p, d in disp.items():
#         if p == 'ascendant':
#             continue
#         hn = d.get('house_number')
#         if hn:
#             houses[hn].append(p)
    
#     # Enhanced conjunction analysis
#     conj_out = {}
#     conjunction_summary = []
    
#     for hn, pls in houses.items():
#         if len(pls) >= 2:  # Only analyze houses with 2+ planets
#             # Get all meaningful combinations
#             combos = _analyze_house_conjunctions(pls)
            
#             for combo in combos:
#                 interpretation = _get_conjunction_interpretation(combo, hn)
#                 conj_out[interpretation['key']] = interpretation
                
#                 # Add to summary
#                 planet_names = ", ".join(combo).title()
#                 house_name = f"{hn}th house"
#                 conjunction_summary.append(f"{planet_names} conjunction in {house_name}")
    
#     # Ascendant analysis
#     friends = [p for p, d in disp.items() if p != 'ascendant' and 'Friendly Sign' in d['status']]
#     neutrals = [p for p, d in disp.items() if p != 'ascendant' and 'Neutral Sign' in d['status']]
#     enemies = [p for p, d in disp.items() if p != 'ascendant' and 'Enemy Sign' in d['status']]
    
#     asc_section = {
#         "sign_name": asc['sign_name'],
#         "lord": asc['sign_lord'],
#         "friends": friends,
#         "neutrals": neutrals,
#         "enemies": enemies,
#         "sign_text": ASC_INT.get('sign', {}).get(str(asc['sign_number']), []),
#         "lord_text": ASC_INT.get('lord', {}).get(asc['sign_lord'], []),
#         "friends_text": sum((ASC_INT.get('friends', {}).get(p, []) for p in friends), []),
#         "neutrals_text": sum((ASC_INT.get('neutrals', {}).get(p, []) for p in neutrals), []),
#         "enemies_text": sum((ASC_INT.get('enemies', {}).get(p, []) for p in enemies), []),
#     }
    
#     # Interpretation building
#     interp: List[str] = []
    
#     # Add author's secular perspective
#     interp.append(
#         "Author's Note: This analysis focuses on behavioral and practical insights rather than "
#         "religious remedies. Personal growth comes through conscious effort, not rituals."
#     )
    
#     # Ascendant interpretation
#     f_str = ", ".join(friends) or "none"
#     n_str = ", ".join(neutrals) or "none"
#     e_str = ", ".join(enemies) or "none"
    
#     interp.append(
#         f"Ascendant ({asc_section['sign_name']}): Lord is {asc_section['lord']}. "
#         f"Friends: {f_str}. Neutrals: {n_str}. Enemies: {e_str}."
#     )
    
#     # Add ascendant texts
#     interp.extend(asc_section['sign_text'])
#     interp.extend(asc_section['lord_text'])
#     interp.extend(asc_section['friends_text'])
#     interp.extend(asc_section['neutrals_text'])
#     interp.extend(asc_section['enemies_text'])
    
#     # Conjunction summary
#     if conjunction_summary:
#         interp.append("Planetary Conjunctions Analysis:")
#         interp.extend([f"• {summary}" for summary in conjunction_summary])
    
#     # Yogas analysis
#     yoga_keys = detect_yogas(astrodata, disp, houses)
#     yoga_section: List[str] = []
    
#     if yoga_keys:
#         names = [YOGAS[k]['name'] for k in yoga_keys]
#         yoga_section.append(f"Detected Yogas: {', '.join(names)}.")
#         yoga_section.append("Focus on developing the positive qualities these combinations suggest through conscious effort.")
#     else:
#         yoga_section.append("No major yogas detected. Focus on consistent personal development.")
    
#     # Arudha Lagna (simplified)
#     lord = asc['sign_lord']
#     lord_house = disp[lord]['house_number'] or asc['house_number']
#     ar = (lord_house - 1 + lord_house - 1) % 12 + 1
#     if ar == 1:
#         ar = 10
#     if ar == 7:
#         ar = 4
    
#     arudha_section = {
#         'house': ar,
#         'planets': houses.get(ar, []),
#         'interpretation': ARUDHA_DATA.get('houses', {}).get(str(ar), [])
#     }
    
#     # Element analysis
#     element_section = get_ascendant_element(disp)
#     interp.append(f"Your Ascendant element is {element_section['element']}.")
    
#     if element_section['interpretation']:
#         interp.extend(element_section['interpretation'])
    
#     # Practical tips based on element
#     element_tips = {
#         "Fire": "Channel energy through regular exercise, team sports, and goal-oriented activities.",
#         "Earth": "Ground yourself through nature walks, gardening, and practical skill-building.",
#         "Air": "Stimulate your mind through reading, discussions, and social networking.",
#         "Water": "Nurture emotional health through creative expression and meditation practices."
#     }
    
#     tip = element_tips.get(element_section['element'])
#     if tip:
#         interp.append(f"Practical advice: {tip}")
    
#     # Final guidance
#     interp.append(
#         "Remember: These planetary patterns suggest tendencies, not fixed destiny. "
#         "Your conscious choices, daily habits, and commitment to growth determine your actual life path. "
#         "Focus on developing emotional intelligence, communication skills, and serving others."
#     )
    
#     # Compile report
#     report = {
#         'ascendant': asc_section,
#         'houses': houses,
#         'conjunctions': conj_out,
#         'conjunction_summary': conjunction_summary,
#         'yogas_found': yoga_keys,
#         'yogas': yoga_section,
#         'arudha_lagna': arudha_section,
#         'interpretation': json_sanitize(interp),
#         'ascendant_element': element_section,
#         'practical_guidance': {
#             'daily_practices': [
#                 "Practice mindfulness and emotional regulation",
#                 "Engage in regular physical exercise",
#                 "Develop communication and listening skills",
#                 "Set clear goals and track progress"
#             ],
#             'relationship_advice': [
#                 "Practice empathy and understanding",
#                 "Communicate openly and honestly",
#                 "Respect boundaries and differences",
#                 "Focus on mutual growth and support"
#             ],
#             'career_guidance': [
#                 "Develop your unique talents consistently",
#                 "Build meaningful professional relationships",
#                 "Maintain integrity and ethical standards",
#                 "Seek opportunities to serve others"
#             ]
#         }
#     }
    
#     return report
