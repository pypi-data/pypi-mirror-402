# """
# astrokundali/astro_chart.py

# Defines House and AstroChart for building Lagna (D1) and various divisional charts (D2…D60) with Parāśara methods for D2, D3, D4, D7 and harmonic for all others.
# """
# from typing import List, Union
# import swisseph as swe
# from .astro_data import AstroData
# from .houses    import equal_houses, get_house_cusps

# class House:
#     """
#     Represents one of the twelve houses in a Kundali.
#     """
#     def __init__(self, sign_num: int):
#         self.sign_num = sign_num    # Rashi number (1–12)
#         self.is_asc   = False       # True if this house is the Ascendant
#         self.planets  = {}          # dict: planet_name -> longitude

# class AstroChart:
#     """
#     Builds D1 (Lagna) and divisional Vargas (D2…D60) from sidereal data.

#     Implements Parāśara subdivisions for:
#       - D2 (Hora): half sign (0°–15°,15°–30°) with odd/even rule ([laurabaratastrologer.com](https://laurabaratastrologer.com/secrets-of-the-hora-chart/?utm_source=chatgpt.com), [astrologyofbharat.org](https://www.astrologyofbharat.org/2020/08/hora-d2-chart-analysis-for-wealth-and.html?utm_source=chatgpt.com))
#       - D3 (Drekkana): decans of 10° with offsets [0,4,8] ([shubhamalock.wordpress.com](https://shubhamalock.wordpress.com/2015/09/27/vedic-method-of-calculating-divisional-charts/?utm_source=chatgpt.com))
#       - D4 (Chaturthamsa): quarters of 7°30′ with offsets [0,1,2,3] ([jyotishabharati.com](https://jyotishabharati.com/download/chaturthamsa.pdf?utm_source=chatgpt.com))
#       - D7 (Saptamsa): septiles with odd/even sign counting ([jyotishajournal.com](https://www.jyotishajournal.com/pdf/2023/vol8issue2/PartB/8-2-9-327.pdf?utm_source=chatgpt.com))

#     All other Vargas (D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60) use harmonic formula.
#     """
#     def __init__(
#         self,
#         astrodata: AstroData,
#         house_system: str = 'equal'
#     ):
#         self._astrodata   = astrodata
#         self.house_system = house_system.lower()
#         self._raw         = astrodata.get_rashi_data()

#     def compute(self) -> List[House]:
#         """
#         Compute the D1 (Rāśi) chart.
#         """
#         raw      = self._raw
#         asc_lon  = raw['ascendant']['lon']
#         asc_sign = raw['ascendant']['sign_num']

#         # 1) House cusps
#         if self.house_system == 'equal':
#             cusps = equal_houses(asc_lon)
#         elif self.house_system == 'whole_sign':
#             base = (int(asc_lon) // 30) * 30
#             cusps = [(base + 30*i) % 360 for i in range(12)]
#         else:
#             flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
#             _, ascmc = swe.houses_ex(
#                 self._astrodata.julian_day,
#                 self._astrodata.lat,
#                 self._astrodata.lon,
#                 b'B', flags
#             )
#             mc = ascmc[1]
#             cusps = get_house_cusps(
#                 self.house_system,
#                 asc_lon,
#                 JD=self._astrodata.julian_day,
#                 lat=self._astrodata.lat,
#                 lon=self._astrodata.lon,
#                 mc=mc
#             )

#         # 2) Build 12 houses
#         houses: List[House] = []
#         sign_cursor = asc_sign
#         for _ in range(12):
#             h = House(sign_cursor)
#             houses.append(h)
#             sign_cursor = 1 if sign_cursor == 12 else sign_cursor + 1
#         houses[0].is_asc = True

#         # 3) Assign planets
#         for pname, info in raw.items():
#             if pname == 'ascendant': continue
#             lon = info['lon']
#             for idx in range(12):
#                 start = cusps[idx]
#                 end   = cusps[(idx+1) % 12]
#                 in_house = (start <= lon < end) if end > start else (lon >= start or lon < start)
#                 if in_house:
#                     houses[idx].planets[pname] = lon
#                     break
#         return houses

