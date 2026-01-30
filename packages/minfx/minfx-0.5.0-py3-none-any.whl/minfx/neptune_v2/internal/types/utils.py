__all__ = ['is_unsupported_float']
import math

def is_unsupported_float(value):
    if isinstance(value, float):
        return math.isinf(value) or math.isnan(value)
    return False