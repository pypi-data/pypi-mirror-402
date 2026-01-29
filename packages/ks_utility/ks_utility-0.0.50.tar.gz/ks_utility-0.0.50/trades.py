import math
import exchange_calendars as ec
import pytz
import datetime
from decimal import Decimal
import pandas as pd

# def handify(volume, base=100):
#     return math.floor(volume/base)*base

# class Calendar():
#     def __init__(self, exchange='XSHG') -> None:
#         self.calendar = ec.get_calendar(exchange)

#     def net_close(self):
#         return self.calendar.next_open(minute=datetime.now()).astimezone(pytz.timezone('PRC'))

# # 是否20cm
# def is_plus(code):
#     return code.startswith('68') or code.startswith('30')

# def get_upper_limit(code, pre_close):
#     rate = 0.2 if is_plus(code) else 0.1
#     return float(round(Decimal(pre_close) * Decimal((1 + rate)), 2))

# def append_suffix(code):
# 	if code.endswith('.SH') or code.endswith('.SZ'):
# 		return code
		
# 	suffix_map = {
# 		'11': '.SH',
# 		'12': '.SZ',
# 		'15': '.SZ',
# 		'51': '.SH',
# 		'56': '.SH',
# 		'58': '.SH',
# 		'00': '.SZ',
# 		'30': '.SZ',
# 		'43': '.BJ',
# 		'60': '.SH',
# 		'68': '.SH',
# 		'83': '.BJ',
# 		'87': '.BJ'
# 	}
# 	return f'{code}{suffix_map[code[0:2]]}'

# 将日线合成周线
def trans_period(bars, p='w'):
    if not len(bars):
        return pd.DataFrame()
    trans_bars = pd.DataFrame()
    day_bars_by_eob = bars.set_index('eob', drop=False)
    trans_bars['open'] = day_bars_by_eob.resample(p).first().to_period(p)['open']
    trans_bars['high'] = day_bars_by_eob.resample(p).max().to_period(p)['high']
    trans_bars['low'] = day_bars_by_eob.resample(p).min().to_period(p)['low']
    trans_bars['close'] = day_bars_by_eob.resample(p).last().to_period(p)['close']
    if 'volume' in day_bars_by_eob:
        trans_bars['volume'] = day_bars_by_eob.resample(p).sum().to_period(p)['volume']
    if 'money' in day_bars_by_eob:
        trans_bars['money'] = day_bars_by_eob.resample(p).sum().to_period(p)['money']
    trans_bars['eob'] = day_bars_by_eob.resample(p).last().to_period(p)['eob']
    trans_bars['symbol'] = day_bars_by_eob.symbol.iloc[0]

    trans_bars = trans_bars.dropna()
    trans_bars = trans_bars[['symbol', 'eob', 'open', 'high', 'low', 'close']]
    trans_bars.reset_index(drop=True, inplace=True)
    return trans_bars

def round_to(value: float, target: float) -> float:
	"""
	Round price to price tick value.
	"""
	value: Decimal = Decimal(str(value))
	target: Decimal = Decimal(str(target))
	rounded: float = float(int(round(value / target)) * target)
	return rounded
