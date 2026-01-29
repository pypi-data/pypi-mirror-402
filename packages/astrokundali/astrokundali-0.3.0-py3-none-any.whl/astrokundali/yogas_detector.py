"""
astrokundali/yogas_detector.py

Enhanced Yoga Detection System with Comprehensive Rules
Implements traditional yogas with secular, practical interpretations
"""

from typing import Dict, List, Any
import math

def detect_yogas(astrodata, dispositions: Dict, houses: Dict) -> List[str]:
    """
    Enhanced yoga detection with comprehensive traditional rules
    Returns list of detected yoga keys for interpretation lookup
    """
    detected_yogas = []
    
    # Basic planetary data extraction
    planets_data = {}
    for planet, data in dispositions.items():
        if planet != 'ascendant':
            planets_data[planet] = {
                'house': data.get('house_number', 0),
                'rashi': data.get('sign_number', 0),
                'longitude': data.get('longitude', 0),
                'lord': data.get('sign_lord', '')
            }
    
    # Get house lords
    house_lords = _get_house_lords(dispositions)
    
    # Detect each yoga category
    detected_yogas.extend(_detect_raj_yogas(planets_data, house_lords))
    detected_yogas.extend(_detect_dhan_yogas(planets_data, house_lords))
    detected_yogas.extend(_detect_pancha_mahapurush_yogas(planets_data))
    detected_yogas.extend(_detect_neech_bhang_yogas(planets_data, dispositions))
    detected_yogas.extend(_detect_dosha_yogas(planets_data))
    detected_yogas.extend(_detect_kaal_sharpa_dosha(planets_data))
    detected_yogas.extend(_detect_special_yogas(planets_data, house_lords))
    
    return list(set(detected_yogas))  # Remove duplicates

def _get_house_lords(dispositions: Dict) -> Dict[int, str]:
    """Extract house lords from dispositions"""
    house_lords = {}
    asc_lord = dispositions['ascendant']['sign_lord']
    
    # Calculate lords for each house based on ascendant
    sign_lords = {
        1: 'mars', 2: 'venus', 3: 'mercury', 4: 'moon', 5: 'sun', 6: 'mercury',
        7: 'venus', 8: 'mars', 9: 'jupiter', 10: 'saturn', 11: 'saturn', 12: 'jupiter'
    }
    
    asc_sign = dispositions['ascendant']['sign_number']
    for house in range(1, 13):
        lord_sign = ((asc_sign + house - 2) % 12) + 1
        house_lords[house] = sign_lords[lord_sign]
    
    return house_lords

def _detect_raj_yogas(planets_data: Dict, house_lords: Dict) -> List[str]:
    """Detect various Raj Yogas"""
    yogas = []
    
    # Budh Aditya Raj Yoga - Enhanced with degree condition
    sun_data = planets_data.get('sun', {})
    mercury_data = planets_data.get('mercury', {})
    
    if (sun_data.get('house') == mercury_data.get('house') and 
        sun_data.get('house', 0) > 0):
        degree_diff = abs(sun_data.get('longitude', 0) - mercury_data.get('longitude', 0))
        if degree_diff <= 12 or degree_diff >= 348:  # Handle circular degree difference
            yogas.append('budha_aditya_raj_yoga')
    
    # Gaja Kesari Raj Yoga - Enhanced with aspect conditions
    jupiter_data = planets_data.get('jupiter', {})
    moon_data = planets_data.get('moon', {})
    
    if jupiter_data.get('house', 0) > 0 and moon_data.get('house', 0) > 0:
        jup_house = jupiter_data['house']
        moon_house = moon_data['house']
        
        # Same house or kendra (1, 4, 7, 10 steps)
        house_diff = abs(jup_house - moon_house)
        if (jup_house == moon_house or 
            house_diff in [3, 6, 9] or 
            house_diff == 0):
            yogas.append('gaja_kesari_raj_yoga')
    
    # Karmadhipati Raj Yoga - 9th and 10th lords together
    ninth_lord = house_lords.get(9)
    tenth_lord = house_lords.get(10)
    
    if ninth_lord and tenth_lord and ninth_lord != tenth_lord:
        ninth_house = planets_data.get(ninth_lord, {}).get('house', 0)
        tenth_house = planets_data.get(tenth_lord, {}).get('house', 0)
        
        if ninth_house == tenth_house and ninth_house > 0:
            yogas.append('karmadhipati_raj_yoga')
    
    # Privartan Raj Yoga - Exchange of house lords
    for house1 in range(1, 13):
        for house2 in range(house1 + 1, 13):
            lord1 = house_lords.get(house1)
            lord2 = house_lords.get(house2)
            
            if lord1 and lord2 and lord1 != lord2:
                lord1_house = planets_data.get(lord1, {}).get('house', 0)
                lord2_house = planets_data.get(lord2, {}).get('house', 0)
                
                if lord1_house == house2 and lord2_house == house1:
                    yogas.append('privartan_raj_yoga')
                    break
    
    return yogas

def _detect_dhan_yogas(planets_data: Dict, house_lords: Dict) -> List[str]:
    """Detect wealth-related yogas"""
    yogas = []
    
    # Dhan Yoga - 2nd and 11th lords together
    second_lord = house_lords.get(2)
    eleventh_lord = house_lords.get(11)
    
    if second_lord and eleventh_lord and second_lord != eleventh_lord:
        second_house = planets_data.get(second_lord, {}).get('house', 0)
        eleventh_house = planets_data.get(eleventh_lord, {}).get('house', 0)
        
        if second_house == eleventh_house and second_house > 0:
            yogas.append('dhan_yoga')
    
    # Daridra Yoga - 11th or 2nd lord in 6th, 8th, 12th
    for lord_house_num in [2, 11]:
        lord = house_lords.get(lord_house_num)
        if lord:
            lord_position = planets_data.get(lord, {}).get('house', 0)
            if lord_position in [6, 8, 12]:
                yogas.append('daridra_yoga')
                break
    
    return yogas

