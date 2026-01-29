from datetime import datetime

class DateConverter:
    """
    Convert UTC calendar date+time to Julian Day.
    """
    def __init__(self, dateinfo):
        self._d = dateinfo

    def to_julian_day(self) -> float:
        dt = datetime(self._d.year, self._d.month, self._d.day,
                      self._d.hour, self._d.minute, self._d.second)
        epoch_jd = 2440587.5  # Unix epoch → JD
        secs_per_day = 86400
        offset = (self._d.utc_offset_hours * 3600 +
                  self._d.utc_offset_minutes * 60)
        return (
            epoch_jd
            + (dt - datetime(1970,1,1)).total_seconds() / secs_per_day
            - offset / secs_per_day
        )
