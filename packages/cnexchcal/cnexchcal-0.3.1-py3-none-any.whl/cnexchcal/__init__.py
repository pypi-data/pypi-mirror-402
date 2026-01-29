from importlib.resources import files   # for external files
from importlib.metadata import version, PackageNotFoundError
import polars as pl
from datetime import date, timedelta

try:
    __version__ = version('cnexchcal')
except PackageNotFoundError:
    __version__ = 'unknown'
    
__doc__ = '''
Exchange Calendars in China mainland
- issession
- nextsession, previoussession
- trade_date_range
- next_nth_tradingday, previous_nth_tradingday
'''

with files('cnexchcal').joinpath('asset', 'festivals.csv').open('rb') as f:
    festivals = pl.read_csv(
        f,
        skip_rows = 2,
        try_parse_dates = True
    )
with files('cnexchcal').joinpath('asset', 'quasi_holidays.csv').open('rb') as f:
    quasiholidays = pl.read_csv(
        f,
        skip_rows = 2,
        try_parse_dates = True
    )
with files('cnexchcal').joinpath('asset', 'weekend_workdays.csv').open('rb') as f:
    weekendworkdays = pl.read_csv(
        f,
        skip_rows = 2,
        try_parse_dates = True
    )
ymin = festivals.get_column('date').dt.year().min()
ymax = festivals.get_column('date').dt.year().max()
dmin = date(ymin, 1, 1)
dmax = date(ymax, 12, 31)

