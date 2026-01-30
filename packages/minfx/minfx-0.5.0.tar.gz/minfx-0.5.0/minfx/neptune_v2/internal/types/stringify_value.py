__all__ = ['StringifyValue', 'extract_if_stringify_value']
import math
from minfx.neptune_v2.constants import MAX_32_BIT_INT, MIN_32_BIT_INT
from minfx.neptune_v2.internal.utils.logger import get_logger
logger = get_logger()

def is_unsupported_float(value):
    if isinstance(value, float):
        return math.isinf(value) or math.isnan(value)
    return False

class StringifyValue:

    def __init__(self, value):
        if isinstance(value, int) and (value > MAX_32_BIT_INT or value < MIN_32_BIT_INT):
            logger.info("Value '%d' is outside the range of 32-bit integers ('%d' to '%d') and will be logged as float", value, MIN_32_BIT_INT, MAX_32_BIT_INT)
            value = float(value)
        if is_unsupported_float(value):
            value = str(value)
        self.__value = value

    @property
    def value(self):
        return self.__value

    def __str__(self):
        return str(self.__value)

    def __repr__(self):
        return repr(self.__value)

def extract_if_stringify_value(val):
    if isinstance(val, StringifyValue):
        return val.value
    return val