def _detect_pancha_mahapurush_yogas(planets_data: Dict) -> List[str]:
    """Detect Pancha Mahapurush Yogas"""
    yogas = []
    
    # Ruchak Yoga - Mars in Kendra houses
    mars_data = planets_data.get('mars', {})
    if mars_data.get('house') in [1, 4, 7, 10]:
        yogas.append('ruchak_yoga')
    
    # Bhadra Yoga - Mercury in Kendra or 3rd/6th houses
    mercury_data = planets_data.get('mercury', {})
    if mercury_data.get('house') in [1, 3, 4, 6, 7, 10]:
        yogas.append('bhadra_yoga')
    
    # Malavya Yoga - Venus in Kendra with specific rashis
    venus_data = planets_data.get('venus', {})
    if (venus_data.get('house') in [1, 4, 7, 10] and 
        venus_data.get('rashi') in [2, 7, 12]):
        yogas.append('malavya_yoga')
    
    # Shash Yoga - Saturn in Kendra with specific rashis
    saturn_data = planets_data.get('saturn', {})
    if (saturn_data.get('house') in [1, 4, 7, 10] and 
        saturn_data.get('rashi') in [7, 10, 11]):
        yogas.append('shash_yoga')
    
    # Hansh Yoga - Jupiter in Kendra with specific rashis
    jupiter_data = planets_data.get('jupiter', {})
    if (jupiter_data.get('house') in [1, 4, 7, 10] and 
        jupiter_data.get('rashi') in [4, 9, 12]):
        yogas.append('hansh_yoga')
    
    return yogas

def _detect_neech_bhang_yogas(planets_data: Dict, dispositions: Dict) -> List[str]:
    """Detect Neech Bhang Raj Yogas"""
    yogas = []
    
    # Debilitation chart
    debilitation_chart = {
        'sun': 7, 'saturn': 1, 'moon': 8, 'jupiter': 10,
        'mars': 4, 'mercury': 12, 'venus': 6
    }
    
    for planet, debil_rashi in debilitation_chart.items():
        planet_data = planets_data.get(planet, {})
        if planet_data.get('rashi') == debil_rashi:
            # Check for cancellation conditions
            # 1. Rashi lord in same house or aspecting
            # 2. Exalted planet in house
            # (Simplified implementation)
            yogas.append('neech_bhang_raj_yoga')
            break
    
    return yogas

def _detect_dosha_yogas(planets_data: Dict) -> List[str]:
    """Detect various doshas"""
    yogas = []
    
    # Manglik Dosha
    mars_data = planets_data.get('mars', {})
    mars_house = mars_data.get('house', 0)
    
    # North India - 1, 4, 7, 8, 12
    # South India - also 2nd house
    if mars_house in [1, 2, 4, 7, 8, 12]:
        yogas.append('manglik_dosha')
    
    return yogas

def _detect_kaal_sharpa_dosha(planets_data: Dict) -> List[str]:
    """Detect Kaal Sharpa Dosha variations"""
    yogas = []
    
    rahu_data = planets_data.get('north_node', {})  # Rahu
    ketu_data = planets_data.get('south_node', {})  # Ketu
    
    if not (rahu_data.get('house') and ketu_data.get('house')):
        return yogas
    
    rahu_house = rahu_data['house']
    ketu_house = ketu_data['house']
    
    # Check if all planets are on one side of Rahu-Ketu axis
    main_planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn']
    
    planets_between = 0
    for planet in main_planets:
        planet_house = planets_data.get(planet, {}).get('house', 0)
        if planet_house > 0:
            # Simplified check - between Rahu and Ketu
            if rahu_house < ketu_house:
                if rahu_house < planet_house < ketu_house:
                    planets_between += 1
            else:
                if planet_house > rahu_house or planet_house < ketu_house:
                    planets_between += 1
    
    if planets_between == len(main_planets):
        # Determine specific type based on Rahu position
        kaal_sharpa_types = {
            1: 'anant_kaal_sharpa_dosha',
            2: 'kulik_kaal_sharpa_dosha',
            3: 'vasuki_kaal_sharpa_dosha',
            4: 'shankhpal_kaal_sharpa_dosha',
            5: 'padma_kaal_sharpa_dosha',
            6: 'mahapadma_kaal_sharpa_dosha',
            7: 'takshak_kaal_sharpa_dosha',
            8: 'karkotak_kaal_sharpa_dosha',
            9: 'shankhchud_kaal_sharpa_dosha',
            10: 'chaatak_kaal_sharpa_dosha',
            11: 'vishdhar_kaal_sharpa_dosha',
            12: 'sheshnag_kaal_sharpa_dosha'
        }
        
        specific_type = kaal_sharpa_types.get(rahu_house)
        if specific_type:
            yogas.append(specific_type)
        
        yogas.append('kaal_sharpa_dosha')
    
    return yogas

def _detect_special_yogas(planets_data: Dict, house_lords: Dict) -> List[str]:
    """Detect other special yogas"""
    yogas = []
    
    # Additional yogas can be added here
    # Examples: Amala Yoga, Vimala Yoga, etc.
    
    return yogas
