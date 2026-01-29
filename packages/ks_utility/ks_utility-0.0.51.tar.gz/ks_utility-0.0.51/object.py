from dataclasses import dataclass, field, asdict
from typing import Optional
from ks_utility.jsons import json_dumps

@dataclass
class BaseData:
    """
    Any data object needs a gateway_name as source
    and should inherit base data.
    """

    gateway_name: str = ''

    extra: dict = field(default=None, init=False)

    def json(self) -> str:
        return json_dumps(self.dict())
    
    def dict(self) -> dict:
        return asdict(self)

@dataclass
class ErrorData(BaseData):
    """
    Tick data contains information about:
        * last trade in market
        * orderbook snapshot
        * intraday market statistics.
    """

    code: Optional[str] = None
    msg: Optional[str] = None
    method: Optional[str] = None
    args: Optional[str] = None
    kvargs: Optional[dict] = None
    traceback: Optional[str] = None

class BaseException(Exception):
    def _to_str(self):
        return f'message={self.message};code={self.code};data={self.data}'

    def __str__(self):
        return self._to_str()

    def __repr__(self):
        return self._to_str()
    
    def __init__(
            self,
            message: str = '',
            code: str = None,
            data: dict = {}
        ):
        self.code = code
        self.message = message
        self.data = data
