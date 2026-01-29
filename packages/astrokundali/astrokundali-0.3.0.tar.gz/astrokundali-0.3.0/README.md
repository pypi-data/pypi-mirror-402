<p align="center">
  <img src="https://github.com/Mirjan-Ali-Sha/astrokundali/blob/main/Icon.png" alt="AstroKundali Icon" width="150" height="150" />
</p>

# AstroKundali
**AstroKundali** is a lightweight and modular Python library for generating Vedic astrology charts using Swiss Ephemeris. It supports traditional North Indian chart plotting, divisional charts (D1 to D60), planetary dispositions, drishti (aspect) logic, advanced calculations like Ashtakavarga, Vimshottari Dasha system, and marriage timing predictions. Designed for flexibility and clarity, it enables both astrologers and developers to compute and visualize personalized Kundalis with precision.

**Request:**
If anyone would like to collaborate or discuss new features, please send me an email. I will get in touch with you.<br>
If you want access to this project's source code, please do the same. I am planning to make this project fully open source in the near future.
<hr>

# Installation
<pre>
pip install astrokundali
  or
!pip install astrokundali  # For Jupyter Notebooks
</pre>

# Quick Start - Package Info
<pre>
from astrokundali import info
info()  # Display comprehensive package documentation
</pre>

---

# USER OPTIONS

## Ayanāṃśa Options

- **`fagan_bradley`** - Fagan–Bradley Ayanāṃśa: Western sidereal offset fixed at 24°02′31″ (January 1 1950)
- **`lahiri`** *(default)* - Lahiri (Chitra‑Paksha/Rohini) Ayanāṃśa: India's official Vedic ayanāṃśa
- **`deluce`** - de Luce Ayanāṃśa: proposed by Robert DeLuce (1877–1964)
- **`raman`** - Raman Ayanāṃśa: introduced by B. V. Raman
- **`krishnamurti`** - Krishnamurti (KP) Ayanāṃśa: developed by K. S. Krishnamurti
- **`sassanian`** - Sassanian Ayanāṃśa: reconstructs pre‑Islamic Persian/Sassanian zodiac data
- **`aldebaran`** - Aldebaran Ayanāṃśa: fixes zero at Aldebaran (15° Taurus)
- **`galcenter`** - Galcenter Ayanāṃśa: anchors zodiac at Milky Way's center

## House‑System Options

- **`equal`** - Equal Houses: twelve 30° houses from exact Ascendant degree
- **`whole_sign`** *(default)* - Whole‑Sign: sign containing Ascendant becomes 1st house
- **`porphyry`** - Porphyry: trisects each cardinal quadrant
- **`placidus`** - Placidus: most common Western quadrant system
- **`koch`** - Koch: time‑based quadrant method
- **`campanus`** - Campanus: divides prime vertical into twelve equal segments
- **`regiomontanus`** - Regiomontanus: splits celestial equator into twelve equal arcs

---

# COMPLETE EXAMPLES

## 1. Configure AstroData (Birth Data)
<pre>
from astrokundali import AstroData

# Parameters: year, month, day, hour, minute, second, utc_hours, utc_minutes, latitude, longitude, ayanamsa
data = AstroData(
    1995,        # Year
    9,           # Month  
    29,          # Day
    2,           # Hour (24-hour format)
    29,          # Minute
    0,           # Second
    5,           # UTC offset hours
    30,          # UTC offset minutes
    22.8873808,  # Latitude
    87.7860174,  # Longitude
    ayanamsa='lahiri'  # Optional, default is 'lahiri'
)
</pre>

---

## 2. Chart Plotting Functions

### Basic Charts
<pre>
from astrokundali import AstroData, plot_lagna_chart, plot_moon_chart, plot_navamsa_chart

data = AstroData(1995, 9, 29, 2, 29, 0, 5, 30, 22.88, 87.78)

# Lagna Chart (D1) - Main birth chart
houses = plot_lagna_chart(data, house_system='whole_sign')

# Moon/Chandra Chart - Moon becomes ascendant
houses = plot_moon_chart(data)

