"""
astrokundali/match.py

Enhanced Ashtakoota (Guna Milan) marriage matching module with dynamic interpretations.
Features:
- Angshik & Purna Manglik dosha classification
- Chandra Manglik Dosha with severity levels
- Dynamic, personalized compatibility interpretations
- House-specific analysis and practical guidance
- Complete 14-animal Yoni compatibility matrix
- Enhanced Graha Maitri scoring
- Advanced dosha cancellation rules
- Weighted compatibility calculation
- Risk assessment with mitigation strategies
"""

import json
import os
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from .astro_data import AstroData
from .dispositions import get_dispositions

# Load constructive remedies from JSON
def load_constructive_remedies():
    """Load constructive remedies from JSON file"""
    try:
        json_path = os.path.join(os.path.dirname(__file__), 'data', 'cons_rem_marriage.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: cons_rem_marriage.json not found. Using default remedies.")
        return {}

CONSTRUCTIVE_REMEDIES = load_constructive_remedies()

# Enhanced mappings with complete data
VARNA_MAP = {1:3, 2:2, 3:1, 4:3, 5:4, 6:2, 7:1, 8:3, 9:4, 10:2, 11:1, 12:4}
VARNA_NAME = {1:'Brahmin', 2:'Kshatriya', 3:'Vaishya', 4:'Shudra'}

VASHA_MAP = {
    1:'Chatushpada', 2:'Manav', 3:'Jalachara', 4:'Jalachara',
    5:'Chatushpada', 6:'Manav', 7:'Manav', 8:'Vanachara',
    9:'Manav', 10:'Chatushpada', 11:'Chatushpada', 12:'Jalachara'
}

# Complete Gana groups mapping
GANA_GROUPS = {
    1:'Deva', 5:'Deva', 7:'Deva', 8:'Deva', 13:'Deva', 15:'Deva', 
    17:'Deva', 22:'Deva', 27:'Deva',
    2:'Manushya', 4:'Manushya', 6:'Manushya', 12:'Manushya', 20:'Manushya', 
    21:'Manushya', 25:'Manushya', 26:'Manushya',
    3:'Rakshasa', 9:'Rakshasa', 10:'Rakshasa', 11:'Rakshasa', 14:'Rakshasa', 
    16:'Rakshasa', 18:'Rakshasa', 19:'Rakshasa', 23:'Rakshasa', 24:'Rakshasa'
}

# Complete 14-animal Yoni mapping
YONI_MAP = {
    1:'Horse', 2:'Elephant', 3:'Sheep', 4:'Snake', 5:'Snake', 6:'Dog',
    7:'Cat', 8:'Sheep', 9:'Cat', 10:'Rat', 11:'Rat', 12:'Cow', 
    13:'Buffalo', 14:'Tiger', 15:'Buffalo', 16:'Tiger', 17:'Deer', 18:'Deer',
    19:'Dog', 20:'Monkey', 21:'Mongoose', 22:'Monkey', 23:'Lion', 24:'Horse',
    25:'Lion', 26:'Cow', 27:'Elephant'
}

# Enhanced Nadi mapping
NADI_MAP = {
    1:'Adi', 6:'Adi', 7:'Adi', 12:'Adi', 13:'Adi', 18:'Adi', 19:'Adi', 24:'Adi', 25:'Adi',
    2:'Madhya', 5:'Madhya', 8:'Madhya', 11:'Madhya', 14:'Madhya', 17:'Madhya', 20:'Madhya', 23:'Madhya', 26:'Madhya',
    3:'Antya', 4:'Antya', 9:'Antya', 10:'Antya', 15:'Antya', 16:'Antya', 21:'Antya', 22:'Antya', 27:'Antya'
}

# Enhanced Koota information
KOOTA_INFO = {
    'Varna': {'max':1, 'desc':'Spiritual Development & Social Compatibility'},
    'Vashya': {'max':2, 'desc':'Mutual Control & Dominance Balance'},
    'Tara': {'max':3, 'desc':'Health, Longevity & Prosperity'},
    'Yoni': {'max':4, 'desc':'Physical & Intimate Compatibility'},
    'Graha Maitri':{'max':5, 'desc':'Mental & Emotional Harmony'},
    'Gana': {'max':6, 'desc':'Temperamental & Behavioral Match'},
    'Bhakoot': {'max':7, 'desc':'Financial & Emotional Stability'},
    'Nadi': {'max':8, 'desc':'Genetic & Health Harmony'}
}

# Planetary friendship matrix
FRIENDSHIP = {
    'sun': {'friends': ['moon','mars','jupiter'], 'enemies': ['venus','saturn'], 'neutral': ['mercury']},
    'moon': {'friends': ['sun','mercury'], 'enemies': [], 'neutral': ['mars','jupiter','venus','saturn']},
    'mars': {'friends': ['sun','moon','jupiter'], 'enemies': ['mercury'], 'neutral': ['venus','saturn']},
    'mercury': {'friends': ['sun','venus'], 'enemies': ['moon','mars'], 'neutral': ['jupiter','saturn']},
    'jupiter': {'friends': ['sun','moon','mars'], 'enemies': ['mercury','venus'], 'neutral': ['saturn']},
    'venus': {'friends': ['mercury','saturn'], 'enemies': ['sun','moon','mars'], 'neutral': ['jupiter']},
    'saturn': {'friends': ['mercury','venus'], 'enemies': ['sun','moon','mars'], 'neutral': ['jupiter']},
    'rahu': {'friends': ['venus','saturn'], 'enemies': ['sun','moon','mars'], 'neutral': ['mercury','jupiter']},
    'ketu': {'friends': ['mars','jupiter'], 'enemies': ['moon','venus'], 'neutral': ['sun','mercury','saturn']}
}

@dataclass
class MatchResult:
    """Data class for match result"""
    koota_name: str
    boy_type: str
    girl_type: str
    obtained: float
    maximum: float
    significance: str

def varna_koota(m1: Dict, m2: Dict) -> float:
    """Calculate Varna Koota (Max: 1)"""
    boy_varna = VARNA_MAP[m1['sign_number']]
    girl_varna = VARNA_MAP[m2['sign_number']]
    
    # Boy's varna should be equal or higher than girl's
    return 1 if boy_varna >= girl_varna else 0

def vashya_koota(m1: Dict, m2: Dict) -> float:
    """Calculate Vashya Koota (Max: 2) with enhanced scoring"""
    vashya_scores = {
        # Same group = 2 points
        ("Chatushpada", "Chatushpada"): 2,
        ("Manav", "Manav"): 2,
        ("Jalachara", "Jalachara"): 2,
        ("Vanachara", "Vanachara"): 2,
        
        # Compatible groups = 1.5 points
        ("Chatushpada", "Manav"): 1.5,
        ("Manav", "Jalachara"): 1.5,
        ("Jalachara", "Vanachara"): 1.5,
        
        # Partially compatible = 1 point
        ("Chatushpada", "Jalachara"): 1,
        ("Chatushpada", "Vanachara"): 1,
        ("Manav", "Vanachara"): 1,
        
        # Incompatible = 0 points
        ("Chatushpada", "Keeta"): 0,
        ("Manav", "Keeta"): 0,
        ("Jalachara", "Keeta"): 0,
        ("Vanachara", "Keeta"): 0
    }
    
    boy_vashya = VASHA_MAP[m1['sign_number']]
    girl_vashya = VASHA_MAP[m2['sign_number']]
    
    return vashya_scores.get((boy_vashya, girl_vashya), 0)

def tara_koota(m1: Dict, m2: Dict) -> float:
    """Calculate Tara Koota (Max: 3) - CORRECTED VERSION"""
    n1, n2 = m1['nakshatra'], m2['nakshatra']
    
    # Calculate remainders
    r1 = (n2 - n1) % 9
    r2 = (n1 - n2) % 9
    
    # Convert 0 to even for logic
    r1 = r1 if r1 else 0
    r2 = r2 if r2 else 0
    
    # Single consolidated scoring (NOT sum of two)
    even_remainders = {0, 2, 4, 6, 8}
    
    if (r1 in even_remainders) and (r2 in even_remainders):
        return 3      # Both even
    elif (r1 in even_remainders) or (r2 in even_remainders):
        return 1.5    # One even, one odd
    else:
        return 0      # Both odd

def yoni_koota(m1: Dict, m2: Dict) -> float:
    """Complete 14-animal Yoni compatibility matrix"""
    yoni_scores = {
        # Same yoni = 4 points
        ("Horse", "Horse"): 4, ("Elephant", "Elephant"): 4, ("Sheep", "Sheep"): 4,
        ("Snake", "Snake"): 4, ("Dog", "Dog"): 4, ("Cat", "Cat"): 4,
        ("Rat", "Rat"): 4, ("Cow", "Cow"): 4, ("Buffalo", "Buffalo"): 4,
        ("Tiger", "Tiger"): 4, ("Deer", "Deer"): 4, ("Monkey", "Monkey"): 4,
        ("Lion", "Lion"): 4, ("Mongoose", "Mongoose"): 4,
        
        # Friendly yonis = 3 points
        ("Horse", "Elephant"): 3, ("Elephant", "Horse"): 3,
        ("Sheep", "Elephant"): 3, ("Elephant", "Sheep"): 3,
        ("Snake", "Cow"): 3, ("Cow", "Snake"): 3,
        ("Dog", "Deer"): 3, ("Deer", "Dog"): 3,
        ("Cat", "Tiger"): 3, ("Tiger", "Cat"): 3,
        ("Rat", "Buffalo"): 3, ("Buffalo", "Rat"): 3,
        ("Monkey", "Lion"): 3, ("Lion", "Monkey"): 3,
        
        # Neutral yonis = 2 points
        ("Horse", "Sheep"): 2, ("Sheep", "Horse"): 2,
        ("Horse", "Dog"): 2, ("Dog", "Horse"): 2,
        ("Elephant", "Buffalo"): 2, ("Buffalo", "Elephant"): 2,
        ("Snake", "Monkey"): 2, ("Monkey", "Snake"): 2,
        ("Cat", "Cow"): 2, ("Cow", "Cat"): 2,
        ("Rat", "Tiger"): 2, ("Tiger", "Rat"): 2,
        ("Deer", "Lion"): 2, ("Lion", "Deer"): 2,
        
        # Unfriendly yonis = 1 point
        ("Horse", "Buffalo"): 1, ("Buffalo", "Horse"): 1,
        ("Elephant", "Tiger"): 1, ("Tiger", "Elephant"): 1,
        ("Sheep", "Dog"): 1, ("Dog", "Sheep"): 1,
        ("Snake", "Deer"): 1, ("Deer", "Snake"): 1,
        ("Cat", "Monkey"): 1, ("Monkey", "Cat"): 1,
        ("Rat", "Lion"): 1, ("Lion", "Rat"): 1,
        
        # Enemy yonis = 0 points
        ("Cat", "Rat"): 0, ("Rat", "Cat"): 0,
        ("Dog", "Cat"): 0, ("Cat", "Dog"): 0,
        ("Mongoose", "Snake"): 0, ("Snake", "Mongoose"): 0,
        ("Tiger", "Cow"): 0, ("Cow", "Tiger"): 0,
        ("Lion", "Elephant"): 0, ("Elephant", "Lion"): 0,
        ("Monkey", "Sheep"): 0, ("Sheep", "Monkey"): 0,
        ("Horse", "Tiger"): 0, ("Tiger", "Horse"): 0,
        ("Buffalo", "Monkey"): 0, ("Monkey", "Buffalo"): 0
    }
    
    boy_yoni = YONI_MAP[m1['nakshatra']]
    girl_yoni = YONI_MAP[m2['nakshatra']]
    
    return yoni_scores.get((boy_yoni, girl_yoni), 2)

def graha_maitri_koota(m1: Dict, m2: Dict) -> float:
    """Enhanced Graha Maitri with complete scoring (0, 0.5, 1, 3, 4, 5)"""
    boy_lord = m1['sign_lord']
    girl_lord = m2['sign_lord']
    
    if boy_lord == girl_lord:
        return 5
    
    boy_relations = FRIENDSHIP.get(boy_lord, {})
    girl_relations = FRIENDSHIP.get(girl_lord, {})
    
    # Check both directions of friendship
    boy_to_girl = 'friends' if girl_lord in boy_relations.get('friends', []) else \
                  'neutral' if girl_lord in boy_relations.get('neutral', []) else \
                  'enemies' if girl_lord in boy_relations.get('enemies', []) else 'neutral'
    
    girl_to_boy = 'friends' if boy_lord in girl_relations.get('friends', []) else \
                  'neutral' if boy_lord in girl_relations.get('neutral', []) else \
                  'enemies' if boy_lord in girl_relations.get('enemies', []) else 'neutral'
    
    # Enhanced scoring based on mutual relationships
    if boy_to_girl == 'friends' and girl_to_boy == 'friends':
        return 4  # Mutual friends
    elif boy_to_girl == 'friends' and girl_to_boy == 'neutral':
        return 3  # One friend, one neutral
    elif boy_to_girl == 'neutral' and girl_to_boy == 'friends':
        return 3  # One neutral, one friend
    elif boy_to_girl == 'neutral' and girl_to_boy == 'neutral':
        return 3  # Both neutral
    elif boy_to_girl == 'friends' and girl_to_boy == 'enemies':
        return 1  # One friend, one enemy
    elif boy_to_girl == 'enemies' and girl_to_boy == 'friends':
        return 1  # One enemy, one friend
    elif boy_to_girl == 'neutral' and girl_to_boy == 'enemies':
        return 0.5  # One neutral, one enemy
    elif boy_to_girl == 'enemies' and girl_to_boy == 'neutral':
        return 0.5  # One enemy, one neutral
    else:  # Both enemies
        return 0

def gana_koota(m1: Dict, m2: Dict) -> float:
    """Calculate Gana Koota (Max: 6)"""
    boy_gana = GANA_GROUPS[m1['nakshatra']]
    girl_gana = GANA_GROUPS[m2['nakshatra']]
    
    if boy_gana == girl_gana:
        return 6
    elif (boy_gana == "Deva" and girl_gana == "Manushya") or \
         (boy_gana == "Manushya" and girl_gana == "Deva"):
        return 5
    elif (boy_gana == "Manushya" and girl_gana == "Rakshasa") or \
         (boy_gana == "Rakshasa" and girl_gana == "Manushya"):
        return 1
    else:  # Deva-Rakshasa
        return 0

def bhakoot_koota(m1: Dict, m2: Dict) -> float:
    """Calculate Bhakoot Koota (Max: 7)"""
    boy_rashi = m1['sign_number']
    girl_rashi = m2['sign_number']
    
    # Calculate bidirectional difference
    diff_boy_to_girl = (girl_rashi - boy_rashi) % 12
    diff_girl_to_boy = (boy_rashi - girl_rashi) % 12
    
    # Convert 0 to 12 for proper calculation
    diff_boy_to_girl = diff_boy_to_girl if diff_boy_to_girl else 12
    diff_girl_to_boy = diff_girl_to_boy if diff_girl_to_boy else 12
    
    # Check for dosha-forming combinations
    dosha_combinations = [
        (2, 12), (12, 2),  # Dwitiya-Dwadash
        (5, 9), (9, 5),    # Panchama-Navama
        (6, 8), (8, 6)     # Shadashtak
    ]
    
    if (diff_boy_to_girl, diff_girl_to_boy) in dosha_combinations:
        return 0
    else:
        return 7

def nadi_koota(m1: Dict, m2: Dict) -> float:
    """Calculate Nadi Koota (Max: 8)"""
    boy_nadi = NADI_MAP[m1['nakshatra']]
    girl_nadi = NADI_MAP[m2['nakshatra']]
    
    if boy_nadi != girl_nadi:
        return 8
    else:
        return 0

def manglik_dosha(data: AstroData) -> str:
    """
    Enhanced Manglik classification
    Returns: 'None', 'Anshik' (partial), or 'Purna' (complete)
    """
    raw = data.get_rashi_data()
    asc = raw['ascendant']['lon'] % 360
    mars = raw['mars']['lon'] % 360
    house = int(((mars - asc) % 360) // 30) + 1
    
    if house in {7, 8}:
        return 'Purna'   # Complete Manglik
    elif house in {1, 2, 4, 12}:
        return 'Anshik'  # Partial Manglik
    else:
        return 'None'    # Non-Manglik

def chandra_manglik_dosha_detailed(data: AstroData) -> Dict[str, Any]:
    """
    Calculate Chandra Manglik Dosha with severity levels
    Returns detailed information about the dosha including severity
    """
    raw = data.get_rashi_data()
    moon_lon = raw['moon']['lon'] % 360
    mars_lon = raw['mars']['lon'] % 360
    
    # Calculate house position from Moon
    house = int(((mars_lon - moon_lon) % 360) // 30) + 1
    
    # Define severity levels
    high_intensity_houses = {7, 8}      # Marriage and transformation houses
    medium_intensity_houses = {1, 4, 5} # Self, home, romance houses  
    low_intensity_houses = {2, 12}      # Family and subconscious houses
    
    if house in high_intensity_houses:
        return {
            'is_chandra_manglik': True,
            'severity': 'High',
            'house': house,
            'description': 'Strong emotional and marital challenges expected'
        }
    elif house in medium_intensity_houses:
        return {
            'is_chandra_manglik': True,
            'severity': 'Medium',
            'house': house,
            'description': 'Moderate emotional compatibility issues'
        }
    elif house in low_intensity_houses:
        return {
            'is_chandra_manglik': True,
            'severity': 'Low',
            'house': house,
            'description': 'Minor emotional adjustments needed'
        }
    else:
        return {
            'is_chandra_manglik': False,
            'severity': 'None',
            'house': house,
            'description': 'No Chandra Manglik Dosha present'
        }

def get_mars_house_position(person_data: Dict) -> int:
    """Get Mars house position for Manglik analysis"""
    # Calculate Mars house position based on dispositions
    # This is a simplified calculation - you may need to adjust based on your data structure
    mars_sign = person_data.get('sign_number', 1)
    return ((mars_sign - 1) % 12) + 1

def get_manglik_house_effects(house: int, gender: str) -> List[str]:
    """Get specific effects of Mars in different houses for Manglik analysis"""
    effects = {
        1: [
            f"Mars in 1st house makes the {gender} physically very strong and assertive",
            f"May lead to dominance issues in relationships",
            f"Temperament can be aggressive and impulsive"
        ],
        2: [
            f"Mars in 2nd house affects family harmony and speech patterns",
            f"May cause financial disagreements due to impulsive spending",
            f"Sharp speech that might hurt partner's feelings"
        ],
        4: [
            f"Mars in 4th house creates domestic unrest and property disputes",
            f"Mother's health may be affected",
            f"Home environment may be tense and argumentative"
        ],
        7: [
            f"Mars in 7th house directly impacts marital happiness",
            f"Partnership conflicts and power struggles are likely",
            f"May cause delays or problems in marriage"
        ],
        8: [
            f"Mars in 8th house brings sudden changes and transformation",
            f"Accidents or health issues are possible",
            f"Intense sexual energy but also relationship turbulence"
        ],
        12: [
            f"Mars in 12th house indicates high sexual energy and desires",
            f"More energetic in bed but may seek multiple partners",
            f"Foreign travel and expenditure on pleasures"
        ]
    }
    
    return effects.get(house, [f"Mars in {house}th house creates moderate energy influences"])

def get_chandra_manglik_effects(house: int, severity: str, gender: str) -> List[str]:
    """Get specific effects of Chandra Manglik based on house and severity"""
    base_effects = {
        1: [f"Self-image conflicts and emotional impulsiveness"],
        2: [f"Family emotional issues and speech-related conflicts"],
        4: [f"Domestic emotional unrest and mother-related concerns"],
        5: [f"Romantic intensity and creative emotional expression"],
        7: [f"Partnership emotional conflicts and marriage challenges"],
        8: [f"Deep emotional transformation and psychological intensity"],
        12: [f"Subconscious emotional conflicts and spiritual seeking"]
    }
    
    effects = base_effects.get(house, [f"Emotional challenges in {house}th house matters"])
    
    if severity == 'High':
        effects.append(f"{severity} intensity - requires careful emotional management")
    elif severity == 'Medium':
        effects.append(f"{severity} impact - manageable with awareness")
    else:
        effects.append(f"{severity} effect - minor emotional adjustments needed")
    
    return effects

def analyze_gana_compatibility(boy_gana: str, girl_gana: str) -> List[str]:
    """Analyze Gana compatibility and provide specific insights"""
    compatibility_matrix = {
        ('Deva', 'Deva'): [
            "Excellent temperamental match - both are spiritually inclined",
            "Mental harmony and similar life approaches",
            "Mutual respect and understanding comes naturally"
        ],
        ('Deva', 'Manushya'): [
            "Good compatibility - spiritual meets practical",
            "Boy's idealistic nature balances Girl's practical approach",
            "Minor adjustments needed in lifestyle preferences"
        ],
        ('Deva', 'Rakshasa'): [
            "Challenging combination - opposite temperaments",
            "Spiritual vs Material conflicts are likely",
            "Significant effort required for mental harmony"
        ],
        ('Manushya', 'Deva'): [
            "Good compatibility - practical meets spiritual",
            "Girl's idealistic nature balances Boy's practical approach",
            "Minor adjustments needed in lifestyle preferences"
        ],
        ('Manushya', 'Manushya'): [
            "Balanced match - similar practical approaches",
            "Good understanding of worldly matters",
            "Harmonious lifestyle and goal alignment"
        ],
        ('Manushya', 'Rakshasa'): [
            "Moderate compatibility - practical meets ambitious",
            "Different priorities may cause occasional conflicts",
            "Compromise needed in decision-making"
        ],
        ('Rakshasa', 'Deva'): [
            "Challenging combination - opposite temperaments",
            "Material vs Spiritual conflicts are likely",
            "Significant effort required for mental harmony"
        ],
        ('Rakshasa', 'Manushya'): [
            "Moderate compatibility - ambitious meets practical",
            "Different priorities may cause occasional conflicts",
            "Compromise needed in decision-making"
        ],
        ('Rakshasa', 'Rakshasa'): [
            "Intense combination - both are highly ambitious",
            "Power struggles and ego clashes possible",
            "Strong physical attraction but mental conflicts likely"
        ]
    }
    
    return compatibility_matrix.get((boy_gana, girl_gana), ["Moderate compatibility expected"])

def analyze_yoni_compatibility(boy_yoni: str, girl_yoni: str) -> List[str]:
    """Analyze Yoni compatibility for physical and intimate harmony"""
    
    # Define animal characteristics
    yoni_traits = {
        'Horse': 'energetic and freedom-loving',
        'Elephant': 'strong and stable',
        'Sheep': 'gentle and mild',
        'Snake': 'mysterious and sensual',
        'Dog': 'loyal and protective',
        'Cat': 'independent and graceful',
        'Rat': 'clever and adaptable',
        'Cow': 'nurturing and patient',
        'Buffalo': 'powerful and determined',
        'Tiger': 'passionate and dominant',
        'Deer': 'gentle and sensitive',
        'Monkey': 'playful and curious',
        'Lion': 'royal and commanding',
        'Mongoose': 'alert and protective'
    }
    
    boy_trait = yoni_traits.get(boy_yoni, 'balanced')
    girl_trait = yoni_traits.get(girl_yoni, 'balanced')
    
    analysis = [f"Boy is {boy_trait} while Girl is {girl_trait}"]
    
    # Same yoni - perfect match
    if boy_yoni == girl_yoni:
        analysis.extend([
            "Perfect physical compatibility - same animal nature",
            "Natural understanding of each other's needs",
            "Excellent intimate harmony and attraction"
        ])
    # Enemy combinations
    elif (boy_yoni == 'Cat' and girl_yoni == 'Rat') or (boy_yoni == 'Rat' and girl_yoni == 'Cat'):
        analysis.extend([
            "Natural enemies - significant physical incompatibility",
            "Attraction-repulsion cycle in intimate moments",
            "Requires major adjustments in physical relationship"
        ])
    elif (boy_yoni == 'Mongoose' and girl_yoni == 'Snake') or (boy_yoni == 'Snake' and girl_yoni == 'Mongoose'):
        analysis.extend([
            "Conflicting natures - predator-prey relationship",
            "Physical tension and misunderstandings likely",
            "Trust issues in intimate relationships"
        ])
    # Friendly combinations
    elif (boy_yoni in ['Horse', 'Elephant'] and girl_yoni in ['Horse', 'Elephant']):
        analysis.extend([
            "Strong physical compatibility - both powerful natures",
            "Good intimate understanding and mutual respect",
            "Balanced energy in physical relationship"
        ])
    else:
        analysis.extend([
            "Moderate physical compatibility with some adjustments needed",
            "Understanding required for different physical needs",
            "Growth possible through patience and communication"
        ])
    
    return analysis

def generate_marriage_recommendation(scores: Dict, major_issues: List, 
                                   compatibility_areas: List) -> List[str]:
    """Generate marriage recommendation with specific suggestions"""
    
    total_score = sum(scores.values())
    max_total = sum(info['max'] for info in KOOTA_INFO.values())
    percentage = (total_score / max_total) * 100
    
    recommendation = []
    
    if percentage >= 70:
        recommendation.append("Marriage Recommendation: HIGHLY FAVORABLE")
        recommendation.append("This combination shows excellent compatibility potential.")
    elif percentage >= 50:
        recommendation.append("Marriage Recommendation: FAVORABLE WITH CARE")
        recommendation.append("This combination can work well with conscious effort and understanding.")
    else:
        recommendation.append("Marriage Recommendation: REQUIRES SIGNIFICANT EFFORT")
        recommendation.append("This combination faces challenges that need serious consideration.")
    
    recommendation.append("")
    
    if major_issues:
        recommendation.append("If you decide to marry, focus on these areas:")
        
        if "Physical and Intimate compatibility" in str(major_issues):
            recommendation.extend([
                "• Physical Compatibility: Regular gym workouts and physical exercise together",
                "• Intimate Understanding: Open communication about physical needs and boundaries",
                "• Fitness Activities: Dancing, sports, or yoga to build physical harmony"
            ])
        
        if "Temperamental conflicts" in str(major_issues):
            recommendation.extend([
                "• Mental Compatibility: Meditation and anger management practices",
                "• Communication Skills: Conflict resolution and active listening training",
                "• Stress Management: Regular relaxation techniques and stress-busting activities"
            ])
        
        if "Financial and Emotional Stability" in str(major_issues):
            recommendation.extend([
                "• Financial Planning: Joint budgeting and financial goal setting",
                "• Emotional Bonding: Regular relationship counseling and emotional sharing",
                "• Trust Building: Transparency in all financial and emotional matters"
            ])
        
        if "Health and Genetic" in str(major_issues):
            recommendation.extend([
                "• Health Management: Regular health check-ups and preventive care",
                "• Lifestyle Harmony: Similar diet, exercise, and wellness routines",
                "• Medical Consultation: Genetic counseling before planning children"
            ])
        
        if "Different Manglik status" in str(major_issues):
            recommendation.extend([
                "• Energy Balance: Regular physical exercise to channel Mars energy",
                "• Patience Practice: Anger management and emotional regulation techniques",
                "• Conflict Resolution: Professional guidance for handling disagreements"
            ])
    
    recommendation.append("")
    recommendation.append("Remember: Compatibility scores indicate tendencies, not certainties. Your commitment, communication, and mutual effort determine the actual success of your relationship.")
    
    return recommendation

def generate_dynamic_interpretation(boy_data: Dict, girl_data: Dict, 
                                  boy_manglik: Dict, girl_manglik: Dict,
                                  ch_mang_a: Dict, ch_mang_b: Dict,
                                  scores: Dict, faults: List) -> str:
    """
    Generate dynamic, personalized compatibility interpretation based on individual characteristics.
    """
    interpretation = []
    
    # Manglik Analysis
    boy_manglik_type = boy_manglik['type']
    girl_manglik_type = girl_manglik['type']
    
    manglik_analysis = []
    
    if boy_manglik_type != 'None':
        if boy_manglik_type == 'Anshik':
            manglik_analysis.append(f"The Boy is Anshik Manglik, indicating moderate Mars influence.")
        else:
            manglik_analysis.append(f"The Boy is Purna Manglik, indicating strong Mars influence.")
            
        # Get Mars house position for specific effects
        boy_mars_house = get_mars_house_position(boy_data)
        manglik_effects = get_manglik_house_effects(boy_mars_house, 'boy')
        manglik_analysis.extend(manglik_effects)
    else:
        manglik_analysis.append("The Boy is not Manglik, indicating balanced Mars energy.")
    
    if girl_manglik_type != 'None':
        if girl_manglik_type == 'Anshik':
            manglik_analysis.append(f"The Girl is Anshik Manglik, indicating moderate Mars influence.")
        else:
            manglik_analysis.append(f"The Girl is Purna Manglik, indicating strong Mars influence.")
            
        # Get Mars house position for specific effects
        girl_mars_house = get_mars_house_position(girl_data)
        manglik_effects = get_manglik_house_effects(girl_mars_house, 'girl')
        manglik_analysis.extend(manglik_effects)
    else:
        manglik_analysis.append("The Girl is not Manglik, indicating balanced Mars energy.")
    
    # Chandra Manglik Analysis
    chandra_analysis = []
    
    if ch_mang_a['is_chandra_manglik']:
        severity = ch_mang_a['severity']
        house = ch_mang_a['house']
        chandra_analysis.append(f"The Boy has {severity} Chandra Manglik (Mars in {house}th house from Moon).")
        chandra_effects = get_chandra_manglik_effects(house, severity, 'boy')
        chandra_analysis.extend(chandra_effects)
    else:
        chandra_analysis.append("The Boy is not Chandra Manglik, indicating emotional balance.")
    
    if ch_mang_b['is_chandra_manglik']:
        severity = ch_mang_b['severity']
        house = ch_mang_b['house']
        chandra_analysis.append(f"The Girl has {severity} Chandra Manglik (Mars in {house}th house from Moon).")
        chandra_effects = get_chandra_manglik_effects(house, severity, 'girl')
        chandra_analysis.extend(chandra_effects)
    else:
        chandra_analysis.append("The Girl is not Chandra Manglik, indicating emotional balance.")
    
    # Gana Compatibility Analysis
    boy_gana = GANA_GROUPS[boy_data['nakshatra']]
    girl_gana = GANA_GROUPS[girl_data['nakshatra']]
    
    gana_analysis = []
    gana_analysis.append(f"The Boy belongs to {boy_gana} Gana and the Girl belongs to {girl_gana} Gana.")
    
    gana_compatibility = analyze_gana_compatibility(boy_gana, girl_gana)
    gana_analysis.extend(gana_compatibility)
    
    # Yoni Compatibility Analysis
    boy_yoni = YONI_MAP[boy_data['nakshatra']]
    girl_yoni = YONI_MAP[girl_data['nakshatra']]
    
    yoni_analysis = []
    yoni_analysis.append(f"The Boy's Yoni is {boy_yoni} and the Girl's Yoni is {girl_yoni}.")
    
    yoni_compatibility = analyze_yoni_compatibility(boy_yoni, girl_yoni)
    yoni_analysis.extend(yoni_compatibility)
    
    # Overall Compatibility Assessment
    overall_analysis = []
    
    # Analyze major compatibility issues
    major_issues = []
    compatibility_areas = []
    
    if scores.get('Nadi', 0) == 0:
        major_issues.append("Health and Genetic Compatibility concerns due to same Nadi")
    
    if scores.get('Bhakoot', 0) == 0:
        major_issues.append("Financial and Emotional Stability challenges")
    
    if scores.get('Gana', 0) <= 1:
        major_issues.append("Temperamental conflicts due to different Gana types")
    
    if scores.get('Yoni', 0) <= 1:
        major_issues.append("Physical and Intimate compatibility concerns")
    
    if boy_manglik['is_manglik'] != girl_manglik['is_manglik']:
        major_issues.append("Different Manglik status creating energy imbalance")
    
    # Positive compatibility areas
    if scores.get('Varna', 0) >= 1:
        compatibility_areas.append("Spiritual and Social compatibility is favorable")
    
    if scores.get('Tara', 0) >= 2:
        compatibility_areas.append("Health and Longevity prospects are good")
    
    if scores.get('Graha Maitri', 0) >= 3:
        compatibility_areas.append("Mental and Emotional harmony is present")
    
    # Compile final interpretation
    interpretation.extend(manglik_analysis)
    interpretation.append("")
    interpretation.extend(chandra_analysis)
    interpretation.append("")
    interpretation.extend(gana_analysis)
    interpretation.append("")
    interpretation.extend(yoni_analysis)
    interpretation.append("")
    
    if compatibility_areas:
        interpretation.append("Positive Compatibility Areas:")
        interpretation.extend([f"• {area}" for area in compatibility_areas])
        interpretation.append("")
    
    if major_issues:
        interpretation.append("Areas Requiring Attention:")
        interpretation.extend([f"• {issue}" for issue in major_issues])
        interpretation.append("")
    
    # Marriage Recommendation
    recommendation = generate_marriage_recommendation(scores, major_issues, compatibility_areas)
    interpretation.extend(recommendation)
    
    return "\n".join(interpretation)

def check_dosha_cancellations(m1: Dict, m2: Dict, faults: List[str], d1: Dict, d2: Dict) -> Dict:
    """Enhanced dosha cancellation with comprehensive rules"""
    canceled_doshas = []
    cancellation_reasons = {}
    
    # Nadi Dosha Cancellation Rules
    if 'Nadi' in faults:
        if m1.get('sign_number') == m2.get('sign_number'):
            canceled_doshas.append('Nadi')
            cancellation_reasons['Nadi'] = 'Same Rashi (Moon Sign) cancels Nadi Dosha'
        elif m1.get('nakshatra') == m2.get('nakshatra'):
            canceled_doshas.append('Nadi')
            cancellation_reasons['Nadi'] = 'Same Nakshatra cancels Nadi Dosha'
        elif _are_planets_friends(m1.get('sign_lord', ''), m2.get('sign_lord', '')):
            canceled_doshas.append('Nadi')
            cancellation_reasons['Nadi'] = 'Friendly Moon sign lords cancel Nadi Dosha'
    
    # Bhakoot Dosha Cancellation Rules
    if 'Bhakoot' in faults:
        if m1.get('sign_lord') == m2.get('sign_lord'):
            canceled_doshas.append('Bhakoot')
            cancellation_reasons['Bhakoot'] = 'Same sign lord cancels Bhakoot Dosha'
        elif _are_planets_friends(m1.get('sign_lord', ''), m2.get('sign_lord', '')):
            canceled_doshas.append('Bhakoot')
            cancellation_reasons['Bhakoot'] = 'Friendly sign lords cancel Bhakoot Dosha'
    
    # Gana Dosha Cancellation Rules
    if 'Gana' in faults:
        if m1.get('sign_lord') == m2.get('sign_lord'):
            canceled_doshas.append('Gana')
            cancellation_reasons['Gana'] = 'Same sign lord cancels Gana Dosha'
    
    return {
        'canceled_doshas': canceled_doshas,
        'cancellation_reasons': cancellation_reasons,
        'active_doshas': [d for d in faults if d not in canceled_doshas]
    }

def calculate_compatibility_percentage(scores: Dict) -> Dict:
    """Enhanced weighted compatibility calculation"""
    koota_weights = {
        'Nadi': 0.25,           # Most important - health & progeny
        'Bhakoot': 0.20,        # Financial & emotional stability
        'Gana': 0.15,           # Temperamental compatibility
        'Yoni': 0.12,           # Physical compatibility
        'Graha Maitri': 0.10,   # Mental compatibility
        'Tara': 0.08,           # Health & longevity
        'Vashya': 0.06,         # Mutual control
        'Varna': 0.04           # Spiritual development
    }
    
    weighted_score = 0
    total_weight = 0
    
    for koota, score in scores.items():
        if koota in koota_weights and koota in KOOTA_INFO:
            max_score = KOOTA_INFO[koota]['max']
            normalized_score = score / max_score
            weight = koota_weights[koota]
            weighted_score += normalized_score * weight
            total_weight += weight
    
    compatibility_percentage = (weighted_score / total_weight) * 100 if total_weight > 0 else 0
    
    koota_breakdown = []
    for koota, score in scores.items():
        if koota in koota_weights and koota in KOOTA_INFO:
            max_score = KOOTA_INFO[koota]['max']
            weight = koota_weights[koota]
            contribution = (score / max_score) * weight * 100
            
            koota_breakdown.append({
                'koota': koota,
                'score': score,
                'max': max_score,
                'weight': weight,
                'contribution': round(contribution, 2),
                'status': 'Strong' if score >= max_score * 0.8 else 'Moderate' if score >= max_score * 0.5 else 'Weak'
            })
    
    koota_breakdown.sort(key=lambda x: x['contribution'], reverse=True)
    
    return {
        'weighted_percentage': round(compatibility_percentage, 2),
        'traditional_percentage': round((sum(scores.values()) / sum(info['max'] for info in KOOTA_INFO.values())) * 100, 2),
        'koota_breakdown': koota_breakdown,
        'primary_strengths': [k for k in koota_breakdown if k['status'] == 'Strong'],
        'areas_for_improvement': [k for k in koota_breakdown if k['status'] == 'Weak']
    }

def assess_relationship_risks(scores: Dict, boy_manglik: Dict, girl_manglik: Dict, canceled_doshas: List) -> Dict:
    """Enhanced risk assessment with cancellation consideration"""
    risks = []
    risk_mitigation = []
    
    # Adjust risks based on cancellations
    effective_nadi_score = 8 if 'Nadi' in canceled_doshas else scores.get('Nadi', 0)
    effective_bhakoot_score = 7 if 'Bhakoot' in canceled_doshas else scores.get('Bhakoot', 0)
    effective_manglik_risk = False if 'Manglik' in canceled_doshas else \
                           (boy_manglik.get('is_manglik', False) != girl_manglik.get('is_manglik', False))
    
    # High-priority risks
    if effective_nadi_score == 0:
        risks.append({
            'level': 'HIGH',
            'area': 'Health & Progeny',
            'description': 'Same Nadi indicates potential health compatibility issues',
            'impact': 'May affect health harmony and genetic compatibility'
        })
        risk_mitigation.append('Focus on healthy lifestyle practices and open health communication')
    
    if effective_bhakoot_score == 0:
        risks.append({
            'level': 'HIGH',
            'area': 'Emotional & Financial Stability',
            'description': 'Bhakoot Dosha indicates emotional and financial challenges',
            'impact': 'May cause disagreements and financial stress'
        })
        risk_mitigation.append('Practice financial planning and emotional regulation techniques')
    
    # Medium-priority risks
    if scores.get('Gana', 0) <= 1:
        risks.append({
            'level': 'MEDIUM',
            'area': 'Temperamental Compatibility',
            'description': 'Different temperaments may cause conflicts',
            'impact': 'May lead to misunderstandings and personality clashes'
        })
        risk_mitigation.append('Develop patience and understanding of different perspectives')
    
    if scores.get('Yoni', 0) <= 1:
        risks.append({
            'level': 'MEDIUM',
            'area': 'Physical & Intimate Compatibility',
            'description': 'Low physical compatibility indicators',
            'impact': 'May affect physical intimacy and attraction'
        })
        risk_mitigation.append('Focus on emotional bonding and open communication')
    
    # Manglik-related risks
    if effective_manglik_risk:
        risks.append({
            'level': 'HIGH',
            'area': 'Manglik Dosha',
            'description': 'Different Manglik status may cause relationship challenges',
            'impact': 'May lead to conflicts and misunderstandings'
        })
        risk_mitigation.append('Practice anger management and conflict resolution techniques')
    
    # Calculate overall risk level
    high_risks = [r for r in risks if r['level'] == 'HIGH']
    medium_risks = [r for r in risks if r['level'] == 'MEDIUM']
    
    overall_risk_level = 'HIGH' if len(high_risks) >= 2 else 'MEDIUM' if len(high_risks) >= 1 or len(medium_risks) >= 3 else 'LOW'
    
    return {
        'overall_risk_level': overall_risk_level,
        'total_risks': len(risks),
        'risk_breakdown': {
            'high': len(high_risks),
            'medium': len(medium_risks),
            'low': 0
        },
        'detailed_risks': risks,
        'mitigation_strategies': risk_mitigation,
        'risk_summary': f"Identified {len(risks)} risk areas with {overall_risk_level} overall risk level"
    }

def generate_enhanced_remedies(faults: List, canceled_doshas: List) -> Dict:
    """Generate enhanced practical remedies"""
    remedies = {}
    
    for fault in faults:
        if fault in canceled_doshas:
            continue
            
        fault_remedies = CONSTRUCTIVE_REMEDIES.get(fault, {})
        
        remedies[fault] = {
            'practical_approaches': fault_remedies.get('practical', []),
            'behavioral_changes': fault_remedies.get('behavioral', []),
            'physical_activities': fault_remedies.get('physical_activities', []),
            'guidance': f"Focus on practical behavioral changes and personal development. The most effective approach combines self-awareness with consistent effort to improve communication and understanding."
        }
    
    return remedies

# Helper functions
def _are_planets_friends(planet1: str, planet2: str) -> bool:
    """Check if two planets are friends"""
    if planet1 in FRIENDSHIP and planet2 in FRIENDSHIP[planet1].get('friends', []):
        return True
    return False

def refine_node_names(report: Any) -> Any:
    """Replace any 'north_node'/'south_node' in all strings with 'rahu'/'ketu'."""
    if isinstance(report, dict):
        return {k.replace('north_node','rahu').replace('south_node','ketu'): refine_node_names(v)
                for k,v in report.items()}
    if isinstance(report,list):
        return [refine_node_names(i) for i in report]
    if isinstance(report,tuple):
        return tuple(refine_node_names(list(report)))
    if isinstance(report,str):
        return report.replace('north_node','rahu').replace('south_node','ketu')\
                     .replace('North_Node','Rahu').replace('South_Node','Ketu')
    return report

def match_kundli(a: AstroData, b: AstroData) -> Dict[str, Any]:
    """
    Enhanced matching function with dynamic interpretations
    """
    # Get dispositions and Moon info
    d1 = get_dispositions(a)
    d2 = get_dispositions(b)
    m1, m2 = d1['moon'], d2['moon']
    
    # Compute koota scores
    scores = {
        'Varna': varna_koota(m1, m2),
        'Vashya': vashya_koota(m1, m2),
        'Tara': tara_koota(m1, m2),
        'Yoni': yoni_koota(m1, m2),
        'Graha Maitri': graha_maitri_koota(m1, m2),
        'Gana': gana_koota(m1, m2),
        'Bhakoot': bhakoot_koota(m1, m2),
        'Nadi': nadi_koota(m1, m2)
    }
    
    total = sum(scores.values())
    max_total = sum(info['max'] for info in KOOTA_INFO.values())
    faults = [k for k, v in scores.items() if v == 0]
    
    # Enhanced Manglik checks
    mg_a = manglik_dosha(a)
    mg_b = manglik_dosha(b)
    boy_manglik = {'is_manglik': mg_a != 'None', 'type': mg_a}
    girl_manglik = {'is_manglik': mg_b != 'None', 'type': mg_b}
    
    if mg_a != mg_b:
        faults.append('Manglik')
    
    # Chandra Manglik details
    ch_mang_a = chandra_manglik_dosha_detailed(a)
    ch_mang_b = chandra_manglik_dosha_detailed(b)
    
    # Generate dynamic interpretation
    dynamic_interpretation = generate_dynamic_interpretation(
        m1, m2, boy_manglik, girl_manglik, ch_mang_a, ch_mang_b, scores, faults
    )
    
    # Advanced analysis
    dosha_cancellations = check_dosha_cancellations(m1, m2, faults, d1, d2)
    compatibility_analysis = calculate_compatibility_percentage(scores)
    risk_assessment = assess_relationship_risks(scores, boy_manglik, girl_manglik, 
                                              dosha_cancellations['canceled_doshas'])
    enhanced_remedies = generate_enhanced_remedies(faults, dosha_cancellations['canceled_doshas'])
    
    # Build enhanced table
    table = []
    for k, pts in scores.items():
        info = KOOTA_INFO[k]
        
        # Determine boy/girl types
        if k == 'Varna':
            boy_type = VARNA_NAME[VARNA_MAP[m1['sign_number']]]
            girl_type = VARNA_NAME[VARNA_MAP[m2['sign_number']]]
        elif k == 'Vashya':
            boy_type = VASHA_MAP[m1['sign_number']]
            girl_type = VASHA_MAP[m2['sign_number']]
        elif k == 'Tara':
            boy_type = f"Nakshatra {m1['nakshatra']}"
            girl_type = f"Nakshatra {m2['nakshatra']}"
        elif k == 'Yoni':
            boy_type = YONI_MAP[m1['nakshatra']]
            girl_type = YONI_MAP[m2['nakshatra']]
        elif k == 'Gana':
            boy_type = GANA_GROUPS[m1['nakshatra']]
            girl_type = GANA_GROUPS[m2['nakshatra']]
        elif k == 'Nadi':
            boy_type = NADI_MAP[m1['nakshatra']]
            girl_type = NADI_MAP[m2['nakshatra']]
        else:
            boy_type = girl_type = ''
        
        # Add cancellation indicator
        significance = info['desc']
        if k in dosha_cancellations['canceled_doshas']:
            significance += f" (✓ CANCELED: {dosha_cancellations['cancellation_reasons'][k]})"
        
        table.append({
            'Particular': f"{k} Koota",
            'Boy': boy_type,
            'Girl': girl_type,
            'Max': info['max'],
            'Obtained': pts,
            'Significance': significance
        })
    
    # Add total row
    table.append({
        'Particular': 'Total',
        'Boy': '-', 'Girl': '-',
        'Max': max_total,
        'Obtained': total,
        'Significance': f"Overall Compatibility: {compatibility_analysis['weighted_percentage']:.1f}% (Traditional: {compatibility_analysis['traditional_percentage']:.1f}%)"
    })
    
    report = {
        'table': table,
        'faults': faults,
        'enhanced_remedies': enhanced_remedies,
        'manglik_status': {
            'boy': {'type': mg_a, 'is_manglik': mg_a != 'None'},
            'girl': {'type': mg_b, 'is_manglik': mg_b != 'None'}
        },
        'chandra_manglik': {
            'boy': ch_mang_a, 
            'girl': ch_mang_b
        },
        'dosha_cancellations': dosha_cancellations,
        'compatibility_analysis': compatibility_analysis,
        'risk_assessment': risk_assessment,
        'interpretation': dynamic_interpretation,  # NEW KEY ADDED
        'summary': {
            'total_score': total,
            'max_score': max_total,
            'traditional_percentage': compatibility_analysis['traditional_percentage'],
            'weighted_percentage': compatibility_analysis['weighted_percentage'],
            'overall_compatibility': 'Excellent' if compatibility_analysis['weighted_percentage'] >= 80 else 'Good' if compatibility_analysis['weighted_percentage'] >= 60 else 'Fair' if compatibility_analysis['weighted_percentage'] >= 40 else 'Poor',
            'risk_level': risk_assessment['overall_risk_level'],
            'active_doshas': dosha_cancellations['active_doshas'],
            'canceled_doshas': dosha_cancellations['canceled_doshas'],
            'cancellation_impact': f"{len(dosha_cancellations['canceled_doshas'])} doshas canceled"
        }
    }
    
    return refine_node_names(report)

# Example usage
if __name__ == '__main__':
    boy = AstroData(1993,6,8,7,45,0,5,30,25.7806522,84.6681699,ayanamsa='lahiri')
    girl = AstroData(1994,10,22,4,43,0,5,30,25.6081691,85.06047,ayanamsa='lahiri')
    from pprint import pprint
    pprint(match_kundli(boy, girl))
