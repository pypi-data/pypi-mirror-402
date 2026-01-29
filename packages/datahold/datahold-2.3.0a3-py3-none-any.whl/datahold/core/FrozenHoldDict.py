from typing import *

import setdoc
from frozendict import frozendict

from .BaseHoldDict import BaseHoldDict
from .FrozenDataDict import FrozenDataDict
from .FrozenHoldObject import FrozenHoldObject

__all__ = ["FrozenHoldDict"]

Key = TypeVar("Key")
Value = TypeVar("Value")


class FrozenHoldDict(FrozenHoldObject, FrozenDataDict, BaseHoldDict[Key, Value]):
    data: frozendict[Key, Value]
    __slots__ = ()

    @setdoc.basic
    def __init__(self: Self, data: Any, /, **kwargs: Any) -> None:
        self._data = frozendict[Key, Value](data, **kwargs)