class ExchCal():
    def __init__(self):
        self.holiday_ennames = ("New Year's Day", "Spring Festival", "Tomb-sweeping Day", "Labour Day", "Dragon Boat Festival",
                                "National Day", "Mid-autumn Festival")
        self.holiday_cnnames = ('元旦', '春节', '清明', '劳动节', '端午', '国庆节', '中秋节')
        # 2024-11-12 国务院发布: 自 2025-01-01 起，春节和劳动节各增加1天 
        self.nholidays = {
            'before2025': (1, 3, 1, 1, 1, 3, 1),   # 11 dates total
            'since2025': (1, 4, 1, 2, 1, 3, 1)   # 13 dates total
        }
        self.special_holiday = {'enname': 'Anti-Fascist 70th Day',
                                'cnname': '中国人民抗日战争暨世界反法西斯战争胜利70周年纪念日',
                                'nholidays': 1
                               }   # extra holiday only for exchanges
    def isholiday(self, d: date | str) -> bool:
        '''
        If d is a holiday (legal festival, quasi-holiday, weekends not work)
        **Parameters**
        - d: date or date string with format 'yyyy-mm-dd'
        **Returns**: bool
        **Example**
        from cnexchcal import ExchCal
        cal = ExchCal()
        cal.isholiday('2026-01-02')  # True, extra holiday on Friday
        cal.isholiday('2026-01-04')  # False, Sunday, swap with extra holiday on 2026-01-02 (Friday)
        '''
        if isinstance(d, str):
            d = date.fromisoformat(d)
        assert dmin <= d <= dmax, 'd is out of range'
        res = ((d.weekday() in (5, 6)) and \
               (d not in weekendworkdays.get_column('date'))) or \
              (d in festivals.get_column('date')) or \
              (d in quasiholidays.get_column('date'))
        return res
    def isworkday(self, d: date | str) -> bool:
        '''
        If d is a workday (regular workday and weekend workday)
        **Parameters**
        - d: date or date string with format 'yyyy-mm-dd'
        **Returns**: bool
        **Example**
        from cnexchcal import ExchCal
        cal = ExchCal()
        cal.isworkday('2026-01-04')  # True, Sunday, swap with extra holiday on 2026-01-02 (Friday)
        '''
        return not self.isholiday(d)
    def issession(self, d: date | str) -> bool:
        '''
        If d is a trading date of exchanges in China mainland. On weekend workday, exchanges are closed.
        **Parameters**
        - d: date or date string with format 'yyyy-mm-dd'
        **Returns**: bool
        **Example**
        from cnexchcal import ExchCal
        cal = ExchCal()
        cal.issession('2026-01-04')  # False, Sunday, but is workday
        '''
        if isinstance(d, str):
             d = date.fromisoformat(d)
        assert dmin <= d <= dmax, 'd is out of range'
        closed = (d.weekday() in (5, 6)) or \
                 (d in festivals.get_column('date')) or \
                 (d in quasiholidays.get_column('date')) or \
                 (d == date(2024, 2, 9))   # special holiday
        return not closed        
    def nextsession(self, d: date | str) -> date:
        '''
        Next trading day from a given date d. If d itself is a trading day, return d itself
        **Parameters**
        - d: date or date string with format 'yyyy-mm-dd'
        **Returns**: date
        **Example**
        from cnexchcal import ExchCal
        cal = ExchCal()
        cal.nextsession('2025-12-31')  # 2026-01-05
        '''
        if isinstance(d, str):
             d = date.fromisoformat(d)
        assert dmin <= d <= dmax, 'd is out of range'
        i = 0
        while (dd := d + timedelta(days = i)) < dmax:
            if self.issession(dd):
                return dd
            i += 1
        raise ValueError('next session is out of range')
    def previoussession(self, d: date | str) -> date:
        '''
        Previous trading date. If d itself is a trading day, return d itself
        **Parameters**
        - d: date or date string with format 'yyyy-mm-dd'
        **Returns**: date
        **Example**
        from cnexchcal import ExchCal
        cal = ExchCal()
        cal.previoussession('2026-01-05')  # 2025-12-31
        '''        
        if isinstance(d, str):
            d = date.fromisoformat(d)
        assert dmin <= d <= dmax, 'd is out of range'
        i = 0
        while (dd := d - timedelta(days = i)) > dmin:
            if self.issession(dd):
                return dd
            i += 1
        raise ValueError('previous session is out of range')        
    def trade_date_range(self, d1: date | str, d2: date | str, closed: str = 'both') -> list[date]:
        '''
        all trading days between d1 and d2
        **Parameters**
        - d1, d2: date or date string with format 'yyyy-mm-dd'
        - closed: 'both', 'left' or 'right'
        **Returns**: list of date
        **Example**
        from cnexchcal import ExchCal
        cal = ExchCal()
        cal.trade_date_range('2025-12-29', '2026-01-05', closed = 'left')
        '''        
        if isinstance(d1, str):
            d1 = date.fromisoformat(d1)
        if isinstance(d2, str):
            d2 = date.fromisoformat(d2)
        if d1 > d2:
            d1, d2 = d2, d1
        assert closed.lower() in ('both', 'left', 'right'), 'value of closed can ONLY be one of "both", "left" or "right"'
        if closed == 'left':
            d2 -= timedelta(days = 1)
        elif closed == 'right':
            d1 += timedelta(days = 1)
        assert dmin <= d1 <= dmax, 'd1 is out of range'
        assert dmin <= d2 <= dmax, 'd2 is out of range'
        return [d for d in pl.date_range(d1, d2, eager = True) if self.issession(d)]    
    def next_nth_tradingday(self, d: date | str, n: int) -> date:
        '''
        Next n-th trading day after the given date d. d itself can be a non-trading day
        **Parameters**
        - d: date or date string with format 'yyyy-mm-dd'
        - n: positive integer
        **Returns**: date
        **Example**
        from cnexchcal import ExchCal
        cal = ExchCal()
        cal.next_nth_tradingday('2025-12-31', 3)
        '''
        if isinstance(d, str):
            d = date.fromisoformat(d)
        i, j = 0, 1
        while i < n:
            dd = d + timedelta(days = j)
            if self.issession(dd):
                i += 1
            j += 1
        return (d + timedelta(days = j - 1))
    def previous_nth_tradingday(self, d: date | str, n: int) -> date:
        '''
        Previous n-th trading day before the given date d. d itself can be a non-trading day
        **Parameters**
        - d: date or date string with format 'yyyy-mm-dd'
        - n: positive integer
        **Returns**: date
        **Example**
        from cnexchcal import ExchCal
        cal = ExchCal()
        cal.previous_nth_tradingday('2026-01-05', 3)
        '''
        if isinstance(d, str):
            d = date.fromisoformat(d)
        i, j = 0, 1
        while i < n:
            dd = d - timedelta(days = j)
            if self.issession(dd):
                i += 1
            j += 1
        return (d - timedelta(days = j - 1))
    def ntradedays(self, yr: int) -> int:
        '''
        Number of trading days in a given year
        **Parameters**
        - yr: int
        **Returns**: int
        **Example**
        from cnexchcal import ExchCal
        cal = ExchCal()
        cal.ntradedays(2025)
        '''
        assert ymin <= yr <= ymax, 'year is out of range'
        d1 = date(yr, 1, 1)
        d2 = date(yr, 12, 31)
        return len(self.trade_date_range(d1, d2))
