from typing import *

import setdoc
from frozendict import frozendict

from datahold.core.HoldDict import HoldDict
from datahold.core.OkayObject import OkayObject

__all__ = ["OkayDict"]


Key = TypeVar("Key")
Value = TypeVar("Value")


class OkayDict(OkayObject, HoldDict[Key, Value]):

    data: frozendict[Key, Value]
    __slots__ = ()

    @setdoc.basic
    def __or__(self: Self, other: Any, /) -> Self:
        return type(self)(self._data | dict(other))
