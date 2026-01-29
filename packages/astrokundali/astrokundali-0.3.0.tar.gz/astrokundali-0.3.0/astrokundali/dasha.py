"""
astrokundali/dasha.py

Vimshottari Dasha System Implementation
- Calculates Mahadasha, Antardasha, and Pratyantardasha periods
- Based on Moon's nakshatra position at birth
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from .astro_data import AstroData

# Vimshottari Dasha periods (total 120 years)
DASHA_YEARS = {
    'ketu': 7,
    'venus': 20,
    'sun': 6,
    'moon': 10,
    'mars': 7,
    'rahu': 18,
    'jupiter': 16,
    'saturn': 19,
    'mercury': 17
}

# Dasha sequence (fixed order in Vimshottari)
DASHA_SEQUENCE = ['ketu', 'venus', 'sun', 'moon', 'mars', 'rahu', 'jupiter', 'saturn', 'mercury']

# Nakshatra lords (1-27)
NAKSHATRA_LORDS = {
    1: 'ketu',      # Ashwini
    2: 'venus',     # Bharani
    3: 'sun',       # Krittika
    4: 'moon',      # Rohini
    5: 'mars',      # Mrigashira
    6: 'rahu',      # Ardra
    7: 'jupiter',   # Punarvasu
    8: 'saturn',    # Pushya
    9: 'mercury',   # Ashlesha
    10: 'ketu',     # Magha
    11: 'venus',    # Purva Phalguni
    12: 'sun',      # Uttara Phalguni
    13: 'moon',     # Hasta
    14: 'mars',     # Chitra
    15: 'rahu',     # Swati
    16: 'jupiter',  # Vishakha
    17: 'saturn',   # Anuradha
    18: 'mercury',  # Jyeshtha
    19: 'ketu',     # Mula
    20: 'venus',    # Purva Ashadha
    21: 'sun',      # Uttara Ashadha
    22: 'moon',     # Shravana
    23: 'mars',     # Dhanishta
    24: 'rahu',     # Shatabhisha
    25: 'jupiter',  # Purva Bhadrapada
    26: 'saturn',   # Uttara Bhadrapada
    27: 'mercury'   # Revati
}

# Nakshatra names for reference
NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]


@dataclass
class DashaPeriod:
    """Represents a planetary period (dasha, antardasha, or pratyantardasha)"""
    planet: str
    start_date: datetime
    end_date: datetime
    level: str = 'mahadasha'  # 'mahadasha', 'antardasha', 'pratyantardasha'
    parent: str = None  # Parent dasha planet (for sub-periods)
    
    @property
    def duration_years(self) -> float:
        """Returns duration in years"""
        return (self.end_date - self.start_date).days / 365.25
    
    def contains_date(self, date: datetime) -> bool:
        """Check if a date falls within this period"""
        return self.start_date <= date <= self.end_date
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'planet': self.planet,
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'level': self.level,
            'parent': self.parent,
            'duration_years': round(self.duration_years, 2)
        }


def get_nakshatra_info(moon_longitude: float) -> Tuple[int, str, str, float]:
    """
    Get nakshatra information from Moon's longitude.
    
    Returns:
        Tuple of (nakshatra_number, nakshatra_name, nakshatra_lord, elapsed_fraction)
    """
    # Each nakshatra spans 13°20' = 13.333... degrees
    nakshatra_span = 360 / 27  # 13.333... degrees
    
    # Calculate nakshatra number (1-27)
    nakshatra_num = int(moon_longitude / nakshatra_span) + 1
    if nakshatra_num > 27:
        nakshatra_num = 27
    
    # Calculate how much of the nakshatra is elapsed (0.0 to 1.0)
    position_in_nakshatra = moon_longitude % nakshatra_span
    elapsed_fraction = position_in_nakshatra / nakshatra_span
    
    nakshatra_name = NAKSHATRA_NAMES[nakshatra_num - 1]
    nakshatra_lord = NAKSHATRA_LORDS[nakshatra_num]
    
    return nakshatra_num, nakshatra_name, nakshatra_lord, elapsed_fraction


def calculate_dasha_balance(astrodata: AstroData) -> Dict[str, Any]:
    """
    Calculate the remaining balance of the birth dasha.
    
    The elapsed portion of the nakshatra determines how much of the
    first dasha lord's period has already passed at birth.
    
    Returns:
        Dict with nakshatra info and dasha balance details
    """
    raw = astrodata.get_rashi_data()
    moon_lon = raw['moon']['lon'] % 360
    
    nak_num, nak_name, nak_lord, elapsed_fraction = get_nakshatra_info(moon_lon)
    
    # Remaining fraction of the first dasha
    remaining_fraction = 1.0 - elapsed_fraction
    
    # Calculate remaining years of first dasha
    total_dasha_years = DASHA_YEARS[nak_lord]
    remaining_years = total_dasha_years * remaining_fraction
    
    return {
        'nakshatra_number': nak_num,
        'nakshatra_name': nak_name,
        'nakshatra_lord': nak_lord,
        'elapsed_fraction': round(elapsed_fraction, 4),
        'remaining_fraction': round(remaining_fraction, 4),
        'total_dasha_years': total_dasha_years,
        'remaining_dasha_years': round(remaining_years, 4),
        'moon_longitude': round(moon_lon, 4)
    }


def get_birth_datetime(astrodata: AstroData) -> datetime:
    """
    Extract birth datetime from AstroData.
    Note: We need to reconstruct the date from julian_day or stored params.
    """
    # Use swisseph to convert julian day back to calendar date
    import swisseph as swe
    
    jd = astrodata.julian_day
    # Add back the UTC offset to get local time
    utc_offset_hours = getattr(astrodata, 'utc_offset_hours', 0)
    utc_offset_minutes = getattr(astrodata, 'utc_offset_minutes', 0)
    total_offset = utc_offset_hours + utc_offset_minutes / 60.0
    
    # Convert JD to calendar date (returns UTC)
    year, month, day, hour_decimal = swe.revjul(jd)
    
    # Convert decimal hour to hours, minutes, seconds
    total_seconds = hour_decimal * 3600
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    
    # Create datetime object (this is UTC, we'll add offset)
    dt = datetime(year, month, day, hours, minutes, seconds)
    
    # Add timezone offset to get local time
    dt = dt + timedelta(hours=total_offset)
    
    return dt


def get_dasha_periods(astrodata: AstroData, years_ahead: int = 100) -> List[DashaPeriod]:
    """
    Generate Mahadasha periods from birth.
    
    Args:
        astrodata: Birth data
        years_ahead: How many years of dashas to calculate (default 100)
        
    Returns:
        List of DashaPeriod objects for major dasha periods
    """
    balance = calculate_dasha_balance(astrodata)
    birth_dt = get_birth_datetime(astrodata)
    
    starting_lord = balance['nakshatra_lord']
    remaining_years = balance['remaining_dasha_years']
    
    # Find starting position in dasha sequence
    start_idx = DASHA_SEQUENCE.index(starting_lord)
    
    periods = []
    current_date = birth_dt
    end_limit = birth_dt + timedelta(days=years_ahead * 365.25)
    
    # First dasha (partial)
    first_end = current_date + timedelta(days=remaining_years * 365.25)
    periods.append(DashaPeriod(
        planet=starting_lord,
        start_date=current_date,
        end_date=first_end,
        level='mahadasha'
    ))
    current_date = first_end
    
    # Subsequent full dashas
    idx = (start_idx + 1) % 9
    while current_date < end_limit:
        planet = DASHA_SEQUENCE[idx]
        years = DASHA_YEARS[planet]
        end_date = current_date + timedelta(days=years * 365.25)
        
        periods.append(DashaPeriod(
            planet=planet,
            start_date=current_date,
            end_date=end_date,
            level='mahadasha'
        ))
        
        current_date = end_date
        idx = (idx + 1) % 9
    
    return periods


def get_antardasha_periods(mahadasha: DashaPeriod) -> List[DashaPeriod]:
    """
    Calculate Antardasha (sub-periods) within a Mahadasha.
    
    The antardasha sequence starts with the mahadasha lord itself,
    then follows the standard sequence from there.
    
    Args:
        mahadasha: The parent Mahadasha period
        
    Returns:
        List of DashaPeriod objects for antardasha periods
    """
    total_days = (mahadasha.end_date - mahadasha.start_date).days
    total_years = DASHA_YEARS[mahadasha.planet]
    
    # Start sequence from the mahadasha lord
    start_idx = DASHA_SEQUENCE.index(mahadasha.planet)
    
    periods = []
    current_date = mahadasha.start_date
    
    for i in range(9):
        idx = (start_idx + i) % 9
        planet = DASHA_SEQUENCE[idx]
        
        # Antardasha duration = (Mahadasha years * Antardasha planet years) / 120
        antardasha_years = (total_years * DASHA_YEARS[planet]) / 120.0
        antardasha_days = antardasha_years * 365.25
        
        end_date = current_date + timedelta(days=antardasha_days)
        
        # Don't exceed mahadasha end
        if end_date > mahadasha.end_date:
            end_date = mahadasha.end_date
        
        periods.append(DashaPeriod(
            planet=planet,
            start_date=current_date,
            end_date=end_date,
            level='antardasha',
            parent=mahadasha.planet
        ))
        
        current_date = end_date
        if current_date >= mahadasha.end_date:
            break
    
    return periods


def get_pratyantardasha_periods(antardasha: DashaPeriod) -> List[DashaPeriod]:
    """
    Calculate Pratyantardasha (sub-sub-periods) within an Antardasha.
    
    Args:
        antardasha: The parent Antardasha period
        
    Returns:
        List of DashaPeriod objects for pratyantardasha periods
    """
    total_days = (antardasha.end_date - antardasha.start_date).days
    
    # Get parent mahadasha years for proportion calculation
    parent_years = DASHA_YEARS[antardasha.parent] if antardasha.parent else DASHA_YEARS[antardasha.planet]
    antardasha_years = (parent_years * DASHA_YEARS[antardasha.planet]) / 120.0
    
    # Start sequence from the antardasha lord
    start_idx = DASHA_SEQUENCE.index(antardasha.planet)
    
    periods = []
    current_date = antardasha.start_date
    
    for i in range(9):
        idx = (start_idx + i) % 9
        planet = DASHA_SEQUENCE[idx]
        
        # Pratyantardasha duration proportional within antardasha
        prat_years = (antardasha_years * DASHA_YEARS[planet]) / 120.0
        prat_days = prat_years * 365.25
        
        end_date = current_date + timedelta(days=prat_days)
        
        # Don't exceed antardasha end
        if end_date > antardasha.end_date:
            end_date = antardasha.end_date
        
        periods.append(DashaPeriod(
            planet=planet,
            start_date=current_date,
            end_date=end_date,
            level='pratyantardasha',
            parent=f"{antardasha.parent}-{antardasha.planet}" if antardasha.parent else antardasha.planet
        ))
        
        current_date = end_date
        if current_date >= antardasha.end_date:
            break
    
    return periods


def get_full_dasha_timeline(astrodata: AstroData, years_ahead: int = 100, 
                           include_antardasha: bool = True,
                           include_pratyantardasha: bool = False) -> Dict[str, Any]:
    """
    Generate complete dasha timeline with optional sub-periods.
    
    Args:
        astrodata: Birth data
        years_ahead: Years to calculate ahead
        include_antardasha: Include antardasha sub-periods
        include_pratyantardasha: Include pratyantardasha sub-sub-periods
        
    Returns:
        Dict with balance info and hierarchical timeline
    """
    balance = calculate_dasha_balance(astrodata)
    mahadashas = get_dasha_periods(astrodata, years_ahead)
    
    timeline = []
    for md in mahadashas:
        md_entry = {
            'mahadasha': md.to_dict(),
            'antardashas': []
        }
        
        if include_antardasha:
            antardashas = get_antardasha_periods(md)
            for ad in antardashas:
                ad_entry = {
                    'antardasha': ad.to_dict(),
                    'pratyantardashas': []
                }
                
                if include_pratyantardasha:
                    pratyantardashas = get_pratyantardasha_periods(ad)
                    ad_entry['pratyantardashas'] = [p.to_dict() for p in pratyantardashas]
                
                md_entry['antardashas'].append(ad_entry)
        
        timeline.append(md_entry)
    
    return {
        'birth_nakshatra': balance,
        'timeline': timeline
    }


def get_current_dasha(astrodata: AstroData, target_date: datetime = None) -> Dict[str, Any]:
    """
    Get the current running dasha-antardasha-pratyantardasha for a given date.
    
    Args:
        astrodata: Birth data
        target_date: Date to check (defaults to now)
        
    Returns:
        Dict with current running periods at all levels
    """
    if target_date is None:
        target_date = datetime.now()
    
    mahadashas = get_dasha_periods(astrodata)
    
    current = {
        'target_date': target_date.strftime('%Y-%m-%d'),
        'mahadasha': None,
        'antardasha': None,
        'pratyantardasha': None
    }
    
    for md in mahadashas:
        if md.contains_date(target_date):
            current['mahadasha'] = md.to_dict()
            
            antardashas = get_antardasha_periods(md)
            for ad in antardashas:
                if ad.contains_date(target_date):
                    current['antardasha'] = ad.to_dict()
                    
                    pratyantardashas = get_pratyantardasha_periods(ad)
                    for pd in pratyantardashas:
                        if pd.contains_date(target_date):
                            current['pratyantardasha'] = pd.to_dict()
                            break
                    break
            break
    
    return current