#     def divisional(
#         self,
#         nth: int,
#         house_system: Union[str, None] = None
#     ) -> List[House]:
#         """
#         Build D-n Vargas:
#         - n=2,3,4,7 follow Parāśara; others harmonic.
#         - Optionally override house_system for this chart.
#         """
#         base_raw = self._astrodata.get_rashi_data()
#         raw_mod  = {}
#         for key, info in base_raw.items():
#             if key == 'ascendant':
#                 raw_mod[key] = info
#                 continue
#             orig_lon = info['lon'] % 360
#             rashi    = info['sign_num'] - 1  # zero-based

#             # D2 Hora
#             if nth == 2:
#                 part = int((orig_lon % 30) // 15)
#                 if (rashi+1) %2 ==1:
#                     # odd sign: 0->same,1->opposite
#                     new_r = (rashi + 6*part) %12
#                 else:
#                     # even sign: 0->opposite,1->same
#                     new_r = (rashi + 6*(1-part))%12
#                 new_lon = new_r*30 + (orig_lon%30)  # ([laurabaratastrologer.com](https://laurabaratastrologer.com/secrets-of-the-hora-chart/?utm_source=chatgpt.com), [astrologyofbharat.org](https://www.astrologyofbharat.org/2020/08/hora-d2-chart-analysis-for-wealth-and.html?utm_source=chatgpt.com))

#             # D3 Drekkana
#             elif nth == 3:
#                 part = int((orig_lon %30)//10)
#                 offsets=[0,4,8]
#                 new_r = (rashi+offsets[part])%12
#                 new_lon = new_r*30 + (orig_lon%30)  # ([shubhamalock.wordpress.com](https://shubhamalock.wordpress.com/2015/09/27/vedic-method-of-calculating-divisional-charts/?utm_source=chatgpt.com))

#             # D4 Chaturthamsa
#             elif nth == 4:
#                 part = int((orig_lon %30)//7.5)
#                 offsets=[0,1,2,3]
#                 new_r = (rashi+offsets[part])%12
#                 new_lon = new_r*30 + (orig_lon%30)  # ([jyotishabharati.com](https://jyotishabharati.com/download/chaturthamsa.pdf?utm_source=chatgpt.com))

#             # D7 Saptamsa
#             elif nth == 7:
#                 part = int((orig_lon %30)//(30/7))
#                 if (rashi+1)%2==1:
#                     new_r = (rashi+part)%12
#                 else:
#                     new_r = (rashi+6+part)%12
#                 new_lon = new_r*30 + (orig_lon%30)  # ([jyotishajournal.com](https://www.jyotishajournal.com/pdf/2023/vol8issue2/PartB/8-2-9-327.pdf?utm_source=chatgpt.com))

#             # All others harmonic
#             else:
#                 new_lon = (orig_lon * nth)%360
#                 new_r   = int(new_lon//30)  # ([en.wikipedia.org](https://en.wikipedia.org/wiki/Varga_%28astrology%29?utm_source=chatgpt.com))

#             raw_mod[key] = {
#                 'lon':      new_lon,
#                 'sign_num': new_r+1,
#                 'retro':    info.get('retro', False)
#             }

#         # swap in raw_mod
#         prev_raw = self._raw
#         self._raw  = raw_mod
#         prev_sys = self.house_system
#         if house_system:
#             self.house_system = house_system.lower()
#         houses = self.compute()
#         # restore
#         self._raw = prev_raw
#         self.house_system = prev_sys
#         return houses

#     # Wrappers
#     def horaChart(self,         sys=None): return self.divisional(2,  sys)
#     def drekkanaChart(self,     sys=None): return self.divisional(3,  sys)
#     def chaturthamshaChart(self,sys=None): return self.divisional(4,  sys)
#     def saptamamshaChart(self,  sys=None): return self.divisional(7,  sys)
#     def navamshaChart(self,     sys=None): return self.divisional(9,  sys)
#     def dashamshaChart(self,    sys=None): return self.divisional(10, sys)
#     def dwadashamshaChart(self, sys=None): return self.divisional(12, sys)
#     def shodashamshaChart(self, sys=None): return self.divisional(16, sys)
#     def vimshamshaChart(self,    sys=None): return self.divisional(20, sys)
#     def chatuvimshamshaChart(self,sys=None):return self.divisional(24, sys)
#     def saptvimshamshaChart(self,sys=None): return self.divisional(27, sys)
#     def trishamshaChart(self,    sys=None): return self.divisional(30, sys)
#     def khavedamshaChart(self,   sys=None): return self.divisional(40, sys)
#     def akshavedamshaChart(self, sys=None): return self.divisional(45, sys)
#     def shashtiamshaChart(self,  sys=None): return self.divisional(60, sys)


