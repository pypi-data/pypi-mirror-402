import sys
import argparse
from .astro_data  import AstroData
from .astro_chart import AstroChart
from .plotter     import plot_kundali, houses_to_json

def main(argv=None):
    p = argparse.ArgumentParser(
        prog="astrokundali",
        description="Generate & plot a North-Indian Kundali"
    )
    # Birth details
    p.add_argument("--year",  type=int, required=True)
    p.add_argument("--month", type=int, required=True)
    p.add_argument("--day",   type=int, required=True)
    p.add_argument("--hour",  type=int, required=True)
    p.add_argument("--minute",type=int, required=True)
    p.add_argument("--second",type=int, required=True)
    # UTC offset
    p.add_argument("--utc-h", type=int, default=0)
    p.add_argument("--utc-m", type=int, default=0)
    # Location
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    # Ayanamsa
    p.add_argument(
        "--ayanamsa",
        choices=list(AYANAMSA.keys()),
        default="lahiri"
    )
    # House system
    p.add_argument(
        "--house-system",
        choices=list(HOUSE_SYSTEMS.keys()),
        default="equal"
    )

    args = p.parse_args(argv)

    raw = AstroData(
        args.year, args.month, args.day,
        args.hour, args.minute, args.second,
        args.utc_h, args.utc_m,
        args.lat, args.lon,
        ayanamsa=args.ayanamsa
    ).get_rashi_data()

    chart = AstroChart(raw, house_system=args.house_system)
    houses = chart.build()

    plot_kundali(houses)
    print(houses_to_json(houses))

if __name__ == "__main__":
    sys.exit(main())