# Navamsa Chart (D9) - Marriage & Partnerships
houses = plot_navamsa_chart(data)
</pre>

### Comprehensive Chart (Advanced)
<pre>
from astrokundali import AstroData, plot_comprehensive_chart

data = AstroData(1995, 9, 29, 2, 29, 0, 5, 30, 22.88, 87.78)

# Full chart with degrees, exaltation/debilitation markers, retrograde indicators
houses = plot_comprehensive_chart(data, house_system='whole_sign', plot_signs=True)
</pre>

### All Divisional Charts (D1-D60)
<pre>
from astrokundali import (
    AstroData,
    plot_lagna_chart,           # D1  - Main Birth Chart
    plot_hora_chart,            # D2  - Prosperity & Wealth
    plot_drekkana_chart,        # D3  - Siblings & Well-being
    plot_chaturthamsha_chart,   # D4  - Luck & Residence
    plot_saptamamsha_chart,     # D7  - Children & Progeny
    plot_navamsa_chart,         # D9  - Marriage & Partnerships
    plot_dashamamsha_chart,     # D10 - Profession & Success
    plot_dwadashamsha_chart,    # D12 - Parents & Ancestry
    plot_shodashamsha_chart,    # D16 - Vehicles & Comforts
    plot_vimshamsha_chart,      # D20 - Spiritual Undertakings
    plot_chatuvimshamsha_chart, # D24 - Education & Learning
    plot_saptvimshamsha_chart,  # D27 - Strength & Stamina
    plot_trishamsha_chart,      # D30 - Miseries & Troubles
    plot_khavedamsha_chart,     # D40 - Auspicious/Inauspicious Effects
    plot_akshavedamsha_chart,   # D45 - General Conduct & Life Themes
    plot_shashtiamsha_chart,    # D60 - Karma & Destiny
)

data = AstroData(1995, 9, 29, 2, 29, 0, 5, 30, 22.88, 87.78)

# Example: Plot multiple charts
houses_d1 = plot_lagna_chart(data)
houses_d9 = plot_navamsa_chart(data)
houses_d10 = plot_dashamamsha_chart(data)
</pre>

---

## 3. Read & Format House Objects
<pre>
from astrokundali import AstroData, plot_lagna_chart, format_houses
import json

data = AstroData(1995, 9, 29, 2, 29, 0, 5, 30, 22.88, 87.78)
houses = plot_lagna_chart(data)

# Convert to readable dictionary
readable = format_houses(houses)
print(json.dumps(readable, indent=2))
</pre>

---

## 4. Planetary Dispositions
<pre>
from astrokundali import AstroData, get_dispositions
import json

data = AstroData(1995, 9, 29, 2, 29, 0, 5, 30, 22.88, 87.78)

# Get detailed planetary positions and status
disp = get_dispositions(data, house_system='whole_sign')
print(json.dumps(disp, indent=2, default=str))

# Each planet includes: sign_number, sign_name, sign_lord, amsha_degree,
# speed, retrograde, nakshatra, pada, nakshatra_lord, navamsa_sign,
# navamsa_lord, house_number, exalted, debilitated, status flags
</pre>

---

## 5. Horoscope Report Generation
<pre>
from astrokundali import AstroData, generate_report, json_sanitize
import json

data = AstroData(1995, 9, 29, 2, 29, 0, 5, 30, 22.88, 87.78)

# Generate comprehensive report (requires ftfy: pip install ftfy)
report = json_sanitize(generate_report(data, house_system='whole_sign'))
print(json.dumps(report, ensure_ascii=False, indent=2))
</pre>

---

## 6. Vimshottari Dasha System (NEW in 0.2.9)

### Calculate Dasha Balance at Birth
<pre>
from astrokundali import AstroData, calculate_dasha_balance

data = AstroData(1995, 9, 29, 2, 29, 0, 5, 30, 22.88, 87.78)

balance = calculate_dasha_balance(data)
print(f"Moon Longitude: {balance['moon_longitude']}°")
print(f"Nakshatra: {balance['nakshatra_name']} (#{balance['nakshatra_number']})")
print(f"Nakshatra Lord: {balance['nakshatra_lord'].title()}")
print(f"Remaining Dasha Years: {balance['remaining_dasha_years']:.2f}")
</pre>

