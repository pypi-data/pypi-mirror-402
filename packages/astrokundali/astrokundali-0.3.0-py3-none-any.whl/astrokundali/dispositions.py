import swisseph as swe
from .astro_data import PLANETS, AstroData
from .astro_chart import AstroChart

# ─── Constants ────────────────────────────────────────────────────────────────

# Drishti (full‐house aspects)
DRISHTI = {
    'sun': [7], 'moon': [7], 'mercury': [7], 'venus': [7],
    'mars': [4, 7, 8], 'jupiter': [5, 7, 9], 'saturn': [3, 7, 10],
    'rahu': [7], 'ketu': [7]
}

def _anticlockwise_house(start: int, steps: int) -> int:
    """Count 'steps' houses anticlockwise from 'start' (1–12), inclusive."""
    return ((start - (steps - 1) - 1) % 12) + 1

# Zodiac sign names
RASHI_NAMES = [
    "Aries","Taurus","Gemini","Cancer",
    "Leo","Virgo","Libra","Scorpio",
    "Sagittarius","Capricorn","Aquarius","Pisces"
]

# Lords of each sign
SIGN_LORDS = {
    1:'mars', 2:'venus', 3:'mercury', 4:'moon',
    5:'sun', 6:'mercury', 7:'venus', 8:'mars',
    9:'jupiter',10:'saturn',11:'saturn',12:'jupiter'
}

# Nakshatra lords (repeated)
NAKSHATRA_LORDS = [
    'ketu','venus','sun','moon','mars','rahu','jupiter','saturn','mercury'
] * 3

# Exaltation and Debilitation mappings (planet -> sign number)
EXALTATIONS = {
    'sun': 1,      # Aries
    'moon': 2,     # Taurus
    'mars': 10,    # Capricorn
    'mercury': 6,  # Virgo
    'jupiter': 4,  # Cancer
    'venus': 12,   # Pisces
    'saturn': 7    # Libra
}
DEBILITATIONS = {
    'sun': 7,      # Libra
    'moon': 8,     # Scorpio
    'mars': 4,     # Cancer
    'mercury': 12, # Pisces
    'jupiter': 10, # Capricorn
    'venus': 6,    # Virgo
    'saturn': 1    # Aries
}

# Planet relationship for sign status
PLANET_RELATIONSHIPS = {
    'sun':    {'friends':['moon','mars','jupiter'], 'enemies':['venus','saturn'], 'neutrals':['mercury']},
    'moon':   {'friends':['sun','mercury'],        'enemies':[],                 'neutrals':['mars','jupiter','venus','saturn']},
    'mars':   {'friends':['sun','moon','jupiter'], 'enemies':['mercury'],         'neutrals':['venus','saturn']},
    'mercury':{'friends':['sun','venus'],          'enemies':['moon','mars'],     'neutrals':['jupiter','saturn']},
    'jupiter':{'friends':['sun','moon','mars'],    'enemies':['mercury','venus'], 'neutrals':['saturn']},
    'venus':  {'friends':['mercury','saturn'],     'enemies':['sun','moon','mars'],'neutrals':['jupiter']},
    'saturn': {'friends':['mercury','venus'],      'enemies':['sun','moon','mars'],'neutrals':['jupiter']},
    'rahu':   {'friends':['venus','saturn'],       'enemies':['sun','moon','mars'],'neutrals':['mercury','jupiter']},
    'ketu':   {'friends':['mars','jupiter'],       'enemies':['moon','venus'],    'neutrals':['sun','mercury','saturn']}
}

