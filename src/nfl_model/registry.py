## `src/nfl_model/registry.py`

from __future__ import annotations
from typing import Callable, Dict

_FACTOR_REGISTRY: Dict[str, Callable] = {}

def register_factor(name: str):
    def _wrap(cls):
        _FACTOR_REGISTRY[name] = cls
        return cls
    return _wrap

def get_factor(name: str):
    try:
        return _FACTOR_REGISTRY[name]
    except KeyError:
        raise KeyError(f"Factor '{name}' not found. Registered: {list(_FACTOR_REGISTRY)}")
