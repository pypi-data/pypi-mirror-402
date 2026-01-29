# Package metadata
__version__ = "0.3.0"
__author__ = "Mirjan Ali Sha"
__email__ = "mastools.help@gmail.com"

# make imports available at package level
from .astro_data  import AstroData
from .astro_chart import AstroChart
from .plotter     import *
# plot_lagna_chart, plot_moon_chart, plot_hora_chart, plot_navamsa_chart,
# plot_drekkana_chart, plot_chaturthamsha_chart, plot_saptamamsha_chart, plot_navamsha_chart, plot_dashamamsha_chart,
# plot_dwadashamsha_chart, plot_shodashamsha_chart, plot_vimshamsha_chart, plot_shashtiamsha_chart,
# plot_chatuvimshamsha_chart, plot_saptvimshamsha_chart, plot_trishamsha_chart, plot_khavedamsha_chart,
# plot_akshavedamsha_chart, plot_shashtiamsha_chart, format_houses, plot_comprehensive_chart
from .dispositions import get_dispositions
from .houses      import get_house_cusps, HOUSE_SYSTEMS
from .match       import match_kundli
from .horoscope   import generate_report, json_sanitize, get_ascendant_element, refine_strings
from .yogas_detector import detect_yogas
from .birthtime_finder import find_birthtime_ranges
from .birthtime_finder import _ascendant_sign
from .dasha import (
    calculate_dasha_balance,
    get_dasha_periods,
    get_antardasha_periods,
    get_pratyantardasha_periods,
    get_full_dasha_timeline,
    get_current_dasha,
    DashaPeriod,
    NAKSHATRA_NAMES,
    NAKSHATRA_LORDS
)
from .marriage_timing import (
    predict_marriage_timing,
    analyze_7th_house,
    get_marriage_significators,
    get_marriage_yogas
)
# Chart_Name, --> Rashi in correct house --> Planet in correct house
# plot_lagna_chart, --> ✓ --> ✓
# plot_moon_chart,  --> ✓ --> ✓
# plot_hora_chart,  --> X --> X [+2 --> ✓ --> X]
# plot_navamsa_chart, --> ✓ --> ✓
# plot_drekkana_chart, --> X --> X [+6 --> ✓ --> X]
# plot_chaturthamsha_chart, --> ✓ --> X
# plot_saptamamsha_chart, --> ✓ --> ✓ [+4 --> ✓ --> X]
# plot_dashamamsha_chart, --> X --> X
# plot_dwadashamsha_chart, --> X --> X
# plot_shodashamsha_chart, --> ✓ --> ✓
# plot_vimshamsha_chart, --> ✓ --> ✓
# plot_chatuvimshamsha_chart, --> X --> X
# plot_saptvimshamsha_chart, --> X --> X [+1 --> ✓ --> ✓]
# plot_trishamsha_chart, --> X --> X
# plot_khavedamsha_chart, --> X --> X  [+1 --> ✓ --> X]
# plot_akshavedamsha_chart, --> X --> X
# plot_shashtiamsha_chart, --> X --> X
def info():
    """
    Display comprehensive information about AstroKundali package.
    Shows available modules, features, and usage examples.
    """
    
    info_text = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                            🌟 ASTROKUNDALI 🌟                                ║
║                    Comprehensive Vedic Astrology Library                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

📋 PACKAGE OVERVIEW:
AstroKundali is a Python library for Vedic astrology calculations and chart 
generation. It provides secular, practical interpretations focused on behavioral 
insights and personal development rather than religious remedies.

🏗️  CORE MODULES:
┌─────────────────┬────────────────────────────────────────────────────────────┐
│ Module          │ Description                                                │
├─────────────────┼────────────────────────────────────────────────────────────┤
│ AstroData       │ Core astronomical calculations and planetary positions      │
│ AstroChart      │ House systems and chart calculations                       │
│ Plotter         │ Comprehensive chart visualization and plotting             │
│ Dispositions    │ Planetary strength, relationships, and status analysis     │
│ Match           │ Kundli matching with Ashtakoota Guna Milan system         │
│ Horoscope       │ Detailed report generation with practical guidance        │
│ YogasDetector   │ Detection of 300+ classical yogas and combinations        │
│ BirthtimeFinder │ Birth time rectification tools                            │
└─────────────────┴────────────────────────────────────────────────────────────┘

🎯 KEY FEATURES:

📊 Chart Generation:
• Rashi Chart (D1) - Main birth chart with comprehensive planetary details
• Navamsa Chart (D9) - Marriage and spiritual potential
• Multiple Divisional Charts (D2, D3, D4, D7, D10, D12, D16, D20, etc.)
• Interactive plotting with degrees, retrograde markers, and aspect indicators

💑 Marriage Matching:
• Complete Ashtakoota system with 8 compatibility factors
• Manglik Dosha analysis (Anshik/Purna classification)
• Chandra Manglik analysis with severity levels  
• Advanced dosha cancellation rules
• Secular remedies focusing on behavioral improvement

🧘 Horoscope Analysis:
• Comprehensive personality analysis by houses and conjunctions
• Risk assessment and positive potential identification
• Love life, career, finance, and health guidance
• Practical recommendations without religious content

⚖️  AUTHOR'S APPROACH:
This library emphasizes evidence-based, practical guidance over religious 
remedies. All interpretations focus on:
• Behavioral development and communication skills
• Physical activities and exercise recommendations  
• Charitable work and community service
• Personal growth through conscious effort
• Compatible with Islamic beliefs and secular worldviews

🚀 QUICK START EXAMPLES:

# Basic Chart Creation
from astrokundali import AstroData, plot_comprehensive_chart
data = AstroData(1990, 5, 15, 14, 30, 0, 5.5, 19.07, 72.88)
houses = plot_comprehensive_chart(data)

# Marriage Compatibility 
from astrokundali import match_kundli
boy = AstroData(1990, 5, 15, 14, 30, 0, 5.5, 19.07, 72.88)
girl = AstroData(1992, 8, 20, 10, 15, 0, 5.5, 28.61, 77.23)
compatibility = match_kundli(boy, girl)

# Horoscope Report
from astrokundali import generate_report
report = generate_report(data)

# Yoga Detection
from astrokundali import detect_yogas, get_dispositions
dispositions = get_dispositions(data)
houses_dict = {i: [] for i in range(1, 13)}  # Build houses dict
yogas = detect_yogas(data, dispositions, houses_dict)

📈 CHART FEATURES:
• Comprehensive planetary details with degrees
• Exaltation (↑) and Debilitation (↓) markers
• Retrograde (Re) indicators
• Color-coded strength (dark/light based on degrees 10-25°)
• Sign lords and aspect (Drishti) visualization
• Multiple house systems support

💡 PRACTICAL APPLICATIONS:
• Personal self-awareness and growth planning
• Relationship compatibility analysis  
• Career guidance and timing
• Health and wellness insights
• Educational and skill development recommendations

🌟 Remember: Your conscious choices and daily efforts shape your destiny more 
than any planetary configuration. Use these insights as tools for growth! 🌟

For detailed documentation, visit: https://github.com/Mirjan-Ali-Sha/astrokundali
"""
    
    print(info_text)
    
    # Additional dynamic information
    try:
        from . import __version__
        print(f"\n📦 Current Version: {__version__}")
    except:
        print(f"\n📦 Current Version: Development Build")
    
    print(f"🐍 Python Compatibility: 3.7+")
    print(f"📅 Build Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}")
    print(f"👨‍💻 Developed with ❤️  for practical astrology enthusiasts")
    
    print("\n" + "="*80)
    print("💡 Pro Tip: Start with plot_comprehensive_chart() to visualize your birth chart!")
    print("="*80)


# 🔮 Yoga Detection:
# • 300+ classical yogas including (InProgress):
#   - Dhan Yogas (Dhan, Dhanakaraka, Dhanapati)
#   - Pancha Mahapurush Yogas (Ruchaka, Bhadra, Hamsa, Malavya, Sasha)
#   - Raj Yogas (Budha-Aditya, Gaja-Kesari, Karmadhipati)
#   - Dhana Yogas for wealth analysis
#   - All 12 types of Kaal Sharpa Dosha variations
#   - Neech Bhang Raj Yoga cancellations

# 🔧 TECHNICAL SPECIFICATIONS:
# • Swiss Ephemeris integration for precise calculations
# • Multiple Ayanamsa support (Lahiri, Krishnamurthy, etc.)
# • Comprehensive house system options
# • JSON-based interpretation system
# • Matplotlib visualization engine

# 📞 USAGE TIPS:
# • All functions include detailed docstrings
# • Use help(function_name) for specific guidance  
# • Results include both traditional and weighted compatibility percentages
# • Secular remedies focus on actionable behavioral changes
# • Regular updates expand yoga database and interpretations