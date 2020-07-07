from datetime import date
import dateutil.easter
from dateutil.relativedelta import relativedelta, SA as Saturday

from typing import Tuple


names = ['Alfa', 'Beta', 'Gamma', 'Delta', 'Epsilon']

name_order_filename = 'names.txt'


def week_from_date(date):
    _, week, _ = date.isocalendar()
    return week

def holiday_weeks(year: int) -> Tuple[int, int]:
    """
    Palauttaa pääsiäis- ja juhannusviikkojen numerot pyydetylle vuodelle.
    
        >>> holiday_weeks(year=2020)
        (15, 25)
        >>> holiday_weeks(year=2025)
        (16, 25)
    """
    easter_week = week_from_date(dateutil.easter.easter(year))
    midsummer_week = week_from_date(date(year, 6, 20) + relativedelta(weekday=Saturday))

    return easter_week, midsummer_week
    
def weeks_per_year(year):
    """
    >>> weeks_per_year(2020)
    53
    >>> weeks_per_year(2021)
    52
    """
    return week_from_date(date(year, 12, 31))

def pick_midsummer_turn(all_names, already_had):
    return random.choice(all_names, already_had)

def distribute_weeks(year):
    ...