def get_dispositions(astrodata: AstroData, house_system: str = 'whole_sign') -> dict:
    """
    Compute dispositions for each body:
      - sign_number, sign_name, sign_lord
      - amsha_degree, speed, retrograde
      - nakshatra, pada, nakshatra_lord
      - navamsa_sign, navamsa_lord
      - house_number, house_sign
      - status flags: ['Friendly Sign'/'Neutral Sign'/'Enemy Sign', 'Own Nakshatra']
      - exalted (bool), debilitated (bool)
    """
    raw = astrodata.get_rashi_data()
    chart = AstroChart(astrodata, house_system=house_system)
    houses = chart.compute()
    dispositions = {}

    # First pass: basic data
    for name, info in raw.items():
        lon = info['lon'] % 360
        sign_num = int(lon // 30) + 1
        amsha = lon % 30

        # Speed & retrograde
        if name in PLANETS:
            pos, _ = swe.calc_ut(
                astrodata.julian_day, PLANETS[name],
                swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
            )
            speed = pos[3]
            retro = speed < 0
        else:
            speed, retro = None, False

        # Nakshatra & Pada
        nak = int(lon * 27 / 360) + 1
        pada = int((lon % (360/27)) / ((360/27)/4)) + 1
        nak_lord = NAKSHATRA_LORDS[nak - 1]

        # Navamsa & its lord
        nav_sign = int(((lon * 9) % 360) // 30) + 1
        nav_lord = SIGN_LORDS[nav_sign]

        # House assignment
        house_number = None
        house_sign = None
        for idx, house in enumerate(houses, start=1):
            if name in house.planets:
                house_number = idx
                house_sign = house.sign_num
                break

        # Exalted / Debilitated
        exalted = (name in EXALTATIONS and EXALTATIONS[name] == sign_num)
        debilitated = (name in DEBILITATIONS and DEBILITATIONS[name] == sign_num)

        dispositions[name] = {
            'sign_number': sign_num,
            'sign_name': RASHI_NAMES[sign_num - 1],
            'sign_lord': SIGN_LORDS[sign_num],
            'amsha_degree': amsha,
            'speed': speed,
            'retrograde': retro,
            'nakshatra': nak,
            'pada': pada,
            'nakshatra_lord': nak_lord,
            'navamsa_sign': nav_sign,
            'navamsa_lord': nav_lord,
            'house_number': house_number,
            'house_sign': house_sign,
            'exalted': exalted,
            'debilitated': debilitated,
            'status': []
        }

    swe.close()

    # Ascendant's sign lord for relational status
    asc_lord = dispositions['ascendant']['sign_lord']

    # Second pass: status flags
    for name, d in dispositions.items():
        if name == 'ascendant':
            continue

        # Sign relationship to ascendant lord
        rel = PLANET_RELATIONSHIPS.get(asc_lord, {})
        if name in rel.get('friends', []):
            d['status'].append('Friendly Sign')
        elif name in rel.get('enemies', []):
            d['status'].append('Enemy Sign')
        else:
            d['status'].append('Neutral Sign')

        # Own Nakshatra
        if name == d['nakshatra_lord']:
            d['status'].append('Own Nakshatra')

    return dispositions
    
# # ─── Old Code ────────────────────────────────────────────────────────────────
# # This section is commented out to avoid confusion with the new implementation.

# # # astrokundali/dispositions.py
# # import swisseph as swe
# # from .astro_data import PLANETS, AstroData
# # from .astro_chart import AstroChart

# # # Names of the 12 zodiac signs
# # RASHI_NAMES = [
# #     "Aries","Taurus","Gemini","Cancer",
# #     "Leo","Virgo","Libra","Scorpio",
# #     "Sagittarius","Capricorn","Aquarius","Pisces"
# # ]

# # # Lords of each sign
# # SIGN_LORDS = {
# #     1: 'mars',    2: 'venus',   3: 'mercury', 4: 'moon',
# #     5: 'sun',     6: 'mercury', 7: 'venus',   8: 'mars',
# #     9: 'jupiter',10: 'saturn', 11: 'saturn', 12: 'jupiter'
# # }

# # # Nakshatra lords repeating sequence
# # NAKSHATRA_LORDS = [
# #     'ketu','venus','sun','moon','mars','rahu','jupiter','saturn','mercury'
# # ] * 3

# # # Debilitation mapping: planet -> debilitated sign number
# # DEBILITATIONS = {
# #     'sun':     7,
# #     'moon':    4,
# #     'mars':    6,
# #     'mercury': 6,
# #     'jupiter': 8,
# #     'venus':   6,
# #     'saturn':  1
# # }


# # def get_dispositions(
# #     astrodata: AstroData,
# #     house_system: str = 'whole_sign'
# # ) -> dict:
# #     """
# #     Compute dispositions for each body: sign, amsha, speed, s lord,
# #     nakshatra, pada, nakshatra lord, navamsa, navamsa lord,
# #     status flags, and house placement.
# #     """
# #     raw = astrodata.get_rashi_data()
# #     # Build house list for assignment
# #     chart = AstroChart(astrodata, house_system=house_system)
# #     houses = chart.compute()

# #     dispositions = {}
# #     for name, info in raw.items():
# #         lon = info['lon'] % 360
# #         sign_num = int(lon // 30) + 1
# #         amsha = lon % 30

# #         # Speed and retrograde
# #         if name not in PLANETS:
# #             speed = None
# #             retro = False
# #         else:
# #             code = PLANETS[name]
# #             pos, _ = swe.calc_ut(
# #                 astrodata.julian_day,
# #                 code,
# #                 swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
# #             )
# #             speed = pos[3]
# #             retro = speed < 0

# #         # Nakshatra and Pada
# #         nak = int(lon * 27 / 360) + 1
# #         pada = int((lon % (360/27)) / ((360/27)/4)) + 1
# #         nak_lord = NAKSHATRA_LORDS[nak - 1]

# #         # Navamsa sign & lord (9th harmonic)
# #         nav_sign = int(((lon * 9) % 360) // 30) + 1
# #         nav_lord = SIGN_LORDS[nav_sign]

# #         # House assignment
# #         house_number = None
# #         house_sign   = None
# #         for idx, house in enumerate(houses, start=1):
# #             if name in house.planets:
# #                 house_number = idx
# #                 house_sign   = house.sign_num
# #                 break

# #         # Status flags
# #         status = []
# #         if name == nak_lord:
# #             status.append('Own Nakshatra')
# #         if name in DEBILITATIONS and DEBILITATIONS[name] == sign_num:
# #             status.append('Debilitated')

# #         dispositions[name] = {
# #             'sign_number':     sign_num,
# #             'sign_name':       RASHI_NAMES[sign_num-1],
# #             'sign_lord':       SIGN_LORDS[sign_num],
# #             'amsha_degree':    amsha,
# #             'speed':           speed,
# #             'retrograde':      retro,
# #             'nakshatra':       nak,
# #             'pada':            pada,
# #             'nakshatra_lord':  nak_lord,
# #             'navamsa_sign':    nav_sign,
# #             'navamsa_lord':    nav_lord,
# #             'house_number':    house_number,
# #             'house_sign':      house_sign,
# #             'status':          status
# #         }
# #     swe.close()
# #     return dispositions

# # astrokundali/dispositions.py

# import swisseph as swe
# from .astro_data import PLANETS, AstroData
# from .astro_chart import AstroChart

# # ─── Constants ────────────────────────────────────────────────────────────────

# # Drishti (full house aspects) distances, anticlockwise inclusive count:
# # • All planets have the 7th‐house aspect :contentReference[oaicite:0]{index=0}  
# # • Mars has additional 4th & 8th :contentReference[oaicite:1]{index=1}  
# # • Jupiter has additional 5th & 9th :contentReference[oaicite:2]{index=2}  
# # • Saturn has additional 3rd & 10th :contentReference[oaicite:3]{index=3}  
# DRISHTI = {
#     'sun':     [7],
#     'moon':    [7],
#     'mercury': [7],
#     'venus':   [7],
#     'mars':    [4, 7, 8],
#     'jupiter': [5, 7, 9],
#     'saturn':  [3, 7, 10],
#     'rahu':    [7],
#     'ketu':    [7]
# }

# def _anticlockwise_house(start: int, steps: int) -> int:
#     """
#     Count 'steps' houses anticlockwise from 'start' (1–12), inclusive.
#     E.g., start=2, steps=7 → 8 :contentReference[oaicite:4]{index=4}.
#     """
#     return ((start - (steps - 1) - 1) % 12) + 1

# # ─── Existing Mappings ────────────────────────────────────────────────────────

# # Names of the 12 zodiac signs
# RASHI_NAMES = [
#     "Aries","Taurus","Gemini","Cancer",
#     "Leo","Virgo","Libra","Scorpio",
#     "Sagittarius","Capricorn","Aquarius","Pisces"
# ]

# # Lords of each sign
# SIGN_LORDS = {
#     1: 'mars',    2: 'venus',   3: 'mercury', 4: 'moon',
#     5: 'sun',     6: 'mercury', 7: 'venus',   8: 'mars',
#     9: 'jupiter',10: 'saturn', 11: 'saturn', 12: 'jupiter'
# }

# # Nakshatra lords repeating sequence
# NAKSHATRA_LORDS = [
#     'ketu','venus','sun','moon','mars','rahu','jupiter','saturn','mercury'
# ] * 3

# # Debilitation mapping: planet -> debilitated sign number
# DEBILITATIONS = {
#     'sun':     7,
#     'moon':    4,
#     'mars':    6,
#     'mercury': 6,
#     'jupiter': 8,
#     'venus':   6,
#     'saturn':  1
# }

# # Planet‐to‐planet relationships (Brihat Parashara, Vic DiCara, PocketPandit)
# PLANET_RELATIONSHIPS = {
#     'sun':     {'friends':['moon','mars','jupiter'],    'enemies':['venus','saturn','rahu','ketu'], 'neutrals':['mercury']},
#     'moon':    {'friends':['sun','mercury'],            'enemies':['rahu','ketu'],                  'neutrals':['mars','jupiter','venus','saturn']},
#     'mars':    {'friends':['sun','moon','jupiter'],     'enemies':['mercury'],                      'neutrals':['venus','saturn','rahu','ketu']},
#     'mercury': {'friends':['sun','venus'],              'enemies':['moon'],                         'neutrals':['mars','jupiter','saturn','rahu','ketu']},
#     'jupiter': {'friends':['sun','moon','mars'],        'enemies':['mercury','venus'],              'neutrals':['saturn','rahu','ketu']},
#     'venus':   {'friends':['mercury','saturn','rahu'],  'enemies':['sun','moon'],                   'neutrals':['mars','jupiter','ketu']},
#     'saturn':  {'friends':['mercury','venus','rahu'],   'enemies':['sun','moon','mars'],             'neutrals':['jupiter','ketu']},
#     'rahu':    {'friends':['mercury','venus','saturn'], 'enemies':['sun','moon','mars'],             'neutrals':['jupiter','ketu']},
#     'ketu':    {'friends':['mercury','venus','saturn'], 'enemies':['sun','moon','mars'],             'neutrals':['jupiter','rahu']}
# }


# def get_dispositions(
#     astrodata: AstroData,
#     house_system: str = 'whole_sign'
# ) -> dict:
#     """
#     Compute dispositions for each body, including:
#       - sign_number, sign_name, sign_lord
#       - amsha_degree, speed, retrograde
#       - nakshatra, pada, nakshatra_lord
#       - navamsa_sign, navamsa_lord
#       - house_number, house_sign
#       - status: ['Friendly Sign'/'Neutral Sign'/'Enemy Sign',
#                  'Own Nakshatra', 'Debilitated']
#     """
#     raw = astrodata.get_rashi_data()
#     chart = AstroChart(astrodata, house_system=house_system)
#     houses = chart.compute()

#     # First pass: build basic dispositions
#     dispositions = {}
#     for name, info in raw.items():
#         lon = info['lon'] % 360
#         sign_num = int(lon // 30) + 1
#         amsha = lon % 30

#         # Speed and retrograde
#         if name in PLANETS:
#             flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
#             pos, _ = swe.calc_ut(astrodata.julian_day, PLANETS[name], flags)
#             speed = pos[3]
#             retro = speed < 0
#         else:
#             speed, retro = None, False

#         # Nakshatra and Pada
#         nak = int(lon * 27 / 360) + 1
#         pada = int((lon % (360/27)) / ((360/27)/4)) + 1
#         nak_lord = NAKSHATRA_LORDS[nak - 1]

#         # Navamsa sign & lord (9th harmonic)
#         nav_sign = int(((lon * 9) % 360) // 30) + 1
#         nav_lord = SIGN_LORDS[nav_sign]

#         # House assignment
#         house_number = None
#         house_sign   = None
#         for idx, house in enumerate(houses, start=1):
#             if name in house.planets:
#                 house_number = idx
#                 house_sign   = house.sign_num
#                 break

#         dispositions[name] = {
#             'sign_number':     sign_num,
#             'sign_name':       RASHI_NAMES[sign_num - 1],
#             'sign_lord':       SIGN_LORDS[sign_num],
#             'amsha_degree':    amsha,
#             'speed':           speed,
#             'retrograde':      retro,
#             'nakshatra':       nak,
#             'pada':            pada,
#             'nakshatra_lord':  nak_lord,
#             'navamsa_sign':    nav_sign,
#             'navamsa_lord':    nav_lord,
#             'house_number':    house_number,
#             'house_sign':      house_sign,
#             'status':          []  # populate next
#         }

#     swe.close()

#     # Determine Ascendant's lord for relationship mapping
#     asc_lord = dispositions['ascendant']['sign_lord']

#     # Second pass: add status flags
#     for name, d in dispositions.items():
#         # Skip Ascendant itself
#         if name == 'ascendant':
#             continue

#         # 1) Planet-to-Ascendant-Lord relationship
#         rel = PLANET_RELATIONSHIPS.get(asc_lord, {})
#         if name in rel.get('friends', []):
#             d['status'].append('Friendly Sign')
#         elif name in rel.get('neutrals', []):
#             d['status'].append('Neutral Sign')
#         elif name in rel.get('enemies', []):
#             d['status'].append('Enemy Sign')

#         # 2) Own Nakshatra?
#         if name == d['nakshatra_lord']:
#             d['status'].append('Own Nakshatra')

#         # 3) Debilitated?
#         if name in DEBILITATIONS and DEBILITATIONS[name] == d['sign_number']:
#             d['status'].append('Debilitated')

#     return dispositions
