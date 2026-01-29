from decimal import Decimal
from math import floor, ceil

def to_decimal(value) -> Decimal:
    return Decimal(str(value))

def round_to(value: float, target: float) -> float:
    """
    Round price to price tick value.
    """
    value: Decimal = Decimal(str(value))
    target: Decimal = Decimal(str(target))
    rounded: Decimal = Decimal(str(int(round(value / target)) * target))
    return rounded


def floor_to(value: float, target: float) -> float:
    """
    Similar to math.floor function, but to target float number.
    """
    value: Decimal = Decimal(str(value))
    target: Decimal = Decimal(str(target))
    result: Decimal = Decimal(str(int(floor(value / target)) * target))
    return result


def ceil_to(value: float, target: float) -> float:
    """
    Similar to math.ceil function, but to target float number.
    """
    value: Decimal = Decimal(str(value))
    target: Decimal = Decimal(str(target))
    result: Decimal = Decimal(str(int(ceil(value / target)) * target))
    return result