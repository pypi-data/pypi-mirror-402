from __future__ import annotations
__all__ = ['QualifiedName', 'SysId', 'UniqueId', 'conform_optional']
from typing import Callable, NewType, TypeVar
UniqueId = NewType('UniqueId', str)
SysId = NewType('SysId', str)
QualifiedName = NewType('QualifiedName', str)
T = TypeVar('T')

def conform_optional(value, cls):
    return cls(value) if value is not None else None