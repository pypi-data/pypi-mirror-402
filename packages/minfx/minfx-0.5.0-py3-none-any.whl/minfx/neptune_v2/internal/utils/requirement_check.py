from __future__ import annotations
__all__ = ['is_installed', 'require_installed']
from functools import lru_cache
from importlib.util import find_spec
from minfx.neptune_v2.exceptions import NeptuneMissingRequirementException

@lru_cache(maxsize=32)
def is_installed(requirement_name):
    return find_spec(requirement_name) is not None

def require_installed(requirement_name, *, suggestion=None):
    if is_installed(requirement_name):
        return
    raise NeptuneMissingRequirementException(requirement_name, suggestion)