### Get Mahadasha Periods
<pre>
from astrokundali import AstroData, get_dasha_periods

data = AstroData(1995, 9, 29, 2, 29, 0, 5, 30, 22.88, 87.78)

# Get Mahadasha timeline (default 100 years ahead)
periods = get_dasha_periods(data, years_ahead=60)

for p in periods[:5]:  # Show first 5 mahadashas
    print(f"{p.planet.upper():10} : {p.start_date.strftime('%Y-%m-%d')} to {p.end_date.strftime('%Y-%m-%d')} ({p.duration_years:.1f} years)")
</pre>

### Get Antardasha (Sub-periods)
<pre>
from astrokundali import AstroData, get_dasha_periods, get_antardasha_periods

data = AstroData(1995, 9, 29, 2, 29, 0, 5, 30, 22.88, 87.78)

mahadashas = get_dasha_periods(data)
first_mahadasha = mahadashas[0]

# Get sub-periods within first mahadasha
antardashas = get_antardasha_periods(first_mahadasha)
for ad in antardashas:
    print(f"  {ad.planet.title():10} : {ad.start_date.strftime('%Y-%m-%d')} to {ad.end_date.strftime('%Y-%m-%d')}")
</pre>

### Get Current Running Dasha
<pre>
from astrokundali import AstroData, get_current_dasha
from datetime import datetime

data = AstroData(1995, 9, 29, 2, 29, 0, 5, 30, 22.88, 87.78)

# Get current running dasha (defaults to today)
current = get_current_dasha(data)
print(f"Mahadasha: {current['mahadasha']['planet'].title()}")
print(f"Antardasha: {current['antardasha']['planet'].title()}")
print(f"Pratyantardasha: {current['pratyantardasha']['planet'].title()}")

# Or check for a specific date
specific_date = datetime(2025, 6, 15)
current = get_current_dasha(data, target_date=specific_date)
</pre>

### Get Full Dasha Timeline
<pre>
from astrokundali import AstroData, get_full_dasha_timeline
import json

data = AstroData(1995, 9, 29, 2, 29, 0, 5, 30, 22.88, 87.78)

# Get complete timeline with all sub-periods
timeline = get_full_dasha_timeline(
    data, 
    years_ahead=30,
    include_antardasha=True,
    include_pratyantardasha=False  # Set True for even more detail
)

# Access the data
for md in timeline['mahadashas'][:2]:
    print(f"Mahadasha: {md['planet'].title()}")
    for ad in md.get('antardashas', [])[:3]:
        print(f"  - Antardasha: {ad['planet'].title()}")
</pre>

---

## 7. Marriage Timing Prediction (NEW in 0.2.9)

### Predict Marriage Years
<pre>
from astrokundali import AstroData, predict_marriage_timing

data = AstroData(1995, 9, 29, 2, 29, 0, 5, 30, 22.88, 87.78)

result = predict_marriage_timing(data, min_age=18, max_age=40)

# Summary
print(result['summary'])

# Top favorable periods
for i, period in enumerate(result['favorable_periods'][:5], 1):
    print(f"\n{i}. {period['start_year']}-{period['end_year']}")
    print(f"   Dasha: {period['mahadasha'].title()}-{period['antardasha'].title()}")
    print(f"   Score: {period['score']} | Confidence: {period['confidence']}")
    print(f"   Factors: {', '.join(period['factors'][:2])}")
</pre>

### Analyze 7th House
<pre>
from astrokundali import AstroData, analyze_7th_house

data = AstroData(1995, 9, 29, 2, 29, 0, 5, 30, 22.88, 87.78)

analysis = analyze_7th_house(data)

print(f"7th House Sign: {analysis['sign_name']}")
print(f"7th House Lord: {analysis['lord'].title()}")
print(f"Lord Position: House {analysis['lord_position']['house']}")
print(f"Planets in 7th: {[p.title() for p in analysis['occupants']]}")
print(f"Aspects on 7th: {[p.title() for p in analysis['aspects']]}")
</pre>

