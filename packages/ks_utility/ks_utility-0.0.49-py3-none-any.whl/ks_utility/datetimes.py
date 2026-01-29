from datetime import datetime
import string
from dateutil.parser import parse
import pytz

DATE_FMT = '%Y-%m-%d'
DATETIME_FMT = DATE_FMT + ' %H:%M:%S.%f' + '%z'

def dt_to_str(time: datetime = None, tpl=DATETIME_FMT):
    if not time:
        time = now()
        
    if isinstance(time, datetime):
        return time.strftime(tpl)
    elif isinstance(time, str):
        return parse(time).strftime(tpl)
    else:
        return time

#dt_str = dt_to_mq(datetime.now())
#dt_str = dt_to_mq('2022-04-14')

def get_date_str(time: datetime = None):
    return dt_to_str(time, DATE_FMT)

def get_tz(tz_str: str=''):
    # 兼容直接传入pytz类型
    if not isinstance(tz_str, str):
        return tz_str
        
    return pytz.timezone(tz_str or 'PRC')

def now(tz=None):
    if not tz:
        tz = get_tz()
    return datetime.now(tz)

def get_utcoffset(dt=None, tz=None):
    if not dt:
        dt = now()
    if tz:
        dt = dt.astimezone(tz)
    zstr = dt.strftime('%z')
    return int(zstr[:3])

# 获取时间对应的取整时间戳
def get_ts_int(dt=None, interval=60):
    if not dt:
        dt = now()
    
    ts = dt.timestamp()

    
    ts_int = int(ts / interval) * interval 

    # 由于时间戳是针对utc时间，所以跨日取整需要调整为相应时区的时间戳，即减去offset的秒数
    if interval >= 86400:
        offset = get_utcoffset(dt)
        ts_int -= offset * 3600
    
    return ts_int

def get_dt_int(dt=None, interval=60, tz: str = 'PRC'):
    ts_int = get_ts_int(dt=dt, interval=interval)
    return from_timestamp(ts=ts_int, tz=tz)

def from_timestamp(ts: int, tz: str = 'PRC'):
    return datetime.fromtimestamp(ts, tz=get_tz(tz))
