from typing import *

import setdoc
from frozendict import frozendict

from .BaseHoldDict import BaseHoldDict
from .DataDict import DataDict
from .HoldObject import HoldObject

__all__ = ["HoldDict"]

Key = TypeVar("Key")
Value = TypeVar("Value")


class HoldDict(HoldObject, DataDict[Key, Value], BaseHoldDict[Key, Value]):
    data: frozendict[Key, Value]
    __slots__ = ()

    @property
    @setdoc.basic
    def data(self: Self) -> frozendict[Key, Value]:
        return self._data

    @data.setter
    def data(self: Self, value: Any) -> None:
        self._data = frozendict[Key, Value](value)