### Get Marriage Significators
<pre>
from astrokundali import AstroData, get_marriage_significators

data = AstroData(1995, 9, 29, 2, 29, 0, 5, 30, 22.88, 87.78)

significators = get_marriage_significators(data)

print("Primary Significators:")
for planet, info in significators['primary'].items():
    print(f"  {planet.title()}: {info['reason']}")

print("\nSecondary Significators:")
for planet, info in significators['secondary'].items():
    print(f"  {planet.title()}: {info['reason']}")
</pre>

### Detect Marriage Yogas
<pre>
from astrokundali import AstroData, get_marriage_yogas

data = AstroData(1995, 9, 29, 2, 29, 0, 5, 30, 22.88, 87.78)

yogas = get_marriage_yogas(data)

for yoga in yogas:
    print(f"Yoga: {yoga['name']}")
    print(f"  Description: {yoga['description']}")
    print(f"  Effect: {yoga['effect']}")
    print()
</pre>

---

## 8. Yogas Detection
<pre>
from astrokundali import AstroData, detect_yogas, get_dispositions, plot_lagna_chart

data = AstroData(1995, 9, 29, 2, 29, 0, 5, 30, 22.88, 87.78)

# Get required data
dispositions = get_dispositions(data)
houses = plot_lagna_chart(data)

# Build houses dict for yoga detection
houses_dict = {i: [] for i in range(1, 13)}
for idx, h in enumerate(houses):
    houses_dict[idx + 1] = list(h.planets.keys())

# Detect yogas
detected_yogas = detect_yogas(data, dispositions, houses_dict)
print("Detected Yogas:", detected_yogas)
</pre>

---

## 9. Birthtime Finder
<pre>
from astrokundali import AstroData, find_birthtime_ranges

data = AstroData(1995, 9, 29, 2, 29, 0, 5, 30, 22.88, 87.78)

# Find ascendant sign ranges for the birth date
ranges = find_birthtime_ranges(data)

# Or with explicit parameters
ranges = find_birthtime_ranges(
    date="1995-09-29",
    latitude=22.88,
    longitude=87.78,
    utc_offset_hours=5,
    utc_offset_minutes=30,
    step_minutes=30,
    ayanamsa='lahiri'
)

import json
print(json.dumps(ranges, indent=2, default=str))
</pre>

---

## 10. Marriage Matching (Kundli Milan)
<pre>
from astrokundali import AstroData, match_kundli
from pprint import pprint

# Create birth data for both persons
boy = AstroData(1990, 1, 1, 10, 0, 0, 5, 30, 19.07, 72.88, ayanamsa='lahiri')
girl = AstroData(1992, 6, 15, 16, 30, 0, 5, 30, 28.61, 77.23, ayanamsa='lahiri')

# Get compatibility analysis
result = match_kundli(boy, girl, house_system='whole_sign')
pprint(result)

# Display summary
print(f"Total Score: {result['total_score']}/36")
print(result['interpretation'])
</pre>

### Format Match Table with Pandas
<pre>
from astrokundali import AstroData, match_kundli
import pandas as pd

boy = AstroData(1990, 1, 1, 10, 0, 0, 5, 30, 19.07, 72.88)
girl = AstroData(1992, 6, 15, 16, 30, 0, 5, 30, 28.61, 77.23)

result = match_kundli(boy, girl)

# Create DataFrame from matching table
df = pd.DataFrame(result['table'])
print(df)
</pre>

---

## 11. House Cusps Calculation
<pre>
from astrokundali import get_house_cusps, HOUSE_SYSTEMS

# List available house systems
print("Available systems:", list(HOUSE_SYSTEMS.keys()))

# Calculate cusps (requires ascendant longitude)
# For most systems, you'll get cusps from AstroChart internally
</pre>

---

# CHANGELOG

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

# License

MIT License - see [LICENSE](LICENSE) for details.

---

# Author

**Mirjan Ali Sha** - mastools.help@gmail.com

For detailed documentation, visit: https://github.com/Mirjan-Ali-Sha/astrokundali