"""
astrokundali/astro_chart.py

Defines House and AstroChart for building Lagna (D1) and various divisional charts (D2…D60) with Parāśara methods for D2, D3, D4, D7 and harmonic for all others.
"""
from typing import List, Union
import swisseph as swe
from .astro_data import AstroData
from .houses    import equal_houses, get_house_cusps

class House:
    """
    Represents one of the twelve houses in a Kundali.
    """
    def __init__(self, sign_num: int):
        self.sign_num = sign_num    # Rashi number (1–12)
        self.is_asc   = False       # True if this house is the Ascendant
        self.planets  = {}          # dict: planet_name -> longitude

class AstroChart:
    """
    Builds D1 (Lagna) and divisional Vargas (D2…D60) from sidereal data.

    Implements Parāśara subdivisions for:
      - D2 (Hora): half sign (0°–15°,15°–30°) with odd/even rule ([laurabaratastrologer.com](https://laurabaratastrologer.com/secrets-of-the-hora-chart/?utm_source=chatgpt.com), [astrologyofbharat.org](https://www.astrologyofbharat.org/2020/08/hora-d2-chart-analysis-for-wealth-and.html?utm_source=chatgpt.com))
      - D3 (Drekkana): decans of 10° with offsets [0,4,8] ([shubhamalock.wordpress.com](https://shubhamalock.wordpress.com/2015/09/27/vedic-method-of-calculating-divisional-charts/?utm_source=chatgpt.com))
      - D4 (Chaturthamsa): quarters of 7°30′ with offsets [0,1,2,3] ([jyotishabharati.com](https://jyotishabharati.com/download/chaturthamsa.pdf?utm_source=chatgpt.com))
      - D7 (Saptamsa): septiles with odd/even sign counting ([jyotishajournal.com](https://www.jyotishajournal.com/pdf/2023/vol8issue2/PartB/8-2-9-327.pdf?utm_source=chatgpt.com))

    All other Vargas (D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60) use harmonic formula.
    """
    def __init__(
        self,
        astrodata: AstroData,
        house_system: str = 'equal'
    ):
        self._astrodata   = astrodata
        self.house_system = house_system.lower()
        self._raw         = astrodata.get_rashi_data()

    def compute(self) -> List[House]:
        """
        Compute the D1 (Rāśi) chart.
        """
        raw      = self._raw
        asc_lon  = raw['ascendant']['lon']
        asc_sign = raw['ascendant']['sign_num']

        # 1) House cusps
        if self.house_system == 'equal':
            cusps = equal_houses(asc_lon)
        elif self.house_system == 'whole_sign':
            base = (int(asc_lon) // 30) * 30
            cusps = [(base + 30*i) % 360 for i in range(12)]
        else:
            flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
            _, ascmc = swe.houses_ex(
                self._astrodata.julian_day,
                self._astrodata.lat,
                self._astrodata.lon,
                b'B', flags
            )
            mc = ascmc[1]
            cusps = get_house_cusps(
                self.house_system,
                asc_lon,
                JD=self._astrodata.julian_day,
                lat=self._astrodata.lat,
                lon=self._astrodata.lon,
                mc=mc
            )

        # 2) Build 12 houses
        houses: List[House] = []
        sign_cursor = asc_sign
        for _ in range(12):
            h = House(sign_cursor)
            houses.append(h)
            sign_cursor = 1 if sign_cursor == 12 else sign_cursor + 1
        houses[0].is_asc = True

        # 3) Assign planets
        for pname, info in raw.items():
            if pname == 'ascendant': continue
            lon = info['lon']
            for idx in range(12):
                start = cusps[idx]
                end   = cusps[(idx+1) % 12]
                in_house = (start <= lon < end) if end > start else (lon >= start or lon < start)
                if in_house:
                    houses[idx].planets[pname] = lon
                    break
        return houses

    def divisional(
        self,
        nth: int,
        house_system: Union[str, None] = None
    ) -> List[House]:
        """
        Build D-n Vargas with Parāśara & harmonic formulas,
        then assign planets and signs *directly* to houses
        using inclusive counting (house 1 = Ascendant sign).
        """
        base = self._astrodata.get_rashi_data()
        raw_mod = {}

        # 1) Calculate the *divisional Ascendant* exactly per Parāśara
        orig_asc = base['ascendant']['lon'] % 360
        asc_idx  = base['ascendant']['sign_num'] - 1  # 0–11

        if   nth == 2:  # Hora: odd/even split
            part = int((orig_asc % 30)//15)
            asc_off = 6*part if ((asc_idx+1)%2)==1 else 6*(1-part)
        elif nth == 3:  # Drekkana: decans 10°
            asc_off = [0,4,8][int((orig_asc %30)//10)]
        elif nth == 4:  # Chaturthamsa: quarters 7°30′
            asc_off = [0,1,2,3][int((orig_asc %30)//7.5)]
        elif nth == 7:  # Saptamsa: septiles / odd-even
            part = int((orig_asc %30)//(30/7))
            asc_off = part if ((asc_idx+1)%2)==1 else 6+part
        else:
            asc_off = 0  # harmonic charts keep the natal rāśi Asc

        new_asc_idx = (asc_idx + asc_off) % 12
        raw_mod['ascendant'] = {
            'lon':      new_asc_idx*30 + (orig_asc%30),
            'sign_num': new_asc_idx+1,
            'retro':    False
        }

        # 2) Compute each planet’s divisional longitude & rashi
        for pn, inf in base.items():
            if pn == 'ascendant':
                continue
            lon0  = inf['lon'] % 360
            idx0  = inf['sign_num'] - 1
            # Parāśara subdivisions:
            if   nth == 2:
                part = int((lon0 %30)//15)
                off  = 6*part if ((idx0+1)%2)==1 else 6*(1-part)
                idx_d = (idx0 + off)%12
                lon_d = idx_d*30 + (lon0%30)
            elif nth == 3:
                part = int((lon0%30)//10)
                idx_d = (idx0 + [0,4,8][part])%12
                lon_d = idx_d*30 + (lon0%30)
            elif nth == 4:
                part = int((lon0%30)//7.5)
                idx_d = (idx0 + [0,1,2,3][part])%12
                lon_d = idx_d*30 + (lon0%30)
            elif nth == 7:
                part = int((lon0%30)//(30/7))
                off  = part if ((idx0+1)%2)==1 else 6+part
                idx_d = (idx0 + off)%12
                lon_d = idx_d*30 + (lon0%30)
            else:
                # harmonic formula
                lon_d = (lon0 * nth)%360
                idx_d = int(lon_d//30)
            raw_mod[pn] = {
                'lon':      lon_d,
                'sign_num': idx_d+1,
                'retro':    inf.get('retro', False)
            }

        # 3) Direct sign→inclusive‐house mapping
        asc_sign = raw_mod['ascendant']['sign_num']
        houses = [House(((asc_sign-1 + i)%12)+1) for i in range(12)]
        houses[0].is_asc = True

        for pn, inf in raw_mod.items():
            if pn == 'ascendant':
                continue
            # inclusive difference from Ascendant
            idx = (inf['sign_num'] - asc_sign) % 12
            houses[idx].planets[pn] = inf['lon']

        return houses

    # Convenience wrappers:
    def horaChart(self,          sys=None): return self.divisional(2,  sys)
    def drekkanaChart(self,      sys=None): return self.divisional(3,  sys)
    def chaturthamshaChart(self, sys=None): return self.divisional(4,  sys)
    def saptamamshaChart(self,   sys=None): return self.divisional(7,  sys)
    def navamshaChart(self,      sys=None): return self.divisional(9,  sys)
    def dashamshaChart(self,     sys=None): return self.divisional(10, sys)
    def dwadashamshaChart(self,  sys=None): return self.divisional(12, sys)
    def shodashamshaChart(self,  sys=None): return self.divisional(16, sys)
    def vimshamshaChart(self,     sys=None): return self.divisional(20, sys)
    def chatuvimshamshaChart(self,sys=None): return self.divisional(24, sys)
    def saptvimshamshaChart(self,sys=None): return self.divisional(27, sys)
    def trishamshaChart(self,     sys=None): return self.divisional(30, sys)
    def khavedamshaChart(self,    sys=None): return self.divisional(40, sys)
    def akshavedamshaChart(self,  sys=None): return self.divisional(45, sys)
    def shashtiamshaChart(self,   sys=None): return self.divisional(60, sys)

    # def divisional(self, nth: int, house_system: Union[str, None] = None) -> List[House]:
    #     """
    #     Build D-n Vargas with proper Parāśara ascendant overrides:
    #     - D2 (Hora), D3 (Drekkana), D4 (Chaturthamsa), D7 (Saptamsa) use Parāśara for both ascendant and chart.
    #     - Others (D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60) use harmonic with original ascendant.
    #     Optionally override house_system for this chart.
    #     """
    #     base_raw   = self._astrodata.get_rashi_data()
    #     raw_mod    = {}
    #     orig_asc   = base_raw['ascendant']['lon'] % 360
    #     orig_asc_r = base_raw['ascendant']['sign_num'] - 1  # 0-11

    #     # Determine new ascendant for Parāśara Vargas
    #     if nth == 2:
    #         # Hora: 0-15°,15-30°; odd/even sign rule
    #         part = int((orig_asc % 30) // 15)
    #         if (orig_asc_r+1) % 2 == 1:
    #             asc_offset = 6 * part
    #         else:
    #             asc_offset = 6 * (1 - part)
    #         new_asc_r = (orig_asc_r + asc_offset) % 12
    #         new_asc_lon = new_asc_r * 30 + (orig_asc % 30)
    #     elif nth == 3:
    #         # Drekkana: decans 0-10,10-20,20-30 => offsets [0,4,8]
    #         part = int((orig_asc % 30) // 10)
    #         asc_offset = [0,4,8][part]
    #         new_asc_r = (orig_asc_r + asc_offset) % 12
    #         new_asc_lon = new_asc_r * 30 + (orig_asc % 30)
    #     elif nth == 4:
    #         # Chaturthamsa: quarters 7.5° => offsets [0,1,2,3]
    #         part = int((orig_asc % 30) // 7.5)
    #         asc_offset = [0,1,2,3][part]
    #         new_asc_r = (orig_asc_r + asc_offset) % 12
    #         new_asc_lon = new_asc_r * 30 + (orig_asc % 30)
    #     elif nth == 7:
    #         # Saptamsa: 7 divisions; odd/even rule
    #         part = int((orig_asc % 30) // (30/7))
    #         if (orig_asc_r+1) % 2 == 1:
    #             asc_offset = part
    #         else:
    #             asc_offset = 6 + part
    #         new_asc_r = (orig_asc_r + asc_offset) % 12
    #         new_asc_lon = new_asc_r * 30 + (orig_asc % 30)
    #     else:
    #         # harmonic Vargas keep original ascendant
    #         new_asc_r = orig_asc_r
    #         new_asc_lon = orig_asc

    #     # Assign new ascendant
    #     raw_mod['ascendant'] = {
    #         'lon':      new_asc_lon,
    #         'sign_num': new_asc_r+1,
    #         'retro':    False
    #     }

    #     # Build positions for other bodies
    #     for key, info in base_raw.items():
    #         if key == 'ascendant':
    #             continue
    #         orig_lon = info['lon'] % 360
    #         rashi     = info['sign_num'] - 1
    #         if nth == 2:
    #             # Hora Parāśara
    #             part = int((orig_lon % 30) // 15)
    #             if (rashi+1) % 2 == 1:
    #                 r_offset = 6 * part
    #             else:
    #                 r_offset = 6 * (1 - part)
    #             new_r = (rashi + r_offset) % 12
    #             new_lon = new_r*30 + (orig_lon % 30)
    #         elif nth == 3:
    #             # Drekkana
    #             part = int((orig_lon % 30) // 10)
    #             new_r = (rashi + [0,4,8][part]) % 12
    #             new_lon = new_r*30 + (orig_lon % 30)
    #         elif nth == 4:
    #             # Chaturthamsha
    #             part = int((orig_lon % 30) // 7.5)
    #             new_r = (rashi + [0,1,2,3][part]) % 12
    #             new_lon = new_r*30 + (orig_lon % 30)
    #         elif nth == 7:
    #             # Saptamsa
    #             part = int((orig_lon % 30) // (30/7))
    #             if (rashi+1) % 2 == 1:
    #                 r_offset = part
    #             else:
    #                 r_offset = 6 + part
    #             new_r = (rashi + r_offset) % 12
    #             new_lon = new_r*30 + (orig_lon % 30)
    #         else:
    #             # harmonic
    #             new_lon = (orig_lon * nth) % 360
    #             new_r   = int(new_lon // 30)
    #         raw_mod[key] = {
    #             'lon':      new_lon,
    #             'sign_num': new_r+1,
    #             'retro':    info.get('retro', False)
    #         }

    #     # Swap and compute
    #     prev_raw = self._raw
    #     self._raw = raw_mod
    #     prev_sys = self.house_system
    #     if house_system:
    #         self.house_system = house_system.lower()
    #     houses = self.compute()
    #     self._raw = prev_raw
    #     self.house_system = prev_sys
    #     return houses

    # Wrappers
#     def horaChart(self,          sys=None): return self.divisional(2,  sys)
#     def drekkanaChart(self,      sys=None): return self.divisional(3,  sys)
#     def chaturthamshaChart(self, sys=None): return self.divisional(4,  sys)
#     def saptamamshaChart(self,   sys=None): return self.divisional(7,  sys)
#     def navamshaChart(self,      sys=None): return self.divisional(9,  sys)
#     def dashamshaChart(self,     sys=None): return self.divisional(10, sys)
#     def dwadashamshaChart(self,  sys=None): return self.divisional(12, sys)
#     def shodashamshaChart(self,  sys=None): return self.divisional(16, sys)
#     def vimshamshaChart(self,     sys=None): return self.divisional(20, sys)
#     def chatuvimshamshaChart(self,sys=None): return self.divisional(24, sys)
#     def saptvimshamshaChart(self,sys=None): return self.divisional(27, sys)
#     def trishamshaChart(self,     sys=None): return self.divisional(30, sys)
#     def khavedamshaChart(self,    sys=None): return self.divisional(40, sys)
#     def akshavedamshaChart(self,  sys=None): return self.divisional(45, sys)
#     def shashtiamshaChart(self,   sys=None): return self.divisional(60, sys)

# # End of astro_chart.py modified divisional logic for Parāśara ascendants and inclusive counting
#     def horaChart(self,         sys=None): return self.divisional(2,  sys)
#     def drekkanaChart(self,     sys=None): return self.divisional(3,  sys)
#     def chaturthamshaChart(self,sys=None): return self.divisional(4,  sys)
#     def saptamamshaChart(self,  sys=None): return self.divisional(7,  sys)
#     def navamshaChart(self,     sys=None): return self.divisional(9,  sys)
#     def dashamshaChart(self,    sys=None): return self.divisional(10, sys)
#     def dwadashamshaChart(self, sys=None): return self.divisional(12, sys)
#     def shodashamshaChart(self, sys=None): return self.divisional(16, sys)
#     def vimshamshaChart(self,    sys=None): return self.divisional(20, sys)
#     def chatuvimshamshaChart(self,sys=None):return self.divisional(24, sys)
#     def saptvimshamshaChart(self,sys=None): return self.divisional(27, sys)
#     def trishamshaChart(self,    sys=None): return self.divisional(30, sys)
#     def khavedamshaChart(self,   sys=None): return self.divisional(40, sys)
#     def akshavedamshaChart(self, sys=None): return self.divisional(45, sys)
#     def shashtiamshaChart(self,  sys=None): return self.divisional(60, sys)


# """
# astrokundali/astro_chart.py

# Defines House and AstroChart for building Lagna (D1) and various divisional charts (D2, D3, D9, etc.).
# """
# from typing import List, Union
# import swisseph as swe
# from .astro_data import AstroData
# from .houses import equal_houses, get_house_cusps


# class House:
#     """
#     Represents one of the twelve houses in a Kundali.
#     """
#     def __init__(self, sign_num: int):
#         self.sign_num = sign_num    # Rashi (zodiac sign) number in this house (1–12)
#         self.is_asc   = False       # True if this house is the Ascendant
#         self.planets  = {}          # Mapping: planet_name -> longitude


# class AstroChart:
#     """
#     Builds a Kundali chart (D1 Lagna and divisional Vargas) from sidereal data.
#     """
#     def __init__(
#         self,
#         astrodata: AstroData,
#         house_system: str = 'equal'
#     ):
#         self._astrodata   = astrodata
#         self.house_system = house_system.lower()
#         # Capture raw sidereal positions for ascendant & planets
#         self._raw         = astrodata.get_rashi_data()

#     def compute(self) -> List[House]:
#         """
#         Compute and return 12 House objects for the main D1 (Lagna) chart.

#         Supported house systems:
#           - 'equal'
#           - 'whole_sign'
#           - any Swiss Ephemeris house code via get_house_cusps
#         """
#         raw = self._raw
#         asc_lon  = raw['ascendant']['lon']
#         asc_sign = raw['ascendant']['sign_num']

#         # 1) Determine cusps
#         if self.house_system == 'equal':
#             cusps = equal_houses(asc_lon)
#         elif self.house_system == 'whole_sign':
#             # each sign is one house starting at the ascendant's sign boundary
#             base = (int(asc_lon) // 30) * 30
#             cusps = [(base + 30*i) % 360 for i in range(12)]
#         else:
#             flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
#             _, ascmc = swe.houses_ex(
#                 self._astrodata.julian_day,
#                 self._astrodata.lat,
#                 self._astrodata.lon,
#                 b'B', flags
#             )
#             mc = ascmc[1]
#             cusps = get_house_cusps(
#                 self.house_system,
#                 asc_lon,
#                 JD=self._astrodata.julian_day,
#                 lat=self._astrodata.lat,
#                 lon=self._astrodata.lon,
#                 mc=mc
#             )

#         # 2) Initialize House instances
#         houses: List[House] = []
#         sign_cursor = asc_sign
#         for _ in range(12):
#             h = House(sign_cursor)
#             houses.append(h)
#             sign_cursor = 1 if sign_cursor == 12 else sign_cursor + 1
#         houses[0].is_asc = True

#         # 3) Place planets in houses
#         for pname, info in raw.items():
#             if pname == 'ascendant':
#                 continue
#             lon = info['lon']
#             for idx in range(12):
#                 start = cusps[idx]
#                 end   = cusps[(idx+1) % 12]
#                 in_house = (start <= lon < end) if end > start else (lon >= start or lon < end)
#                 if in_house:
#                     houses[idx].planets[pname] = lon
#                     break

#         return houses

#     def divisional(self, nth: int, house_system: Union[str,None] = None) -> List[House]:
#         """
#         Generic Varga builder: D-n chart where n = 2,3,9,10,12,16,20,24,27,30,40,45,60.

#         Multiplies each planet's longitude by nth, mods by 360, and then casts via compute().
#         Optionally override house_system for that divisional chart.
#         """
#         # 1) Build modified raw
#         base_raw = self._astrodata.get_rashi_data()
#         raw_mod  = {}
#         for key, info in base_raw.items():
#             if key == 'ascendant':
#                 # keep Asc as-is for primary rotating methods
#                 raw_mod[key] = info
#             else:
#                 new_lon = (info['lon'] * nth) % 360
#                 raw_mod[key] = {
#                     'lon':      new_lon,
#                     'sign_num': int(new_lon // 30) + 1,
#                     'retro':    info.get('retro', False)
#                 }
#         # 2) Temporarily swap in the new raw
#         prev_raw = self._raw
#         self._raw = raw_mod
#         # 3) Compute with optionally new house system
#         prev_system = self.house_system
#         if house_system:
#             self.house_system = house_system.lower()
#         houses = self.compute()
#         # 4) Restore
#         self._raw = prev_raw
#         self.house_system = prev_system
#         return houses

#     # Convenience wrappers for common Vargas:
#     def horaChart(self, house_system: Union[str,None] = None) -> List[House]:
#         return self.divisional(2, house_system)

#     def drekkanaChart(self, house_system: Union[str,None] = None) -> List[House]:
#         return self.divisional(3, house_system)

#     def navamshaChart(self, house_system: Union[str,None] = None) -> List[House]:
#         return self.divisional(9, house_system)

#     def dashamshaChart(self, house_system: Union[str,None] = None) -> List[House]:
#         return self.divisional(10, house_system)

#     def dwadashamshaChart(self, house_system: Union[str,None] = None) -> List[House]:
#         return self.divisional(12, house_system)

#     def shodashamshaChart(self, house_system: Union[str,None] = None) -> List[House]:
#         return self.divisional(16, house_system)

#     def vimshamshaChart(self, house_system: Union[str,None] = None) -> List[House]:
#         return self.divisional(20, house_system)

#     def chatuvimshamshaChart(self, house_system: Union[str,None] = None) -> List[House]:
#         return self.divisional(24, house_system)

#     def saptvimshamshaChart(self, house_system: Union[str,None] = None) -> List[House]:
#         return self.divisional(27, house_system)

#     def trishamshaChart(self, house_system: Union[str,None] = None) -> List[House]:
#         return self.divisional(30, house_system)

#     def khavedamshaChart(self, house_system: Union[str,None] = None) -> List[House]:
#         return self.divisional(40, house_system)

#     def akshavedamshaChart(self, house_system: Union[str,None] = None) -> List[House]:
#         return self.divisional(45, house_system)

#     def shashtiamshaChart(self, house_system: Union[str,None] = None) -> List[House]:
#         return self.divisional(60, house_system)


# # astrokundali/astro_chart.py
# from typing import List
# import swisseph as swe
# from .astro_data import AstroData
# from .houses import get_house_cusps

# class House:
#     """
#     Represents one of the twelve houses in a Kundali.
#     """
#     def __init__(self, sign_num: int):
#         self.sign_num    = sign_num
#         self.is_asc      = False
#         self.planets     = {}  # planet_name -> longitude

# class AstroChart:
#     """
#     Builds a North-Indian Lagna chart using pyswisseph data.
#     """
#     def __init__(
#         self,
#         astrodata: AstroData,
#         house_system: str = "equal"
#     ):
#         # Store AstroData instance for raw positions and ephemeris
#         self._astrodata  = astrodata
#         # Raw sidereal positions dict: ascendant + planets
#         self._raw        = astrodata.get_rashi_data()
#         self.house_system = house_system

#     def compute(self) -> List[House]:
#         """
#         Return a list of 12 House objects populated with
#         sidereal planet longitudes and Ascendant flag.
#         """
#         raw = self._raw
#         # Ascendant longitude and sign
#         asc_lon  = raw["ascendant"]["lon"]
#         sign0    = raw["ascendant"]["sign_num"]

#         # Compute MC (Midheaven) via Swiss Ephemeris
#         flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
#         _, ascmc = swe.houses_ex(
#             self._astrodata.julian_day,
#             self._astrodata.lat,
#             self._astrodata.lon,
#             b'B', flags
#         )
#         mc = ascmc[1]

#         # Calculate 12 house cusps
#         cusps = get_house_cusps(
#             self.house_system,
#             asc_lon,
#             JD=self._astrodata.julian_day,
#             lat=self._astrodata.lat,
#             lon=self._astrodata.lon,
#             mc=mc
#         )

#         # Initialize House objects
#         houses: List[House] = []
#         current_sign = sign0
#         for _ in range(12):
#             house = House(current_sign)
#             houses.append(house)
#             current_sign = 1 if current_sign == 12 else current_sign + 1

#         # Mark the first house as Ascendant
#         houses[0].is_asc = True

#         # Assign each body to its house
#         for name, info in raw.items():
#             if name == "ascendant":
#                 continue
#             lon = info["lon"]
#             for i in range(12):
#                 start = cusps[i]
#                 end   = cusps[(i+1) % 12]
#                 # handle wrap-around
#                 in_house = (start <= lon < end) if end > start else (lon >= start or lon < end)
#                 if in_house:
#                     houses[i].planets[name] = lon
#                     break

#         return houses
