from decimal import Decimal
from enum import Enum
from datetime import datetime
from typing import Optional
import json

from .datetimes import DATETIME_FMT

# 自定义的序列化函数
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return str(obj)  # 或者 str(obj) 如果你想将Decimal转换为字符串
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, datetime):
        return obj.strftime(DATETIME_FMT)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def json_dumps(data, cls: Optional[json.JSONEncoder] = None):
    return json.dumps(
        data,
        indent=4,
        ensure_ascii=False,
        default=decimal_default,
        cls=cls
    )

def json_loads(json_str: str):
    try:
        json_obj = json.loads(json_str)
    except:
        json_obj = {}
    return json_obj

def json_load(fp: str):
    try:
        json_obj = json.load(fp)
    except:
        json_obj = {}
    return json_obj