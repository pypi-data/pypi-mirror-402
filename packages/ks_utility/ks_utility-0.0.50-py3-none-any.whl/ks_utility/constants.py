from enum import Enum

class RetCode(Enum):
    OK = 'OK'
    ERROR = 'ERROR'
    ASYNC = 'ASYNC'

RET_OK = RetCode.OK
RET_ERROR = RetCode.ERROR
RET_ASYNC = RetCode.ASYNC

class Environment(Enum):
    REAL = 'REAL'
    TEST = 'TEST'