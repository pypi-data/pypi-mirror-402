from __future__ import annotations
from functools import wraps
from typing import Callable, ParamSpec, TypeVar
from minfx.neptune_v2.common.warnings import warn_once
from minfx.neptune_v2.exceptions import NeptuneParametersCollision
__all__ = ['deprecated', 'deprecated_parameter']
P = ParamSpec('P')
R = TypeVar('R')

def deprecated(*, alternative=None):

    def deco(func):

        @wraps(func)
        def inner(*args, **kwargs):
            additional_info = f', use `{alternative}` instead' if alternative else ' and will be removed'
            warn_once(message=f"`{func.__name__}` is deprecated{additional_info}. We'll end support of it in next major release.")
            return func(*args, **kwargs)
        return inner
    return deco

def deprecated_parameter(*, deprecated_kwarg_name, required_kwarg_name):

    def deco(f):

        @wraps(f)
        def inner(*args, **kwargs):
            if deprecated_kwarg_name in kwargs:
                if required_kwarg_name in kwargs:
                    raise NeptuneParametersCollision(required_kwarg_name, deprecated_kwarg_name, method_name=f.__name__)
                warn_once(message=f"Parameter `{deprecated_kwarg_name}` is deprecated, use `{required_kwarg_name}` instead. We'll end support of it in next major release.")
                kwargs[required_kwarg_name] = kwargs[deprecated_kwarg_name]
                del kwargs[deprecated_kwarg_name]
            return f(*args, **kwargs)
        return inner
    return deco

def model_registry_deprecation(func):

    @wraps(func)
    def inner(*args, **kwargs):
        warn_once("Neptune's model registry has been deprecated and will be removed in a future release.Use runs to store model metadata instead. For more, see https://docs-legacy.neptune.ai/model_registry/.If you are already using the model registry, you can migrate existing metadata to runs.Learn how: https://docs-legacy.neptune.ai/model_registry/migrate_to_runs/.")
        return func(*args, **kwargs)
    return inner